"""
WhatsApp Automation for JARVIS - Enhanced Version
==================================================
Send messages, make calls, manage contacts with proper error handling
"""

import pywhatkit as kit
import pyautogui
import time
from datetime import datetime
import os
import logging
import webbrowser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppAutomation:
    def __init__(self):
        self.is_initialized = False
        self.last_action_time = None
        self.min_delay = 5  # Minimum seconds between actions
        logger.info("[WhatsApp] Automation module loaded")
    
    def _validate_phone(self, phone):
        """Validate phone number format"""
        if not phone:
            return False, "Phone number is required"
        
        if not phone.startswith('+'):
            return False, "Phone number must start with + (country code)"
        
        # Remove + and check if remaining is digits
        digits = phone[1:].replace(' ', '').replace('-', '')
        if not digits.isdigit():
            return False, "Phone number must contain only digits after +"
        
        if len(digits) < 10:
            return False, "Phone number too short"
        
        return True, "Valid"
    
    def _wait_if_needed(self):
        """Ensure minimum delay between actions"""
        if self.last_action_time:
            elapsed = time.time() - self.last_action_time
            if elapsed < self.min_delay:
                wait_time = self.min_delay - elapsed
                logger.info(f"[WhatsApp] Waiting {wait_time:.1f}s before next action")
                time.sleep(wait_time)
        
        self.last_action_time = time.time()
    
    def send_message(self, phone, message, instant=True):
        """
        Send a WhatsApp message with error handling
        
        Args:
            phone: Phone number with country code (e.g., "+1234567890")
            message: Message text to send
            instant: If True, send immediately. If False, schedule for next minute
        """
        try:
            # Validate phone
            valid, error_msg = self._validate_phone(phone)
            if not valid:
                logger.error(f"[WhatsApp] Invalid phone: {error_msg}")
                return {"status": "error", "message": error_msg}
            
            # Validate message
            if not message or not message.strip():
                return {"status": "error", "message": "Message cannot be empty"}
            
            # Wait if needed
            self._wait_if_needed()
            
            logger.info(f"[WhatsApp] Sending message to {phone}")
            
            if instant:
                # Send instantly with increased wait time
                kit.sendwhatmsg_instantly(
                    phone_no=phone,
                    message=message,
                    wait_time=20,  # Wait for WhatsApp Web to load
                    tab_close=True,
                    close_time=3
                )
            else:
                # Schedule for next minute
                now = datetime.now()
                hour = now.hour
                minute = now.minute + 1
                
                if minute >= 60:
                    minute = 0
                    hour += 1
                    if hour >= 24:
                        hour = 0
                
                kit.sendwhatmsg(
                    phone_no=phone,
                    message=message,
                    time_hour=hour,
                    time_min=minute,
                    wait_time=20,
                    tab_close=True
                )
            
            logger.info(f"[WhatsApp] ✅ Message sent successfully to {phone}")
            return {
                "status": "success",
                "message": f"Message sent to {phone}",
                "phone": phone,
                "content": message
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[WhatsApp] ❌ Send message error: {error_msg}")
            
            # Provide helpful error messages
            if "internet" in error_msg.lower():
                return {"status": "error", "message": "No internet connection"}
            elif "whatsapp" in error_msg.lower():
                return {"status": "error", "message": "WhatsApp Web not logged in. Please log in manually first."}
            else:
                return {"status": "error", "message": f"Failed to send: {error_msg}"}
    
    def send_message_to_group(self, group_name, message):
        """
        Send message to a WhatsApp group
        
        Args:
            group_name: Name of the WhatsApp group
            message: Message text to send
        """
        try:
            if not group_name or not group_name.strip():
                return {"status": "error", "message": "Group name is required"}
            
            if not message or not message.strip():
                return {"status": "error", "message": "Message cannot be empty"}
            
            self._wait_if_needed()
            
            logger.info(f"[WhatsApp] Sending to group: {group_name}")
            
            now = datetime.now()
            hour = now.hour
            minute = now.minute + 1
            
            if minute >= 60:
                minute = 0
                hour += 1
                if hour >= 24:
                    hour = 0
            
            kit.sendwhatmsg_to_group(
                group_id=group_name,
                message=message,
                time_hour=hour,
                time_min=minute,
                wait_time=20,
                tab_close=True
            )
            
            logger.info(f"[WhatsApp] ✅ Group message sent to '{group_name}'")
            return {
                "status": "success",
                "message": f"Message sent to group '{group_name}'",
                "group": group_name
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[WhatsApp] ❌ Group message error: {error_msg}")
            return {"status": "error", "message": f"Failed to send to group: {error_msg}"}
    
    def make_call(self, phone):
        """
        Make a WhatsApp call (opens WhatsApp Web and initiates call)
        
        Args:
            phone: Phone number with country code
        """
        try:
            # Validate phone
            valid, error_msg = self._validate_phone(phone)
            if not valid:
                return {"status": "error", "message": error_msg}
            
            self._wait_if_needed()
            
            logger.info(f"[WhatsApp] Initiating call to {phone}")
            
            # Open WhatsApp Web chat
            phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')
            url = f"https://web.whatsapp.com/send?phone={phone_clean}"
            webbrowser.open(url)
            
            # Wait for page to load
            time.sleep(10)
            
            # Note: Actual call button clicking requires screen coordinates
            # which vary by screen resolution. User may need to click manually.
            
            logger.info(f"[WhatsApp] ✅ Call page opened for {phone}")
            return {
                "status": "success",
                "message": f"WhatsApp call page opened for {phone}. Click the call button to initiate.",
                "phone": phone
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[WhatsApp] ❌ Call error: {error_msg}")
            return {"status": "error", "message": f"Failed to initiate call: {error_msg}"}
    
    def send_bulk_messages(self, contacts, message):
        """
        Send the same message to multiple contacts
        
        Args:
            contacts: List of phone numbers with country codes
            message: Message to send
        """
        if not contacts or len(contacts) == 0:
            return {"status": "error", "message": "No contacts provided"}
        
        if not message or not message.strip():
            return {"status": "error", "message": "Message cannot be empty"}
        
        results = []
        success_count = 0
        fail_count = 0
        
        logger.info(f"[WhatsApp] Sending bulk messages to {len(contacts)} contacts")
        
        for i, phone in enumerate(contacts):
            logger.info(f"[WhatsApp] Sending {i+1}/{len(contacts)} to {phone}")
            
            result = self.send_message(phone, message, instant=False)
            results.append({"phone": phone, "result": result})
            
            if result.get("status") == "success":
                success_count += 1
            else:
                fail_count += 1
            
            # Delay between messages (pywhatkit handles this, but add extra)
            if i < len(contacts) - 1:
                time.sleep(3)
        
        logger.info(f"[WhatsApp] ✅ Bulk send complete: {success_count} success, {fail_count} failed")
        
        return {
            "status": "success",
            "message": f"Sent to {success_count}/{len(contacts)} contacts",
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    
    def send_image(self, phone, image_path, caption=None, auto_caption=True):
        """
        Send an image via WhatsApp with optional VQA-generated caption
        
        Args:
            phone: Phone number with country code
            image_path: Path to image file
            caption: Optional caption text (if None and auto_caption=True, generates with VQA)
            auto_caption: If True, auto-generate caption using VQA when caption is None
        """
        try:
            # Validate phone
            valid, error_msg = self._validate_phone(phone)
            if not valid:
                return {"status": "error", "message": error_msg}
            
            # Validate image path
            if not os.path.exists(image_path):
                return {"status": "error", "message": f"Image not found: {image_path}"}
            
            # Auto-generate caption if needed
            if not caption and auto_caption:
                try:
                    from Backend.vqa_service import get_vqa_service
                    logger.info("[WhatsApp] Generating smart caption with VQA...")
                    
                    vqa = get_vqa_service()
                    result = vqa.analyze_image_vqa(image_path, "Describe this image briefly")
                    
                    if result.get('success'):
                        caption = result['caption']
                        
                        # Add OCR text if present
                        if result.get('ocr_text'):
                            ocr_preview = result['ocr_text'][:100]
                            if len(result['ocr_text']) > 100:
                                ocr_preview += "..."
                            caption += f"\n\nText in image: {ocr_preview}"
                        
                        logger.info(f"[WhatsApp] Auto-caption: {caption}")
                except Exception as e:
                    logger.warning(f"[WhatsApp] Auto-caption failed: {e}")
                    caption = ""  # Send without caption if VQA fails
            
            self._wait_if_needed()
            
            logger.info(f"[WhatsApp] Sending image to {phone}")
            
            # Send image using pywhatkit
            now = datetime.now()
            hour = now.hour
            minute = now.minute + 1
            
            if minute >= 60:
                minute = 0
                hour += 1
                if hour >= 24:
                    hour = 0
            
            kit.sendwhats_image(
                receiver=phone,
                img_path=image_path,
                caption=caption or "",
                wait_time=20,
                tab_close=True
            )
            
            logger.info(f"[WhatsApp] ✅ Image sent successfully to {phone}")
            return {
                "status": "success",
                "message": f"Image sent to {phone}",
                "phone": phone,
                "image_path": image_path,
                "caption": caption
            }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[WhatsApp] ❌ Send image error: {error_msg}")
            return {"status": "error", "message": f"Failed to send image: {error_msg}"}
    
    def get_status(self):
        """Get WhatsApp automation status"""
        return {
            "status": "ready",
            "module": "WhatsApp Automation",
            "features": [
                "Send instant messages",
                "Send scheduled messages",
                "Send group messages",
                "Make calls (opens WhatsApp Web)",
                "Bulk messaging",
                "Error handling & logging"
            ],
            "requirements": [
                "WhatsApp Web must be logged in",
                "Internet connection required",
                "Phone number must include country code (+)"
            ]
        }

# Global instance
whatsapp = WhatsAppAutomation()

if __name__ == "__main__":
    print("WhatsApp Automation Test")
    print(whatsapp.get_status())
