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
try:
    from Backend.ActionHistory import action_history
except ImportError:
    action_history = None

class EnhancedImageGenerator:
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # API keys from environment
        self.pollinations_api = "https://image.pollinations.ai/prompt/"
        self.pollinations_api_key = os.getenv("POLLINATIONS_API_KEY", "")
        self.stability_api_key = os.getenv("STABILITY_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    
    def generate_pollinations(self, prompt: str, num_images: int = 1, 
                             width: int = 1024, height: int = 1024, model: str = None,
                             user_id: str = None) -> List[str]:
        """
        Generate images using Pollinations AI
        
        Args:
            prompt: Image description
            num_images: Number of images to generate
            width: Image width
            height: Image height
            model: Image model (default: flux)
            user_id: Optional user ID
            
        Returns:
            List of image file paths
        """
        images = []
        import urllib.parse
        import requests
        
        for i in range(num_images):
            try:
                # Clean and encode prompt
                if not prompt: prompt = "abstract art"
                safe_prompt = str(prompt).strip()
                
                # URL encode the prompt
                encoded_prompt = urllib.parse.quote(safe_prompt)
                
                # Generate seed for variety
                seed = int(datetime.now().timestamp() * 1000) + i
                
                # Use the simple image.pollinations.ai endpoint - no auth needed!
                # Format: https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={s}&nologo=true
                api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                params = {
                    "width": width,
                    "height": height,
                    "seed": seed,
                    "nologo": "true",
                    "model": model or "flux"
                }
                
                print(f"[ImageGen] Calling Pollinations: {safe_prompt[:50]}...")
                
                # Make the request (no auth headers needed for this endpoint)
                response = requests.get(api_url, params=params, timeout=60)
                
                if response.status_code == 200 and response.content:
                    # Save image to file
                    filename = f"pollinations_{seed}.png"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    # Return relative path for serving
                    images.append(f"/data/Images/{filename}")
                    print(f"[ImageGen] ✓ Image saved: {filename}")
                else:
                    print(f"[ImageGen] ✗ API error {response.status_code}: {response.text[:100] if response.text else 'No response'}")
                    
            except Exception as e:
                print(f"[ImageGen] Error: {e}")
                import traceback
                traceback.print_exc()
        
        # Log action
        try:
            if images and action_history:
                action_history.log_action(
                    action_type="image_gen",
                    params={"prompt": prompt, "num_images": num_images},
                    description=f"Generate image: {prompt[:30]}..."
                )
        except:
            pass
        
        print(f"[ImageGen] Generated {len(images)} image(s)")
        return images

        

    def generate_variations(self, image_url: str, num_variations: int = 3, user_id: str = None) -> List[str]:
        """Generate variations of an existing image"""
        variations = []
        import urllib.parse
        import requests
        
        try:
            if image_url.startswith('http'):
                response = requests.get(image_url, timeout=10)
                source_image = response.content
            else:
                with open(image_url, 'rb') as f:
                    source_image = f.read()
            
            temp_path = os.path.join(self.output_dir, f"temp_source_{int(datetime.now().timestamp())}.png")
            with open(temp_path, 'wb') as f:
                f.write(source_image)
            
            for i in range(num_variations):
                seed = int(datetime.now().timestamp() * 1000) + i
                
                if self.pollinations_api_key:
                    encoded_prompt = urllib.parse.quote(f"variation {i+1}")
                    api_url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
                    headers = {"Authorization": f"Bearer {self.pollinations_api_key}"}
                    params = {'seed': seed, 'nologo': 'true', 'width': 1024, 'height': 1024}
                    
                    response = requests.get(api_url, headers=headers, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        filename = f"variation_{seed}.png"
                        filepath = os.path.join(self.output_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        variations.append(f"/data/Images/{filename}")
                        print(f"[ImageGen] Variation {i+1} saved: {filename}")
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            print(f"[ImageGen] Error generating variations: {e}")
        
        return variations

    def upscale_image(self, image_url: str, scale: int = 2, user_id: str = None) -> str:
        """Upscale image 2x or 4x"""
        try:
            import requests
            from PIL import Image
            import io
            
            if image_url.startswith('http'):
                response = requests.get(image_url, timeout=10)
                img = Image.open(io.BytesIO(response.content))
            else:
                img = Image.open(image_url)
            
            new_size = (img.width * scale, img.height * scale)
            upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
            
            filename = f"upscaled_{scale}x_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(self.output_dir, filename)
            upscaled.save(filepath, 'PNG')
            
            print(f"[ImageGen] Image upscaled {scale}x: {filename}")
            return f"/data/Images/{filename}"
            
        except Exception as e:
            print(f"[ImageGen] Error upscaling: {e}")
            return ""

    def remove_background(self, image_url: str, user_id: str = None) -> str:
        """Remove background from image"""
        try:
            import requests
            removebg_key = os.getenv("REMOVE_BG_API_KEY", "")
            
            if removebg_key:
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    data={'image_url': image_url, 'size': 'auto'},
                    headers={'X-Api-Key': removebg_key},
                    timeout=30
                )
                
                if response.status_code == 200:
                    filename = f"nobg_{int(datetime.now().timestamp())}.png"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"[ImageGen] Background removed: {filename}")
                    return f"/data/Images/{filename}"
            else:
                print("[ImageGen] No REMOVE_BG_API_KEY configured")
                
        except Exception as e:
            print(f"[ImageGen] Error removing background: {e}")
        
        return ""
    def generate_with_style(self, prompt: str, style: str = "realistic", 
                           num_images: int = 1, user_id: str = None) -> List[str]:
        """
        Generate images with specific artistic styles
        
        Args:
            prompt: Base prompt
            style: Style preset
            num_images: Number of images
            user_id: Optional user ID for user-specific storage
            
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
        
        return self.generate_pollinations(enhanced_prompt, num_images, user_id=user_id)
    
    def generate_variations(self, base_prompt: str, variations: List[str], 
                           num_per_variation: int = 1, user_id: str = None) -> Dict[str, List[str]]:
        """
        Generate multiple variations of a base prompt
        """
        results = {}
        
        for variation in variations:
            full_prompt = f"{base_prompt}, {variation}"
            images = self.generate_pollinations(full_prompt, num_per_variation, user_id=user_id)
            results[variation] = images
        
        return results
    
    def generate_hd(self, prompt: str, num_images: int = 1, user_id: str = None) -> List[str]:
        """
        Generate high-definition images (1920x1080)
        """
        return self.generate_pollinations(prompt, num_images, width=1920, height=1080, user_id=user_id)
    
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
    
    # ==================== V2 FEATURES ====================
    
    def ai_enhance_prompt(self, simple_prompt: str) -> str:
        """
        Use AI (LLM) to creatively enhance a simple prompt into a detailed image description.
        This creates much better images than basic keyword enhancement.
        """
        try:
            from Backend.LLM import ChatCompletion
            
            enhance_request = f"""You are an expert AI image prompt engineer. Transform this simple idea into a detailed, vivid image generation prompt.

INPUT: {simple_prompt}

Create a prompt that includes:
- Detailed visual description
- Lighting and atmosphere
- Art style or medium
- Quality modifiers (8k, detailed, professional)
- Mood and emotion

Respond with ONLY the enhanced prompt, no explanations. Keep it under 100 words."""

            enhanced = ChatCompletion(
                messages=[{"role": "user", "content": enhance_request}],
                model="llama-3.3-70b-versatile",
                text_only=True,
                inject_memory=False
            )
            
            print(f"[ImageGen V2] AI Enhanced: {simple_prompt} → {enhanced[:80]}...")
            return enhanced.strip()
            
        except Exception as e:
            print(f"[ImageGen V2] AI enhancement failed: {e}, using basic enhancement")
            return self.enhance_prompt(simple_prompt)
    
    def smart_generate(self, prompt: str, num_images: int = 1) -> Dict:
        """
        Smart generate: AI analyzes the prompt and picks the best style automatically.
        Returns images with metadata about what style was chosen.
        """
        try:
            from Backend.LLM import ChatCompletion
            
            # Ask AI to pick best style
            style_request = f"""Analyze this image request and pick the best style from this list:
realistic, anime, oil_painting, watercolor, sketch, 3d_render, cyberpunk, fantasy, minimalist, vintage, comic, pixel_art, neon, vaporwave, steampunk, art_nouveau, pop_art, impressionist, surrealist, gothic, pastel, low_poly, isometric, film_noir, ukiyo_e, art_deco

REQUEST: {prompt}

Reply with ONLY the style name, nothing else."""

            chosen_style = ChatCompletion(
                messages=[{"role": "user", "content": style_request}],
                model="llama-3.1-8b-instant",
                text_only=True,
                inject_memory=False
            ).strip().lower().replace(" ", "_")
            
            # Validate style
            valid_styles = ["realistic", "anime", "oil_painting", "watercolor", "sketch", "3d_render", 
                          "cyberpunk", "fantasy", "minimalist", "vintage", "comic", "pixel_art",
                          "neon", "vaporwave", "steampunk", "art_nouveau", "pop_art", "impressionist",
                          "surrealist", "gothic", "pastel", "low_poly", "isometric", "film_noir", 
                          "ukiyo_e", "art_deco"]
            
            if chosen_style not in valid_styles:
                chosen_style = "realistic"
            
            print(f"[ImageGen V2] Smart Generate chose style: {chosen_style}")
            
            # Generate with chosen style
            # Using Flux model for best quality on all styles
            images = self.generate_with_style(prompt, chosen_style, num_images)
            
            # Log action for retry ONLY AFTER SUCCESS
            if images and action_history:
                action_history.log_action(
                    action_type="smart_image_gen",
                    params={"prompt": prompt, "num_images": num_images, "style": chosen_style},
                    description=f"Smart Gen ({chosen_style}): {prompt[:30]}..."
                )
            
            return {
                "status": "success",
                "images": images,
                "style": chosen_style,
                "prompt": prompt,
                "message": f"Generated {len(images)} image(s) in {chosen_style} style"
            }
            
        except Exception as e:
            print(f"[ImageGen V2] Smart generate error: {e}")
            # Fallback to realistic
            images = self.generate_with_style(prompt, "realistic", num_images)
            return {
                "status": "success",
                "images": images,
                "style": "realistic",
                "prompt": prompt,
                "message": f"Generated {len(images)} image(s)"
            }
    
    # ==================== SOCIAL MEDIA PRESETS ====================
    
    def generate_instagram_post(self, prompt: str) -> List[str]:
        """Generate Instagram-optimized square image (1080x1080)"""
        enhanced = f"{prompt}, instagram aesthetic, vibrant, eye-catching, social media worthy"
        return self.generate_pollinations(enhanced, 1, width=1080, height=1080)
    
    def generate_instagram_story(self, prompt: str) -> List[str]:
        """Generate Instagram Story image (1080x1920)"""
        enhanced = f"{prompt}, vertical format, instagram story aesthetic, engaging"
        return self.generate_pollinations(enhanced, 1, width=1080, height=1920)
    
    def generate_twitter_post(self, prompt: str) -> List[str]:
        """Generate Twitter/X optimized image (1200x675)"""
        enhanced = f"{prompt}, twitter card format, attention-grabbing, social media"
        return self.generate_pollinations(enhanced, 1, width=1200, height=675)
    
    def generate_youtube_thumbnail(self, prompt: str) -> List[str]:
        """Generate YouTube thumbnail (1280x720)"""
        enhanced = f"{prompt}, youtube thumbnail, bold, eye-catching, high contrast, exciting"
        return self.generate_pollinations(enhanced, 1, width=1280, height=720)
    
    def generate_linkedin_post(self, prompt: str) -> List[str]:
        """Generate LinkedIn optimized image (1200x627)"""
        enhanced = f"{prompt}, professional, corporate, linkedin aesthetic, business"
        return self.generate_pollinations(enhanced, 1, width=1200, height=627)
    
    def generate_facebook_cover(self, prompt: str) -> List[str]:
        """Generate Facebook cover photo (820x312)"""
        enhanced = f"{prompt}, facebook cover, wide format, professional"
        return self.generate_pollinations(enhanced, 1, width=820, height=312)
    
    def generate_wallpaper(self, prompt: str, resolution: str = "1080p") -> List[str]:
        """Generate desktop wallpaper"""
        resolutions = {
            "1080p": (1920, 1080),
            "2k": (2560, 1440),
            "4k": (3840, 2160),
            "ultrawide": (2560, 1080)
        }
        w, h = resolutions.get(resolution, (1920, 1080))
        enhanced = f"{prompt}, desktop wallpaper, stunning, high quality, {resolution}"
        return self.generate_pollinations(enhanced, 1, width=w, height=h)
    
    def generate_phone_wallpaper(self, prompt: str) -> List[str]:
        """Generate phone wallpaper (1080x2340)"""
        enhanced = f"{prompt}, phone wallpaper, vertical, stunning, amoled friendly"
        return self.generate_pollinations(enhanced, 1, width=1080, height=2340)
    
    def get_available_styles(self) -> List[str]:
        """Return list of all available styles"""
        return [
            "realistic", "anime", "oil_painting", "watercolor", "sketch", "3d_render",
            "cyberpunk", "fantasy", "minimalist", "vintage", "comic", "pixel_art",
            "neon", "vaporwave", "steampunk", "art_nouveau", "pop_art", "impressionist",
            "surrealist", "gothic", "pastel", "low_poly", "isometric", "film_noir",
            "ukiyo_e", "art_deco"
        ]
    
    def get_available_presets(self) -> List[str]:
        """Return list of all available presets/formats"""
        return [
            "square", "portrait", "landscape", "banner", "hd",
            "instagram_post", "instagram_story", "twitter_post", "youtube_thumbnail",
            "linkedin_post", "facebook_cover", "wallpaper_1080p", "wallpaper_4k", 
            "phone_wallpaper"
        ]

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
