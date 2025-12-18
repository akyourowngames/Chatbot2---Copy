from typing import Dict, Any
from .base import Tool
import datetime
import dateutil.parser

class ReminderTool(Tool):
    def __init__(self):
        super().__init__(
            name="reminder",
            description="Set reminders for specific dates and times.",
            domain="system_control", # or new domain 'scheduling'
            priority="MEDIUM",
            allowed_intents=["reminder", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "What to remind the user about"
                },
                "time": {
                    "type": "string",
                    "description": "Time for the reminder (e.g. '2025-01-20 15:00' or '5pm tomorrow'). ISO format preferred."
                }
            },
            "required": ["text", "time"]
        }

    def execute(self, text: str, time: str, **kwargs) -> str:
        try:
            # Import backend
            try:
                from Backend.Reminder import set_reminder
            except ImportError:
                return "Reminder module not found."

            # Parse time
            try:
                # Use dateutil for fuzzy parsing if available, else simple formats
                parsed_time = dateutil.parser.parse(time)
            except:
                # Fallback to direct try or error
                return f"Could not parse time: '{time}'. Please use a format like 'YYYY-MM-DD HH:MM'."

            # Check if future
            if parsed_time < datetime.datetime.now():
                return "Cannot set reminder in the past."

            # Set reminder
            result = set_reminder(text, parsed_time)
            return f"Reminder set: {result}"

        except Exception as e:
            return f"Reminder Error: {str(e)}"
