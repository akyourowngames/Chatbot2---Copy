"""
Advanced Document Generator - Production Ready
===============================================
Generate professional, content-rich PDFs using:
- HTML/CSS templates (beautiful, consistent design)
- Playwright rendering (primary)
- WeasyPrint fallback
- Structured LLM content generation

Document Types:
- expo_submission: AI Expo/Conference submission
- pitch_document: Startup pitch deck
- technical_guide: Whitepaper/guide
- professional_report: General business report
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Legacy imports for backward compatibility
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

# New template-based system
try:
    from Backend.Documents.schemas import DOCUMENT_TYPES, validate_schema, get_schema_prompt
    from Backend.Documents.content_generator import content_generator
    from Backend.Documents.renderer import document_renderer
    NEW_SYSTEM_AVAILABLE = True
    print("[DocumentGenerator] ✅ New template system loaded")
except ImportError as e:
    NEW_SYSTEM_AVAILABLE = False
    print(f"[DocumentGenerator] ⚠️ Using legacy system: {e}")

try:
    from Backend.LLM import ChatCompletion
except ImportError:
    def ChatCompletion(messages, model, text_only): 
        return '{"error": "LLM unavailable"}'


class DocumentGenerator:
    """
    Professional document generator supporting multiple formats and templates.
    
    Usage:
        generator = DocumentGenerator()
        
        # New template-based (recommended)
        result = generator.generate(
            topic="KAI AI Assistant Expo Submission",
            document_type="expo_submission"
        )
        
        # Legacy (backward compatible)
        result = generator.create_document("My Report", "pdf")
    """
    
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Documents")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Brand colors (used by legacy system)
        self.primary_color = colors.HexColor('#2563EB')
        self.secondary_color = colors.HexColor('#1E40AF')
        self.accent_color = colors.HexColor('#F59E0B')
        self.text_color = colors.HexColor('#1F2937')
        self.light_bg = colors.HexColor('#F3F4F6')
    
    # ==================== NEW TEMPLATE-BASED SYSTEM ====================
    
    def generate(
        self, 
        topic: str,
        document_type: str = "professional_report",
        content: Dict[str, Any] = None,
        additional_context: str = None,
        user_id: str = None,
        filename: str = None
    ) -> Dict[str, Any]:
        """
        Generate a professional document using the new template system.
        
        Args:
            topic: Document topic/title
            document_type: One of: expo_submission, pitch_document, technical_guide, professional_report
            content: Pre-generated content (optional, will use LLM if not provided)
            additional_context: Extra instructions for content generation
            user_id: User ID for cloud storage
            filename: Custom filename
            
        Returns:
            Dict with:
                - success: bool
                - filepath: str
                - url: str  
                - format: str (pdf, html, or markdown)
                - title: str
                - warning/error: str (if any)
        """
        if not NEW_SYSTEM_AVAILABLE:
            print("[DocumentGenerator] Falling back to legacy system")
            return self._legacy_generate(topic, document_type, user_id)
        
        print(f"[DocumentGenerator] Generating {document_type}: {topic[:50]}...")
        
        # Step 1: Generate or validate content
        if content is None:
            content = content_generator.generate(topic, document_type, additional_context)
        else:
            # Validate provided content
            try:
                content = validate_schema(content, document_type)
            except ValueError as e:
                print(f"[DocumentGenerator] Schema validation error: {e}")
                # Try to fix by adding defaults
                content["document_type"] = document_type
                content.setdefault("title", topic)
        
        # Step 2: Render to PDF (with fallbacks)
        result = document_renderer.render_pdf(content, filename, user_id)
        
        # Add title to result
        result["title"] = content.get("title", topic)
        
        # Step 3: Upload to cloud if available
        if result["success"] and result["format"] == "pdf":
            result = self._upload_to_cloud(result, user_id)
        
        return result
    
    def _upload_to_cloud(self, result: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """Upload generated document to Supabase if available."""
        try:
            from Backend.SupabaseDB import supabase_db
            if supabase_db:
                print(f"[DocumentGenerator] Uploading to cloud...")
                cloud_url = supabase_db.upload_pdf(
                    result["filepath"], 
                    folder='documents', 
                    user_id=user_id
                )
                if cloud_url:
                    result["url"] = cloud_url
                    print(f"[DocumentGenerator] ✅ Uploaded: {cloud_url}")
        except Exception as e:
            print(f"[DocumentGenerator] Cloud upload failed: {e}")
        return result
    
    def _legacy_generate(self, topic: str, document_type: str, user_id: str = None) -> Dict[str, Any]:
        """Fallback to legacy ReportLab-based generation."""
        try:
            result = self.generate_pdf(topic, user_id=user_id)
            return {
                "success": True,
                "filepath": result.get("filepath", ""),
                "url": result.get("url", ""),
                "format": "pdf",
                "title": result.get("title", topic),
                "warning": "Generated using legacy system"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "format": "none"
            }
    
    def get_document_types(self) -> List[str]:
        """Get list of supported document types."""
        if NEW_SYSTEM_AVAILABLE:
            return DOCUMENT_TYPES
        return ["pdf", "ppt"]
    
    # ==================== LEGACY SYSTEM (backward compatibility) ====================
    
    def _get_llm_content(self, topic: str, doc_type: str = "report") -> Dict[str, Any]:
        """Generate structured content using LLM (legacy method)."""
        import json
        
        prompt = f"""
        Create content for a professional {doc_type} about "{topic}".
        Return ONLY valid JSON:
        {{
            "title": "Title",
            "subtitle": "Subtitle",
            "sections": [
                {{"heading": "Section 1", "content": "...", "type": "paragraph"}},
                {{"heading": "Key Points", "content": "", "type": "bullet", "data": ["Point 1", "Point 2"]}}
            ]
        }}
        """
        
        try:
            response = ChatCompletion(
                messages=[{"role": "system", "content": "Output ONLY JSON"}, {"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                text_only=True
            )
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        except Exception as e:
            print(f"[DocumentGenerator] LLM error: {e}")
            return {
                "title": topic,
                "sections": [{"heading": "Content", "content": "Content generation failed.", "type": "paragraph"}]
            }
    
    def generate_pdf(self, topic: str, content: Dict[str, Any] = None, filename: str = None, user_id: str = None) -> Dict[str, str]:
        """Legacy PDF generation using ReportLab."""
        import re
        
        if content is None:
            content = self._get_llm_content(topic, "report")
        
        title = content.get("title", topic)
        if not filename:
            filename = f"{title.replace(' ', '_')[:50]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('MainTitle', parent=styles['Title'], fontSize=28, spaceAfter=20, textColor=self.primary_color)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, spaceBefore=20, spaceAfter=10, textColor=self.secondary_color)
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=10, alignment=TA_JUSTIFY)
        
        elements.append(Spacer(1, 100))
        elements.append(Paragraph(title, title_style))
        if "subtitle" in content:
            elements.append(Paragraph(content["subtitle"], ParagraphStyle('Sub', parent=body_style, alignment=TA_CENTER)))
        elements.append(Spacer(1, 50))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", ParagraphStyle('Date', parent=body_style, alignment=TA_CENTER)))
        elements.append(PageBreak())
        
        for section in content.get("sections", []):
            if section.get("heading"):
                elements.append(Paragraph(section["heading"], heading_style))
            
            sec_type = section.get("type", "paragraph")
            text = section.get("content", "")
            
            if sec_type == "paragraph" and text:
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                elements.append(Paragraph(text, body_style))
            elif sec_type == "bullet":
                if text:
                    elements.append(Paragraph(text, body_style))
                for item in section.get("data", []):
                    elements.append(Paragraph(f"• {item}", body_style))
            elif sec_type == "table" and section.get("data"):
                t = Table(section["data"])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.white),
                ]))
                elements.append(t)
            
            elements.append(Spacer(1, 12))
        
        doc.build(elements)
        
        pdf_url = f"/data/Documents/{filename}"
        try:
            from Backend.SupabaseDB import supabase_db
            if supabase_db:
                cloud_url = supabase_db.upload_pdf(filepath, folder='documents', user_id=user_id)
                if cloud_url:
                    pdf_url = cloud_url
        except:
            pass
        
        return {"filepath": filepath, "url": pdf_url, "filename": filename, "title": title}
    
    def generate_presentation(self, topic: str, content: Dict[str, Any] = None, filename: str = None, user_id: str = None) -> str:
        """Generate PowerPoint presentation (legacy)."""
        if content is None:
            content = self._get_llm_content(topic, "presentation")
        
        title = content.get("title", topic)
        if not filename:
            filename = f"{title.replace(' ', '_')[:50]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
        filepath = os.path.join(self.output_dir, filename)
        
        prs = Presentation()
        
        # Title slide
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = title
        slide.placeholders[1].text = f"Generated by Kai AI\n{datetime.now().strftime('%B %d, %Y')}"
        
        # Content slides
        for slide_data in content.get("slides", []):
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = slide_data.get("title", "")
            tf = slide.placeholders[1].text_frame
            tf.clear()
            for point in slide_data.get("content", []):
                p = tf.add_paragraph()
                p.text = point
                p.space_after = Pt(10)
        
        prs.save(filepath)
        return filepath
    
    def create_document(self, topic: str, doc_type: str = "pdf", user_id: str = None) -> Dict[str, Any]:
        """
        Unified entry point (legacy compatibility).
        
        For new code, use generate() with document_type parameter instead.
        """
        if "presentation" in doc_type.lower() or "ppt" in doc_type.lower():
            filepath = self.generate_presentation(topic, user_id=user_id)
            return {"success": True, "filepath": filepath, "format": "pptx"}
        
        # Use new system if available
        if NEW_SYSTEM_AVAILABLE:
            return self.generate(topic, "professional_report", user_id=user_id)
        
        # Legacy fallback
        result = self.generate_pdf(topic, user_id=user_id)
        return {"success": True, **result, "format": "pdf"}


# Global Instance
document_generator = DocumentGenerator()

# Convenience functions
def generate_document(topic: str, document_type: str = "professional_report", **kwargs) -> Dict[str, Any]:
    """Generate a professional document."""
    return document_generator.generate(topic, document_type, **kwargs)

def get_supported_types() -> List[str]:
    """Get list of supported document types."""
    return document_generator.get_document_types()


if __name__ == "__main__":
    print("\n=== Testing New Document System ===\n")
    
    # Test each document type
    test_cases = [
        ("KAI - AI Desktop Assistant", "expo_submission"),
        ("TechStartup Funding Round", "pitch_document"),
        ("Building REST APIs with FastAPI", "technical_guide"),
        ("Q4 2025 Performance Review", "professional_report"),
    ]
    
    for topic, doc_type in test_cases:
        print(f"\n--- Testing {doc_type} ---")
        result = document_generator.generate(topic, doc_type)
        print(f"Success: {result.get('success')}")
        print(f"Format: {result.get('format')}")
        print(f"URL: {result.get('url')}")
        if result.get("warning"):
            print(f"Warning: {result.get('warning')}")
        if result.get("error"):
            print(f"Error: {result.get('error')}")
