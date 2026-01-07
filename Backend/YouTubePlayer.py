"""
YouTube Player Module
=====================
Full-length music and video playback using YouTube API
"""

import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional

class YouTubePlayer:
    def __init__(self):
        """Initialize YouTube API client"""
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                print("[YouTube] OK - API initialized")
            except Exception as e:
                self.youtube = None
                print(f"[YouTube] ERROR - API initialization failed: {e}")
        else:
            self.youtube = None
            print("[YouTube] WARNING - No API key configured")
    
    def search_music(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for music videos"""
        if not self.youtube:
            return []
        
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                videoCategoryId='10'
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                video = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'description': item['snippet']['description'][:200],
                    'embed_url': f"https://www.youtube.com/embed/{item['id']['videoId']}",
                    'watch_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video)
            
            print(f"[YouTube] Found {len(videos)} music videos")
            return videos
            
        except Exception as e:
            print(f"[YouTube] Search error: {e}")
            return []
    
    def search_videos(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for any videos"""
        if not self.youtube:
            return []
        
        try:
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video'
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                video = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'description': item['snippet']['description'][:200],
                    'embed_url': f"https://www.youtube.com/embed/{item['id']['videoId']}",
                    'watch_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video)
            
            print(f"[YouTube] Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            print(f"[YouTube] Search error: {e}")
            return []
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed information about a video"""
        if not self.youtube:
            return None
        
        try:
            response = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return None
            
            item = response['items'][0]
            return {
                'id': video_id,
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'channel': item['snippet']['channelTitle'],
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'duration': item['contentDetails']['duration'],
                'views': item['statistics'].get('viewCount', 0),
                'likes': item['statistics'].get('likeCount', 0),
                'embed_url': f"https://www.youtube.com/embed/{video_id}",
                'watch_url': f"https://www.youtube.com/watch?v={video_id}"
            }
            
        except Exception as e:
            print(f"[YouTube] Error getting details: {e}")
            return None

# Initialize YouTube player
youtube_player = YouTubePlayer()
