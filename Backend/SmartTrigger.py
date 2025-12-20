"""
Smart Trigger System - JARVIS Level
====================================
Intelligent phrase detection with flexible activation
"""

import re
from typing import List, Tuple, Optional

class SmartTrigger:
    def __init__(self, use_classifier=False):
        self.use_classifier = use_classifier
        self.classifier = None
        if self.use_classifier:
            try:
                from Backend.LocalClassifier import LocalClassifier
                self.classifier = LocalClassifier(use_model=True)
            except Exception as e:
                print(f"[SmartTrigger] Failed to load LocalClassifier: {e}")
        
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
            
            # Web Scraping - Enhanced patterns
            "scrape": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:scrape|extract|get)\s+(?:data\s+)?(?:from\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:fetch|retrieve)\s+(?:information\s+)?(?:from\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:analyze|read|parse)\s+(?:the\s+)?(?:website|page|site)\s+(.+)",
                    r"(?:jarvis\s+)?(?:what's on|what is on|summarize)\s+(.+\.(?:com|org|net|io|co).*)",
                ],
                "keywords": [
                    "scrape", "scrape website", "scrape url", "scrape page",
                    "extract data", "extract from", "get data from",
                    "fetch website", "fetch page", "fetch url",
                    "analyze website", "analyze page", "read website",
                    "parse website", "parse page", "get content from"
                ]
            },
            
            # Live Streams (Radio & TV) - NEW
            "stream": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:play|stream|tune\s+in\s+to)\s+(?:the\s+)?(?:radio|music\s+radio|live\s+radio)\s*(.+)?",
                    r"(?:jarvis\s+)?(?:play|watch|stream)\s+(?:live\s+)?(?:tv|news|television)\s*(.+)?",
                    r"(?:jarvis\s+)?(?:listen\s+to|tune\s+to)\s+(.+?)(?:\s+radio|\s+stream)?",
                    r"(?:jarvis\s+)?(?:play|stream)\s+(?:lofi|jazz|classical|ambient|focus|chill)\s*(?:music|radio|beats)?",
                ],
                "keywords": [
                    "play radio", "stream radio", "live radio", "tune in",
                    "listen to radio", "lofi radio", "jazz radio", "classical radio",
                    "stream lofi", "chill beats radio", "focus radio",
                    "watch news", "live news", "stream news", "live tv",
                    "watch tv", "stream tv", "news channel", "sky news", "bbc news",
                    "ambient radio", "nature sounds radio", "rain sounds radio"
                ]
            },
            
            # Spotify Music - NEW (for songs, artists, albums)
            "spotify": {
                "patterns": [
                    r"(?:jarvis\s+)?(?:play|listen to)\s+(?:the\s+)?(?:song\s+)?(.+?)(?:\s+on\s+spotify)?",
                    r"(?:jarvis\s+)?(?:spotify|music)\s+(.+)",
                    r"(?:jarvis\s+)?(?:play|queue)\s+(?:some\s+)?(.+?)(?:\s+music)?",
                ],
                "keywords": [
                    "play", "play music", "play song", "play songs", "listen to",
                    "spotify", "on spotify", "play on spotify",
                    "play artist", "play album", "play playlist",
                    "queue", "queue song", "add to queue",
                    "play drake", "play taylor", "play weeknd", "play ed sheeran",
                    "play pop", "play rock", "play hip hop", "play jazz music",
                    "play classical music", "play indie", "play electronic",
                    "play lofi", "play chill", "play relaxing music",
                    "what song", "next song", "skip song", "previous song"
                ]
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
                    r"(?:jarvis\s+)?(?:generate|create|make|draw)\s+(?:an?|the)?\s*image\s+(?:of\s+)?(.+)",
                    r"(?:jarvis\s+)?(?:generate|create)\s+(?:a\s+)?picture\s+(?:of\s+)?(.+)",
                    r"(?:jarvis\s+)?image\s+of\s+(.+)",
                ],
                "keywords": ["generate image", "create image", "draw", "picture of", "image of"]
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

        # 2. SEMANTIC CLASSIFICATION (Run in parallel if classifier available)
        if self.use_classifier and self.classifier:
            try:
                result = self.classifier.classify(query)
                intent = result.get("intent")
                conf = result.get("confidence", 0.0)
                
                # Map classifier intent to SmartTrigger types
                mapping = {
                    "vision_analysis": "vision",
                    "web_search": "chrome",
                    "memory_update": "memory",
                    "memory_query": "memory",
                    "code_generation": "general",
                    "system_command": "system",
                    "file_operation": "file",
                    "chat_response": "general"
                }
                
                mapped_trigger = mapping.get(intent, "general")
                if mapped_trigger != "general" and conf > 0.4:
                    semantic_result = (mapped_trigger, query, conf)
            except Exception as e:
                print(f"[SmartTrigger] Semantic classification error: {e}")

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
