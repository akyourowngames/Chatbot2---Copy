from typing import Dict, Any
from .base import Tool

class TranslatorTool(Tool):
    def __init__(self):
        super().__init__(
            name="translator",
            description="Translate text between languages.",
            domain="utilities",
            priority="LOW",
            allowed_intents=["translation", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to translate"
                },
                "target_language": {
                    "type": "string",
                    "description": "Target language code (e.g. 'es', 'fr', 'en') or name"
                },
                "source_language": {
                    "type": "string",
                    "description": "Source language code (default 'auto')"
                }
            },
            "required": ["text", "target_language"]
        }

    def execute(self, text: str, target_language: str, source_language: str = "auto", **kwargs) -> str:
        try:
            from Backend.Translator import translator
            
            result = translator.translate(text, target_language, source_language)
            
            if result.get("status") == "success":
                return f"Translation: {result.get('translation')} (from {result.get('source_lang_name')} to {result.get('target_lang_name')})"
            elif result.get("status") == "partial":
                return f"Partial Translation: {result.get('message')}"
            else:
                return f"Translation Failed: {result.get('error', 'Unknown error')}"

        except ImportError:
            return "Translator module not found."
        except Exception as e:
            return f"Translator Error: {str(e)}"
