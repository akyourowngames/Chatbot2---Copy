import json
from typing import Dict, Any, List
from .base import Tool
from Backend.DocumentGenerator import document_generator # Use the global instance
import os

class DocumentTool(Tool):
    def __init__(self):
        super().__init__(
            name="document_creation",
            description="Create professional, AI-written PDF reports or PowerPoint presentations. Just provide a topic.",
            domain="file_operation", 
            priority="HIGH",
            allowed_intents=["file_operation", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The type of document: 'pdf' (report/article) or 'presentation' (pptx).",
                    "enum": ["pdf", "presentation"]
                },
                "topic": {
                    "type": "string",
                    "description": "The main topic or title of the document. Be specific for better results."
                }
            },
            "required": ["topic"]
        }

    def execute(self, topic: str, type: str = "pdf", **kwargs) -> str:
        try:
            filepath = document_generator.create_document(topic, type)
            return f"Successfully created {type.upper()} document about '{topic}': {filepath}"
            
        except Exception as e:
            return f"Document Creation Error: {str(e)}"
