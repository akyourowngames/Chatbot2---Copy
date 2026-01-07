

"""
Smart Trigger System - JARVIS Level (UPGRADED)
===============================================
Intelligent phrase detection with ENSEMBLE approach:
Regex patterns + Semantic classifier for best accuracy.
"""

import re
from typing import List, Tuple, Optional

class SmartTrigger:
    def __init__(self, use_classifier=True):  # ENABLED BY DEFAULT
        self.use_classifier = use_classifier
        self.classifier = None
        
        # === INTENT MAPPING: LocalClassifier -> SmartTrigger ===
        self.classifier_intent_map = {
            "vision_analysis": "vision",
            "web_search": "chrome",
            "memory_update": "memory",
            "memory_query": "memory",
            "code_generation": "code",
            "system_command": "system",
            "file_operation": "file",
            "workflow_trigger": "workflow",
            "chat_response": "general",
            "conversation_meta": "general"
        }
        
        if self.use_classifier:
            try:
                from Backend.LocalClassifier import LocalClassifier
                self.classifier = LocalClassifier(use_model=False)  # Fast keyword mode
                print("[SmartTrigger] 🧠 Classifier ENABLED for ensemble detection")
            except Exception as e:
                print(f"[SmartTrigger] Classifier load error: {e}")
        
        # Define trigger patterns with flexibility
        self.triggers = {
            # Chrome Automation
            "chrome": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:open|go to|navigate to|visit)\s+(.+)(?:\s+in\s+chrome)?",
                    r"(?:jarvis\s+)?chrome\s+(.+)",
                    r"(?:jarvis\s+)?search\s+(?:for\s+)?(.+)(?:\s+on\s+google)?",
                ],
                "keywords": ["chrome", "browser", "google", "search", "navigate", "visit"]
            },
            
            # Vision
            "vision": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:what's|what is|whats)\s+on\s+(?:my\s+)?screen",
                    r"(?:jarvis\s+)?(?:look at|see|analyze|check)\s+(?:my\s+)?(?:screen|display)",
                    r"(?:jarvis\s+)?(?:take a\s+)?(?:look|peek)",
                ],
                "keywords": ["screen", "look", "see", "vision", "analyze", "display"]
            },
            
            # Memory
            "memory": {
                "patterns": [
                    r"(?:jarvis\s+)?remember\s+(?:that\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:save|store|note)\s+(?:this|that)\s+(.+)",
                    r"(?:jarvis\s+)?(?:what do you|do you)\s+remember\s+(?:about\s+)?(.+)",
                ],
                "keywords": ["remember", "recall", "memory", "save", "note"]
            },
            
            # System Control
            "system": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:increase|decrease|raise|lower)\s+(?:the\s+)?(?:volume|brightness)",
                    r"(?:jarvis\s+)?(?:mute|unmute)",
                    r"(?:jarvis\s+)?(?:lock|unlock)\s+(?:my\s+)?(?:screen|computer)",
                    r"(?:jarvis\s+)?(?:take a\s+)?screenshot",
                    r"(?:jarvis\s+)?(?:show|minimize)\s+(?:the\s+)?desktop",
                    r"(?:jarvis\s+)?(?:shutdown|restart|reboot|sleep|hibernate)\s+(?:my\s+)?computer",
                    r"(?:jarvis\s+)?check\s+(?:battery|power)\s+(?:status|level)?",
                ],
                "keywords": ["volume", "brightness", "mute", "lock", "screenshot", "desktop", "shutdown", "restart", "sleep", "hibernate", "battery"]
            },
            
            # File Operations (MEGA Enhanced - Sea of Keywords)
            "file": {
                "patterns": [
                    # Create
                    r"(?:jarvis\s+)?(?:create|make|new|add|generate)\s+(?:a\s+)?(?:new\s+)?(?:file|folder|directory|doc|document|text file)\s+(?:named\s+|called\s+)?(.+)",
                    # Delete - single and bulk
                    r"(?:jarvis\s+)?(?:delete|remove|erase|trash|destroy|get rid of)\s+(?:the\s+)?(?:file|folder|all files|everything)?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:delete|remove|clear|empty|clean)\s+(?:all|every|the)\s+(?:files?|folders?|items?|contents?)",
                    r"(?:jarvis\s+)?(?:clean up|cleanup|clear out|empty out|wipe)\s+(?:the\s+)?(.+)?",
                    # Copy
                    r"(?:jarvis\s+)?(?:copy|duplicate|replicate|clone)\s+(.+?)\s+(?:to|into|in)\s+(.+)",
                    r"(?:jarvis\s+)?(?:make a copy|create copy|backup)\s+(?:of\s+)?(.+)",
                    # Move
                    r"(?:jarvis\s+)?(?:move|transfer|relocate|shift|put)\s+(.+?)\s+(?:to|into|in)\s+(.+)",
                    # Rename
                    r"(?:jarvis\s+)?(?:rename|change name|call it)\s+(.+?)\s+(?:to|as)\s+(.+)",
                    # List/Show
                    r"(?:jarvis\s+)?(?:list|show|display|view|see|what's in)\s+(?:all\s+)?(?:files?|folders?|contents?)?\s*(?:in|of|from)?\s*(.+)?",
                    # Search/Find - require "file" keyword
                    r"(?:jarvis\s+)?(?:search|find|look for|locate|where is)\s+(?:the\s+)?(?:file|folder)\s+(.+)",
                    # Open folder/explorer
                    r"(?:jarvis\s+)?(?:open|go to|navigate to|show me|browse)\s+(?:the\s+)?(?:folder|directory)?\s*(.+)?",
                    r"(?:jarvis\s+)?open\s+(?:file\s+)?(?:explorer|manager|finder)",
                    # Keyboard shortcuts
                    r"(?:jarvis\s+)?(?:select all|select everything|ctrl a)",
                    r"(?:jarvis\s+)?(?:copy|copy this|ctrl c)",
                    r"(?:jarvis\s+)?(?:cut|cut this|ctrl x)",
                    r"(?:jarvis\s+)?(?:paste|paste here|ctrl v)",
                    r"(?:jarvis\s+)?(?:undo|undo that|ctrl z)",
                    r"(?:jarvis\s+)?(?:redo|redo that|ctrl y)",
                    # Organize/Sort
                    r"(?:jarvis\s+)?(?:organize|sort|arrange|order)\s+(?:my\s+)?(?:files?|folders?|downloads?)?",
                    # Compress/Extract
                    r"(?:jarvis\s+)?(?:zip|compress|archive)\s+(.+)",
                    r"(?:jarvis\s+)?(?:unzip|extract|decompress)\s+(.+)",
                ],
                "keywords": [
                    # Basic operations
                    "file", "folder", "directory", "files", "folders",
                    "create file", "make file", "new file", "add file",
                    "create folder", "make folder", "new folder",
                    # Delete variations (SEA OF WORDS)
                    "delete", "delete file", "delete folder", "delete all", "delete everything",
                    "delete all files", "delete files", "delete all folders",
                    "remove", "remove file", "remove folder", "remove all", "remove all files",
                    "remove everything", "remove files", "remove it", "remove this",
                    "erase", "erase file", "erase all", "erase everything", "trash", "trash file", "trash all",
                    "clear all files", "clear all", "clear folder", "clear directory",
                    "empty folder", "empty directory", "empty trash", "empty recycle bin",
                    "clean folder", "clean up", "cleanup", "clean directory",
                    "clear out", "wipe", "wipe folder", "wipe all", "wipe files",
                    "get rid of", "throw away", "discard", "purge", "purge files",
                    # Copy variations
                    "copy", "copy file", "copy folder", "copy all", "copy to",
                    "duplicate", "duplicate file", "clone", "replicate",
                    "backup", "backup files", "make backup", "create backup",
                    "copy everything", "copy all files",
                    # Move variations
                    "move", "move file", "move folder", "move to", "transfer",
                    "relocate", "shift", "put in", "move all", "move all files",
                    "transfer files", "move everything",
                    # Rename
                    "rename", "rename file", "rename folder", "change name",
                    # List/Show
                    "list", "list files", "list folders", "show files", "show folders",
                    "what files", "what's in", "whats in", "contents", "view files",
                    "display files", "see files", "show me files", "list all",
                    "show all files", "show everything", "list everything",
                    # Search/Find - SPECIFIC to file operations only
                    "search file", "search files", "find file", "find files in",
                    "locate file", "where is file", "look for file", "search for file", "find all files",
                    # Open/Navigate
                    "open folder", "open directory", "go to folder", "navigate",
                    "explorer", "file explorer", "file manager", "open explorer",
                    "browse", "browse files", "browse folder", "open files",
                    # Keyboard shortcuts
                    "select all", "select everything", "copy", "cut", "paste",
                    "undo", "redo", "ctrl a", "ctrl c", "ctrl x", "ctrl v", "ctrl z",
                    # Common folders
                    "documents", "downloads", "desktop", "pictures", "videos", "music",
                    "home", "temp", "trash", "recycle bin", "my files", "my documents",
                    # Organize
                    "organize", "organize files", "sort", "sort files", "arrange",
                    "organize downloads", "sort downloads", "arrange files",
                    # Archive
                    "zip", "unzip", "compress", "extract", "archive", "zip files",
                    "unzip files", "extract files", "compress files",
                    # Read/Write
                    "read file", "open file", "show file", "write file", "save file"
                ]
            },


            
            # App Control
            "app": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:open|launch|start)\s+(.+)",
                    r"(?:jarvis\s+)?(?:close|quit|exit)\s+(.+)",
                ],
                "keywords": ["open", "close", "launch", "start", "quit"]
            },
            

            
            # Website Capture (PDF) - NEW
            "capture": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:capture|save|convert)\s+(?:the\s+)?(?:website|page|url|site)\s+(.+?)(?:\s+(?:as|to)\s+pdf)?",
                    r"(?:jarvis\s+)?(?:save|download)\s+(.+?)\s+(?:as|to)\s+pdf",
                    r"(?:jarvis\s+)?(?:screenshot|capture)\s+(?:and\s+save\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:make|create|generate)\s+(?:a\s+)?pdf\s+(?:of|from)\s+(.+)",
                ],
                "keywords": [
                    "capture website", "capture page", "capture url",
                    "save as pdf", "save to pdf", "convert to pdf",
                    "website to pdf", "page to pdf", "url to pdf",
                    "download page", "download as pdf", "pdf of website",
                    "screenshot website", "screenshot page"
                ]
            },
            
            # Workflows (including Smart Workflows) - STRICT PATTERNS
            "workflow": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:start|begin|run|activate)\s+(?:my\s+)?(.+?)\s+(?:workflow|routine|mode)",
                    r"(?:jarvis\s+)?(?:execute)\s+(.+?)\s+(?:workflow|routine)",
                    r"(?:jarvis\s+)?(?:morning|work|gaming|focus|presentation|night)\s+(?:mode|routine)",
                ],
                "keywords": [
                    # Must be specific phrases, not single words
                    "start workflow", "run workflow", "activate workflow",
                    "morning routine", "morning mode", "start my day",
                    "work mode", "work routine", "office mode", "productive mode", "coding mode",
                    "gaming mode", "game mode",
                    "focus mode", "focus time", "deep work mode",
                    "presentation mode", "meeting mode", "demo mode",
                    "night mode", "sleep mode", "bedtime routine", "end my day",
                    "research mode", "study mode",
                    "break time", "take a break mode"
                ]
            },

            # Automation Chain Interactions (New)
            # Note: notepad commands are handled by priority check in detect()
            "interaction": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:write|type|draft|compose)\s+(?:a\s+|an\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:save)\s+(?:this\s+)?(?:file\s+)?(?:as\s+)?(.+)?",
                    r"(?:jarvis\s+)?(?:fill)\s+(?:this\s+)?(?:form|box|field)\s+(?:with\s+)?(.+)"
                ],
                "keywords": [
                    "write a letter", "write email", "type this", "draft a", "compose a",
                    "save file", "save as", "save document",
                    "fill form", "fill this"
                ]
            },

            # Confirmation for pending actions
            "confirm": {
                "patterns": [],
                "keywords": [
                    "yes", "yeah", "yep", "yes please", "sure", "do it", "go ahead",
                    "confirm", "proceed", "ok", "okay", "write it", "type it", "yes write"
                ]
            },

            # Email Automation
            "email": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:send|compose|draft|write)\s+(?:an?\s+)?email\s+(?:to\s+)?(.+?)(?:\s+about\s+(.+))?",
                    r"(?:jarvis\s+)?email\s+(.+?)(?:\s+about\s+(.+))?",
                ],
                "keywords": [
                    "send email", "compose email", "draft email", "write email",
                    "email to", "send mail", "mail to"
                ]
            },

            # Form Filling
            "form_fill": {
                "patterns": [
                    r"(?:jarvis\s+)?fill\s+(?:this\s+)?(?:form|fields?)\s*(?:with\s+)?(?:my\s+)?(?:details|info|data)?",
                    r"(?:jarvis\s+)?auto\s*fill\s+(?:this\s+)?(?:form|page)?",
                ],
                "keywords": [
                    "fill form", "fill this form", "auto fill", "autofill",
                    "fill with my details", "use my info"
                ]
            },
            
            # App Switching
            "switch": {
                "patterns": [
                    r"(?:jarvis\s+)?switch\s+(?:to\s+)?(?:app|application)?(?:\s+(.+))?",
                    r"(?:jarvis\s+)?focus\s+(?:on\s+)?(?:the\s+)?(?:window|app)?(?:\s+(.+))?",
                ],
                "keywords": ["switch", "focus", "window", "tab", "change app"]
            },
            
            # Gesture Control (Beast Mode)
            "gesture": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:start|stop|enable|disable)\s+(?:the\s+)?(?:gesture|vision|face)\s+(?:control|engine)?",
                    r"(?:jarvis\s+)?(?:track|follow)\s+(?:my\s+)?(?:nose|face|hands)",
                    r"(?:jarvis\s+)?(?:turn on|turn off)\s+gestures",
                    r"(?:jarvis\s+)?(?:wink|smile|blink)\s+action",
                ],
                "keywords": ["gesture", "vision control", "track nose", "face tracking", "gestures", "nose cursor"]
            },
            
            # Music/Media Control
            "music": {
                "patterns": [
                    r"(?:jarvis\s+)?play\s+(?:some\s+)?(?:music|song|track|audio)?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:pause|resume|stop)\s+(?:the\s+)?(?:music|song|track)?",
                    r"(?:jarvis\s+)?(?:next|previous|skip)\s+(?:song|track)?",
                    r"(?:jarvis\s+)?(?:increase|decrease)\s+(?:music\s+)?volume",
                ],
                "keywords": ["play", "music", "song", "pause", "resume", "stop", "next", "previous", "skip"]
            },

            # Gestures
            "gesture": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:start|stop|enable|disable)\s+(?:hand\s+)?gestures?",
                    r"(?:jarvis\s+)?turn\s+(?:on|off)\s+gestures?",
                ],
                "keywords": ["gesture", "hand control", "mouse control"]
            },
            
            # Reminders
            "reminder": {
                "patterns": [
                    r"(?:jarvis\s+)?remind\s+(?:me\s+)?to\s+(.+?)(?:\s+at\s+(.+))?",
                    r"(?:jarvis\s+)?set\s+(?:a\s+)?reminder\s+(?:for\s+)?(.+)",
                ],
                "keywords": ["reminder", "remind me", "alarm"]
            },
            
            # Image Generation
            "image": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:generate|create|make|draw)\s+(?:an?\s+)?(?:realistic\s+)?image\s+(?:of\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:generate|create)\s+(?:a\s+)?picture\s+(?:of\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:realistic\s+)?image\s+of\s+(.+)",
                ],
                "keywords": ["generate image", "create image", "draw", "picture of", "image of", "realistic image"]
            },

            # Math/Calculator
            "math": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:calculate|solve|compute)\s+(.+)",
                    r"(?:jarvis\s+)?what\s+is\s+(?:the\s+)?(?:result|value)\s+of\s+(.+)",
                ],
                "keywords": ["calculate", "solve", "math", "plus", "minus", "divided by", "multiplied by"]
            },

            # Translator
            "translate": {
                "patterns": [
                    r"(?:jarvis\s+)?translate\s+(.+?)\s+(?:to|into)\s+(.+)",
                    r"(?:jarvis\s+)?how\s+do\s+you\s+say\s+(.+?)\s+in\s+(.+)",
                ],
                "keywords": ["translate", "translation", "language"]
            },
            
            # Documents (PDF)
            "document": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:create|generate|make)\s+(?:a\s+)?(?:pdf|document|report)\s+(?:about|on|for|of)?\s*(.+)",
                    r"(?:jarvis\s+)?generate\s+(?:a\s+)?pdf\s+(.+)",
                ],
                "keywords": ["create pdf", "generate pdf", "pdf about", "make document", "generate report", "make a pdf"]
            },
            
            # Video Player
            "video": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:play|watch|show)\s+(?:video|youtube)?\s*(?:of\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:search|find)\s+(?:video|youtube)\s+(?:for\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:stop|pause)\s+(?:the\s+)?video",
                ],
                "keywords": ["play video", "watch video", "youtube", "play youtube", "stop video"]
            },
            
            # WhatsApp Automation
            "whatsapp": {
                "patterns": [
                    r"(?:send|write)\s+(?:a\s+)?(?:whatsapp\s+)?(?:message|msg|text)\s+to\s+(.+?)(?:\s+saying|\s*:)\s+(.+)",
                    r"(?:call|ring)\s+(.+?)\s+(?:on|via|through)\s+whatsapp",
                    r"(?:message|send\s+to)\s+(?:whatsapp\s+)?group\s+(.+?)(?:\s+saying|\s*:)\s+(.+)",
                    r"(?:whatsapp|message)\s+(.+?)(?:\s+saying|\s*:)\s+(.+)",
                ],
                "keywords": ["whatsapp", "send whatsapp", "call on whatsapp", "whatsapp group", "message on whatsapp"]
            },
            
            # Instagram Automation
            "instagram": {
                "patterns": [
                    r"(?:login|log in|sign in)\s+(?:to\s+)?instagram(?:\s+as\s+)?(?:\s+(.+))?",
                    r"(?:send|write)\s+(?:instagram\s+)?(?:dm|direct message|message)\s+to\s+(.+?)(?:\s+saying|\s*:)\s+(.+)",
                    r"(?:check|get|show)\s+(?:my\s+)?instagram\s+(?:messages|dms)",
                    r"(?:follow|unfollow)\s+(?:user\s+)?(.+?)\s+(?:on\s+)?instagram",
                    r"(?:search|find)\s+(?:instagram\s+)?(?:users?\s+)?(?:for\s+)?(.+)",
                    r"(?:get|show)\s+(?:instagram\s+)?(?:posts|feed)\s+(?:from|of)\s+(.+)",
                    r"(?:like|comment on)\s+(?:instagram\s+)?post",
                    r"(?:get|show)\s+(?:my\s+)?(?:instagram\s+)?followers",
                    r"(?:get|show)\s+(?:my\s+)?(?:instagram\s+)?following",
                    r"(?:post|upload)\s+(?:to\s+)?instagram",
                    r"(?:start|stop)\s+(?:instagram\s+)?(?:monitoring|dm monitoring)",
                ],
                "keywords": ["instagram", "insta", "ig", "dm", "follow", "unfollow", "instagram post", "instagram message"]
            },
            
            # RAG - Chat with Documents (NEW)
            "rag": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:add|upload|use)\s+(?:this\s+)?(?:url|link|website|page)\s+(?:for\s+)?(?:chat|questions?|rag)\s*:?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:chat|talk)\s+(?:with|about)\s+(?:my\s+)?(?:document|pdf|file|url)",
                    r"(?:jarvis\s+)?(?:what|tell me|explain)\s+(?:does|about)\s+(?:the\s+)?(?:document|pdf|article)\s+(?:say|mention|describe)\s+(?:about\s+)?(.+)?",
                    r"(?:jarvis\s+)?(?:ask|question)\s+(?:the\s+)?(?:document|pdf|article)\s+(?:about\s+)?(.+)?",
                    r"(?:jarvis\s+)?(?:summarize|analyze|read)\s+(?:this\s+)?(?:url|link|page|website)\s*:?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:add|upload)\s+(.+?)\s+(?:for|to)\s+(?:chat|rag|questions?)",
                ],
                "keywords": [
                    "add url for chat", "upload url for chat", "use url for chat",
                    "add link for chat", "upload link for questions", "add website for chat",
                    "chat with document", "chat with my document", "talk to document",
                    "chat with pdf", "talk to pdf", "ask document", "ask pdf",
                    "what does the document say", "what does my pdf say",
                    "summarize url", "summarize this url", "analyze url", "read this url",
                    "add for rag", "upload for rag", "document chat", "pdf chat"
                ]
            },
            
            # Multi-Agent System (NEW)
            "agents": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:use\s+)?(?:agents?|team|multi.?agent)\s+(?:to\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:research\s+and\s+write|research\s+then\s+write)\s+(?:about\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:deeply?\s+)?(?:research|investigate|analyze)\s+(.+?)\s+(?:and\s+)?(?:write|create|generate)\s+(?:a\s+)?(?:report|article|summary)",
                    r"(?:jarvis\s+)?(?:have\s+the\s+)?agents?\s+(?:work\s+on|handle|do)\s+(.+)",
                    r"(?:jarvis\s+)?(?:full\s+)?(?:research\s+)?pipeline\s+(?:on|for|about)\s+(.+)",
                ],
                "keywords": [
                    "use agents", "use the agents", "multi-agent", "agent team",
                    "research and write", "research then write", "deeply research",
                    "have agents", "agents work on", "full pipeline",
                    "research pipeline", "agent pipeline", "team of agents"
                ]
            },
            
            # Code Execution (NEW)
            "code": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:run|execute)\s+(?:this\s+)?(?:python\s+)?code\s*:?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:write|create|generate)\s+(?:a\s+)?(?:python|javascript|code)\s+(?:for|to|that)\s+(.+)",
                    r"(?:jarvis\s+)?(?:debug|fix)\s+(?:this\s+)?(?:code|error|bug)\s*:?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:explain|what\s+does)\s+(?:this\s+)?code\s*:?\s*(.+)?",
                    r"(?:jarvis\s+)?(?:help\s+me\s+)?(?:code|program|write\s+a\s+script)\s+(?:for|to|that)\s+(.+)",
                ],
                "keywords": [
                    "run code", "run this code", "execute code", "execute python",
                    "write code", "write python", "create code", "generate code",
                    "debug code", "fix code", "fix this error", "debug this",
                    "write a script", "code for", "program that", "python code"
                ]
            },
            
            # Device/System Status (Local Agent)
            "device_status": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:check|show|get|what['\s]?s|tell me)\s+(?:my\s+)?(?:pc|computer|device|system)\s+(?:status|stats|health|info|details)?",
                    r"(?:jarvis\s+)?(?:system|device|pc|computer)\s+status",
                    r"(?:jarvis\s+)?(?:how|what)\s+(?:is|are)\s+(?:my\s+)?(?:pc|computer|system)\s+(?:doing|running|performing)?",
                    r"(?:jarvis\s+)?(?:is\s+)?(?:my\s+)?(?:pc|computer|device)\s+(?:online|connected|available)\s*\??",
                    r"(?:jarvis\s+)?(?:check|show|get)\s+(?:cpu|ram|memory|uptime)",
                ],
                "keywords": [
                    "system status", "device status", "pc status", "computer status",
                    "check my pc", "check my computer", "check my device", "check my system",
                    "how is my pc", "how is my computer", "how is my system",
                    "is my pc online", "is my computer online", "is my device online",
                    "pc health", "system health", "computer health", "device health",
                    "show system status", "get system status", "what's my pc status",
                    "cpu usage", "ram usage", "memory usage", "system uptime",
                    "check cpu", "check ram", "check memory", "check uptime"
                ]
            },
            
            # Notepad Writing (Local Agent - write_notepad command)
            # FLEXIBLE patterns for natural language detection
            # Includes CREATIVE WRITING patterns for poems, letters, notes, etc.
            "notepad": {
                "patterns": [
                    # === CREATIVE WRITING PATTERNS (generate content) ===
                    # "write a poem about X in notepad"
                    r"(?:jarvis\s+)?(?:write|compose|create|craft)\s+(?:a\s+)?(?:poem|haiku|verse|letter|note|story|reflection|paragraph)\s+(?:about|to|for|on)\s+(.+?)(?:\s+in\s+notepad)?$",
                    # "in notepad write a poem about X"
                    r"(?:jarvis\s+)?(?:in\s+)?notepad\s+(?:write|compose|create)\s+(?:a\s+)?(?:poem|letter|note|story)\s+(?:about|to|for)\s+(.+)",
                    # Continuation patterns
                    r"(?:jarvis\s+)?(?:add|append|continue)\s+(?:another\s+)?(?:stanza|verse|paragraph|section)(?:\s+in\s+notepad)?",
                    r"(?:jarvis\s+)?(?:continue|extend)\s+(?:the\s+)?(?:poem|letter|story|writing)(?:\s+in\s+notepad)?",
                    
                    # === DIRECT WRITING PATTERNS (write exact text) ===
                    # "write X to notepad" / "type X in notepad"
                    r"(?:jarvis\s+)?(?:can you\s+)?(?:please\s+)?(?:write|type|put|add)\s+(.+?)\s+(?:to|in|into|on)\s+notepad",
                    # "write to notepad: X" / "notepad: X"
                    r"(?:jarvis\s+)?(?:write|type|put|add)\s+(?:to|in|into)\s+notepad\s*[:]\s*(.+)",
                    r"(?:jarvis\s+)?notepad\s*[:]\s*(.+)",
                    # "take a note: X" / "note: X"
                    r"(?:jarvis\s+)?(?:take|make)\s+(?:a\s+)?note\s*[:]\s*(.+)",
                    r"(?:jarvis\s+)?note\s*[:]\s*(.+)",
                    # "note down X" / "jot down X"
                    r"(?:jarvis\s+)?(?:note|jot)\s+(?:this\s+)?down\s*[:]\s*(.+)",
                    r"(?:jarvis\s+)?(?:note|jot)\s+(?:this\s+)?down\s+(.+)",
                    # "notepad and write X" / "open notepad and type X"
                    r"(?:jarvis\s+)?(?:open\s+)?notepad\s+(?:and\s+)?(?:write|type)\s*[:]\s*(.+)",
                    r"(?:jarvis\s+)?(?:open\s+)?notepad\s+(?:and\s+)?(?:write|type)\s+(.+)",
                    # "save X to notepad" / "remember X in notepad"
                    r"(?:jarvis\s+)?(?:save|store|remember|keep)\s+(.+?)\s+(?:to|in|into|on)\s+notepad",
                    # "can you write X in notepad"
                    r"(?:jarvis\s+)?(?:can you|could you|please)\s+(?:write|type|note|jot)\s+(.+?)\s+(?:to|in|into|on)\s+notepad",
                    # Simple patterns for command extraction
                    r"(?:jarvis\s+)?(?:write|type)\s+(?:in\s+)?notepad\s+(.+)",
                ],
                "keywords": [
                    # === CREATIVE WRITING KEYWORDS ===
                    "write a poem", "compose a poem", "create a poem", "poem about", "poem for",
                    "write a letter", "compose a letter", "letter to", "letter for",
                    "write a note", "make a note about", "note about",
                    "write a story", "short story about", "story about",
                    "write a reflection", "reflection on", "reflection about",
                    "add another stanza", "add a verse", "continue the poem",
                    "add another paragraph", "continue writing", "extend the",
                    
                    # === ACTION + NOTEPAD ===
                    "write to notepad", "write in notepad", "type in notepad", "type to notepad",
                    "add to notepad", "put in notepad", "save to notepad", "store in notepad",
                    # Note variations
                    "take a note", "take note", "make a note", "make note",
                    "note down", "note this down", "jot down", "jot this down",
                    # Notepad + action
                    "notepad write", "notepad type", "notepad:", "note:",
                    "open notepad and write", "open notepad and type",
                    # Natural phrasing
                    "write this to notepad", "type this in notepad", "put this in notepad",
                    "can you note", "note this for me", "notepad this",
                    "remind me in notepad", "save this to notepad", "remember in notepad",
                    # Short triggers
                    "to notepad", "in notepad", "into notepad"
                ]
            },
            
            # Writing Continuity - Continue, Extend, Refine previous writing
            # This catches continuation requests when user wants to extend what Kai just wrote
            "continue_writing": {
                "patterns": [
                    # Continue / Keep going
                    r"(?:jarvis\s+)?continue\s+(?:this|that|writing|it|the\s+\w+)?",
                    r"(?:jarvis\s+)?keep\s+(?:going|writing)",
                    r"(?:jarvis\s+)?go\s+on",
                    # Add more content
                    r"(?:jarvis\s+)?add\s+(?:another|more|a|one\s+more|\d+\s+more)\s+(?:stanza|stanzas|verse|verses|paragraph|paragraphs|section|sections|line|lines)",
                    r"(?:jarvis\s+)?(?:write|give\s+me)\s+(?:another|more|one\s+more|\d+\s+more)\s+(?:stanza|verse|paragraph|line|lines)",
                    # Extend / Expand
                    r"(?:jarvis\s+)?extend\s+(?:this|that|it|the\s+\w+)?",
                    r"(?:jarvis\s+)?expand\s+(?:on\s+)?(?:this|that|it)?",
                    r"(?:jarvis\s+)?make\s+(?:it|this|that)\s+longer",
                    # Rewrite / Change ending
                    r"(?:jarvis\s+)?rewrite\s+(?:the\s+)?(?:last\s+)?(?:part|ending|section|paragraph|stanza)",
                    r"(?:jarvis\s+)?change\s+(?:the\s+)?(?:ending|last\s+part|tone|mood)",
                    r"(?:jarvis\s+)?redo\s+(?:the\s+)?(?:ending|last\s+part)",
                    # Mood modifications
                    r"(?:jarvis\s+)?make\s+(?:it|this|that|the\s+ending)\s+(?:darker|lighter|happier|sadder|shorter|better|stronger|more\s+\w+)",
                ],
                "keywords": [
                    # Continuation
                    "continue this", "continue that", "continue writing", "continue it",
                    "keep going", "keep writing", "go on", "more please",
                    # Adding content
                    "add another stanza", "add a verse", "add another verse",
                    "add another paragraph", "add more lines", "add two more lines",
                    "one more stanza", "another stanza", "one more verse",
                    "write another stanza", "give me another",
                    # Extending
                    "extend this", "extend it", "extend the poem", "extend the paragraph",
                    "make it longer", "expand this", "expand on that", "expand on this",
                    # Refinement / Rewriting
                    "rewrite the ending", "rewrite the last part", "rewrite this",
                    "change the ending", "change the tone", "change the mood",
                    "redo the ending", "fix the ending",
                    # Mood modifications
                    "make it darker", "make it lighter", "make it happier",
                    "make it sadder", "make it shorter", "make the ending better",
                    "make it more dramatic", "make it more emotional",
                    "make it stronger", "make it softer"
                ]
            }
        }
        self.use_classifier = use_classifier
        self.classifier = LocalClassifier() if use_classifier else None
    
    def detect(self, query: str) -> Tuple[str, Optional[str], float]:
        """
        Detect intent using ENSEMBLE approach (Best of Regex & Semantic).
        Returns: (trigger_type, extracted_command, confidence)
        """
        query_lower = query.lower().strip()
        
        # --- Result Candidates ---
        regex_result = ("general", None, 0.0)
        semantic_result = ("general", None, 0.0)

        # PRIORITY CHECK: Notepad commands (EXPLICIT REQUEST ONLY)
        # Chat is DEFAULT. Notepad only when user explicitly asks for it.
        # This ensures "write a poem" goes to chat, but "write a poem in notepad" goes to notepad.
        explicit_notepad_keywords = [
            "to notepad", "in notepad", "into notepad", "on notepad",
            "notepad:", "notepad and", "open notepad",
            "on my pc", "on my computer", "to my pc", "to my computer",
            "on my desktop", "to my desktop"
        ]
        
        # Only trigger notepad if user EXPLICITLY requested it
        has_explicit_notepad_request = any(kw in query_lower for kw in explicit_notepad_keywords)
        
        if has_explicit_notepad_request:
            # User explicitly wants to write to notepad/PC
            for pattern in self.triggers.get("notepad", {}).get("patterns", []):
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match and match.groups() and match.group(1):
                    return ("notepad", match.group(1).strip(), 1.0)
            # Fallback: return the whole query
            return ("notepad", query, 0.9)

        # PRIORITY CHECK: Open/Close App Commands
        # These should be detected before search to avoid "open brave" triggering web search
        whitelisted_apps = [
            # Browsers
            "browser", "chrome", "firefox", "edge", "brave", "opera", "vivaldi", "safari",
            # Development
            "vscode", "code", "terminal", "cmd", "powershell", "postman", "docker",
            # Productivity
            "notepad", "word", "excel", "outlook", "powerpoint", "onenote", "notion", "obsidian",
            # Communication
            "teams", "slack", "discord", "zoom", "skype", "telegram", "whatsapp", "signal",
            # Media
            "spotify", "vlc", "itunes", "winamp", "obs", "audacity",
            # System
            "explorer", "calculator", "paint", "snipping", "settings",
            # Games
            "steam", "epicgames", "epic", "origin", "ubisoft", "gog"
        ]
        
        # Check for "open X" pattern
        open_match = re.match(r"^(?:jarvis\s+)?(?:open|launch|start|run)\s+(\w+)(?:\s+app)?$", query_lower)
        if open_match:
            app_name = open_match.group(1)
            if app_name in whitelisted_apps:
                return ("open_app", app_name, 1.0)
        
        # Check for "close X" pattern  
        close_match = re.match(r"^(?:jarvis\s+)?(?:close|quit|exit|stop|kill|terminate)\s+(\w+)(?:\s+app)?$", query_lower)
        if close_match:
            app_name = close_match.group(1)
            if app_name in whitelisted_apps:
                return ("close_app", app_name, 1.0)

        # PRIORITY CHECK: System Controls (volume, brightness, mute, lock)
        # Volume patterns
        volume_set = re.match(r"^(?:jarvis\s+)?(?:set\s+)?volume\s+(?:to\s+)?(\d+)(?:\s*%)?$", query_lower)
        if volume_set:
            level = int(volume_set.group(1))
            return ("system_control", {"action": "set_volume", "level": level}, 1.0)
        
        if re.match(r"^(?:jarvis\s+)?(?:turn\s+)?volume\s+(?:up|higher|increase|louder)$", query_lower):
            return ("system_control", {"action": "volume_up"}, 1.0)
        
        if re.match(r"^(?:jarvis\s+)?(?:turn\s+)?volume\s+(?:down|lower|decrease|quieter)$", query_lower):
            return ("system_control", {"action": "volume_down"}, 1.0)
        
        if any(kw in query_lower for kw in ["increase volume", "raise volume", "louder", "turn up volume"]):
            return ("system_control", {"action": "volume_up"}, 0.95)
        
        if any(kw in query_lower for kw in ["decrease volume", "lower volume", "quieter", "turn down volume"]):
            return ("system_control", {"action": "volume_down"}, 0.95)
        
        # Mute patterns
        if re.match(r"^(?:jarvis\s+)?(?:mute|silence)(?:\s+(?:my\s+)?(?:pc|computer|audio|sound))?$", query_lower):
            return ("system_control", {"action": "mute"}, 1.0)
        
        if re.match(r"^(?:jarvis\s+)?unmute(?:\s+(?:my\s+)?(?:pc|computer|audio|sound))?$", query_lower):
            return ("system_control", {"action": "unmute"}, 1.0)
        
        # Brightness patterns
        brightness_set = re.match(r"^(?:jarvis\s+)?(?:set\s+)?brightness\s+(?:to\s+)?(\d+)(?:\s*%)?$", query_lower)
        if brightness_set:
            level = int(brightness_set.group(1))
            return ("system_control", {"action": "set_brightness", "level": level}, 1.0)
        
        if re.match(r"^(?:jarvis\s+)?(?:increase|raise|higher)\s+brightness$", query_lower):
            return ("system_control", {"action": "brightness_up"}, 1.0)
        
        if re.match(r"^(?:jarvis\s+)?(?:decrease|lower|dim)\s+brightness$", query_lower):
            return ("system_control", {"action": "brightness_down"}, 1.0)
        
        # Natural language brightness: full, max, min
        if any(kw in query_lower for kw in ["brightness full", "full brightness", "brightness max", "max brightness", "maximum brightness"]):
            return ("system_control", {"action": "set_brightness", "level": 100}, 0.95)
        
        if any(kw in query_lower for kw in ["brightness min", "min brightness", "minimum brightness", "brightness low", "lowest brightness"]):
            return ("system_control", {"action": "set_brightness", "level": 10}, 0.95)
        
        if any(kw in query_lower for kw in ["brighter", "more brightness", "increase brightness"]):
            return ("system_control", {"action": "brightness_up"}, 0.95)
        
        if any(kw in query_lower for kw in ["dimmer", "less brightness", "decrease brightness", "lower brightness"]):
            return ("system_control", {"action": "brightness_down"}, 0.95)
        
        # Lock screen patterns
        if re.match(r"^(?:jarvis\s+)?lock(?:\s+(?:my\s+)?(?:screen|pc|computer))?$", query_lower):
            return ("system_control", {"action": "lock_screen"}, 1.0)
        
        if any(kw in query_lower for kw in ["lock my screen", "lock my pc", "lock my computer", "lock screen"]):
            return ("system_control", {"action": "lock_screen"}, 0.95)

        # PRIORITY CHECK: File Manager (sandboxed file operations)
        # Create folder patterns
        folder_match = re.match(r"^(?:jarvis\s+)?(?:create|make|new)\s+(?:a\s+)?folder\s+(?:called\s+|named\s+|for\s+)?(.+)$", query_lower)
        if folder_match:
            folder_name = folder_match.group(1).strip()
            return ("file_manager", {"action": "create_folder", "name": folder_name}, 1.0)
        
        if any(kw in query_lower for kw in ["create folder", "make folder", "new folder", "create a folder"]):
            return ("file_manager", {"action": "create_folder"}, 0.9)
        
        # Save file patterns (linked to writing context)
        save_match = re.match(r"^(?:jarvis\s+)?save\s+(?:this|that|it)\s+(?:as\s+)?(?:a\s+)?(?:file)?(?:\s+called\s+|\s+named\s+)?(.*)$", query_lower)
        if save_match:
            file_name = save_match.group(1).strip() if save_match.group(1) else None
            return ("file_manager", {"action": "save_file", "name": file_name}, 1.0)
        
        if any(kw in query_lower for kw in ["save this as", "save as file", "save to file", "save this file"]):
            return ("file_manager", {"action": "save_file"}, 0.95)
        
        # List files patterns
        if any(kw in query_lower for kw in ["list files", "show files", "show my files", "list my files", 
                                             "my kai files", "kai files", "what files", "show my kai"]):
            return ("file_manager", {"action": "list_files"}, 0.95)
        
        # Open folder patterns
        if any(kw in query_lower for kw in ["open kai folder", "open my kai", "open folder", "show folder",
                                             "open documents", "open my documents"]):
            return ("file_manager", {"action": "open_folder"}, 0.95)
        
        # Delete file patterns (careful - only Kai-created)
        delete_match = re.match(r"^(?:jarvis\s+)?(?:delete|remove)\s+(?:the\s+)?(?:file\s+)?(?:called\s+|named\s+)?(.+)$", query_lower)
        if delete_match:
            file_name = delete_match.group(1).strip()
            if file_name and file_name not in ["file", "it", "this", "that"]:
                return ("file_manager", {"action": "delete_file", "name": file_name}, 0.95)
        
        if any(kw in query_lower for kw in ["delete last file", "delete the last", "remove last file"]):
            return ("file_manager", {"action": "delete_file", "name": "last"}, 0.95)

        # PRIORITY CHECK: Writing Continuity (continue, extend, refine)
        # These should be detected before other patterns to avoid conflicts
        continuation_keywords = [
            "continue this", "continue that", "continue writing", "continue it",
            "keep going", "keep writing", "go on",
            "add another stanza", "add a verse", "add another verse", "add another paragraph",
            "add more lines", "add two more lines", "one more stanza", "another stanza",
            "extend this", "extend it", "extend the", "make it longer", "expand this",
            "rewrite the ending", "rewrite the last", "change the ending", "change the tone",
            "make it darker", "make it lighter", "make it happier", "make it sadder",
            "make it shorter", "make it better", "make it stronger"
        ]
        
        if any(kw in query_lower for kw in continuation_keywords):
            # Check if this is truly a continuation (not a new creative request)
            # New creative requests have "about", "for", "to" after the content type
            is_new_creative = any(phrase in query_lower for phrase in [
                "poem about", "poem for", "letter to", "letter for", "story about",
                "write a poem", "write a letter", "compose a", "create a"
            ])
            
            if not is_new_creative:
                # User wants to continue/modify existing content
                for pattern in self.triggers.get("continue_writing", {}).get("patterns", []):
                    match = re.search(pattern, query_lower, re.IGNORECASE)
                    if match:
                        return ("continue_writing", query, 1.0)
                # Keyword match fallback
                return ("continue_writing", query, 0.95)

        # 1. REGEX MATCHING
        for trigger_name, data in self.triggers.items():
            for pattern in data["patterns"]:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    command = match.group(1).strip() if match.groups() and match.group(1) else query
                    regex_result = (trigger_name, command, 1.0)  # Regex exact match = 1.0 confidence
                    break
            if regex_result[2] == 1.0:
                break  # Found exact regex match, stop searching
            
            # Keyword fallback (lower confidence)
            if any(kw in query_lower for kw in data["keywords"]):
                if 0.7 > regex_result[2]:  # Only if no better match found
                    regex_result = (trigger_name, query, 0.7)

        # 2. SEMANTIC CLASSIFICATION (Run if classifier available)
        if self.use_classifier and self.classifier:
            try:
                result = self.classifier.classify(query)
                intent = result.get("intent")
                conf = result.get("confidence", 0.0)
                
                # Use class-level intent mapping
                mapped_trigger = self.classifier_intent_map.get(intent, "general")
                
                # Only use classifier result if it's actionable and confident
                if mapped_trigger != "general" and conf > 0.4:
                    semantic_result = (mapped_trigger, query, conf)
                elif mapped_trigger == "general" and conf > 0.6:
                    # High confidence general = let it through
                    semantic_result = ("general", query, conf * 0.8)
            except Exception as e:
                print(f"[SmartTrigger] Classifier error: {e}")

        # 3. ENSEMBLE: Compare and return BEST result
        print(f"[SmartTrigger-Ensemble] Regex: {regex_result[0]}({regex_result[2]:.2f}), Semantic: {semantic_result[0]}({semantic_result[2]:.2f})")
        
        if regex_result[2] >= semantic_result[2]:
            return regex_result
        else:
            return semantic_result
    
    def is_chrome_command(self, query: str) -> bool:
        """Quick check if it's a Chrome command"""
        trigger, _, _ = self.detect(query)
        return trigger == "chrome"
    
    def is_vision_command(self, query: str) -> bool:
        """Quick check if it's a vision command"""
        trigger, _, _ = self.detect(query)
        return trigger == "vision"
    
    def is_memory_command(self, query: str) -> bool:
        """Quick check if it's a memory command"""
        trigger, _, _ = self.detect(query)
        return trigger == "memory"
    
    def extract_chrome_action(self, query: str) -> Tuple[str, str]:
        """
        Extract Chrome action and target
        Returns: (action, target)
        """
        query_lower = query.lower().strip()
        
        # Search patterns
        if re.search(r"search\s+(?:for\s+)?(.+)", query_lower):
            match = re.search(r"search\s+(?:for\s+)?(.+)", query_lower)
            return ("search", match.group(1))
        
        # Open URL patterns
        if re.search(r"(?:open|go to|visit)\s+(.+)", query_lower):
            match = re.search(r"(?:open|go to|visit)\s+(.+)", query_lower)
            target = match.group(1).replace("in chrome", "").strip()
            return ("open", target)
        
        # Navigation
        if "back" in query_lower:
            return ("back", "")
        if "forward" in query_lower:
            return ("forward", "")
        if "refresh" in query_lower:
            return ("refresh", "")
        
        # Tab management
        if "new tab" in query_lower:
            return ("new_tab", "")
        if "close tab" in query_lower:
            return ("close_tab", "")
        
        return ("unknown", query)

# Global instance
smart_trigger = SmartTrigger()

if __name__ == "__main__":
    # Test
    test_queries = [
        "Jarvis open google.com",
        "search for Python tutorials",
        "what's on my screen",
        "remember that I like pizza",
        "increase volume",
        "create file test.txt",
        "scrape data from example.com"
    ]
    
    for query in test_queries:
        trigger, command, _ = smart_trigger.detect(query)
        print(f"Query: {query}")
        print(f"  Trigger: {trigger}")
        print(f"  Command: {command}")
        print()
