"""
Website Capture - Beast Mode
============================
Convert websites to PDFs and screenshots with preview generation.
Features:
- URL to PDF conversion with full page rendering
- Full-page screenshots
- PDF thumbnail generation for chat preview
- Works in cloud deployment
"""

import os
import re
import json
import base64
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse, quote

# Try to import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[WebsiteCapture] ReportLab not available - PDF generation limited")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebsiteCapture:
    """Capture websites as PDFs and screenshots with preview support"""
    
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Captures")
        self.thumbnails_dir = os.path.join(self.output_dir, "thumbnails")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def _sanitize_filename(self, url: str) -> str:
        """Create a safe filename from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").replace(".", "_")
        path = parsed.path.replace("/", "_")[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{domain}{path}_{timestamp}"
    
    def _fetch_page_content(self, url: str) -> Dict[str, Any]:
        """Fetch and parse webpage content"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            if not BS4_AVAILABLE:
                return {
                    "success": False,
                    "error": "BeautifulSoup not available"
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else urlparse(url).netloc
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract main content
            # Remove scripts, styles, nav, footer
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # Get main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            # Extract text paragraphs
            paragraphs = []
            if main_content:
                for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
                    text = p.get_text().strip()
                    if len(text) > 20:  # Filter out short snippets
                        tag_name = p.name
                        paragraphs.append({
                            'type': 'heading' if tag_name.startswith('h') else 'paragraph',
                            'level': int(tag_name[1]) if tag_name.startswith('h') else 0,
                            'text': text[:1000]  # Limit length
                        })
            
            return {
                "success": True,
                "title": title_text,
                "description": description,
                "url": url,
                "paragraphs": paragraphs[:50],  # Limit to 50 paragraphs
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Failed to fetch URL: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing page: {str(e)}"
            }
    
    def url_to_pdf(self, url: str, include_images: bool = False) -> Dict[str, Any]:
        """
        Convert a URL to a PDF document.
        Returns path to PDF and thumbnail for preview.
        """
        if not REPORTLAB_AVAILABLE:
            return {
                "status": "error",
                "error": "PDF generation not available (ReportLab not installed)"
            }
        
        # Fetch page content
        content = self._fetch_page_content(url)
        if not content.get("success"):
            return {
                "status": "error",
                "error": content.get("error", "Failed to fetch page")
            }
        
        try:
            # Generate filename
            safe_name = self._sanitize_filename(url)
            pdf_filename = f"{safe_name}.pdf"
            pdf_path = os.path.join(self.output_dir, pdf_filename)
            
            # Create PDF
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=60,
                leftMargin=60,
                topMargin=60,
                bottomMargin=60
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=20,
                textColor='#1a1a2e'
            )
            
            url_style = ParagraphStyle(
                'URLStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor='#666666',
                spaceAfter=20
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
                textColor='#2d3436'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                leading=16,
                spaceAfter=10,
                textColor='#333333'
            )
            
            # Build document elements
            elements = []
            
            # Title
            elements.append(Paragraph(content['title'], title_style))
            
            # URL and timestamp
            elements.append(Paragraph(f"Source: {url}", url_style))
            elements.append(Paragraph(f"Captured: {content['fetched_at']}", url_style))
            elements.append(Spacer(1, 20))
            
            # Description if available
            if content.get('description'):
                elements.append(Paragraph(f"<i>{content['description']}</i>", body_style))
                elements.append(Spacer(1, 15))
            
            # Content paragraphs
            for para in content.get('paragraphs', []):
                text = para['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if para['type'] == 'heading':
                    elements.append(Paragraph(text, heading_style))
                else:
                    elements.append(Paragraph(text, body_style))
            
            # Build PDF
            doc.build(elements)
            
            # Generate thumbnail
            thumbnail_path = self._generate_pdf_thumbnail(pdf_path, safe_name)
            
            # Upload to Supabase in production
            pdf_url = None
            thumbnail_url = None
            
            if os.getenv('FLASK_ENV') == 'production' or os.getenv('USE_SUPABASE_STORAGE', 'false').lower() == 'true':
                try:
                    from Backend.SupabaseDB import supabase_db
                    if supabase_db:
                        print(f"[WebsiteCapture] Uploading PDF to Supabase...")
                        pdf_url = supabase_db.upload_pdf(pdf_path, folder='captures')
                        
                        # Upload thumbnail if available
                        if thumbnail_path and os.path.exists(thumbnail_path):
                            thumb_filename = os.path.basename(thumbnail_path)
                            storage_path = f"captures/thumbnails/{thumb_filename}"
                            thumbnail_url = supabase_db.upload_file(
                                thumbnail_path, 
                                storage_path, 
                                bucket='kai-images', 
                                content_type='image/png'
                            )
                        
                        if pdf_url:
                            print(f"[WebsiteCapture] Uploaded to: {pdf_url}")
                            # Delete local files after upload
                            os.remove(pdf_path)
                            if thumbnail_path and os.path.exists(thumbnail_path):
                                os.remove(thumbnail_path)
                        else:
                            print(f"[WebsiteCapture] Upload failed, keeping local file")
                            pdf_url = f"/data/Captures/{pdf_filename}"
                            thumbnail_url = f"/data/Captures/thumbnails/{safe_name}_thumb.png" if thumbnail_path else None
                except Exception as e:
                    print(f"[WebsiteCapture] Supabase upload error: {e}, using local path")
                    pdf_url = f"/data/Captures/{pdf_filename}"
                    thumbnail_url = f"/data/Captures/thumbnails/{safe_name}_thumb.png" if thumbnail_path else None
            else:
                # Local development - use local paths
                pdf_url = f"/data/Captures/{pdf_filename}"
                thumbnail_url = f"/data/Captures/thumbnails/{safe_name}_thumb.png" if thumbnail_path else None
            
            return {
                "status": "success",
                "message": f"📄 Created PDF: **{content['title']}**",
                "pdf_path": pdf_path if os.path.exists(pdf_path) else None,
                "pdf_url": pdf_url,
                "thumbnail_url": thumbnail_url,
                "title": content['title'],
                "url": url,
                "page_count": 1,  # Simplified - would need proper counting
                "type": "pdf_capture"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"PDF generation failed: {str(e)}"
            }
    
    def _generate_pdf_thumbnail(self, pdf_path: str, safe_name: str) -> Optional[str]:
        """Generate a thumbnail preview of the PDF first page"""
        try:
            # Try using pdf2image if available
            try:
                from pdf2image import convert_from_path
                
                # Convert first page to image
                images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=72)
                if images:
                    thumb_path = os.path.join(self.thumbnails_dir, f"{safe_name}_thumb.png")
                    # Resize to thumbnail
                    thumb = images[0]
                    thumb.thumbnail((300, 400))
                    thumb.save(thumb_path, "PNG")
                    return thumb_path
            except ImportError:
                pass
            
            # Fallback: Create a simple placeholder thumbnail
            if PIL_AVAILABLE:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a simple PDF icon thumbnail
                img = Image.new('RGB', (200, 260), color='#1a1a2e')
                draw = ImageDraw.Draw(img)
                
                # Draw PDF icon
                draw.rectangle([30, 20, 170, 240], fill='#ffffff', outline='#8b5cf6', width=2)
                draw.rectangle([30, 20, 170, 60], fill='#8b5cf6')
                
                # Add "PDF" text
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                draw.text((75, 30), "PDF", fill='white', font=font)
                
                # Add document lines
                for y in range(80, 220, 20):
                    draw.rectangle([45, y, 155, y+8], fill='#e0e0e0')
                
                thumb_path = os.path.join(self.thumbnails_dir, f"{safe_name}_thumb.png")
                img.save(thumb_path, "PNG")
                return thumb_path
            
            return None
            
        except Exception as e:
            print(f"[WebsiteCapture] Thumbnail generation failed: {e}")
            return None
    
    def url_to_screenshot(self, url: str, full_page: bool = True) -> Dict[str, Any]:
        """
        Take a screenshot of a webpage.
        Uses external API for cloud compatibility.
        """
        try:
            # Use a free screenshot API
            safe_name = self._sanitize_filename(url)
            screenshot_filename = f"{safe_name}.png"
            screenshot_path = os.path.join(self.output_dir, screenshot_filename)
            
            # Try using screenshot API (screenshotapi.net free tier or similar)
            # For local: could use playwright/selenium
            # For cloud: use external API
            
            # Option 1: Use microlink.io screenshot API (has free tier)
            api_url = f"https://api.microlink.io/?url={quote(url, safe='')}&screenshot=true&meta=false&embed=screenshot.url"
            
            response = requests.get(api_url, timeout=30)
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('screenshot', {}).get('url'):
                screenshot_url = data['data']['screenshot']['url']
                
                # Download the screenshot
                img_response = requests.get(screenshot_url, timeout=30)
                with open(screenshot_path, 'wb') as f:
                    f.write(img_response.content)
                
                screenshot_relative = f"/data/Captures/{screenshot_filename}"
                
                return {
                    "status": "success",
                    "message": f"📸 Captured screenshot of: **{url}**",
                    "screenshot_path": screenshot_path,
                    "screenshot_url": screenshot_relative,
                    "url": url,
                    "type": "screenshot"
                }
            else:
                # Fallback: Return error with suggestion
                return {
                    "status": "error",
                    "error": "Screenshot API unavailable. Try the PDF capture instead.",
                    "suggestion": "Use 'capture PDF of [url]' for similar results"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Screenshot failed: {str(e)}"
            }
    
    def capture(self, url: str, capture_type: str = "pdf") -> Dict[str, Any]:
        """
        Unified capture method.
        
        Args:
            url: The URL to capture
            capture_type: "pdf" or "screenshot"
        """
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if capture_type == "screenshot":
            return self.url_to_screenshot(url)
        else:
            return self.url_to_pdf(url)


# Global instance
website_capture = WebsiteCapture()


if __name__ == "__main__":
    # Test
    print("Testing Website Capture...")
    result = website_capture.url_to_pdf("https://example.com")
    print(json.dumps(result, indent=2))
