"""
Enhanced Image Generation - Multiple AI Models
===============================================
Advanced image generation with DALL-E, Stable Diffusion, and more
"""

import os
import requests
import base64
from datetime import datetime
from typing import List, Optional, Dict
import asyncio
from pathlib import Path

class EnhancedImageGenerator:
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # API keys from environment
        self.pollinations_api = "https://image.pollinations.ai/prompt/"
        self.stability_api_key = os.getenv("STABILITY_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    def generate_pollinations(self, prompt: str, num_images: int = 1, 
                             width: int = 1024, height: int = 1024) -> List[str]:
        """
        Generate images using Pollinations AI (Free, no API key needed)
        
        Args:
            prompt: Image description
            num_images: Number of images to generate
            width: Image width
            height: Image height
            
        Returns:
            List of image file paths
        """
        images = []
        
        for i in range(num_images):
            try:
                # Encode prompt
                encoded_prompt = requests.utils.quote(prompt)
                
                # Generate unique URL with seed for variety
                seed = datetime.now().microsecond + i
                url = f"{self.pollinations_api}{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
                
                # Download image
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Save image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{prompt[:30].replace(' ', '_')}_{timestamp}_{i+1}.png"
                    filepath = os.path.join(self.output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    images.append(filepath)
                    print(f"✓ Generated image {i+1}/{num_images}")
                else:
                    print(f"✗ Failed to generate image {i+1}")
                    
            except Exception as e:
                print(f"Error generating image {i+1}: {e}")
        
        return images
    
    def generate_with_style(self, prompt: str, style: str = "realistic", 
                           num_images: int = 1) -> List[str]:
        """
        Generate images with specific artistic styles
        
        Args:
            prompt: Base prompt
            style: Style preset (realistic, anime, oil_painting, watercolor, sketch, 3d_render, etc.)
            num_images: Number of images
            
        Returns:
            List of image paths
        """
        style_prompts = {
            # Classic styles
            "realistic": "photorealistic, highly detailed, 8k, professional photography, sharp focus",
            "anime": "anime style, manga, vibrant colors, detailed, studio ghibli inspired",
            "oil_painting": "oil painting, classical art style, textured brushstrokes, museum quality",
            "watercolor": "watercolor painting, soft colors, artistic, flowing",
            "sketch": "pencil sketch, hand-drawn, artistic linework, detailed shading",
            "3d_render": "3D render, octane render, unreal engine 5, highly detailed, volumetric lighting",
            "cyberpunk": "cyberpunk style, neon lights, futuristic, sci-fi, blade runner inspired",
            "fantasy": "fantasy art, magical, ethereal, detailed, mystical atmosphere",
            "minimalist": "minimalist design, clean, simple, modern, negative space",
            "vintage": "vintage style, retro, nostalgic, aged, film grain",
            "comic": "comic book style, bold lines, vibrant colors, dynamic composition",
            "pixel_art": "pixel art, 8-bit style, retro gaming, nostalgic",
            # New artistic styles
            "neon": "neon aesthetic, glowing lights, vibrant colors, dark background, synthwave",
            "vaporwave": "vaporwave aesthetic, 80s/90s nostalgia, pink and cyan, retro digital art",
            "steampunk": "steampunk style, victorian era, brass and copper, mechanical, gears",
            "art_nouveau": "art nouveau style, organic flowing lines, decorative, ornamental, elegant",
            "pop_art": "pop art style, andy warhol inspired, bold colors, halftone dots",
            "impressionist": "impressionist painting, monet style, light brushstrokes, dreamy atmosphere",
            "surrealist": "surrealist art, dali inspired, dreamlike, impossible scenes, melting forms",
            "gothic": "gothic art style, dark atmosphere, dramatic lighting, mysterious, ornate",
            "pastel": "pastel colors, soft aesthetic, dreamy, gentle, kawaii inspired",
            "low_poly": "low poly 3D art, geometric shapes, minimalist 3D, flat shading",
            "isometric": "isometric art, 3D perspective, detailed miniature, game asset style",
            "film_noir": "film noir style, black and white, high contrast, dramatic shadows, cinematic",
            "ukiyo_e": "ukiyo-e style, japanese woodblock print, traditional, waves, nature",
            "art_deco": "art deco style, geometric patterns, gold and black, 1920s glamour, elegant"
        }

        
        style_suffix = style_prompts.get(style, style_prompts["realistic"])
        enhanced_prompt = f"{prompt}, {style_suffix}"
        
        return self.generate_pollinations(enhanced_prompt, num_images)
    
    def generate_variations(self, base_prompt: str, variations: List[str], 
                           num_per_variation: int = 1) -> Dict[str, List[str]]:
        """
        Generate multiple variations of a base prompt
        
        Args:
            base_prompt: Base image description
            variations: List of variation descriptions
            num_per_variation: Images per variation
            
        Returns:
            Dict mapping variation to image paths
        """
        results = {}
        
        for variation in variations:
            full_prompt = f"{base_prompt}, {variation}"
            images = self.generate_pollinations(full_prompt, num_per_variation)
            results[variation] = images
        
        return results
    
    def generate_hd(self, prompt: str, num_images: int = 1) -> List[str]:
        """
        Generate high-definition images (1920x1080)
        
        Args:
            prompt: Image description
            num_images: Number of images
            
        Returns:
            List of image paths
        """
        return self.generate_pollinations(prompt, num_images, width=1920, height=1080)
    
    def generate_square(self, prompt: str, num_images: int = 1, size: int = 1024) -> List[str]:
        """
        Generate square images (perfect for social media)
        
        Args:
            prompt: Image description
            num_images: Number of images
            size: Square size (default 1024x1024)
            
        Returns:
            List of image paths
        """
        return self.generate_pollinations(prompt, num_images, width=size, height=size)
    
    def generate_portrait(self, prompt: str, num_images: int = 1) -> List[str]:
        """
        Generate portrait-oriented images (768x1024)
        
        Args:
            prompt: Image description
            num_images: Number of images
            
        Returns:
            List of image paths
        """
        return self.generate_pollinations(prompt, num_images, width=768, height=1024)
    
    def generate_landscape(self, prompt: str, num_images: int = 1) -> List[str]:
        """
        Generate landscape-oriented images (1024x768)
        
        Args:
            prompt: Image description
            num_images: Number of images
            
        Returns:
            List of image paths
        """
        return self.generate_pollinations(prompt, num_images, width=1024, height=768)
    
    def generate_banner(self, prompt: str, num_images: int = 1) -> List[str]:
        """
        Generate wide banner images (1920x480)
        
        Args:
            prompt: Image description
            num_images: Number of images
            
        Returns:
            List of image paths
        """
        return self.generate_pollinations(prompt, num_images, width=1920, height=480)
    
    def enhance_prompt(self, simple_prompt: str) -> str:
        """
        Enhance a simple prompt with quality modifiers
        
        Args:
            simple_prompt: Basic description
            
        Returns:
            Enhanced prompt
        """
        quality_modifiers = [
            "highly detailed",
            "professional quality",
            "8k resolution",
            "sharp focus",
            "vibrant colors",
            "masterpiece"
        ]
        
        return f"{simple_prompt}, {', '.join(quality_modifiers)}"
    
    def list_generated_images(self, limit: int = 20) -> List[Dict[str, str]]:
        """
        List recently generated images
        
        Args:
            limit: Maximum number of images to return
            
        Returns:
            List of image info dicts
        """
        images = []
        
        if os.path.exists(self.output_dir):
            files = sorted(
                Path(self.output_dir).glob("*.png"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for file in files[:limit]:
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "size": file.stat().st_size,
                    "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        
        return images

# Global instance
enhanced_image_gen = EnhancedImageGenerator()

if __name__ == "__main__":
    # Test image generation
    print("Testing Enhanced Image Generator...")
    
    # Generate realistic image
    images = enhanced_image_gen.generate_with_style(
        "a beautiful sunset over mountains",
        style="realistic",
        num_images=1
    )
    print(f"Generated {len(images)} realistic images")
    
    # Generate anime style
    anime_images = enhanced_image_gen.generate_with_style(
        "a cute cat",
        style="anime",
        num_images=1
    )
    print(f"Generated {len(anime_images)} anime images")
    
    # List recent images
    recent = enhanced_image_gen.list_generated_images(5)
    print(f"\nRecent images: {len(recent)}")
    for img in recent:
        print(f"  - {img['filename']}")
