"""
TypeQuery - Web Version
=======================
Simplified query processing for web deployment.
Local-only features (Automation, SpeechToText, TextToSpeech) are disabled.
"""

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Chatbot import ChatBot

# Stub imports for web compatibility
def Automation(*args, **kwargs):
    """Automation is not available on web deployment."""
    return None

def SpeechRecognition(*args, **kwargs):
    """Speech recognition is not available on web deployment."""
    return None

def TextToSpeech(*args, **kwargs):
    """Text-to-speech is not available on web deployment."""
    return None


# Web scraping integration
try:
    from Backend.DirectWebScrapingIntegration import integrate_web_scraping
except ImportError:
    def integrate_web_scraping(*args, **kwargs):
        return None


# Helper stubs for web deployment
def SetAssistantStatus(status):
    print(f"[Status] {status}")

def ShowTextToScreen(text):
    print(text)

def QueryModifier(query):
    return query

TempDirectoryPath = "/tmp"
Assistantname = "KAI"
Username = "User"


def TypeQuery(query):
    """
    Process a query and return a response.
    Web-compatible version - no automation.
    """
    TaskExecution = False 
    ImageExecution = False
    ImageGenerationQuery = ""
    
    SetAssistantStatus("Thinking...")
    
    try:
        Decision = FirstLayerDMM(query)
        print(f"Decision: {Decision}")
        
        # Normalize decisions
        normalized = []
        for item in Decision:
            if item.startswith("general "):
                rest = item[len("general "):]
                normalized.append(rest)
            else:
                normalized.append(item)
        Decision = normalized
        
    except Exception as e:
        print(f"Decision error: {e}")
        # Fallback to chat
        return ChatBot(query)
    
    G = any([i for i in Decision if "general" in str(i).lower()])
    R = any([i for i in Decision if "realtime" in str(i).lower()])
    
    Merged_query = " and ".join([str(i) for i in Decision])
    
    # Check for image generation
    for queries in Decision:
        if "generate " in str(queries).lower():
            ImageGenerationQuery = str(queries)
            ImageExecution = True
    
    # Handle anime streaming
    A = any([i for i in Decision if "anime" in str(i).lower()])
    if A:
        try:
            SetAssistantStatus("Loading anime...")
            from Backend.AnimeStreaming import anime_system
            
            # Extract anime name and episode from query
            anime_query = query.lower()
            for prefix in ["watch anime ", "play anime ", "stream anime ", "anime ", "watch ", "play ", "stream "]:
                if anime_query.startswith(prefix):
                    anime_query = anime_query[len(prefix):]
                    break
            
            # Check for episode number
            import re
            ep_match = re.search(r'\bepisode\s+(\d+)\b', anime_query)
            episode = int(ep_match.group(1)) if ep_match else 1
            anime_name = re.sub(r'\bepisode\s+\d+\b', '', anime_query).strip()
            
            # Get stream data
            result = anime_system.watch_anime(anime_name, episode)
            
            if result.get("status") == "success":
                # Return with proper metadata for frontend
                return {
                    "type": "anime",
                    "text": result.get("message", f"🎬 Now playing: {anime_name} Episode {episode}"),
                    "anime": result  # Pass all the stream data
                }
            else:
                return f"❌ Could not stream '{anime_name}': {result.get('message', 'Unknown error')}"
        except Exception as e:
            print(f"Anime error: {e}")
            return f"❌ Anime streaming error: {str(e)}"
    
    # Handle realtime searches
    if R:
        try:
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(Merged_query)
            return Answer
        except Exception as e:
            print(f"Search error: {e}")
            return ChatBot(Merged_query)
    
    # Handle general queries
    try:
        Answer = ChatBot(Merged_query)
        return Answer
    except Exception as e:
        return f"Error processing query: {e}"


if __name__ == "__main__":
    # Test
    result = TypeQuery("What is the weather today?")
    print(f"Result: {result}")
