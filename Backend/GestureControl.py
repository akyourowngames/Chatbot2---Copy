"""
Hand Gesture Control - JARVIS Level
====================================
Control your PC with hand gestures using webcam
Powered by MediaPipe and OpenCV
"""

import cv2
import mediapipe as mp
import pyautogui
import math
import time
from typing import Optional, Tuple

class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        self.screen_width, self.screen_height = pyautogui.size()
        self.smoothing = 5
        self.prev_x, self.prev_y = 0, 0
        
        self.is_running = False
        self.cap = None
        
        # Gesture states
        self.pinch_threshold = 40
        self.is_clicking = False
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5  # seconds
        
    def start(self):
        """Start gesture control"""
        self.cap = cv2.VideoCapture(0)
        self.is_running = True
        print("🎮 Gesture Control Started!")
        print("Gestures:")
        print("  ✋ Open hand = Move cursor")
        print("  👌 Pinch (thumb + index) = Click")
        print("  ✌️ Peace sign = Scroll")
        print("  👊 Fist = Stop gesture control")
        
    def stop(self):
        """Stop gesture control"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🛑 Gesture Control Stopped")
    
    def get_distance(self, point1, point2):
        """Calculate distance between two points"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def detect_gesture(self, hand_landmarks):
        """Detect hand gesture"""
        # Get finger tips and bases
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        index_base = hand_landmarks.landmark[5]
        middle_base = hand_landmarks.landmark[9]
        
        # Calculate distances
        thumb_index_dist = self.get_distance(thumb_tip, index_tip) * 1000
        
        # Check if fingers are extended
        index_extended = index_tip.y < index_base.y
        middle_extended = middle_tip.y < middle_base.y
        
        # Pinch gesture (click)
        if thumb_index_dist < self.pinch_threshold:
            return "pinch"
        
        # Peace sign (scroll)
        elif index_extended and middle_extended:
            return "peace"
        
        # Fist (stop)
        elif not index_extended and not middle_extended:
            return "fist"
        
        # Open hand (move)
        else:
            return "move"
    
    def process_frame(self):
        """Process one frame"""
        if not self.cap or not self.is_running:
            return False
        
        success, frame = self.cap.read()
        if not success:
            return False
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hand detection
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
                
                # Get index finger tip position
                index_tip = hand_landmarks.landmark[8]
                
                # Convert to screen coordinates
                x = int(index_tip.x * self.screen_width)
                y = int(index_tip.y * self.screen_height)
                
                # Smooth movement
                smooth_x = self.prev_x + (x - self.prev_x) / self.smoothing
                smooth_y = self.prev_y + (y - self.prev_y) / self.smoothing
                
                # Detect gesture
                gesture = self.detect_gesture(hand_landmarks)
                
                current_time = time.time()
                
                if gesture == "move":
                    # Move cursor
                    pyautogui.moveTo(smooth_x, smooth_y, duration=0.1)
                    self.prev_x, self.prev_y = smooth_x, smooth_y
                    cv2.putText(frame, "MOVE", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                elif gesture == "pinch":
                    # Click
                    if not self.is_clicking and (current_time - self.last_gesture_time) > self.gesture_cooldown:
                        pyautogui.click()
                        self.is_clicking = True
                        self.last_gesture_time = current_time
                        cv2.putText(frame, "CLICK", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    self.is_clicking = False
                
                if gesture == "peace":
                    cv2.putText(frame, "SCROLL", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                
                elif gesture == "fist":
                    cv2.putText(frame, "STOP", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    return "stop"
        
        # Display frame
        cv2.imshow("JARVIS Gesture Control", frame)
        
        # Check for 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return "stop"
        
        return True
    
    def run(self):
        """Main gesture control loop"""
        self.start()
        
        try:
            while self.is_running:
                result = self.process_frame()
                if result == "stop":
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

# Global instance
gesture_controller = GestureController()

if __name__ == "__main__":
    print("Starting Hand Gesture Control...")
    print("Press 'q' or make a fist to stop")
    gesture_controller.run()
