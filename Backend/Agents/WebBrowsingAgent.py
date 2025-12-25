"""
Web Browsing Agent - Browser Automation with Playwright
=======================================================
Automate complex web interactions, form filling, and data extraction.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebBrowsingAgent(BaseAgent):
    """
    Agent that can control a web browser to automate tasks.
    Uses Playwright for robust browser automation.
    """
    
    def __init__(self):
        super().__init__(
            name="WebNavigator",
            specialty="Web browsing and automation",
            description="I can navigate websites, click elements, fill forms, and extract data"
        )
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self.headless = True
        logger.info("[WEB-AGENT] Initialized (Playwright will load on demand)")
    
    async def _ensure_browser(self):
        """Ensure browser is running."""
        if self._browser is not None:
            return
        
        try:
            from playwright.async_api import async_playwright
            
            logger.info("[WEB-AGENT] Starting Playwright browser...")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self._page = await self._context.new_page()
            logger.info("[WEB-AGENT] Browser ready")
            
        except ImportError:
            logger.error("[WEB-AGENT] Playwright not installed. Install with: pip install playwright && playwright install")
            raise Exception("Playwright not installed")
        except Exception as e:
            logger.error(f"[WEB-AGENT] Browser startup failed: {e}")
            raise
    
    async def _close_browser(self):
        """Close browser and cleanup."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self._browser = None
            self._page = None
            self._context = None
            self._playwright = None
            logger.info("[WEB-AGENT] Browser closed")
        except Exception as e:
            logger.error(f"[WEB-AGENT] Cleanup error: {e}")
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a web browsing task.
        
        Args:
            task: Natural language description of what to do
            context: Optional context with specific instructions
            
        Returns:
            Result with extracted data or action confirmation
        """
        try:
            # Run async execution
            result = asyncio.run(self._execute_async(task, context))
            return result
        except Exception as e:
            logger.error(f"[WEB-AGENT] Execution error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_async(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Async execution of web task."""
        try:
            await self._ensure_browser()
            
            # Parse task to determine actions
            actions = await self._parse_task(task, context)
            
            # Execute actions
            results = []
            for action in actions:
                action_result = await self._execute_action(action)
                results.append(action_result)
            
            # Synthesize results
            output = await self._synthesize_web_results(task, results)
            
            return {
                "status": "success",
                "agent": self.name,
                "task": task,
                "actions_performed": len(results),
                "output": output,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            # Keep browser open for potential follow-up tasks
            # await self._close_browser()
            pass
    
    async def _parse_task(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse natural language task into browser actions."""
        if not self.llm:
            # Fallback: simple keyword detection
            return self._simple_parse(task)
        
        prompt = f"""You are a web automation planner. Convert this task into browser actions.

TASK: {task}

Available actions:
- navigate: {{\"action\": \"navigate\", \"url\": \"https://...\"}}
- click: {{\"action\": \"click\", \"selector\": \"CSS selector or text\"}}
- fill: {{\"action\": \"fill\", \"selector\": \"CSS selector\", \"value\": \"text\"}}
- extract: {{\"action\": \"extract\", \"selector\": \"CSS selector\", \"attribute\": \"text|href|src\"}}
- screenshot: {{\"action\": \"screenshot\", \"path\": \"filename.png\"}}
- wait: {{\"action\": \"wait\", \"seconds\": 2}}

Respond with JSON array of actions:
[
  {{\"action\": \"navigate\", \"url\": \"...\"}},
  {{\"action\": \"extract\", \"selector\": \"h1\", \"attribute\": \"text\"}}
]

Your response (JSON array only):"""
        
        try:
            response = self.llm(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                inject_memory=False
            )
            
            # Extract JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            actions = json.loads(response)
            return actions if isinstance(actions, list) else [actions]
            
        except Exception as e:
            logger.warning(f"[WEB-AGENT] Task parsing failed: {e}, using simple parse")
            return self._simple_parse(task)
    
    def _simple_parse(self, task: str) -> List[Dict[str, Any]]:
        """Simple task parsing fallback."""
        actions = []
        task_lower = task.lower()
        
        # Extract URL if present
        import re
        url_match = re.search(r'https?://[^\s]+', task)
        if url_match:
            actions.append({"action": "navigate", "url": url_match.group()})
        
        # Detect common actions
        if "click" in task_lower:
            actions.append({"action": "click", "selector": "button, a"})
        if "fill" in task_lower or "enter" in task_lower:
            actions.append({"action": "fill", "selector": "input", "value": "test"})
        if "screenshot" in task_lower or "capture" in task_lower:
            actions.append({"action": "screenshot", "path": "screenshot.png"})
        
        return actions if actions else [{"action": "error", "message": "Could not parse task"}]
    
    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single browser action."""
        action_type = action.get("action")
        
        try:
            if action_type == "navigate":
                url = action.get("url")
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                return {"action": "navigate", "url": url, "status": "success"}
            
            elif action_type == "click":
                selector = action.get("selector")
                await self._page.click(selector, timeout=10000)
                return {"action": "click", "selector": selector, "status": "success"}
            
            elif action_type == "fill":
                selector = action.get("selector")
                value = action.get("value")
                await self._page.fill(selector, value, timeout=10000)
                return {"action": "fill", "selector": selector, "status": "success"}
            
            elif action_type == "extract":
                selector = action.get("selector")
                attribute = action.get("attribute", "text")
                
                if attribute == "text":
                    elements = await self._page.query_selector_all(selector)
                    texts = [await el.text_content() for el in elements[:10]]  # Limit to 10
                    return {"action": "extract", "selector": selector, "data": texts}
                else:
                    elements = await self._page.query_selector_all(selector)
                    attrs = [await el.get_attribute(attribute) for el in elements[:10]]
                    return {"action": "extract", "selector": selector, "data": attrs}
            
            elif action_type == "screenshot":
                path = action.get("path", "screenshot.png")
                await self._page.screenshot(path=path, full_page=True)
                return {"action": "screenshot", "path": path, "status": "success"}
            
            elif action_type == "wait":
                seconds = action.get("seconds", 1)
                await asyncio.sleep(seconds)
                return {"action": "wait", "seconds": seconds, "status": "success"}
            
            else:
                return {"action": action_type, "status": "error", "message": "Unknown action"}
                
        except Exception as e:
            logger.error(f"[WEB-AGENT] Action failed ({action_type}): {e}")
            return {"action": action_type, "status": "error", "message": str(e)}
    
    async def _synthesize_web_results(self, task: str, results: List[Dict]) -> str:
        """Synthesize action results into readable output."""
        if not self.llm:
            return str(results)
        
        results_text = "\n".join([
            f"- {r.get('action')}: {r.get('status', 'unknown')} | Data: {r.get('data', 'N/A')}"
            for r in results
        ])
        
        prompt = f"""Summarize these web automation results.

TASK: {task}

ACTIONS PERFORMED:
{results_text}

Provide a clear summary of what was accomplished:"""
        
        try:
            response = self.llm(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                inject_memory=False
            )
            return response.strip()
        except:
            return results_text
    
    async def cleanup(self):
        """Manual cleanup if needed."""
        await self._close_browser()


# Global instance
web_browsing_agent = WebBrowsingAgent()


# Convenience function
def browse_web(task: str) -> Dict[str, Any]:
    """Execute a web browsing task."""
    return web_browsing_agent.execute(task)


# Test
if __name__ == "__main__":
    print("🌐 Testing Web Browsing Agent\n")
    
    # Test: Navigate to a website
    result = web_browsing_agent.execute("Go to https://example.com and extract the h1 text")
    print(f"Result: {result.get('output')}\n")
    
    # Cleanup
    asyncio.run(web_browsing_agent.cleanup())
