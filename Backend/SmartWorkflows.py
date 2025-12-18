"""
Smart Workflows - Pre-defined Automation Routines
=================================================
Unique feature: One command triggers multiple coordinated actions
This differentiates KAI from web-based AI assistants
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Pre-defined workflow templates
SMART_WORKFLOWS = {
    "morning_routine": {
        "name": "Morning Routine",
        "description": "Start your day: email, calendar, news, and energizing music",
        "steps": [
            {"action": "speak", "text": "Good morning! Let me set up your day."},
            {"action": "open_app", "target": "chrome"},
            {"action": "wait", "seconds": 2},
            {"action": "open_url", "url": "https://mail.google.com"},
            {"action": "open_url", "url": "https://calendar.google.com"},
            {"action": "play_music", "query": "morning energy playlist"},
            {"action": "speak", "text": "Your morning setup is ready!"}
        ]
    },
    
    "work_mode": {
        "name": "Work Mode",
        "description": "Focus environment: code editor, browser, low volume",
        "steps": [
            {"action": "speak", "text": "Activating work mode."},
            {"action": "close_distractions"},
            {"action": "open_app", "target": "code"},
            {"action": "open_app", "target": "chrome"},
            {"action": "set_volume", "level": 30},
            {"action": "speak", "text": "Work environment ready. Stay focused!"}
        ]
    },
    
    "gaming_mode": {
        "name": "Gaming Mode", 
        "description": "Close work apps, open Discord, max volume",
        "steps": [
            {"action": "speak", "text": "Game time! Setting up gaming mode."},
            {"action": "close_app", "target": "code"},
            {"action": "close_app", "target": "slack"},
            {"action": "open_app", "target": "discord"},
            {"action": "set_volume", "level": 80},
            {"action": "speak", "text": "Gaming mode activated. Have fun!"}
        ]
    },
    
    "focus_mode": {
        "name": "Focus Mode",
        "description": "Minimize distractions, mute notifications",
        "steps": [
            {"action": "speak", "text": "Entering focus mode. No distractions."},
            {"action": "close_distractions"},
            {"action": "minimize_all"},
            {"action": "set_volume", "level": 0},
            {"action": "play_music", "query": "lo-fi focus beats"},
            {"action": "set_volume", "level": 20},
            {"action": "speak", "text": "Focus mode active. Deep work time."}
        ]
    },
    
    "presentation_mode": {
        "name": "Presentation Mode",
        "description": "Clean desktop, full brightness, mute sounds",
        "steps": [
            {"action": "speak", "text": "Setting up for presentation."},
            {"action": "minimize_all"},
            {"action": "set_brightness", "level": 100},
            {"action": "set_volume", "level": 50},
            {"action": "speak", "text": "Ready for your presentation!"}
        ]
    },
    
    "break_time": {
        "name": "Break Time",
        "description": "Lock screen, play relaxing music for 5 minutes",
        "steps": [
            {"action": "speak", "text": "Time for a break! Relax for 5 minutes."},
            {"action": "play_music", "query": "relaxing nature sounds"},
            {"action": "set_volume", "level": 40}
        ]
    },
    
    "night_mode": {
        "name": "Night Mode",
        "description": "Dim brightness, close apps, prepare for shutdown",
        "steps": [
            {"action": "speak", "text": "Winding down for the night."},
            {"action": "set_brightness", "level": 30},
            {"action": "stop_music"},
            {"action": "close_all_browsers"},
            {"action": "speak", "text": "Good night! Sweet dreams."}
        ]
    },
    
    "research_mode": {
        "name": "Research Mode",
        "description": "Multiple browser tabs for research",
        "steps": [
            {"action": "speak", "text": "Setting up research environment."},
            {"action": "open_app", "target": "chrome"},
            {"action": "open_url", "url": "https://scholar.google.com"},
            {"action": "open_url", "url": "https://wikipedia.org"},
            {"action": "open_app", "target": "notepad"},
            {"action": "speak", "text": "Research mode ready. Happy learning!"}
        ]
    }
}


class SmartWorkflows:
    """Execute pre-defined multi-step automation workflows"""
    
    def __init__(self):
        self.workflows = SMART_WORKFLOWS
        self.running_workflow = None
        self.should_stop = False
        
    def list_workflows(self) -> List[Dict[str, str]]:
        """List all available workflows"""
        return [
            {"name": wf["name"], "description": wf["description"], "command": key}
            for key, wf in self.workflows.items()
        ]
    
    def get_workflow_names(self) -> List[str]:
        """Get just the workflow command names"""
        return list(self.workflows.keys())
    
    def find_workflow(self, query: str) -> Optional[str]:
        """Find workflow by fuzzy matching"""
        query_lower = query.lower().replace("_", " ").replace("-", " ")
        
        # Direct match
        for key in self.workflows:
            if key.replace("_", " ") in query_lower:
                return key
        
        # Keyword matching
        keywords = {
            "morning_routine": ["morning", "wake up", "start day", "good morning"],
            "work_mode": ["work", "office", "productive", "coding"],
            "gaming_mode": ["game", "gaming", "play games"],
            "focus_mode": ["focus", "concentrate", "no distractions", "deep work"],
            "presentation_mode": ["present", "presentation", "meeting", "demo"],
            "break_time": ["break", "rest", "pause", "relax"],
            "night_mode": ["night", "sleep", "bedtime", "end day"],
            "research_mode": ["research", "study", "learn", "investigate"]
        }
        
        for workflow_key, kws in keywords.items():
            if any(kw in query_lower for kw in kws):
                return workflow_key
        
        return None
    
    async def execute_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Execute a workflow by name"""
        if workflow_name not in self.workflows:
            # Try to find by fuzzy match
            found = self.find_workflow(workflow_name)
            if found:
                workflow_name = found
            else:
                return {
                    "status": "error",
                    "message": f"Workflow '{workflow_name}' not found. Available: {', '.join(self.workflows.keys())}"
                }
        
        workflow = self.workflows[workflow_name]
        self.running_workflow = workflow_name
        self.should_stop = False
        
        results = []
        print(f"[WORKFLOW] Starting: {workflow['name']}")
        
        for i, step in enumerate(workflow["steps"]):
            if self.should_stop:
                results.append({"step": i, "status": "cancelled"})
                break
            
            try:
                result = await self._execute_step(step)
                results.append({"step": i, "action": step["action"], "status": "success", "result": result})
            except Exception as e:
                results.append({"step": i, "action": step["action"], "status": "error", "error": str(e)})
                print(f"[WORKFLOW] Step {i} failed: {e}")
        
        self.running_workflow = None
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        return {
            "status": "completed",
            "workflow": workflow["name"],
            "steps_completed": success_count,
            "total_steps": len(workflow["steps"]),
            "results": results
        }
    
    async def _execute_step(self, step: Dict[str, Any]) -> str:
        """Execute a single workflow step"""
        action = step.get("action", "")
        
        if action == "speak":
            text = step.get("text", "")
            try:
                from Backend.TextToSpeech import TTS
                TTS(text)
            except:
                print(f"[WORKFLOW] TTS: {text}")
            return f"Spoke: {text}"
        
        elif action == "wait":
            seconds = step.get("seconds", 1)
            await asyncio.sleep(seconds)
            return f"Waited {seconds}s"
        
        elif action == "open_app":
            target = step.get("target", "")
            try:
                from Backend.Automation import OpenApp
                await asyncio.to_thread(OpenApp, target)
            except Exception as e:
                # Fallback
                import subprocess
                subprocess.Popen(f'start {target}', shell=True)
            return f"Opened {target}"
        
        elif action == "close_app":
            target = step.get("target", "")
            try:
                from Backend.Automation import CloseApp
                await asyncio.to_thread(CloseApp, target)
            except:
                pass
            return f"Closed {target}"
        
        elif action == "open_url":
            url = step.get("url", "")
            import webbrowser
            webbrowser.open(url)
            return f"Opened URL: {url}"
        
        elif action == "play_music":
            query = step.get("query", "lofi music")
            try:
                from Backend.MusicPlayerV2 import music_player_v2
                result = music_player_v2.search_and_play(query)
                return result.get("message", f"Playing: {query}")
            except:
                return f"Music: {query}"
        
        elif action == "stop_music":
            try:
                from Backend.MusicPlayerV2 import music_player_v2
                music_player_v2.stop()
            except:
                pass
            return "Music stopped"
        
        elif action == "set_volume":
            level = step.get("level", 50)
            try:
                from Backend.MusicPlayerV2 import music_player_v2
                music_player_v2.set_volume(level)
            except:
                pass
            return f"Volume: {level}%"
        
        elif action == "set_brightness":
            level = step.get("level", 100)
            try:
                import screen_brightness_control as sbc
                sbc.set_brightness(level)
            except:
                pass
            return f"Brightness: {level}%"
        
        elif action == "minimize_all":
            try:
                import keyboard
                keyboard.press_and_release("win+d")
            except:
                pass
            return "Minimized all windows"
        
        elif action == "close_distractions":
            distractions = ["discord", "slack", "whatsapp", "telegram", "spotify"]
            for app in distractions:
                try:
                    from Backend.Automation import CloseApp
                    await asyncio.to_thread(CloseApp, app)
                except:
                    pass
            return "Closed distraction apps"
        
        elif action == "close_all_browsers":
            browsers = ["chrome", "firefox", "edge", "brave"]
            for browser in browsers:
                try:
                    from Backend.Automation import CloseApp
                    await asyncio.to_thread(CloseApp, browser)
                except:
                    pass
            return "Closed browsers"
        
        else:
            return f"Unknown action: {action}"
    
    def stop_workflow(self):
        """Stop currently running workflow"""
        self.should_stop = True
        return {"status": "stopping", "workflow": self.running_workflow}
    
    def add_custom_workflow(self, name: str, description: str, steps: List[Dict]) -> bool:
        """Add a custom workflow"""
        key = name.lower().replace(" ", "_")
        self.workflows[key] = {
            "name": name,
            "description": description,
            "steps": steps,
            "custom": True
        }
        return True


# Global instance
smart_workflows = SmartWorkflows()


if __name__ == "__main__":
    # Test
    print("Available workflows:")
    for wf in smart_workflows.list_workflows():
        print(f"  - {wf['command']}: {wf['description']}")
