"""
Web Music Player for KAI
=========================
Searches YouTube and returns embeddable URLs for frontend playback.
Works in cloud deployment - no server-side audio needed!
"""

import os
import re
import requests
from urllib.parse import quote_plus

def search_youtube(query: str, max_results: int = 1) -> list:
    """
    Search YouTube without API key using web scraping.
    Returns list of video info dicts with id, title, url.
    """
    try:
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(search_url, headers=headers, timeout=5)
        
        # Extract video IDs from page
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
        
        # Remove duplicates while preserving order
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
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "embed_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            })
        
        return results
        
    except Exception as e:
        print(f"[WebMusicPlayer] YouTube search error: {e}")
        return []


def get_music_response(query: str) -> dict:
    """
    Process a music play request and return data for frontend embedding.
    """
    # Clean up query
    play_keywords = ["play", "play music", "play song", "play video", "listen to"]
    clean_query = query.lower()
    for keyword in play_keywords:
        clean_query = clean_query.replace(keyword, "").strip()
    
    if not clean_query:
        clean_query = "lofi hip hop beats"  # Default music
    
    # Add "music" or "song" to improve search for vague queries
    if len(clean_query.split()) <= 2 and "music" not in clean_query:
        clean_query += " music"
    
    results = search_youtube(clean_query, max_results=1)
    
    if results:
        video = results[0]
        return {
            "status": "success",
            "message": f"🎵 Now playing: **{clean_query}**",
            "video_id": video["video_id"],
            "embed_url": video["embed_url"],
            "watch_url": video["url"],
            "thumbnail": video["thumbnail"],
            "type": "music_embed"
        }
    else:
        return {
            "status": "error",
            "message": f"❌ Couldn't find music for: {clean_query}",
            "type": "text"
        }


# Test
if __name__ == "__main__":
    result = get_music_response("play lofi beats")
    print(result)
