"""
Instagram Automation for JARVIS - Advanced Monitoring & Automation
===================================================================
Monitor DMs, check messages, auto-reply, post content, and more
"""

import instagrapi
from instagrapi import Client
import time
import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramAutomation:
    def __init__(self):
        self.client = None
        self.is_logged_in = False
        self.username = None
        self.monitoring_active = False
        self.monitor_thread = None
        self.last_checked_dm = None
        self.message_callbacks = []
        
        # Load credentials if available
        self.creds_file = os.path.join("Data", "instagram_creds.json")
        os.makedirs("Data", exist_ok=True)
        
        logger.info("[Instagram] Automation module loaded")
    
    def login(self, username: str, password: str, save_session: bool = True) -> Dict[str, Any]:
        """
        Login to Instagram account
        
        Args:
            username: Instagram username
            password: Instagram password
            save_session: Save session for future use
        """
        try:
            logger.info(f"[Instagram] Logging in as {username}...")
            
            self.client = Client()
            self.client.delay_range = [1, 3]  # Delay between requests
            
            # Try to load existing session
            session_file = os.path.join("Data", f"instagram_session_{username}.json")
            if os.path.exists(session_file) and save_session:
                try:
                    self.client.load_settings(session_file)
                    self.client.login(username, password)
                    logger.info("[Instagram] Logged in using saved session")
                except Exception as e:
                    logger.warning(f"[Instagram] Session load failed: {e}, logging in fresh")
                    self.client = Client()
                    self.client.delay_range = [1, 3]
                    self.client.login(username, password)
            else:
                self.client.login(username, password)
            
            # Save session
            if save_session:
                self.client.dump_settings(session_file)
            
            self.is_logged_in = True
            self.username = username
            
            # Save credentials (encrypted in production!)
            if save_session:
                with open(self.creds_file, 'w') as f:
                    json.dump({"username": username}, f)
            
            logger.info(f"[Instagram] ✅ Successfully logged in as {username}")
            
            return {
                "status": "success",
                "message": f"Logged in as {username}",
                "username": username
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Instagram] ❌ Login failed: {error_msg}")
            
            if "challenge_required" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "Instagram requires verification. Please verify your account manually first."
                }
            elif "checkpoint" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "Account checkpoint required. Please log in via app/web first."
                }
            elif "incorrect" in error_msg.lower() or "password" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "Incorrect username or password"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Login failed: {error_msg}"
                }
    
    def logout(self) -> Dict[str, Any]:
        """Logout from Instagram"""
        try:
            if self.client and self.is_logged_in:
                self.stop_monitoring()
                self.client.logout()
                self.is_logged_in = False
                self.username = None
                logger.info("[Instagram] Logged out successfully")
                return {"status": "success", "message": "Logged out"}
            return {"status": "error", "message": "Not logged in"}
        except Exception as e:
            logger.error(f"[Instagram] Logout error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _ensure_logged_in(self) -> bool:
        """Check if logged in"""
        if not self.is_logged_in or not self.client:
            logger.error("[Instagram] Not logged in")
            return False
        return True
    
    def get_direct_messages(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get recent direct messages
        
        Args:
            limit: Number of conversations to fetch
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Fetching {limit} DM threads...")
            
            threads = self.client.direct_threads(amount=limit)
            
            messages = []
            for thread in threads:
                last_message = thread.messages[0] if thread.messages else None
                
                messages.append({
                    "thread_id": thread.id,
                    "users": [user.username for user in thread.users],
                    "last_message": {
                        "text": last_message.text if last_message else "",
                        "timestamp": last_message.timestamp.isoformat() if last_message else "",
                        "from_me": last_message.user_id == self.client.user_id if last_message else False
                    } if last_message else None,
                    "unread": thread.read_state == 0
                })
            
            logger.info(f"[Instagram] ✅ Fetched {len(messages)} conversations")
            
            return {
                "status": "success",
                "messages": messages,
                "count": len(messages)
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Get DMs error: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_direct_message(self, username: str, message: str) -> Dict[str, Any]:
        """
        Send a direct message to a user
        
        Args:
            username: Instagram username to send to
            message: Message text
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            if not message or not message.strip():
                return {"status": "error", "message": "Message cannot be empty"}
            
            logger.info(f"[Instagram] Sending DM to @{username}...")
            
            # Get user ID
            user_id = self.client.user_id_from_username(username)
            
            # Send message
            self.client.direct_send(message, [user_id])
            
            logger.info(f"[Instagram] ✅ Message sent to @{username}")
            
            return {
                "status": "success",
                "message": f"Message sent to @{username}",
                "recipient": username,
                "content": message
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Send DM error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_notifications(self) -> Dict[str, Any]:
        """Get recent notifications"""
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info("[Instagram] Fetching notifications...")
            
            # Get activity feed
            notifications = self.client.news_inbox()
            
            formatted_notifications = []
            for notif in notifications.get('new_stories', [])[:20]:
                formatted_notifications.append({
                    "type": notif.get('story_type'),
                    "text": notif.get('text', ''),
                    "timestamp": notif.get('timestamp', '')
                })
            
            logger.info(f"[Instagram] ✅ Fetched {len(formatted_notifications)} notifications")
            
            return {
                "status": "success",
                "notifications": formatted_notifications,
                "count": len(formatted_notifications)
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Get notifications error: {e}")
            return {"status": "error", "message": str(e)}
    
    def post_photo(self, image_path: str, caption: str = "") -> Dict[str, Any]:
        """
        Post a photo to Instagram feed
        
        Args:
            image_path: Path to image file
            caption: Photo caption
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            if not os.path.exists(image_path):
                return {"status": "error", "message": f"Image not found: {image_path}"}
            
            logger.info(f"[Instagram] Posting photo: {image_path}...")
            
            media = self.client.photo_upload(image_path, caption)
            
            logger.info(f"[Instagram] ✅ Photo posted successfully")
            
            return {
                "status": "success",
                "message": "Photo posted successfully",
                "media_id": media.id,
                "caption": caption
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Post photo error: {e}")
            return {"status": "error", "message": str(e)}
    
    def post_story(self, image_path: str) -> Dict[str, Any]:
        """
        Post a story to Instagram
        
        Args:
            image_path: Path to image file
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            if not os.path.exists(image_path):
                return {"status": "error", "message": f"Image not found: {image_path}"}
            
            logger.info(f"[Instagram] Posting story: {image_path}...")
            
            media = self.client.photo_upload_to_story(image_path)
            
            logger.info(f"[Instagram] ✅ Story posted successfully")
            
            return {
                "status": "success",
                "message": "Story posted successfully",
                "media_id": media.id
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Post story error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get information about a user"""
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Getting info for @{username}...")
            
            user_id = self.client.user_id_from_username(username)
            user_info = self.client.user_info(user_id)
            
            return {
                "status": "success",
                "user": {
                    "username": user_info.username,
                    "full_name": user_info.full_name,
                    "biography": user_info.biography,
                    "followers": user_info.follower_count,
                    "following": user_info.following_count,
                    "posts": user_info.media_count,
                    "is_private": user_info.is_private,
                    "is_verified": user_info.is_verified
                }
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Get user info error: {e}")
            return {"status": "error", "message": str(e)}
    
    def start_monitoring(self, check_interval: int = 30) -> Dict[str, Any]:
        """
        Start monitoring for new messages and notifications
        
        Args:
            check_interval: Seconds between checks
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            if self.monitoring_active:
                return {"status": "error", "message": "Monitoring already active"}
            
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(check_interval,),
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info(f"[Instagram] ✅ Monitoring started (checking every {check_interval}s)")
            
            return {
                "status": "success",
                "message": f"Monitoring started (interval: {check_interval}s)"
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Start monitoring error: {e}")
            return {"status": "error", "message": str(e)}
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("[Instagram] Monitoring stopped")
        return {"status": "success", "message": "Monitoring stopped"}
    
    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        logger.info("[Instagram] Monitor loop started")
        
        while self.monitoring_active:
            try:
                # Check for new DMs
                result = self.get_direct_messages(limit=5)
                
                if result.get("status") == "success":
                    messages = result.get("messages", [])
                    
                    for msg in messages:
                        if msg.get("unread"):
                            logger.info(f"[Instagram] 📩 New unread message from {msg['users']}")
                            # Trigger callbacks
                            for callback in self.message_callbacks:
                                try:
                                    callback(msg)
                                except Exception as e:
                                    logger.error(f"[Instagram] Callback error: {e}")
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"[Instagram] Monitor loop error: {e}")
                time.sleep(interval)
        
        logger.info("[Instagram] Monitor loop stopped")
    
    def add_message_callback(self, callback):
        """Add a callback function for new messages"""
        self.message_callbacks.append(callback)
    
    def like_post(self, media_id: str) -> Dict[str, Any]:
        """
        Like a post
        
        Args:
            media_id: Instagram media ID
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Liking post {media_id}...")
            self.client.media_like(media_id)
            
            logger.info(f"[Instagram] ✅ Post liked")
            return {"status": "success", "message": "Post liked successfully"}
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Like error: {e}")
            return {"status": "error", "message": str(e)}
    
    def comment_on_post(self, media_id: str, comment: str) -> Dict[str, Any]:
        """
        Comment on a post
        
        Args:
            media_id: Instagram media ID
            comment: Comment text
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            if not comment or not comment.strip():
                return {"status": "error", "message": "Comment cannot be empty"}
            
            logger.info(f"[Instagram] Commenting on post {media_id}...")
            self.client.media_comment(media_id, comment)
            
            logger.info(f"[Instagram] ✅ Comment posted")
            return {
                "status": "success",
                "message": "Comment posted successfully",
                "comment": comment
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Comment error: {e}")
            return {"status": "error", "message": str(e)}
    
    def follow_user(self, username: str) -> Dict[str, Any]:
        """Follow a user"""
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Following @{username}...")
            user_id = self.client.user_id_from_username(username)
            self.client.user_follow(user_id)
            
            logger.info(f"[Instagram] ✅ Now following @{username}")
            return {
                "status": "success",
                "message": f"Now following @{username}",
                "username": username
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Follow error: {e}")
            return {"status": "error", "message": str(e)}
    
    def unfollow_user(self, username: str) -> Dict[str, Any]:
        """Unfollow a user"""
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Unfollowing @{username}...")
            user_id = self.client.user_id_from_username(username)
            self.client.user_unfollow(user_id)
            
            logger.info(f"[Instagram] ✅ Unfollowed @{username}")
            return {
                "status": "success",
                "message": f"Unfollowed @{username}",
                "username": username
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Unfollow error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_followers(self, username: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get followers list
        
        Args:
            username: Username to get followers for (None = own account)
            limit: Maximum number of followers to fetch
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            target_username = username or self.username
            logger.info(f"[Instagram] Getting followers for @{target_username}...")
            
            user_id = self.client.user_id_from_username(target_username)
            followers = self.client.user_followers(user_id, amount=limit)
            
            follower_list = [
                {
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified
                }
                for user in followers.values()
            ]
            
            logger.info(f"[Instagram] ✅ Fetched {len(follower_list)} followers")
            
            return {
                "status": "success",
                "followers": follower_list,
                "count": len(follower_list)
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Get followers error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_following(self, username: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get following list
        
        Args:
            username: Username to get following for (None = own account)
            limit: Maximum number to fetch
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            target_username = username or self.username
            logger.info(f"[Instagram] Getting following for @{target_username}...")
            
            user_id = self.client.user_id_from_username(target_username)
            following = self.client.user_following(user_id, amount=limit)
            
            following_list = [
                {
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified
                }
                for user in following.values()
            ]
            
            logger.info(f"[Instagram] ✅ Fetched {len(following_list)} following")
            
            return {
                "status": "success",
                "following": following_list,
                "count": len(following_list)
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Get following error: {e}")
            return {"status": "error", "message": str(e)}
    
    def search_users(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search for users
        
        Args:
            query: Search query
            limit: Maximum results
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Searching for '{query}'...")
            
            results = self.client.search_users(query, amount=limit)
            
            user_list = [
                {
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified,
                    "is_private": user.is_private,
                    "follower_count": user.follower_count
                }
                for user in results
            ]
            
            logger.info(f"[Instagram] ✅ Found {len(user_list)} users")
            
            return {
                "status": "success",
                "users": user_list,
                "count": len(user_list)
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Search error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_user_posts(self, username: str, limit: int = 12) -> Dict[str, Any]:
        """
        Get user's recent posts
        
        Args:
            username: Instagram username
            limit: Number of posts to fetch
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            logger.info(f"[Instagram] Getting posts for @{username}...")
            
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, amount=limit)
            
            posts = [
                {
                    "media_id": media.id,
                    "caption": media.caption_text if media.caption_text else "",
                    "like_count": media.like_count,
                    "comment_count": media.comment_count,
                    "media_type": str(media.media_type),
                    "taken_at": media.taken_at.isoformat()
                }
                for media in medias
            ]
            
            logger.info(f"[Instagram] ✅ Fetched {len(posts)} posts")
            
            return {
                "status": "success",
                "posts": posts,
                "count": len(posts)
            }
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Get posts error: {e}")
            return {"status": "error", "message": str(e)}
    
    def auto_reply(self, keywords: Dict[str, str], enable: bool = True) -> Dict[str, Any]:
        """
        Set up auto-reply for DMs based on keywords
        
        Args:
            keywords: Dictionary of {keyword: reply_message}
            enable: Enable or disable auto-reply
        """
        try:
            if not self._ensure_logged_in():
                return {"status": "error", "message": "Not logged in"}
            
            if enable:
                self.auto_reply_keywords = keywords
                logger.info(f"[Instagram] ✅ Auto-reply enabled with {len(keywords)} keywords")
                return {
                    "status": "success",
                    "message": f"Auto-reply enabled with {len(keywords)} keywords",
                    "keywords": list(keywords.keys())
                }
            else:
                self.auto_reply_keywords = {}
                logger.info("[Instagram] Auto-reply disabled")
                return {"status": "success", "message": "Auto-reply disabled"}
        
        except Exception as e:
            logger.error(f"[Instagram] ❌ Auto-reply error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get Instagram automation status"""
        return {
            "status": "ready" if self.is_logged_in else "not_logged_in",
            "module": "Instagram Automation Enhanced",
            "logged_in": self.is_logged_in,
            "username": self.username,
            "monitoring_active": self.monitoring_active,
            "features": [
                "Send/receive direct messages",
                "Monitor DMs in real-time",
                "Get notifications",
                "Post photos and stories",
                "Get user information",
                "Like posts",
                "Comment on posts",
                "Follow/unfollow users",
                "Get followers/following lists",
                "Search users",
                "Get user posts",
                "Auto-reply to DMs",
                "Session persistence"
            ],
            "requirements": [
                "Valid Instagram account",
                "Internet connection",
                "Account must not have 2FA enabled (or use session)"
            ]
        }

# Global instance
instagram = InstagramAutomation()

if __name__ == "__main__":
    print("Instagram Automation Test")
    print(instagram.get_status())
