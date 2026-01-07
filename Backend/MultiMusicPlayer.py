"""
Multi-Source Music Player - Beast Mode
=======================================
Unified music player supporting multiple platforms:
- YouTube (existing)
- Spotify (embeds)
- SoundCloud (embeds)
Features:
- Auto-source selection
- Playlist support
- Embed-ready URLs for web playback
"""

import re
import json
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import quote_plus, urlparse

try:
    from Backend.YouTubePlayer import youtube_player
except ImportError:
    youtube_player = None

class MultiMusicPlayer:
    """Play music from YouTube, Spotify, and SoundCloud"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Platform detection patterns
        self.platform_patterns = {

            'soundcloud': [
                r'soundcloud\.com/([^/]+)/([^/\?]+)',
                r'm\.soundcloud\.com/([^/]+)/([^/\?]+)'
            ],
            'youtube': [
                r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})'
            ]
        }
    
    def _detect_platform(self, query: str) -> tuple:
        """Detect if query is a URL and which platform it's from"""
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    return platform, match.groups()
        return None, None
    
    # ==================== YOUTUBE ====================
    
    def search_youtube(self, query: str, max_results: int = 1) -> List[Dict]:
        """Search YouTube for music using API or scraping"""
        # Try API first if available
        if youtube_player and youtube_player.youtube:
            try:
                # Use the API player
                api_results = youtube_player.search_music(query, max_results)
                if api_results:
                    # Convert to MultiMusicPlayer format
                    formatted = []
                    for video in api_results:
                        formatted.append({
                            "platform": "youtube",
                            "video_id": video['id'],
                            "url": video['watch_url'],
                            "embed_url": video['embed_url'],
                            "thumbnail": video['thumbnail'],
                            "title": video['title'],
                            "author": video['channel']
                        })
                    return formatted
            except Exception as e:
                print(f"[MultiMusicPlayer] API search failed, falling back to scraping: {e}")
        
        # Fallback to scraping
        try:
            search_url = f"https://www.youtube.com/results?search_query={quote_plus(query + ' music')}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            # Extract video IDs
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
            
            # Remove duplicates
            seen = set()
            unique_ids = []
            for vid in video_ids:
                if vid not in seen:
                    seen.add(vid)
                    unique_ids.append(vid)
                    if len(unique_ids) >= max_results:
                        break
            
            results = []
            for video_id in unique_ids:
                results.append({
                    "platform": "youtube",
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "embed_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1",
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                })
            
            return results
            
        except Exception as e:
            print(f"[MultiMusicPlayer] YouTube search error: {e}")
            return []
    

    
    # ==================== SOUNDCLOUD ====================
    
    def search_soundcloud(self, query: str) -> Optional[Dict]:
        """Search SoundCloud (via web scraping)"""
        try:
            search_url = f"https://soundcloud.com/search/sounds?q={quote_plus(query)}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            # Try to find track URLs in the page
            track_urls = re.findall(r'href="(/[^/]+/[^/"]+)"', response.text)
            
            # Filter for likely track URLs (not user pages, not explore, etc.)
            valid_tracks = []
            exclude_paths = ['explore', 'stream', 'search', 'discover', 'charts', 'upload', 'you', 'messages', 'settings']
            
            for track_url in track_urls:
                parts = track_url.strip('/').split('/')
                if len(parts) == 2 and parts[0] not in exclude_paths:
                    full_url = f"https://soundcloud.com{track_url}"
                    if full_url not in valid_tracks:
                        valid_tracks.append(full_url)
                        if len(valid_tracks) >= 1:
                            break
            
            if valid_tracks:
                # Get embed info for the first track
                return self.get_soundcloud_embed(valid_tracks[0])
            
            # Fallback: return search URL
            return {
                "platform": "soundcloud",
                "type": "search",
                "search_url": search_url,
                "message": f"🔊 Search on SoundCloud: {search_url}"
            }
            
        except Exception as e:
            print(f"[MultiMusicPlayer] SoundCloud search error: {e}")
            return None
    
    def get_soundcloud_embed(self, url: str) -> Optional[Dict]:
        """Get SoundCloud embed info using oEmbed"""
        try:
            oembed_url = f"https://soundcloud.com/oembed?format=json&url={quote_plus(url)}"
            response = requests.get(oembed_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract the iframe src from embed HTML
                embed_html = data.get("html", "")
                iframe_match = re.search(r'src="([^"]+)"', embed_html)
                embed_src = iframe_match.group(1) if iframe_match else None
                
                # Add autoplay parameter
                if embed_src and 'auto_play' not in embed_src:
                    embed_src += '&auto_play=true'
                
                return {
                    "platform": "soundcloud",
                    "title": data.get("title", "SoundCloud Track"),
                    "author": data.get("author_name", "Unknown Artist"),
                    "thumbnail": data.get("thumbnail_url"),
                    "url": url,
                    "embed_url": embed_src,
                    "embed_html": embed_html
                }
            
            return None
            
        except Exception as e:
            print(f"[MultiMusicPlayer] SoundCloud embed error: {e}")
            return None
    
    # ==================== UNIFIED PLAY ====================
    
    def play(self, query: str, source: str = "auto") -> Dict[str, Any]:
        """
        Main play method - searches and returns playable content.
        
        Args:
            query: Search query or URL
            source: "auto", "youtube", "soundcloud"
            
        Returns:
            Dictionary with embed URL and metadata for frontend playback
        """
        # Check if query is a URL
        platform, match_groups = self._detect_platform(query)
        
        if platform:
            # Direct URL provided
            if platform == 'soundcloud':
                result = self.get_soundcloud_embed(query)
                if result:
                    return self._format_response(result, query)
            
            elif platform == 'youtube':
                video_id = match_groups[0] if match_groups else None
                if video_id:
                    return self._format_response({
                        "platform": "youtube",
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "embed_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1",
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        "title": "YouTube Video"
                    }, query)
        
        # Search query - use specified source or auto
        clean_query = self._clean_query(query)
        
        if source == "soundcloud":
            result = self.search_soundcloud(clean_query)
            if result:
                return self._format_response(result, query)
        
        elif source == "youtube" or source == "auto":
            # YouTube is the most reliable, try it first for auto
            results = self.search_youtube(clean_query)
            if results:
                return self._format_response(results[0], query)
            
            # If auto and YouTube failed, try SoundCloud
            if source == "auto":
                result = self.search_soundcloud(clean_query)
                if result:
                    return self._format_response(result, query)
        
        # Nothing found
        return {
            "status": "error",
            "error": f"Could not find music for: {clean_query}",
            "suggestion": "Try a different search term or paste a direct URL from YouTube or SoundCloud."
        }
    
    def _clean_query(self, query: str) -> str:
        """Remove common play keywords from query"""
        keywords = ['play', 'music', 'song', 'listen to', 'stream', 'put on', 'play me']
        clean = query.lower()
        for keyword in keywords:
            clean = clean.replace(keyword, '').strip()
        return clean if clean else query
    
    def _format_response(self, result: Dict, original_query: str) -> Dict[str, Any]:
        """Format the response for frontend consumption"""
        platform = result.get("platform", "unknown")
        
        # Platform-specific icons
        icons = {
            "youtube": "🎬",
            "soundcloud": "🔊"
        }
        icon = icons.get(platform, "🎶")
        
        return {
            "status": "success",
            "type": "music",
            "platform": platform,
            "title": result.get("title", "Music"),
            "author": result.get("author", "Unknown Artist"),
            "thumbnail": result.get("thumbnail"),
            "url": result.get("url"),
            "embed_url": result.get("embed_url"),
            "video_id": result.get("video_id"),  # For YouTube
            "message": f"{icon} Now playing: **{result.get('title', original_query)}**",
            "music": {
                "platform": platform,
                "embed_url": result.get("embed_url"),
                "video_id": result.get("video_id"),
                "thumbnail": result.get("thumbnail"),
                "title": result.get("title")
            }
        }
    
    def get_available_sources(self) -> List[Dict]:
        """Return list of available music sources"""
        return [
            {
                "id": "youtube",
                "name": "YouTube",
                "icon": "🎬",
                "description": "Search YouTube for music videos",
                "supports_search": True,
                "supports_url": True
            },

            {
                "id": "soundcloud",
                "name": "SoundCloud",
                "icon": "🔊",
                "description": "Search SoundCloud for tracks",
                "supports_search": True,
                "supports_url": True
            }
        ]


# Global instance
multi_music_player = MultiMusicPlayer()


if __name__ == "__main__":
    # Test
    print("Testing Multi-Source Music Player...")
    
    # Test YouTube search
    print("\n=== YouTube Search ===")
    result = multi_music_player.play("lofi beats", source="youtube")
    print(json.dumps(result, indent=2))
    
    # Test SoundCloud search
    print("\n=== SoundCloud Search ===")
    result = multi_music_player.play("electronic music", source="soundcloud")
    print(json.dumps(result, indent=2))
