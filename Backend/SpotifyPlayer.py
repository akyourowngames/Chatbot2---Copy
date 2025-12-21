"""
Spotify Player Integration for KAI
Uses Spotify Web API for music search and playback
"""
import os
import requests
import base64
from datetime import datetime, timedelta

class SpotifyPlayer:
    """Spotify Web API integration for music playback"""
    
    def __init__(self):
        # User's Spotify credentials
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID', 'df80b0cc4cb54a07aa65367f65893634')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', '2fea2d46dfa34976bfc99dca80624d48')
        
        self.token = None
        self.token_expires = None
        self.base_url = "https://api.spotify.com/v1"
        
    def _get_auth_header(self):
        """Get base64 encoded auth header"""
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def _get_token(self):
        """Get or refresh access token using Client Credentials flow"""
        # Check if token is still valid
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
            
        try:
            url = "https://accounts.spotify.com/api/token"
            headers = {
                "Authorization": f"Basic {self._get_auth_header()}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result["access_token"]
                # Token expires in 'expires_in' seconds (usually 3600)
                self.token_expires = datetime.now() + timedelta(seconds=result.get("expires_in", 3600) - 60)
                return self.token
            else:
                print(f"[Spotify] Token error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[Spotify] Auth error: {e}")
            return None
    
    def search(self, query: str, search_type: str = "track", limit: int = 10, artist: str = None):
        """
        Search Spotify catalog with improved matching
        
        Args:
            query: Search query (song/album name)
            search_type: track, album, artist, playlist
            limit: Number of results
            artist: Optional artist name to filter results
            
        Returns:
            List of results with embed URLs
        """
        token = self._get_token()
        if not token:
            return {"status": "error", "message": "Failed to authenticate with Spotify"}
            
        try:
            url = f"{self.base_url}/search"
            headers = {"Authorization": f"Bearer {token}"}
            
            # Clean query - remove "on spotify", "play", etc.
            clean_query = query.lower()
            for phrase in ["on spotify", "play ", "spotify", "song ", "music "]:
                clean_query = clean_query.replace(phrase, "")
            clean_query = clean_query.strip()
            
            # Build smart search query
            search_query = clean_query
            parsed_artist = artist
            
            if search_type == "track":
                # Parse "song by artist" format
                if " by " in clean_query:
                    parts = clean_query.split(" by ", 1)
                    track_name = parts[0].strip()
                    parsed_artist = parts[1].strip() if len(parts) > 1 else ""
                    if parsed_artist:
                        # Use both formats for better matching
                        search_query = f'{track_name} {parsed_artist}'
                        print(f"[Spotify] Parsed: track='{track_name}' artist='{parsed_artist}'")
                elif artist:
                    search_query = f'{clean_query} {artist}'
            
            params = {
                "q": search_query,
                "type": search_type,
                "limit": limit,
                "market": "IN"  # Use India market for Hindi songs
            }
            
            print(f"[Spotify] Search query: '{search_query}'")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                results = []
                items_key = f"{search_type}s"  # tracks, albums, artists, playlists
                
                if items_key in data and "items" in data[items_key]:
                    for item in data[items_key]["items"]:
                        result = {
                            "id": item["id"],
                            "name": item["name"],
                            "uri": item["uri"],
                            "external_url": item["external_urls"]["spotify"],
                            "embed_url": f"https://open.spotify.com/embed/{search_type}/{item['id']}?utm_source=generator&theme=0"
                        }
                        
                        # Add type-specific data
                        if search_type == "track":
                            result["artists"] = ", ".join([a["name"] for a in item.get("artists", [])])
                            result["album"] = item.get("album", {}).get("name", "")
                            result["duration_ms"] = item.get("duration_ms", 0)
                            result["preview_url"] = item.get("preview_url")
                            # Get album art
                            images = item.get("album", {}).get("images", [])
                            result["thumbnail"] = images[0]["url"] if images else None
                            
                        elif search_type == "artist":
                            images = item.get("images", [])
                            result["thumbnail"] = images[0]["url"] if images else None
                            result["genres"] = item.get("genres", [])[:3]
                            result["followers"] = item.get("followers", {}).get("total", 0)
                            
                        elif search_type == "album":
                            result["artists"] = ", ".join([a["name"] for a in item.get("artists", [])])
                            result["release_date"] = item.get("release_date", "")
                            images = item.get("images", [])
                            result["thumbnail"] = images[0]["url"] if images else None
                            
                        elif search_type == "playlist":
                            result["owner"] = item.get("owner", {}).get("display_name", "Unknown")
                            result["tracks_total"] = item.get("tracks", {}).get("total", 0)
                            images = item.get("images", [])
                            result["thumbnail"] = images[0]["url"] if images else None
                            
                        results.append(result)
                
                return {
                    "status": "success",
                    "query": query,
                    "type": search_type,
                    "results": results,
                    "count": len(results)
                }
            else:
                return {"status": "error", "message": f"Search failed: {response.status_code}"}
                
        except Exception as e:
            print(f"[Spotify] Search error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_track(self, track_id: str):
        """Get track details by ID"""
        token = self._get_token()
        if not token:
            return None
            
        try:
            url = f"{self.base_url}/tracks/{track_id}"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                item = response.json()
                images = item.get("album", {}).get("images", [])
                return {
                    "id": item["id"],
                    "name": item["name"],
                    "artists": ", ".join([a["name"] for a in item.get("artists", [])]),
                    "album": item.get("album", {}).get("name", ""),
                    "duration_ms": item.get("duration_ms", 0),
                    "preview_url": item.get("preview_url"),
                    "external_url": item["external_urls"]["spotify"],
                    "embed_url": f"https://open.spotify.com/embed/track/{item['id']}?utm_source=generator&theme=0",
                    "thumbnail": images[0]["url"] if images else None
                }
            return None
            
        except Exception as e:
            print(f"[Spotify] Get track error: {e}")
            return None
    
    def play(self, query: str):
        """
        Search and return playable result for chat
        
        Args:
            query: What to play (song name, artist, etc)
            
        Returns:
            Dict with embed URL and metadata for chat display
        """
        # Determine search type from query
        search_type = "track"  # Default to track
        
        query_lower = query.lower()
        if "playlist" in query_lower:
            search_type = "playlist"
            query = query_lower.replace("playlist", "").strip()
        elif "album" in query_lower:
            search_type = "album"
            query = query_lower.replace("album", "").strip()
        elif "artist" in query_lower or "by" not in query_lower:
            # If just a name with no "by", might be artist
            pass
            
        # Search Spotify
        results = self.search(query, search_type, limit=1)
        
        if results.get("status") == "success" and results.get("results"):
            item = results["results"][0]
            
            # Format response for chat
            if search_type == "track":
                message = f"🎵 Now playing: **{item['name']}** by {item['artists']}"
            elif search_type == "artist":
                message = f"🎤 Playing top tracks from **{item['name']}**"
            elif search_type == "album":
                message = f"💿 Playing album: **{item['name']}** by {item['artists']}"
            elif search_type == "playlist":
                message = f"📋 Playing playlist: **{item['name']}** ({item.get('tracks_total', 0)} tracks)"
            else:
                message = f"🎵 Playing: **{item['name']}**"
                
            return {
                "status": "success",
                "message": message,
                "type": "spotify",
                "spotify": {
                    "embed_url": item["embed_url"],
                    "name": item["name"],
                    "thumbnail": item.get("thumbnail"),
                    "external_url": item["external_url"],
                    "artists": item.get("artists", ""),
                    "search_type": search_type
                }
            }
        else:
            # Fallback message
            return {
                "status": "not_found",
                "message": f"🔍 Couldn't find '{query}' on Spotify. Try a different search term.",
                "type": "text"
            }
    
    def get_recommendations(self, seed_tracks: list = None, seed_artists: list = None, limit: int = 5):
        """Get track recommendations based on seeds"""
        token = self._get_token()
        if not token:
            return {"status": "error", "message": "Failed to authenticate"}
            
        try:
            url = f"{self.base_url}/recommendations"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"limit": limit, "market": "US"}
            
            if seed_tracks:
                params["seed_tracks"] = ",".join(seed_tracks[:5])
            if seed_artists:
                params["seed_artists"] = ",".join(seed_artists[:5])
                
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tracks = []
                for item in data.get("tracks", []):
                    images = item.get("album", {}).get("images", [])
                    tracks.append({
                        "id": item["id"],
                        "name": item["name"],
                        "artists": ", ".join([a["name"] for a in item.get("artists", [])]),
                        "thumbnail": images[0]["url"] if images else None,
                        "embed_url": f"https://open.spotify.com/embed/track/{item['id']}?utm_source=generator&theme=0"
                    })
                return {"status": "success", "tracks": tracks}
            return {"status": "error", "message": "Failed to get recommendations"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Singleton instance
spotify_player = SpotifyPlayer()


def get_spotify_response(query: str):
    """Helper function for chat integration"""
    return spotify_player.play(query)
