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
    
    def _clean_music_query(self, query: str) -> dict:
        """
        🧠 Use LLM to clean and fix music query - corrects spelling, extracts song/artist
        
        Returns:
            {"song": str, "artist": str or None, "cleaned": str}
        """
        try:
            import requests
            import os
            import json
            
            # Get Groq API key
            groq_key = os.getenv('GROQ_API_KEY')
            if not groq_key:
                # Try from env_vars if available
                try:
                    from Backend.EnvLoader import env_vars
                    groq_key = env_vars.get('GROQ_API_KEY')
                except:
                    pass
            
            if not groq_key:
                print("[Spotify] No Groq key for query cleaning, using raw query")
                return {"song": query, "artist": None, "cleaned": query}
            
            # Fast LLM call to clean the query
            prompt = f"""You are a music search assistant. Given a user's music request, extract:
1. The exact song name (fix any spelling mistakes)
2. The artist name (if mentioned)

User request: "{query}"

Reply ONLY with JSON format:
{{"song": "correct song name", "artist": "artist name or null"}}

Examples:
- "abhi tho party shuru hui ha by badshah" -> {{"song": "abhi toh party shuru hui hai", "artist": "badshah"}}
- "play pal pal" -> {{"song": "pal pal dil ke paas", "artist": null}}
- "play tum hi ho arjit" -> {{"song": "tum hi ho", "artist": "arijit singh"}}"""

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 100
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Parse JSON response
                try:
                    parsed = json.loads(content)
                    song = parsed.get("song", query)
                    artist = parsed.get("artist")
                    
                    if artist:
                        cleaned = f'{song} {artist}'
                    else:
                        cleaned = song
                    
                    print(f"[Spotify] 🧠 LLM cleaned: '{query}' -> song='{song}', artist='{artist}'")
                    return {"song": song, "artist": artist, "cleaned": cleaned}
                except json.JSONDecodeError:
                    print(f"[Spotify] LLM parse error, using raw query")
                    return {"song": query, "artist": None, "cleaned": query}
            else:
                print(f"[Spotify] LLM error {response.status_code}, using raw query")
                return {"song": query, "artist": None, "cleaned": query}
                
        except Exception as e:
            print(f"[Spotify] Query cleaning error: {e}")
            return {"song": query, "artist": None, "cleaned": query}
    
    def search(self, query: str, search_type: str = "track", limit: int = 10, artist: str = None):
        """
        🚀 UPGRADED Spotify Search with intelligent query parsing
        
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
            
            # === ENHANCED QUERY CLEANING ===
            clean_query = query.lower().strip()
            
            # Remove common noise phrases (more comprehensive)
            noise_phrases = [
                "on spotify", "in spotify", "from spotify", "spotify",
                "play ", "play the ", "play me ", "play some ",
                "song ", "the song ", "a song ",
                "music ", "some music ", "the music ",
                "can you play", "please play", "i want to hear", "i wanna hear",
                "put on ", "queue ", "listen to ", "start playing ",
                "play the song", "play song"
            ]
            for phrase in noise_phrases:
                clean_query = clean_query.replace(phrase, "")
            clean_query = clean_query.strip()
            
            # === SIMPLIFIED SEARCH - Just use the query directly! ===
            # The complex parsing was causing WRONG songs to be returned
            # Spotify's search is smart enough - let it do the work
            search_query = clean_query
            
            # If artist was explicitly passed, use Spotify's field syntax
            if artist and search_type == "track":
                search_query = f'track:"{clean_query}" artist:"{artist}"'
                print(f"[Spotify] 🎯 Targeted search: song='{clean_query}' artist='{artist}'")
            
            params = {
                "q": search_query,
                "type": search_type,
                "limit": limit,
                "market": "IN"  # India market for local songs
            }
            
            print(f"[Spotify] Search: '{search_query}' (type={search_type})")
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
        🚀 ENHANCED play - intelligently determines what to search for
        
        Args:
            query: What to play (song name, artist, genre, mood, etc)
            
        Returns:
            Dict with embed URL and metadata for chat display
        """
        query_lower = query.lower().strip()
        search_type = "track"  # Default to track search
        
        # === LLM-POWERED QUERY CLEANING ===
        # Use AI to fix spelling mistakes and extract song/artist
        llm_result = self._clean_music_query(query_lower)
        song_name = llm_result.get("song", query_lower)
        parsed_artist = llm_result.get("artist")
        
        # Build clean search query
        if parsed_artist:
            clean_query = f"{song_name} {parsed_artist}"
        else:
            clean_query = song_name
        
        # === SMART TYPE DETECTION ===
        # Only check for explicit playlist/album keywords (not in song titles)
        # Use stricter matching - must start with keyword or be standalone
        if query_lower.startswith("playlist ") or " playlist" in query_lower:
            search_type = "playlist"
            clean_query = query_lower.replace("playlist", "").strip()
        elif query_lower.startswith("album ") or " album" in query_lower:
            search_type = "album"
            clean_query = query_lower.replace("album", "").strip()
        elif any(kw in query_lower for kw in ["songs by", "music by", "tracks by", "top songs"]):
            search_type = "artist"
            for phrase in ["songs by", "music by", "tracks by", "top songs by", "top songs"]:
                clean_query = clean_query.replace(phrase, "").strip()
        # Genre/mood detection - only if query IS the genre (short queries)
        elif len(query_lower.split()) <= 3 and any(
            query_lower.strip() == genre or query_lower.startswith(genre + " ") 
            for genre in ["chill", "sad", "happy", "workout", "study", "sleep", "romantic", "lofi", "jazz"]
        ):
            search_type = "playlist"
        # Explicit Hindi/Bollywood playlist request
        elif any(kw in query_lower for kw in ["bollywood playlist", "hindi playlist", "punjabi playlist"]):
            search_type = "playlist"
        
        print(f"[Spotify] 🔍 Search: '{clean_query}' (type={search_type}, artist={parsed_artist})")
        
        # === PRIMARY SEARCH ===
        results = self.search(clean_query, search_type, limit=5, artist=parsed_artist)
        
        # === FALLBACK: If no track found, try simpler search ===
        if results.get("status") != "success" or not results.get("results"):
            if search_type == "track" and parsed_artist:
                # Try with just song name
                print(f"[Spotify] Fallback: searching just song name...")
                results = self.search(song_name, "track", limit=5)
            
            if results.get("status") != "success" or not results.get("results"):
                # Try as artist
                print(f"[Spotify] Fallback: trying as artist...")
                results = self.search(song_name if not parsed_artist else parsed_artist, "artist", limit=3)
        
        if results.get("status") == "success" and results.get("results"):
            # Use actual search type from results (may have changed)
            actual_type = results.get("type", search_type)
            item = results["results"][0]
            
            # Format response for chat
            if actual_type == "track":
                message = f"🎵 Now playing: **{item['name']}** by {item.get('artists', 'Unknown')}"
            elif actual_type == "artist":
                message = f"🎤 Playing top tracks from **{item['name']}**"
            elif actual_type == "album":
                message = f"💿 Playing album: **{item['name']}** by {item.get('artists', 'Unknown')}"
            elif actual_type == "playlist":
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
                    "search_type": actual_type
                }
            }
        else:
            # Fallback message
            return {
                "status": "not_found",
                "message": f"🔍 Couldn't find '{query}' on Spotify. Try being more specific (e.g., 'Shape of You by Ed Sheeran').",
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
