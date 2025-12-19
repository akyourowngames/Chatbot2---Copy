"""
Smart Workflows - Web Version
=============================
Workflow information and templates for web deployment.
Actual execution requires local PC (desktop version).
"""

import asyncio
from typing import Dict, List, Any, Optional

# Pre-defined workflow templates (for reference/display only on web)
SMART_WORKFLOWS = {
    "morning_routine": {
        "name": "Morning Routine",
        "description": "Start your day: email, calendar, news, and energizing music",
        "steps": [
            {"action": "speak", "text": "Good morning! Let me set up your day."},
            {"action": "open_url", "url": "https://mail.google.com"},
            {"action": "open_url", "url": "https://calendar.google.com"},
            {"action": "speak", "text": "Your morning setup is ready!"}
        ]
    },
    
    "work_mode": {
        "name": "Work Mode",
        "description": "Focus environment: code editor, browser, low volume",
        "steps": [
            {"action": "speak", "text": "Activating work mode."},
            {"action": "speak", "text": "Work environment ready. Stay focused!"}
        ]
    },
    
    "focus_mode": {
        "name": "Focus Mode",
        "description": "Minimize distractions, play lo-fi music",
        "steps": [
            {"action": "speak", "text": "Entering focus mode."},
            {"action": "play_music", "query": "lo-fi focus beats"},
            {"action": "speak", "text": "Focus mode active. Deep work time."}
        ]
    },
    
    "research_mode": {
        "name": "Research Mode",
        "description": "Open research resources",
        "steps": [
            {"action": "speak", "text": "Setting up research environment."},
            {"action": "open_url", "url": "https://scholar.google.com"},
            {"action": "open_url", "url": "https://wikipedia.org"},
            {"action": "speak", "text": "Research mode ready!"}
        ]
    }
}


class SmartWorkflows:
    """Smart Workflows - Web Version (limited functionality)"""
    
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
            "morning_routine": ["morning", "wake up", "start day"],
            "work_mode": ["work", "office", "productive"],
            "focus_mode": ["focus", "concentrate", "deep work"],
            "research_mode": ["research", "study", "learn"]
        }
        
        for workflow_key, kws in keywords.items():
            if any(kw in query_lower for kw in kws):
                return workflow_key
        
        return None
    
    async def execute_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Execute workflow - returns web-friendly response"""
        if workflow_name not in self.workflows:
            found = self.find_workflow(workflow_name)
            if found:
                workflow_name = found
            else:
                return {
                    "status": "error",
                    "message": f"Workflow '{workflow_name}' not found. Available: {', '.join(self.workflows.keys())}"
                }
        
        workflow = self.workflows[workflow_name]
        
        # On web, we can only provide URLs to open
        results = []
        urls_to_open = []
        
        for step in workflow["steps"]:
            if step.get("action") == "open_url":
                urls_to_open.append(step.get("url", ""))
            elif step.get("action") == "speak":
                results.append(step.get("text", ""))
        
        return {
            "status": "web_mode",
            "workflow": workflow["name"],
            "message": " ".join(results),
            "urls": urls_to_open,
            "note": "⚠️ Full workflow execution requires the desktop version of KAI. On web, only URLs can be opened."
        }
    
    def stop_workflow(self):
        """Stop currently running workflow"""
        self.should_stop = True
        return {"status": "stopped"}
    
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
    print("Available workflows:")
    for wf in smart_workflows.list_workflows():
        print(f"  - {wf['command']}: {wf['description']}")
