"""
Multi-Step Workflows - Firebase-Backed Persistent Storage
==========================================================
Execute complex automation sequences with Firebase persistence
"""

import asyncio
from typing import List, Dict, Callable, Optional
import logging

# Import Firebase DAL
try:
    from Backend.FirebaseDAL import FirebaseDAL
    from Backend.FirebaseStorage import get_firebase_storage
    firebase_available = True
except ImportError:
    firebase_available = False
    logging.warning("[WORKFLOW] Firebase not available, using fallback mode")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Firebase-backed workflow engine"""
    
    def __init__(self):
        """Initialize workflow engine"""
        if firebase_available:
            storage = get_firebase_storage()
            self.dal = FirebaseDAL(storage.db) if storage.db else None
        else:
            self.dal = None
        
        self.collection = "workflows"
        self.default_workflows = self._get_default_workflows()
        logger.info("[WORKFLOW] Workflow engine initialized")
    
    def _get_default_workflows(self) -> Dict:
        """Get default workflow templates"""
        return {
            "start workday": {
                "description": "Start your productive workday",
                "steps": [
                    {"action": "open", "target": "vscode"},
                    {"action": "open", "target": "chrome"},
                    {"action": "chrome", "target": "open gmail.com"},
                    {"action": "system", "target": "volume up"},
                    {"action": "speak", "target": "Workday started! Ready to be productive."}
                ],
                "enabled": True
            },
            "end workday": {
                "description": "End your workday and relax",
                "steps": [
                    {"action": "close", "target": "vscode"},
                    {"action": "close", "target": "chrome"},
                    {"action": "system", "target": "lock screen"},
                    {"action": "speak", "target": "Great work today! Screen locked."}
                ],
                "enabled": True
            },
            "focus mode": {
                "description": "Enter deep focus mode",
                "steps": [
                    {"action": "system", "target": "minimize all"},
                    {"action": "open", "target": "vscode"},
                    {"action": "system", "target": "mute"},
                    {"action": "speak", "target": "Focus mode activated. No distractions."}
                ],
                "enabled": True
            },
            "research": {
                "description": "Research a topic (requires topic parameter)",
                "steps": [
                    {"action": "chrome", "target": "search {topic}"},
                    {"action": "chrome", "target": "new tab"},
                    {"action": "chrome", "target": "open scholar.google.com"},
                    {"action": "speak", "target": "Research mode ready for {topic}"}
                ],
                "enabled": True
            },
            "break time": {
                "description": "Take a break",
                "steps": [
                    {"action": "system", "target": "minimize all"},
                    {"action": "chrome", "target": "open youtube.com"},
                    {"action": "system", "target": "volume up"},
                    {"action": "speak", "target": "Break time! Relax for a bit."}
                ],
                "enabled": True
            },
            "meeting prep": {
                "description": "Prepare for a meeting",
                "steps": [
                    {"action": "system", "target": "minimize all"},
                    {"action": "open", "target": "teams"},
                    {"action": "system", "target": "volume up"},
                    {"action": "system", "target": "brightness up"},
                    {"action": "speak", "target": "Meeting preparation complete!"}
                ],
                "enabled": True
            }
        }
    
    async def execute_workflow(self, workflow_name: str, user_id: str = "default", parameters: Dict = None):
        """
        Execute a workflow
        
        Args:
            workflow_name: Name of the workflow to execute
            user_id: User ID
            parameters: Optional parameters for workflow steps
            
        Returns:
            List of step results
        """
        workflow_name = workflow_name.lower().strip()
        parameters = parameters or {}
        
        # Try to get user's custom workflow first
        workflow = self.get_workflow(workflow_name, user_id)
        
        # Fall back to default workflows
        if not workflow and workflow_name in self.default_workflows:
            workflow = self.default_workflows[workflow_name]
        
        if not workflow:
            return f"Workflow '{workflow_name}' not found"
        
        # Check if workflow is enabled
        if not workflow.get("enabled", True):
            return f"Workflow '{workflow_name}' is disabled"
        
        logger.info(f"[WORKFLOW] Executing workflow: {workflow_name}")
        logger.info(f"[WORKFLOW]   {workflow['description']}")
        
        results = []
        steps = workflow.get("steps", [])
        
        for i, step in enumerate(steps, 1):
            try:
                # Replace parameters in target
                target = step["target"]
                for key, value in parameters.items():
                    target = target.replace(f"{{{key}}}", str(value))
                
                logger.info(f"[WORKFLOW]   Step {i}/{len(steps)}: {step['action']} {target}")
                
                # Execute step
                result = await self._execute_step(step["action"], target)
                results.append(result)
                
                # Small delay between steps
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[WORKFLOW]   ❌ Step {i} failed: {e}")
                results.append(f"Failed: {e}")
        
        logger.info(f"[WORKFLOW] ✅ Workflow '{workflow_name}' completed!")
        return results
    
    async def _execute_step(self, action: str, target: str):
        """Execute a single workflow step - Web Version"""
        
        if action == "speak":
            # Return the text instead of TTS (web mode)
            logger.info(f"[WORKFLOW] Message: {target}")
            return f"Message: {target}"
        
        elif action == "wait":
            await asyncio.sleep(float(target))
            return f"Waited {target}s"
        
        else:
            # On web, automation is not available
            command = f"{action} {target}"
            logger.info(f"[WORKFLOW] (Web mode) Would execute: {command}")
            return f"⚠️ '{command}' - requires desktop version"
    
    def create_workflow(self, name: str, description: str, steps: List[Dict], user_id: str = "default") -> bool:
        """
        Create a new workflow
        
        Args:
            name: Workflow name
            description: Workflow description
            steps: List of workflow steps
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.dal:
                logger.warning("[WORKFLOW] Firebase DAL not available")
                return False
            
            workflow_data = {
                "name": name.lower(),
                "description": description,
                "steps": steps,
                "enabled": True
            }
            
            workflow_id = self.dal.create(self.collection, user_id, workflow_data)
            
            if workflow_id:
                logger.info(f"[WORKFLOW] Created workflow '{name}' for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[WORKFLOW] Create workflow error: {e}")
            return False
    
    def list_workflows(self, user_id: str = "default") -> List[str]:
        """
        List all available workflows (default + user's custom)
        
        Args:
            user_id: User ID
            
        Returns:
            List of workflow descriptions
        """
        workflows = []
        
        # Add default workflows
        for name, workflow in self.default_workflows.items():
            workflows.append(f"{name}: {workflow['description']}")
        
        # Add user's custom workflows
        if self.dal:
            try:
                custom_workflows = self.dal.list(self.collection, user_id, limit=100)
                for wf in custom_workflows:
                    name = wf.get("name", "")
                    desc = wf.get("description", "")
                    workflows.append(f"{name}: {desc} (custom)")
            except Exception as e:
                logger.error(f"[WORKFLOW] List workflows error: {e}")
        
        return workflows
    
    def get_workflow(self, name: str, user_id: str = "default") -> Optional[Dict]:
        """
        Get workflow details
        
        Args:
            name: Workflow name
            user_id: User ID
            
        Returns:
            Workflow dictionary if found, None otherwise
        """
        if not self.dal:
            return self.default_workflows.get(name.lower())
        
        try:
            # Search for workflow by name
            workflows = self.dal.list(
                self.collection,
                user_id,
                filters={"name": name.lower()},
                limit=1
            )
            
            if workflows:
                return workflows[0]
            
            return None
            
        except Exception as e:
            logger.error(f"[WORKFLOW] Get workflow error: {e}")
            return None
    
    def update_workflow(self, workflow_id: str, updates: Dict, user_id: str = "default") -> bool:
        """
        Update a workflow
        
        Args:
            workflow_id: Workflow document ID
            updates: Fields to update
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.dal:
            return False
        
        try:
            return self.dal.update(self.collection, user_id, workflow_id, updates)
        except Exception as e:
            logger.error(f"[WORKFLOW] Update workflow error: {e}")
            return False
    
    def delete_workflow(self, workflow_id: str, user_id: str = "default") -> bool:
        """
        Delete a workflow
        
        Args:
            workflow_id: Workflow document ID
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.dal:
            return False
        
        try:
            return self.dal.delete(self.collection, user_id, workflow_id)
        except Exception as e:
            logger.error(f"[WORKFLOW] Delete workflow error: {e}")
            return False


# Global instance
workflow_engine = WorkflowEngine()


# Quick access function
async def run_workflow(name: str, user_id: str = "default", **params):
    """Quick workflow execution"""
    return await workflow_engine.execute_workflow(name, user_id, params)


# ==================== TESTING ====================

if __name__ == "__main__":
    print("⚙️ Testing Workflow Engine\n")
    
    async def test():
        test_user_id = "test_user_123"
        
        print("1. Available workflows:")
        for wf in workflow_engine.list_workflows(test_user_id):
            print(f"   - {wf}")
        
        print("\n2. Creating custom workflow:")
        success = workflow_engine.create_workflow(
            "test workflow",
            "A test workflow",
            [
                {"action": "speak", "target": "Testing workflow"},
                {"action": "wait", "target": "1"}
            ],
            test_user_id
        )
        print(f"   Created: {success}")
        
        print("\n3. Executing 'focus mode' workflow:")
        results = await workflow_engine.execute_workflow("focus mode", test_user_id)
        print(f"   Results: {len(results)} steps executed")
    
    asyncio.run(test())
    print("\n✅ Workflow engine tests completed!")

