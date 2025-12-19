"""
Live Stream Player - Beast Mode
================================
Stream live TV channels and radio stations.
Features:
- Built-in database of free radio stations
- Live TV news and music channels
- Genre/category filtering
- Search functionality
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime


class LiveStreamPlayer:
    """Stream live TV and radio stations"""
    
    def __init__(self):
        # Built-in radio stations database
        self.radio_stations = [
            # === LOFI / CHILL ===
            {
                "id": "lofi-girl",
                "name": "Lofi Girl Radio",
                "genre": "lofi",
                "category": "music",
                "type": "youtube",
                "stream_id": "jfKfPfyJRdk",  # Lofi Girl YouTube live
                "thumbnail": "https://img.youtube.com/vi/jfKfPfyJRdk/hqdefault.jpg",
                "description": "24/7 lofi hip hop beats to relax/study to"
            },
            {
                "id": "chillhop",
                "name": "Chillhop Radio",
                "genre": "lofi",
                "category": "music",
                "type": "youtube",
                "stream_id": "5yx6BWlEVcY",
                "thumbnail": "https://img.youtube.com/vi/5yx6BWlEVcY/hqdefault.jpg",
                "description": "Chillhop 24/7 live radio"
            },
            
            # === JAZZ ===
            {
                "id": "jazz-lounge",
                "name": "Smooth Jazz Lounge",
                "genre": "jazz",
                "category": "music",
                "type": "youtube",
                "stream_id": "Dx5qFachd3A",
                "thumbnail": "https://img.youtube.com/vi/Dx5qFachd3A/hqdefault.jpg",
                "description": "Relaxing smooth jazz 24/7"
            },
            {
                "id": "coffee-jazz",
                "name": "Coffee Shop Jazz",
                "genre": "jazz",
                "category": "music",
                "type": "youtube",
                "stream_id": "fEvM-OUbaKs",
                "thumbnail": "https://img.youtube.com/vi/fEvM-OUbaKs/hqdefault.jpg",
                "description": "Jazz music for working and relaxing"
            },
            
            # === CLASSICAL ===
            {
                "id": "classical-radio",
                "name": "Classical Music Radio",
                "genre": "classical",
                "category": "music",
                "type": "youtube",
                "stream_id": "jgpJVI3tDbY",
                "thumbnail": "https://img.youtube.com/vi/jgpJVI3tDbY/hqdefault.jpg",
                "description": "Beautiful classical music 24/7"
            },
            
            # === POP / TOP HITS ===
            {
                "id": "pop-hits",
                "name": "Pop Hits Radio",
                "genre": "pop",
                "category": "music",
                "type": "youtube",
                "stream_id": "36YnV9STBqc",
                "thumbnail": "https://img.youtube.com/vi/36YnV9STBqc/hqdefault.jpg",
                "description": "Latest pop hits streaming live"
            },
            
            # === EDM / ELECTRONIC ===
            {
                "id": "edm-radio",
                "name": "EDM Dance Radio",
                "genre": "electronic",
                "category": "music",
                "type": "youtube",
                "stream_id": "c-gDheYUQzY",
                "thumbnail": "https://img.youtube.com/vi/c-gDheYUQzY/hqdefault.jpg",
                "description": "Electronic dance music 24/7"
            },
            
            # === AMBIENT / FOCUS ===
            {
                "id": "focus-music",
                "name": "Focus Music Radio",
                "genre": "ambient",
                "category": "music",
                "type": "youtube",
                "stream_id": "lTRiuFIWV54",
                "thumbnail": "https://img.youtube.com/vi/lTRiuFIWV54/hqdefault.jpg",
                "description": "Music for concentration and focus"
            },
            
            # === NATURE SOUNDS ===
            {
                "id": "rain-sounds",
                "name": "Rain & Thunder",
                "genre": "nature",
                "category": "ambient",
                "type": "youtube",
                "stream_id": "mPZkdNFkNps",
                "thumbnail": "https://img.youtube.com/vi/mPZkdNFkNps/hqdefault.jpg",
                "description": "Relaxing rain and thunder sounds"
            },
        ]
        
        # Built-in TV channels database
        self.tv_channels = [
            # === NEWS ===
            {
                "id": "sky-news",
                "name": "Sky News",
                "genre": "news",
                "category": "tv",
                "type": "youtube",
                "stream_id": "9Auq9mYxFEE",
                "thumbnail": "https://img.youtube.com/vi/9Auq9mYxFEE/hqdefault.jpg",
                "description": "Sky News live 24/7"
            },
            {
                "id": "al-jazeera",
                "name": "Al Jazeera English",
                "genre": "news",
                "category": "tv",
                "type": "youtube",
                "stream_id": "F-POY4Q0QSI",
                "thumbnail": "https://img.youtube.com/vi/F-POY4Q0QSI/hqdefault.jpg",
                "description": "Al Jazeera English live"
            },
            {
                "id": "france24",
                "name": "France 24",
                "genre": "news",
                "category": "tv",
                "type": "youtube",
                "stream_id": "h3MuIUNCCzI",
                "thumbnail": "https://img.youtube.com/vi/h3MuIUNCCzI/hqdefault.jpg",
                "description": "France 24 English live"
            },
            {
                "id": "dw-news",
                "name": "DW News",
                "genre": "news",
                "category": "tv",
                "type": "youtube",
                "stream_id": "GE_SfNVNyqk",
                "thumbnail": "https://img.youtube.com/vi/GE_SfNVNyqk/hqdefault.jpg",
                "description": "DW News live from Germany"
            },
            {
                "id": "ndtv",
                "name": "NDTV India",
                "genre": "news",
                "category": "tv",
                "type": "youtube",
                "stream_id": "MN8p-Vrn6G0",
                "thumbnail": "https://img.youtube.com/vi/MN8p-Vrn6G0/hqdefault.jpg",
                "description": "NDTV India live news"
            },
            
            # === TECH ===
            {
                "id": "nasa-tv",
                "name": "NASA TV",
                "genre": "science",
                "category": "tv",
                "type": "youtube",
                "stream_id": "21X5lGlDOfg",
                "thumbnail": "https://img.youtube.com/vi/21X5lGlDOfg/hqdefault.jpg",
                "description": "NASA TV live stream"
            },
        ]
        
        # All available genres
        self.genres = {
            "music": ["lofi", "jazz", "classical", "pop", "electronic", "ambient", "nature"],
            "tv": ["news", "science", "sports"]
        }
    
    def get_radio_stations(self, genre: str = None) -> List[Dict]:
        """Get list of available radio stations"""
        stations = self.radio_stations
        
        if genre:
            stations = [s for s in stations if s.get("genre") == genre.lower()]
        
        return [{
            "id": s["id"],
            "name": s["name"],
            "genre": s["genre"],
            "thumbnail": s.get("thumbnail"),
            "description": s.get("description")
        } for s in stations]
    
    def get_tv_channels(self, genre: str = None) -> List[Dict]:
        """Get list of available TV channels"""
        channels = self.tv_channels
        
        if genre:
            channels = [c for c in channels if c.get("genre") == genre.lower()]
        
        return [{
            "id": c["id"],
            "name": c["name"],
            "genre": c["genre"],
            "thumbnail": c.get("thumbnail"),
            "description": c.get("description")
        } for c in channels]
    
    def get_all_streams(self) -> Dict[str, List]:
        """Get all available streams organized by category"""
        return {
            "radio": self.get_radio_stations(),
            "tv": self.get_tv_channels(),
            "genres": self.genres
        }
    
    def search(self, query: str) -> List[Dict]:
        """Search for stations by name or genre"""
        query_lower = query.lower()
        results = []
        
        # Search radio stations
        for station in self.radio_stations:
            if (query_lower in station["name"].lower() or 
                query_lower in station.get("genre", "").lower() or
                query_lower in station.get("description", "").lower()):
                results.append({**station, "type": "radio"})
        
        # Search TV channels
        for channel in self.tv_channels:
            if (query_lower in channel["name"].lower() or 
                query_lower in channel.get("genre", "").lower() or
                query_lower in channel.get("description", "").lower()):
                results.append({**channel, "type": "tv"})
        
        return results
    
    def play_station(self, station_id: str) -> Dict[str, Any]:
        """Play a specific station by ID"""
        # Search in radio stations
        for station in self.radio_stations:
            if station["id"] == station_id:
                return self._format_stream_response(station, "radio")
        
        # Search in TV channels
        for channel in self.tv_channels:
            if channel["id"] == station_id:
                return self._format_stream_response(channel, "tv")
        
        return {
            "status": "error",
            "error": f"Station not found: {station_id}",
            "available_stations": [s["id"] for s in self.radio_stations + self.tv_channels]
        }
    
    def play_by_query(self, query: str) -> Dict[str, Any]:
        """Play a stream matching the query (smart search)"""
        query_lower = query.lower()
        
        # Check for keywords
        is_radio = any(word in query_lower for word in ['radio', 'music', 'listen', 'stream'])
        is_tv = any(word in query_lower for word in ['tv', 'news', 'watch', 'live'])
        
        # Search for matching stations
        results = self.search(query)
        
        if not results:
            # Try genre matching
            for genre in self.genres.get("music", []):
                if genre in query_lower:
                    results = [s for s in self.radio_stations if s.get("genre") == genre]
                    if results:
                        break
            
            for genre in self.genres.get("tv", []):
                if genre in query_lower:
                    results = [c for c in self.tv_channels if c.get("genre") == genre]
                    if results:
                        break
        
        if results:
            best_match = results[0]
            stream_type = "radio" if best_match in self.radio_stations or best_match.get("type") == "radio" else "tv"
            return self._format_stream_response(best_match, stream_type)
        
        # Default to lofi if nothing matches
        if is_radio or not is_tv:
            return self._format_stream_response(self.radio_stations[0], "radio")
        else:
            return self._format_stream_response(self.tv_channels[0], "tv")
    
    def _format_stream_response(self, stream: Dict, stream_type: str) -> Dict[str, Any]:
        """Format stream data for frontend playback"""
        stream_id = stream.get("stream_id")
        
        # Generate embed URL based on type
        if stream.get("type") == "youtube":
            embed_url = f"https://www.youtube.com/embed/{stream_id}?autoplay=1"
            watch_url = f"https://www.youtube.com/watch?v={stream_id}"
        else:
            embed_url = stream.get("url", "")
            watch_url = embed_url
        
        icon = "📻" if stream_type == "radio" else "📺"
        
        return {
            "status": "success",
            "type": "stream",
            "stream_type": stream_type,
            "id": stream.get("id"),
            "name": stream.get("name"),
            "genre": stream.get("genre"),
            "description": stream.get("description"),
            "thumbnail": stream.get("thumbnail"),
            "embed_url": embed_url,
            "watch_url": watch_url,
            "video_id": stream_id,
            "message": f"{icon} Now streaming: **{stream.get('name')}**",
            "music": {  # Compatible with existing music player format
                "platform": "youtube",
                "embed_url": embed_url,
                "video_id": stream_id,
                "thumbnail": stream.get("thumbnail"),
                "title": stream.get("name")
            }
        }
    
    def get_genres(self) -> Dict[str, List[str]]:
        """Get available genres for each category"""
        return self.genres


# Global instance
live_stream_player = LiveStreamPlayer()


if __name__ == "__main__":
    print("Testing Live Stream Player...")
    
    # List all radio stations
    print("\n=== Radio Stations ===")
    for station in live_stream_player.get_radio_stations():
        print(f"  • {station['name']} ({station['genre']})")
    
    # List all TV channels
    print("\n=== TV Channels ===")
    for channel in live_stream_player.get_tv_channels():
        print(f"  • {channel['name']} ({channel['genre']})")
    
    # Test playback
    print("\n=== Play Test ===")
    result = live_stream_player.play_by_query("lofi music")
    print(json.dumps(result, indent=2))
