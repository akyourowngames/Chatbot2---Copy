"""
Creative Agent - Artist & Storyteller
=====================================
Specializes in creative writing, image generation prompts, and unique ideas.
"""

from Backend.Agents.AutonomousAgent import AutonomousAgent

class CreativeAgent(AutonomousAgent):
    """
    Autonomous agent for creative tasks.
    """
    def __init__(self):
        super().__init__(
            name="Creative Agent",
            specialty="Creative writing, image generation, ideation",
            description="I generate creative content, image prompts, and unique ideas that stand out."
        )
        self._register_creative_tools()
        
    def _register_creative_tools(self):
        # Image generation tool stub - real implementation would call DALL-E/Midjourney integration
        def generate_image_prompt(params: str):
            """Improve an image prompt."""
            return f"Midjourney Prompt: {params} --v 6.0 --ar 16:9 --style raw"
            
        self.register_tool(
            name="enhance_prompt",
            func=generate_image_prompt,
            description="Enhance a basic image description into a professional prompt.",
            parameters="description: str"
        )

creative_agent = CreativeAgent()
