"""
Multi-modal Agent - Combined Image and Text Reasoning
=====================================================
Analyzes images with text context for complex multi-modal tasks.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64
import os

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiModalAgent(BaseAgent):
    """
    Agent that combines vision and text understanding.
    Can analyze images with context, answer visual questions, compare images, etc.
    """
    
    def __init__(self):
        super().__init__(
            name="VisionReasoner",
            specialty="Multi-modal image and text analysis",
            description="I analyze images in context, answer visual questions, and combine image+text reasoning"
        )
        self._vision_service = None
        logger.info("[MULTIMODAL-AGENT] Initialized")
    
    @property
    def vision_service(self):
        """Lazy load Vision Service."""
        if self._vision_service is None:
            try:
                from Backend.VisionService import VisionService
                self._vision_service = VisionService()
            except Exception as e:
                logger.error(f"[MULTIMODAL-AGENT] Failed to load VisionService: {e}")
        return self._vision_service
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute multi-modal analysis task.
        
        Args:
            task: What to analyze (question or instruction about images)
            context: Must include 'images' (list of file paths or URLs)
            
        Returns:
            Analysis results combining visual and textual understanding
        """
        try:
            logger.info(f"[MULTIMODAL-AGENT] Task: {task[:50]}...")
            
            # Extract images
            images = self._get_images(task, context)
            
            if not images:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": "No images provided",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Determine task type
            task_type = self._determine_task_type(task, len(images))
            
            # Execute based on task type
            if task_type == "single_analysis":
                result = self._analyze_single_image(images[0], task)
            elif task_type == "comparison":
                result = self._compare_images(images, task)
            elif task_type == "sequence":
                result = self._analyze_sequence(images, task)
            elif task_type == "visual_qa":
                result = self._visual_qa(images[0], task)
            else:
                result = self._general_multimodal(images, task)
            
            return {
                "status": "success",
                "agent": self.name,
                "task": task,
                "images_analyzed": len(images),
                "task_type": task_type,
                "output": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[MULTIMODAL-AGENT] Execution error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_images(self, task: str, context: Dict[str, Any]) -> List[str]:
        """Extract image paths from context or task."""
        images = []
        
        # From context
        if context and "images" in context:
            img_list = context["images"]
            if isinstance(img_list, str):
                images = [img_list]
            elif isinstance(img_list, list):
                images = img_list
        elif context and "image" in context:
            images = [context["image"]]
        
        # Try to find image paths in task
        if not images:
            import re
            patterns = [
                r'[\w\-\\\/:.]+\.(?:jpg|jpeg|png|gif|bmp|webp)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, task, re.IGNORECASE)
                images.extend(matches)
        
        return images
    
    def _determine_task_type(self, task: str, num_images: int) -> str:
        """Determine what type of multi-modal task to perform."""
        task_lower = task.lower()
        
        if num_images > 1:
            if any(word in task_lower for word in ["compare", "difference", "versus", "vs", "vs."]):
                return "comparison"
            elif any(word in task_lower for word in ["sequence", "series", "progression", "timeline"]):
                return "sequence"
        
        if any(word in task_lower for word in ["what", "how", "why", "where", "when", "who"]):
            return "visual_qa"
        
        if any(word in task_lower for word in ["analyze", "describe", "explain"]):
            return "single_analysis"
        
        return "general"
    
    def _analyze_single_image(self, image_path: str, task: str) -> str:
        """Deep analysis of a single image."""
        if not self.vision_service:
            return "Vision service not available"
        
        try:
            # Use vision service for basic analysis
            vision_result = self.vision_service.analyze_image(
                image_path,
                prompt="Provide a detailed analysis of this image including objects, scene, mood, and notable details."
            )
            
            if vision_result.get("status") == "error":
                return f"Vision analysis failed: {vision_result.get('message')}"
            
            analysis = vision_result.get("analysis", "No analysis available")
            
            # Enhance with LLM reasoning
            if self.llm:
                prompt = f"""Based on this visual analysis, provide insights for the task.

TASK: {task}

VISUAL ANALYSIS:
{analysis}

Enhanced insights:"""
                
                enhanced = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return f"{analysis}\n\n💡 Enhanced Insights:\n{enhanced.strip()}"
            
            return analysis
            
        except Exception as e:
            logger.error(f"[MULTIMODAL-AGENT] Single image analysis failed: {e}")
            return f"Analysis failed: {e}"
    
    def _compare_images(self, images: List[str], task: str) -> str:
        """Compare multiple images."""
        if not self.vision_service:
            return "Vision service not available"
        
        try:
            # Analyze each image
            analyses = []
            for i, img in enumerate(images[:5]):  # Limit to 5 images
                result = self.vision_service.analyze_image(
                    img,
                    prompt="Describe this image concisely focusing on key visual elements."
                )
                
                if result.get("status") == "success":
                    analyses.append(f"Image {i+1}: {result.get('analysis', 'N/A')}")
            
            # Compare with LLM
            if self.llm and analyses:
                analyses_text = "\n\n".join(analyses)
                
                prompt = f"""Compare these images based on the task.

TASK: {task}

IMAGE ANALYSES:
{analyses_text}

Comparison (similarities, differences, insights):"""
                
                comparison = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return comparison.strip()
            
            return "\n\n".join(analyses)
            
        except Exception as e:
            return f"Image comparison failed: {e}"
    
    def _analyze_sequence(self, images: List[str], task: str) -> str:
        """Analyze a sequence of images (progression, timeline)."""
        if not self.vision_service:
            return "Vision service not available"
        
        try:
            # Analyze each image in sequence
            sequence_analysis = []
            for i, img in enumerate(images[:10]):
                result = self.vision_service.analyze_image(
                    img,
                    prompt="Describe what's happening in this image."
                )
                
                if result.get("status") == "success":
                    sequence_analysis.append(f"Step {i+1}: {result.get('analysis', 'N/A')}")
            
            # Synthesize sequence understanding
            if self.llm and sequence_analysis:
                sequence_text = "\n".join(sequence_analysis)
                
                prompt = f"""Analyze this sequence of images and explain the progression.

TASK: {task}

SEQUENCE:
{sequence_text}

What story or progression do these images show?"""
                
                synthesis = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return synthesis.strip()
            
            return "\n".join(sequence_analysis)
            
        except Exception as e:
            return f"Sequence analysis failed: {e}"
    
    def _visual_qa(self, image_path: str, question: str) -> str:
        """Answer questions about an image."""
        if not self.vision_service:
            return "Vision service not available"
        
        try:
            # Use vision service with specific question
            result = self.vision_service.analyze_image(
                image_path,
                prompt=f"Answer this question about the image: {question}"
            )
            
            if result.get("status") == "success":
                return result.get("analysis", "Could not answer question")
            else:
                return f"Visual Q&A failed: {result.get('message')}"
                
        except Exception as e:
            return f"Visual Q&A error: {e}"
    
    def _general_multimodal(self, images: List[str], task: str) -> str:
        """General multi-modal reasoning."""
        if len(images) == 1:
            return self._analyze_single_image(images[0], task)
        else:
            return self._compare_images(images, task)


# Global instance
multimodal_agent = MultiModalAgent()


# Convenience functions
def analyze_image(image_path: str, question: str = None) -> Dict[str, Any]:
    """Analyze a single image."""
    task = question if question else "Analyze this image in detail"
    return multimodal_agent.execute(task, {"images": [image_path]})


def compare_images(image_paths: List[str], task: str = "Compare these images") -> Dict[str, Any]:
    """Compare multiple images."""
    return multimodal_agent.execute(task, {"images": image_paths})


# Test
if __name__ == "__main__":
    print("👁️ Testing Multi-modal Agent\n")
    print("Note: Requires image files and Vision Service to fully test")
    print("Example usage:")
    print("  - analyze_image('screenshot.png', 'What UI elements are visible?')")
    print("  - compare_images(['before.png', 'after.png'], 'What changed?')")
