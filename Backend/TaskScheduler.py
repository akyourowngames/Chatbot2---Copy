"""
Task Scheduler - Reminders and Scheduled Tasks
===============================================
Schedule one-time and recurring tasks for KAI
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional
import json
import os
from dataclasses import dataclass, asdict
import re

@dataclass
class ScheduledTask:
    id: str
    name: str
    action: str  # Command to execute
    scheduled_time: datetime
    recurring: bool = False
    interval_minutes: int = 0  # For recurring tasks
    enabled: bool = True
    last_run: datetime = None
    
    def to_dict(self):
        d = asdict(self)
        d['scheduled_time'] = self.scheduled_time.isoformat()
        d['last_run'] = self.last_run.isoformat() if self.last_run else None
        return d
    
    @classmethod
    def from_dict(cls, d):
        d['scheduled_time'] = datetime.fromisoformat(d['scheduled_time'])
        d['last_run'] = datetime.fromisoformat(d['last_run']) if d['last_run'] else None
        return cls(**d)


class TaskScheduler:
    """
    Schedule reminders and recurring tasks.
    Examples:
    - "Remind me to take a break in 30 minutes"
    - "Remind me every 2 hours to drink water"
    - "Schedule daily standup at 9 AM"
    """
    
    def __init__(self, callback: Callable = None):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.callback = callback  # Called when task triggers
        self.is_running = False
        self.scheduler_thread = None
        self.data_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "Data", "scheduled_tasks.json"
        )
        
        # Load saved tasks
        self._load_tasks()
    
    def start(self):
        """Start the scheduler thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("[SCHEDULER] Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        print("[SCHEDULER] Task scheduler stopped")
    
    def add_reminder(self, text: str, minutes: int = None, at_time: str = None) -> Dict[str, Any]:
        """
        Add a one-time reminder.
        
        Args:
            text: Reminder text
            minutes: Minutes from now
            at_time: Specific time like "9:00 AM" or "14:30"
        """
        task_id = f"reminder_{int(time.time())}"
        
        if minutes:
            scheduled_time = datetime.now() + timedelta(minutes=minutes)
        elif at_time:
            scheduled_time = self._parse_time(at_time)
        else:
            return {"status": "error", "message": "Specify minutes or time"}
        
        task = ScheduledTask(
            id=task_id,
            name=text,
            action=f"reminder:{text}",
            scheduled_time=scheduled_time,
            recurring=False
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        time_str = scheduled_time.strftime("%I:%M %p")
        return {
            "status": "success",
            "message": f"⏰ Reminder set for {time_str}: {text}",
            "id": task_id,
            "time": time_str
        }
    
    def add_recurring(self, text: str, interval_minutes: int, start_now: bool = False) -> Dict[str, Any]:
        """
        Add a recurring reminder.
        
        Args:
            text: Reminder text
            interval_minutes: Interval in minutes
            start_now: If True, first run is now; else after interval
        """
        task_id = f"recurring_{int(time.time())}"
        
        if start_now:
            scheduled_time = datetime.now()
        else:
            scheduled_time = datetime.now() + timedelta(minutes=interval_minutes)
        
        task = ScheduledTask(
            id=task_id,
            name=text,
            action=f"reminder:{text}",
            scheduled_time=scheduled_time,
            recurring=True,
            interval_minutes=interval_minutes
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        return {
            "status": "success",
            "message": f"🔁 Recurring reminder set every {interval_minutes} minutes: {text}",
            "id": task_id,
            "interval": interval_minutes
        }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            return {"status": "success", "message": f"Cancelled task: {task_id}"}
        return {"status": "error", "message": f"Task not found: {task_id}"}
    
    def list_tasks(self) -> Dict[str, Any]:
        """List all scheduled tasks"""
        task_list = []
        for task in self.tasks.values():
            task_list.append({
                "id": task.id,
                "name": task.name,
                "time": task.scheduled_time.strftime("%I:%M %p"),
                "recurring": task.recurring,
                "interval": task.interval_minutes if task.recurring else None
            })
        
        return {
            "status": "success",
            "count": len(task_list),
            "tasks": task_list
        }
    
    def parse_natural_language(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language reminder requests.
        Examples:
        - "remind me to take a break in 30 minutes"
        - "remind me every 2 hours to drink water"
        - "set alarm for 9 AM"
        """
        query_lower = query.lower()
        
        # Extract the reminder text
        reminder_text = query
        for remove in ["remind me to", "remind me", "set reminder", "set alarm", "alarm", "reminder"]:
            reminder_text = reminder_text.lower().replace(remove, "").strip()
        
        # Check for recurring pattern
        recurring_match = re.search(r"every\s+(\d+)\s*(hour|minute|min|hr)s?", query_lower)
        if recurring_match:
            amount = int(recurring_match.group(1))
            unit = recurring_match.group(2)
            
            if "hour" in unit or "hr" in unit:
                minutes = amount * 60
            else:
                minutes = amount
            
            # Clean reminder text
            reminder_text = re.sub(r"every\s+\d+\s*(hour|minute|min|hr)s?", "", reminder_text).strip()
            reminder_text = re.sub(r"^to\s+", "", reminder_text).strip()
            
            return self.add_recurring(reminder_text or "Reminder", minutes)
        
        # Check for "in X minutes/hours"
        in_time_match = re.search(r"in\s+(\d+)\s*(hour|minute|min|hr)s?", query_lower)
        if in_time_match:
            amount = int(in_time_match.group(1))
            unit = in_time_match.group(2)
            
            if "hour" in unit or "hr" in unit:
                minutes = amount * 60
            else:
                minutes = amount
            
            # Clean reminder text
            reminder_text = re.sub(r"in\s+\d+\s*(hour|minute|min|hr)s?", "", reminder_text).strip()
            reminder_text = re.sub(r"^to\s+", "", reminder_text).strip()
            
            return self.add_reminder(reminder_text or "Reminder", minutes=minutes)
        
        # Check for specific time
        time_match = re.search(r"(?:at|for)\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?", query_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            
            scheduled_time = datetime.now().replace(hour=hour, minute=minute, second=0)
            if scheduled_time < datetime.now():
                scheduled_time += timedelta(days=1)
            
            # Clean reminder text
            reminder_text = re.sub(r"(?:at|for)\s+\d{1,2}:?\d{0,2}\s*(am|pm)?", "", reminder_text).strip()
            reminder_text = re.sub(r"^to\s+", "", reminder_text).strip()
            
            return self.add_reminder(
                reminder_text or "Reminder", 
                minutes=int((scheduled_time - datetime.now()).total_seconds() / 60)
            )
        
        return {"status": "error", "message": "Could not parse reminder. Try: 'remind me in 30 minutes to...'"}
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime"""
        now = datetime.now()
        
        # Try common formats
        for fmt in ["%I:%M %p", "%H:%M", "%I %p", "%I:%M%p"]:
            try:
                parsed = datetime.strptime(time_str.strip(), fmt)
                result = now.replace(hour=parsed.hour, minute=parsed.minute, second=0)
                if result < now:
                    result += timedelta(days=1)
                return result
            except ValueError:
                continue
        
        return now + timedelta(hours=1)  # Default: 1 hour from now
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            now = datetime.now()
            
            for task_id, task in list(self.tasks.items()):
                if not task.enabled:
                    continue
                
                if now >= task.scheduled_time:
                    # Task is due!
                    print(f"[SCHEDULER] Task triggered: {task.name}")
                    
                    if self.callback:
                        self.callback(task)
                    
                    if task.recurring:
                        # Reschedule
                        task.scheduled_time = now + timedelta(minutes=task.interval_minutes)
                        task.last_run = now
                    else:
                        # One-time, remove it
                        del self.tasks[task_id]
                    
                    self._save_tasks()
            
            time.sleep(10)  # Check every 10 seconds
    
    def _save_tasks(self):
        """Save tasks to file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                data = {tid: t.to_dict() for tid, t in self.tasks.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SCHEDULER] Save error: {e}")
    
    def _load_tasks(self):
        """Load tasks from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for tid, tdata in data.items():
                        self.tasks[tid] = ScheduledTask.from_dict(tdata)
                print(f"[SCHEDULER] Loaded {len(self.tasks)} scheduled tasks")
        except Exception as e:
            print(f"[SCHEDULER] Load error: {e}")


# Global instance
task_scheduler = TaskScheduler()


if __name__ == "__main__":
    def on_task(task):
        print(f"[TEST] Task triggered: {task.name}")
    
    task_scheduler.callback = on_task
    task_scheduler.start()
    
    # Test
    result = task_scheduler.parse_natural_language("remind me in 1 minute to test")
    print(result)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        task_scheduler.stop()
