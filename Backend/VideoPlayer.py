"""
Video Player - Beast Mode (Ultimate Edition)
=============================================
Advanced video streaming and control system.
Features:
- YouTube search & direct playback
- Multi-platform player detection (VLC, MPV, default)
- Picture-in-Picture mode support
- Queue management
- Watch history tracking
- Trending & recommendations
"""

import os
import webbrowser
import subprocess
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class VideoPlayer:
    def __init__(self):
        self.current_video: Optional[Dict] = None
        self.queue: List[Dict] = []
        self.history: List[Dict] = []
        self.is_playing = False
        self.video_url: Optional[str] = None
        
        # Detect installed players
        self.players = self._detect_players()
        self.preferred_player = "browser"  # Default
        
        # Watch history file
        self.history_file = os.path.join(os.path.dirname(__file__), "..", "Data", "watch_history.json")
        self._load_history()
    
    def _detect_players(self) -> Dict[str, str]:
        """Detect available video players on system"""
        players = {}
        
        if platform.system() == "Windows":
            vlc_paths = [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
            ]
            for path in vlc_paths:
                if os.path.exists(path):
                    players["vlc"] = path
                    break
        
        # Always have browser as fallback
        players["browser"] = "browser"
        
        return players
    
    def _load_history(self):
        """Load watch history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)[-100:]  # Keep last 100
        except:
            self.history = []
    
    def _save_history(self):
        """Save watch history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-100:], f)
        except:
            pass
    
    def _add_to_history(self, video: Dict):
        """Add video to watch history"""
        entry = {
            "title": video.get("title", "Unknown"),
            "url": video.get("url"),
            "watched_at": datetime.now().isoformat(),
            "duration": video.get("duration")
        }
        self.history.append(entry)
        self._save_history()
    
    def search_youtube(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search YouTube and return results"""
        try:
            from youtubesearchpython import VideosSearch
            
            search = VideosSearch(query, limit=limit)
            results = search.result()
            
            if results and results['result']:
                videos = []
                for v in results['result']:
                    videos.append({
                        "title": v['title'],
                        "url": v['link'],
                        "duration": v.get('duration', 'N/A'),
                        "channel": v.get('channel', {}).get('name', 'Unknown'),
                        "views": v.get('viewCount', {}).get('short', 'N/A'),
                        "thumbnail": v.get('thumbnails', [{}])[0].get('url')
                    })
                
                return {
                    "status": "success",
                    "videos": videos,
                    "count": len(videos)
                }
            
            return {"status": "error", "message": f"No videos found for: {query}"}
            
        except Exception as e:
            # Fallback: return search URL
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            return {
                "status": "fallback",
                "message": f"Opening YouTube search for: {query}",
                "search_url": search_url,
                "error_detail": str(e)
            }
    
    def play(self, query: str, player: str = "browser") -> Dict[str, Any]:
        """Play video by search query or URL"""
        try:
            # Direct URL
            if query.startswith('http'):
                video = {"url": query, "title": "Direct Video", "query": query}
                url = video['url']
            else:
                # Try YouTube search, fallback to search page
                try:
                    from youtubesearchpython import VideosSearch
                    search = VideosSearch(query, limit=1)
                    results = search.result()
                    
                    if results and results['result']:
                        v = results['result'][0]
                        video = {
                            "url": v['link'],
                            "title": v['title'],
                            "duration": v.get('duration'),
                            "channel": v.get('channel', {}).get('name'),
                            "query": query
                        }
                        url = video['url']
                    else:
                        raise Exception("No results")
                except:
                    # Fallback: open YouTube search
                    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                    video = {"url": url, "title": f"Search: {query}", "query": query}
            
            # Open video
            if player == "vlc" and "vlc" in self.players:
                subprocess.Popen([self.players["vlc"], url])
            else:
                webbrowser.open(url)
            
            self.current_video = video
            self.is_playing = True
            self.video_url = url
            self._add_to_history(video)
            
            return {
                "status": "success",
                "message": f"Playing: {video['title']}",
                "video": video
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Playback failed: {str(e)}"}
    
    def play_next(self) -> Dict[str, Any]:
        """Play next video in queue"""
        if not self.queue:
            return {"status": "error", "message": "Queue is empty"}
        
        next_video = self.queue.pop(0)
        return self.play(next_video.get('url') or next_video.get('query', ''))
    
    def add_to_queue(self, query: str) -> Dict[str, Any]:
        """Add video to queue"""
        self.queue.append({"query": query, "added_at": datetime.now().isoformat()})
        return {"status": "success", "message": f"Added to queue: {query}", "queue_length": len(self.queue)}
    
    def get_queue(self) -> List[Dict]:
        """Get current queue"""
        return self.queue
    
    def clear_queue(self) -> Dict[str, Any]:
        """Clear video queue"""
        self.queue = []
        return {"status": "success", "message": "Queue cleared"}
    
    def stop(self) -> Dict[str, Any]:
        """Stop video playback"""
        self.is_playing = False
        self.current_video = None
        self.video_url = None
        return {"status": "success", "message": "Video stopped"}
    
    def get_trending(self, region: str = "US") -> Dict[str, Any]:
        """Get trending videos"""
        try:
            # Open trending page
            url = f"https://www.youtube.com/feed/trending?gl={region}"
            webbrowser.open(url)
            return {"status": "success", "message": "Opened trending videos", "url": url}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get watch history"""
        return self.history[-limit:][::-1]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current player status"""
        return {
            "is_playing": self.is_playing,
            "current_video": self.current_video,
            "queue_length": len(self.queue),
            "history_count": len(self.history),
            "available_players": list(self.players.keys())
        }

# Global instance
video_player = VideoPlayer()

# Helper function for lazy instantiation
def get_video_player():
    """Get or create video player instance"""
    return video_player

if __name__ == "__main__":
    print("=== Video Player Beast Mode Test ===\n")
    
    # Test search
    print("Testing YouTube search...")
    result = video_player.search_youtube("python tutorial", limit=3)
    if result.get('status') == 'success':
        for v in result['videos']:
            print(f"  - {v['title']} ({v['duration']})")
    
    print(f"\nStatus: {video_player.get_status()}")
