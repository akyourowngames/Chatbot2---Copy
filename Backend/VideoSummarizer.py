"""
YouTube Video Summarizer - Beast Mode
======================================
Extract transcripts from YouTube videos and generate AI summaries.
Features:
- Automatic transcript extraction
- AI-powered summarization with key points
- Works without API keys (uses public data)
- Thumbnail and metadata extraction
"""

import re
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs

# Try to import youtube_transcript_api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable
    )
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("[VideoSummarizer] youtube-transcript-api not installed. Run: pip install youtube-transcript-api")

# Import LLM for summarization
try:
    from Backend.LLM import ChatCompletion
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def ChatCompletion(messages, model=None, text_only=True):
        return "LLM not available for summarization."


class VideoSummarizer:
    """Summarize YouTube videos using transcripts and AI"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Supported languages for transcripts (in order of preference)
        self.preferred_languages = ['en', 'en-US', 'en-GB', 'hi', 'es', 'fr', 'de', 'pt', 'ja', 'ko', 'zh']
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata (title, thumbnail, duration) without API key"""
        try:
            # Use oembed endpoint (no API key needed)
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", "Unknown Title"),
                    "author": data.get("author_name", "Unknown"),
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    "thumbnail_hq": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "embed_url": f"https://www.youtube.com/embed/{video_id}"
                }
            else:
                return {
                    "title": "Video",
                    "author": "Unknown",
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "embed_url": f"https://www.youtube.com/embed/{video_id}"
                }
                
        except Exception as e:
            print(f"[VideoSummarizer] Error getting video info: {e}")
            return {
                "title": "Video",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }
    
    def _get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Extract transcript from YouTube video"""
        if not TRANSCRIPT_API_AVAILABLE:
            return {
                "success": False,
                "error": "Transcript API not available. Install: pip install youtube-transcript-api"
            }
        
        try:
            # Try to get transcript in preferred languages
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            language = None
            
            # First try manually created transcripts
            try:
                for lang in self.preferred_languages:
                    try:
                        transcript = transcript_list.find_manually_created_transcript([lang])
                        language = lang
                        break
                    except:
                        continue
            except:
                pass
            
            # Then try auto-generated
            if not transcript:
                try:
                    for lang in self.preferred_languages:
                        try:
                            transcript = transcript_list.find_generated_transcript([lang])
                            language = lang
                            break
                        except:
                            continue
                except:
                    pass
            
            # Last resort: get any available transcript
            if not transcript:
                try:
                    for t in transcript_list:
                        transcript = t
                        language = t.language_code
                        break
                except:
                    pass
            
            if not transcript:
                return {
                    "success": False,
                    "error": "No transcript available for this video"
                }
            
            # Fetch the transcript
            transcript_data = transcript.fetch()
            
            # Combine transcript segments
            full_text = " ".join([entry["text"] for entry in transcript_data])
            
            # Calculate duration
            if transcript_data:
                last_entry = transcript_data[-1]
                duration_seconds = last_entry.get("start", 0) + last_entry.get("duration", 0)
                duration_formatted = f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}"
            else:
                duration_formatted = "Unknown"
            
            return {
                "success": True,
                "text": full_text,
                "segments": transcript_data,
                "language": language,
                "duration": duration_formatted,
                "word_count": len(full_text.split())
            }
            
        except TranscriptsDisabled:
            return {
                "success": False,
                "error": "Transcripts are disabled for this video"
            }
        except NoTranscriptFound:
            return {
                "success": False,
                "error": "No transcript found for this video"
            }
        except VideoUnavailable:
            return {
                "success": False,
                "error": "Video is unavailable"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get transcript: {str(e)}"
            }
    
    def _generate_summary(self, transcript_text: str, video_title: str, max_length: int = 500) -> Dict[str, Any]:
        """Generate AI summary from transcript"""
        if not LLM_AVAILABLE:
            # Fallback: Simple extractive summary
            sentences = transcript_text.split('.')
            summary = '. '.join(sentences[:5]) + '.'
            return {
                "summary": summary[:max_length],
                "key_points": ["AI summary not available - showing first part of transcript"],
                "method": "extractive"
            }
        
        # Limit transcript to avoid token limits
        max_transcript_chars = 8000
        truncated_transcript = transcript_text[:max_transcript_chars]
        if len(transcript_text) > max_transcript_chars:
            truncated_transcript += "... [transcript truncated]"
        
        prompt = f"""You are an expert video summarizer. Summarize this YouTube video transcript concisely.

VIDEO TITLE: {video_title}

TRANSCRIPT:
{truncated_transcript}

Provide:
1. A clear, engaging summary (2-3 paragraphs)
2. 5 key takeaways as bullet points
3. Who this video is best for

Format your response as JSON:
{{
    "summary": "Your summary here...",
    "key_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
    "target_audience": "Description of who would benefit from this video"
}}"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = ChatCompletion(messages, model="groq", text_only=True)
            
            # Parse JSON response
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                result["method"] = "ai"
                return result
            else:
                # If no JSON found, use the response as summary
                return {
                    "summary": response[:max_length],
                    "key_points": ["See full summary above"],
                    "target_audience": "General audience",
                    "method": "ai"
                }
                
        except Exception as e:
            print(f"[VideoSummarizer] AI summary failed: {e}")
            # Fallback to extractive
            sentences = transcript_text.split('.')
            summary = '. '.join(sentences[:5]) + '.'
            return {
                "summary": summary[:max_length],
                "key_points": ["Summary generated from first part of transcript"],
                "method": "extractive_fallback"
            }
    
    def summarize(self, url: str) -> Dict[str, Any]:
        """
        Main method: Summarize a YouTube video.
        
        Args:
            url: YouTube video URL or video ID
            
        Returns:
            Dictionary with summary, key points, video info, thumbnail
        """
        # Extract video ID
        video_id = self._extract_video_id(url)
        if not video_id:
            return {
                "status": "error",
                "error": "Could not extract video ID from URL. Please provide a valid YouTube URL."
            }
        
        # Get video info
        video_info = self._get_video_info(video_id)
        
        # Get transcript
        transcript_result = self._get_transcript(video_id)
        
        if not transcript_result.get("success"):
            # Return partial info even if transcript fails
            return {
                "status": "error",
                "error": transcript_result.get("error"),
                "video_info": video_info,
                "suggestion": "This video doesn't have a transcript available. Try another video."
            }
        
        # Generate AI summary
        summary_result = self._generate_summary(
            transcript_result["text"],
            video_info.get("title", "Video")
        )
        
        return {
            "status": "success",
            "type": "video_summary",
            "video_id": video_id,
            "title": video_info.get("title"),
            "author": video_info.get("author", "Unknown"),
            "thumbnail": video_info.get("thumbnail"),
            "url": video_info.get("url"),
            "embed_url": video_info.get("embed_url"),
            "duration": transcript_result.get("duration"),
            "word_count": transcript_result.get("word_count"),
            "language": transcript_result.get("language"),
            "summary": summary_result.get("summary"),
            "key_points": summary_result.get("key_points", []),
            "target_audience": summary_result.get("target_audience", "General audience"),
            "summary_method": summary_result.get("method"),
            "message": f"📺 **{video_info.get('title')}**\n\n{summary_result.get('summary')}"
        }
    
    def get_transcript_only(self, url: str) -> Dict[str, Any]:
        """Get just the transcript without summarization"""
        video_id = self._extract_video_id(url)
        if not video_id:
            return {"status": "error", "error": "Invalid YouTube URL"}
        
        transcript_result = self._get_transcript(video_id)
        
        if not transcript_result.get("success"):
            return {
                "status": "error",
                "error": transcript_result.get("error")
            }
        
        return {
            "status": "success",
            "video_id": video_id,
            "transcript": transcript_result["text"],
            "duration": transcript_result.get("duration"),
            "word_count": transcript_result.get("word_count"),
            "language": transcript_result.get("language")
        }


# Global instance
video_summarizer = VideoSummarizer()


if __name__ == "__main__":
    # Test with a sample video
    print("Testing Video Summarizer...")
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = video_summarizer.summarize(test_url)
    
    print(json.dumps(result, indent=2))
