"""
JARVIS-Level Gesture & Face Control System - BEAST MODE
========================================================
Next-gen human-computer interaction using Hand Gestures, Face Expressions, and Head Tracking.
"""

import cv2
import mediapipe as mp
import pyautogui
import math
import time
import numpy as np
from typing import Optional, Tuple, Dict
import threading

class JarvisGestureSystem:
    def __init__(self):
        # MediaPipe setup (Hands + Face Mesh)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Screen & Sensitivity
        self.screen_width, self.screen_height = pyautogui.size()
        self.smoothing = 5 # Lower is faster
        self.prev_x, self.prev_y = 0, 0
        
        # State
        self.is_running = False
        self.mode = "cursor" # modes: cursor, scroll, paint, system
        self.is_paused = False
        
        # Face State
        self.last_wink_time = 0
        self.smile_start = 0
        
        # Gesture Mapping
        self.gesture_actions = {
            "pinch": self.action_click,
            "fist": self.action_drag,
            "peace": self.mode_scroll,
            "thumbs_up": self.action_esc,
            "ok": self.mode_paint,
        }

    def speak(self, text: str):
        try:
            from Backend.TextToSpeech_Enhanced import TextToSpeech
            threading.Thread(target=lambda: TextToSpeech(text), daemon=True).start()
        except: print(f"🔊 {text}")

    # ==================== DETECTION LOGIC (BEAST) ====================

    def get_distance(self, p1, p2):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def detect_face_gestures(self, face_landmarks):
        """Beast Mode Face Awareness"""
        # Landmarks: 145, 159 (Left Eye), 374, 386 (Right Eye), 13, 14 (Lips)
        lm = face_landmarks.landmark
        
        # Wink Detection
        left_eye_dist = self.get_distance(lm[145], lm[159])
        right_eye_dist = self.get_distance(lm[374], lm[386])
        
        # Smile Detection
        mouth_dist = self.get_distance(lm[61], lm[291])
        mouth_height = self.get_distance(lm[0], lm[17])
        smile_ratio = mouth_dist / mouth_height if mouth_height != 0 else 0
        
        # Nose Pointer (God-View)
        nose = lm[1]
        
        return {
            'wink_left': left_eye_dist < 0.01,
            'wink_right': right_eye_dist < 0.01,
            'smile': smile_ratio > 3.5,
            'nose': (nose.x, nose.y)
        }

    # ==================== ACTIONS (BEAST) ====================

    def action_click(self): pyautogui.click()
    def action_drag(self): pyautogui.mouseDown()
    def action_release(self): pyautogui.mouseUp()
    def action_esc(self): pyautogui.press('esc')
    def mode_scroll(self): self.mode = "scroll"
    def mode_paint(self): self.mode = "paint"

    # ==================== CORE ENGINE ====================

    def process_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h_results = self.hands.process(rgb)
        f_results = self.face_mesh.process(rgb)
        
        # 1. Face Control
        if f_results.multi_face_landmarks:
            face_gestures = self.detect_face_gestures(f_results.multi_face_landmarks[0])
            
            # Nose Driving (If hands not visible)
            if not h_results.multi_hand_landmarks and self.mode == "cursor":
                nx, ny = face_gestures['nose']
                tx = int(nx * self.screen_width)
                ty = int(ny * self.screen_height)
                # Smoothing
                tx = self.prev_x + (tx - self.prev_x) / 10
                ty = self.prev_y + (ty - self.prev_y) / 10
                pyautogui.moveTo(tx, ty)
                self.prev_x, self.prev_y = tx, ty

            # Expression Triggers
            if face_gestures['smile']:
                cv2.putText(frame, "SMILE DETECTED: FOCUS MODE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if face_gestures['wink_left']:
                pyautogui.press('prevtrack')
                time.sleep(0.3)
            elif face_gestures['wink_right']:
                pyautogui.press('nexttrack')
                time.sleep(0.3)

        # 2. Hand Gestures
        if h_results.multi_hand_landmarks:
            for hand_landmarks in h_results.multi_hand_landmarks:
                # Get Cursor Pos (Index Finger)
                itip = hand_landmarks.landmark[8]
                ttip = hand_landmarks.landmark[4]
                
                cx = int(itip.x * self.screen_width)
                cy = int(itip.y * self.screen_height)
                
                # Smoothed Move
                cx = self.prev_x + (cx - self.prev_x) / self.smoothing
                cy = self.prev_y + (cy - self.prev_y) / self.smoothing
                
                # Check Pinch (Distance between Thumb and Index)
                dist = self.get_distance(itip, ttip)
                
                if dist < 0.05: # Pinch
                    pyautogui.click()
                    cv2.putText(frame, "CLICK", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                else:
                    pyautogui.moveTo(cx, cy)
                
                self.prev_x, self.prev_y = cx, cy

        return frame

    def run(self):
        self.is_running = True
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.speak("KAI Vision Engine - Beast Mode Activated")
        
        while self.is_running:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            
            processed = self.process_frame(frame)
            
            cv2.imshow("KAI VISION ENGINE", processed)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            
        cap.release()
        cv2.destroyAllWindows()
        self.is_running = False

# Global instance
jarvis_gesture = JarvisGestureSystem()

if __name__ == "__main__":
    jarvis_gesture.run()
