import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from collections import deque, Counter

import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import keyboard
import os
import psutil

try:
    import win32gui  # type: ignore
    import win32process  # type: ignore
except Exception:
    win32gui = None
    win32process = None
try:
    import pygetwindow as gw  # type: ignore
except Exception:
    gw = None


@dataclass
class GestureAction:
    type: str
    value: Optional[str] = None
    args: Optional[Dict] = None


class GestureController:
    """Real-time hand gesture recognition and action mapper using MediaPipe + OpenCV.

    Gestures detected (initial set):
      - open_palm, fist, point, pinch, swipe_left, swipe_right, swipe_up, swipe_down

    Actions schema (in config json):
      {
        "open_palm": {"type": "keyboard_send", "value": "media_play_pause"},
        "pinch_in": {"type": "keyboard_send", "value": "volume_down"},
        "pinch_out": {"type": "keyboard_send", "value": "volume_up"},
        "swipe_up": {"type": "scroll", "args": {"amount": 800}},
        "swipe_down": {"type": "scroll", "args": {"amount": -800}},
        "screenshot": {"type": "keyboard_hotkey", "value": "print_screen"},
        "snip_tool": {"type": "keyboard_hotkey", "value": "win+shift+s"}
      }
    """

    def __init__(self, config_path: Path, camera_index: int = 0, min_detection_confidence: float = 0.6, min_tracking_confidence: float = 0.6, force_profile: Optional[str] = None, enable_hot_reload: bool = True):
        self.config_path = Path(config_path)
        self.camera_index = camera_index
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.config = self._load_config(self.config_path)
        self.force_profile = force_profile
        self.enable_hot_reload = enable_hot_reload
        self._config_mtime: float = os.path.getmtime(self.config_path) if self.config_path.exists() else 0.0

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.prev_center: Optional[Tuple[int, int]] = None
        self.prev_time = time.time()
        self.pinch_prev_dist: Optional[float] = None
        self.last_pinch_time: float = 0.0
        self.cooldowns: Dict[str, float] = {}
        self.cooldown_seconds = float((self.config.get("settings", {}) or {}).get("cooldown_seconds", 0.5))

        # Temporal gesture state
        self.hold_state: Dict[str, float] = {}
        self.hold_threshold_seconds = float((self.config.get("settings", {}) or {}).get("hold_seconds", 1.0))

        # Motion history for circle detection
        self.center_history: List[Tuple[int, int]] = []
        self.center_history_max = int((self.config.get("settings", {}) or {}).get("circle_window", 24))

        # EMA smoothing for center and landmark coords
        s = (self.config.get("settings", {}) or {})
        self.ema_alpha = float(s.get("ema_alpha", 0.4))
        self.smoothed_center: Optional[Tuple[float, float]] = None
        self.smoothed_points: Optional[np.ndarray] = None

        # Gesture debouncing and majority vote
        self.gesture_vote_window = int(s.get("gesture_vote_window", 7))
        self.gesture_vote_threshold = int(s.get("gesture_vote_threshold", 4))
        self.gesture_buffer: deque = deque(maxlen=self.gesture_vote_window)
        self.per_gesture_refractory_s: float = float(s.get("per_gesture_refractory_seconds", 0.6))
        self.last_trigger_time_by_gesture: Dict[str, float] = {}

        # App profile hysteresis
        self._last_app: str = "global"
        self._last_app_seen_at: float = 0.0
        self.app_switch_stable_ms: int = int(s.get("app_switch_stable_ms", 400))
        self._app_locked: str = "global"

        # Optional restrict to right hand only (based on handedness label if available)
        self.right_hand_only: bool = bool(s.get("right_hand_only", False))

        # Mode state (e.g., scroll_mode)
        self.active_mode: Optional[str] = None
        self.mode_started_at: float = 0.0
        self.mode_anchor_center: Optional[Tuple[int, int]] = None
        self.mode_timeout_seconds = 8.0

        # PyAutoGUI safety
        pyautogui.FAILSAFE = False

    @staticmethod
    def _load_config(path: Path) -> Dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def _gesture_cooldown_ready(self, gesture: str) -> bool:
        now = time.time()
        last = self.cooldowns.get(gesture, 0)
        if now - last >= self.cooldown_seconds:
            self.cooldowns[gesture] = now
            return True
        return False

    def _maybe_reload_config(self):
        if not self.enable_hot_reload:
            return
        try:
            if not self.config_path.exists():
                return
            mtime = os.path.getmtime(self.config_path)
            if mtime != self._config_mtime:
                self._config_mtime = mtime
                self.config = self._load_config(self.config_path)
        except Exception:
            pass

    @staticmethod
    def _process_name_from_hwnd(hwnd: int) -> Optional[str]:
        try:
            if win32process is None or win32gui is None:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            for p in psutil.process_iter(["pid", "name"]):
                if p.info["pid"] == pid:
                    return (p.info["name"] or "").lower()
        except Exception:
            return None
        return None

    def _active_app_key(self) -> str:
        # Determine current app profile key with hysteresis
        now = time.time()
        if self.force_profile:
            return self.force_profile

        current = "global"
        if win32gui is not None:
            try:
                hwnd = win32gui.GetForegroundWindow()
                pname = self._process_name_from_hwnd(hwnd) or ""
                if pname.endswith("chrome.exe"):
                    current = "chrome"
                elif pname.endswith("explorer.exe"):
                    current = "explorer"
                elif pname.endswith("code.exe"):
                    current = "vscode"
                elif pname:
                    current = os.path.splitext(pname)[0]
            except Exception:
                pass
        if current == "global" and gw is not None:
            try:
                win = gw.getActiveWindow()
                title = (win.title or "").lower() if win else ""
                if "chrome" in title:
                    current = "chrome"
                elif "visual studio code" in title or "vs code" in title:
                    current = "vscode"
                elif "file explorer" in title:
                    current = "explorer"
            except Exception:
                pass

        if current != self._last_app:
            self._last_app = current
            self._last_app_seen_at = now
        elif (now - self._last_app_seen_at) * 1000 >= self.app_switch_stable_ms:
            self._app_locked = self._last_app or "global"
        return self._app_locked

    def _resolve_action(self, gesture: str, active_app: str) -> Optional[GestureAction]:
        # Support new schema with profiles + legacy flat schema
        cfg = self.config or {}
        if "profiles" in cfg:
            profiles = cfg.get("profiles", {})
            app_profile = profiles.get(active_app, {})
            global_profile = profiles.get("global", {})
            mapping = app_profile.get(gesture) or global_profile.get(gesture)
            if mapping:
                try:
                    return GestureAction(**mapping)
                except Exception:
                    return None
        else:
            mapping = cfg.get(gesture)
            if mapping:
                try:
                    return GestureAction(**mapping)
                except Exception:
                    return None
        return None

    @staticmethod
    def _landmarks_to_np(results, image_shape: Tuple[int, int]) -> Optional[np.ndarray]:
        if not results.multi_hand_landmarks:
            return None
        h, w = image_shape
        hand_landmarks = results.multi_hand_landmarks[0]
        points = []
        for lm in hand_landmarks.landmark:
            points.append([int(lm.x * w), int(lm.y * h)])
        return np.array(points, dtype=np.int32)

    @staticmethod
    def _bbox_area(points: np.ndarray) -> int:
        x_min, y_min = points[:, 0].min(), points[:, 1].min()
        x_max, y_max = points[:, 0].max(), points[:, 1].max()
        return int(max(0, x_max - x_min) * max(0, y_max - y_min))

    @staticmethod
    def _is_finger_extended(points: np.ndarray, tip_idx: int, pip_idx: int) -> bool:
        return points[tip_idx][1] < points[pip_idx][1]

    def _classify_static_gesture(self, pts: np.ndarray) -> Optional[str]:
        # Finger indices as per MediaPipe (tips: 4,8,12,16,20; PIP joints: 3,6,10,14,18)
        thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip = 4, 8, 12, 16, 20
        thumb_ip, index_pip, middle_pip, ring_pip, pinky_pip = 3, 6, 10, 14, 18

        fingers_extended = [
            self._is_finger_extended(pts, index_tip, index_pip),
            self._is_finger_extended(pts, middle_tip, middle_pip),
            self._is_finger_extended(pts, ring_tip, ring_pip),
            self._is_finger_extended(pts, pinky_tip, pinky_pip),
        ]

        # Heuristic for thumb: compare x depending on hand side; fallback to tip vs ip y
        thumb_extended = pts[4][0] < pts[3][0] or pts[4][1] < pts[3][1]

        if all(fingers_extended) and thumb_extended:
            return "open_palm"
        if not any(fingers_extended) and not thumb_extended:
            return "fist"
        if fingers_extended[0] and not any(fingers_extended[1:]) and not thumb_extended:
            return "point"

        # Pinch detection based on distance between thumb tip (4) and index tip (8)
        pinch_dist = np.linalg.norm(pts[4] - pts[8])
        if self.pinch_prev_dist is None:
            self.pinch_prev_dist = pinch_dist
        else:
            # Basic pinch closed
            pinch_close = float((self.config.get("settings", {}) or {}).get("pinch_close_px", 35))
            if pinch_dist < pinch_close:
                return "pinch"
        return None

    def _detect_swipe(self, center: Tuple[int, int]) -> Optional[str]:
        if self.prev_center is None:
            self.prev_center = center
            return None
        dx = center[0] - self.prev_center[0]
        dy = center[1] - self.prev_center[1]
        self.prev_center = center

        thresh = int((self.config.get("settings", {}) or {}).get("swipe_threshold_px", 60))
        if abs(dx) > abs(dy):
            if dx > thresh:
                return "swipe_right"
            if dx < -thresh:
                return "swipe_left"
        else:
            if dy > thresh:
                return "swipe_down"
            if dy < -thresh:
                return "swipe_up"
        return None

    def _update_temporal_gestures(self, static_gesture: Optional[str], pts: Optional[np.ndarray]) -> Optional[str]:
        now = time.time()
        detected: Optional[str] = None
        # Hold detection for open_palm
        if static_gesture == "open_palm":
            start = self.hold_state.get("open_palm_start", 0.0)
            if start == 0.0:
                self.hold_state["open_palm_start"] = now
            elif now - start >= self.hold_threshold_seconds:
                detected = "hold_open_palm"
        else:
            self.hold_state.pop("open_palm_start", None)

        # Pinch in/out (direction based on change in thumb-index distance)
        if pts is not None:
            dist = float(np.linalg.norm(pts[4] - pts[8]))
            last = self.pinch_prev_dist if self.pinch_prev_dist is not None else dist
            delta = dist - last
            # Significant change thresholds
            pinch_delta = float((self.config.get("settings", {}) or {}).get("pinch_delta_px", 8))
            if delta <= -pinch_delta:
                detected = detected or "pinch_in"
            elif delta >= pinch_delta:
                detected = detected or "pinch_out"
            self.pinch_prev_dist = dist

        # Double pinch (two pinch closures within 0.5s)
        if static_gesture == "pinch":
            if now - self.last_pinch_time <= 0.5:
                detected = detected or "double_pinch"
                self.last_pinch_time = 0.0
            else:
                self.last_pinch_time = now

        return detected

    def _update_circle_detection(self, center: Tuple[int, int]) -> Optional[str]:
        # Simple circle detection by centroid path closure and area
        self.center_history.append(center)
        if len(self.center_history) > self.center_history_max:
            self.center_history.pop(0)
        if len(self.center_history) < self.center_history_max:
            return None
        pts = np.array(self.center_history, dtype=np.float32)
        # Compute closed polygon area (shoelace) and perimeter
        x = pts[:, 0]
        y = pts[:, 1]
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        perim = np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1))
        if perim < 1e-3:
            return None
        circularity = 4 * np.pi * area / (perim * perim + 1e-6)
        if 0.5 <= circularity <= 1.2:
            # Determine direction via signed area
            signed_area = 0.5 * (np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            return "circle_clockwise" if signed_area < 0 else "circle_ccw"
        return None

    def _enter_mode(self, mode_name: str, center: Tuple[int, int]):
        self.active_mode = mode_name
        self.mode_started_at = time.time()
        self.mode_anchor_center = center

    def _exit_mode(self):
        self.active_mode = None
        self.mode_anchor_center = None
        self.mode_started_at = 0.0

    def _execute_action(self, gesture: str, active_app: Optional[str] = None, center: Optional[Tuple[int, int]] = None):
        action = self._resolve_action(gesture, active_app or "global")

        try:
            if action.type == "keyboard_send" and action.value:
                # Support common aliases for media/volume keys
                key_value = action.value
                aliases = {
                    "media_play_pause": ["media play pause", "play/pause media"],
                    "volume_up": ["volume up"],
                    "volume_down": ["volume down"],
                    "volume_mute": ["volume mute"],
                }
                # Try primary name first, then aliases
                try:
                    keyboard.send(key_value)
                except Exception:
                    for alt in aliases.get(key_value, []):
                        try:
                            keyboard.send(alt)
                            break
                        except Exception:
                            continue
            elif action.type == "keyboard_hotkey" and action.value:
                combo = action.value.split("+")
                pyautogui.hotkey(*combo)
            elif action.type == "scroll":
                amt = 800
                if action.args and isinstance(action.args.get("amount", None), int):
                    amt = action.args["amount"]
                pyautogui.scroll(amt)
            elif action.type == "move_mouse":
                dx = int((action.args or {}).get("dx", 0))
                dy = int((action.args or {}).get("dy", 0))
                pyautogui.moveRel(dx, dy, duration=0)
            elif action.type == "click":
                button = (action.args or {}).get("button", "left")
                pyautogui.click(button=button)
            elif action.type == "type_text" and action.value:
                pyautogui.typewrite(action.value)
            elif action.type == "window" and action.value:
                if action.value == "win_desktop":
                    pyautogui.hotkey("win", "d")
                elif action.value == "win_switch_win":
                    pyautogui.hotkey("alt", "tab")
                elif action.value == "win_minimize":
                    pyautogui.hotkey("win", "down")
                elif action.value == "win_maximize":
                    pyautogui.hotkey("win", "up")
            elif action.type == "chrome" and action.value:
                if action.value == "chrome_new_tab":
                    pyautogui.hotkey("ctrl", "t")
                elif action.value == "chrome_close_tab":
                    pyautogui.hotkey("ctrl", "w")
                elif action.value == "chrome_next_tab":
                    pyautogui.hotkey("ctrl", "tab")
                elif action.value == "chrome_prev_tab":
                    pyautogui.hotkey("ctrl", "shift", "tab")
            elif action.type == "mode" and action.value and center is not None:
                self._enter_mode(action.value, center)
        except Exception:
            # Avoid crashing the loop on automation errors
            pass

    def run(self, show_preview: bool = True):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError("Could not open webcam. Check camera permissions or index.")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb)
                self._maybe_reload_config()

                # Optional right-hand only filter via handedness
                if getattr(results, 'multi_handedness', None) and self.right_hand_only:
                    labels = [h.classification[0].label for h in results.multi_handedness]
                    if "Right" not in labels:
                        results.multi_hand_landmarks = None

                if results.multi_hand_landmarks:
                    pts = self._landmarks_to_np(results, (frame.shape[0], frame.shape[1]))
                    # Filter by bbox area to avoid tiny/noisy detections
                    if pts is not None:
                        min_area = int((self.config.get("settings", {}) or {}).get("min_bbox_area", 2500))
                        if self._bbox_area(pts) < min_area:
                            pts = None

                if results.multi_hand_landmarks and pts is not None:
                    # Smooth landmarks
                    if self.smoothed_points is None:
                        self.smoothed_points = pts.astype(np.float32)
                    else:
                        self.smoothed_points = (
                            self.ema_alpha * pts.astype(np.float32)
                            + (1 - self.ema_alpha) * self.smoothed_points
                        )
                    pts_s = self.smoothed_points.astype(np.int32)
                    # Draw landmarks
                    self.mp_draw.draw_landmarks(
                        frame,
                        results.multi_hand_landmarks[0],
                        self.mp_hands.HAND_CONNECTIONS,
                    )

                    raw_center = tuple(np.mean(pts_s, axis=0).astype(int))
                    # Smooth center
                    if self.smoothed_center is None:
                        self.smoothed_center = (float(raw_center[0]), float(raw_center[1]))
                    else:
                        self.smoothed_center = (
                            self.ema_alpha * float(raw_center[0]) + (1 - self.ema_alpha) * self.smoothed_center[0],
                            self.ema_alpha * float(raw_center[1]) + (1 - self.ema_alpha) * self.smoothed_center[1],
                        )
                    center = (int(self.smoothed_center[0]), int(self.smoothed_center[1]))
                    cv2.circle(frame, center, 5, (0, 255, 0), -1)

                    static_gesture = self._classify_static_gesture(pts_s)
                    swipe_gesture = self._detect_swipe(center)
                    temporal_gesture = self._update_temporal_gestures(static_gesture, pts_s)
                    circle_gesture = self._update_circle_detection(center)

                    # Gesture priority: mode handling > swipe > temporal > circle > static
                    detected = None
                    active_app = self._active_app_key()

                    # Mode handling (e.g., scroll mode for Chrome): when active, use vertical movement for scroll
                    if self.active_mode == "scroll_mode" and self.mode_anchor_center is not None:
                        dy = center[1] - self.mode_anchor_center[1]
                        speed = 1.0
                        cfg_modes = (self.config.get("modes", {}) if isinstance(self.config, dict) else {})
                        mode_cfg = cfg_modes.get("scroll_mode", {}) if isinstance(cfg_modes, dict) else {}
                        try:
                            speed = float(mode_cfg.get("speed", 1.0))
                        except Exception:
                            speed = 1.0
                        scroll_amt = int(-dy * speed)
                        if abs(scroll_amt) > 10:
                            pyautogui.scroll(scroll_amt)
                            self.mode_anchor_center = center
                        # Exit mode conditions
                        if static_gesture == "fist" or (time.time() - self.mode_started_at > self.mode_timeout_seconds):
                            self._exit_mode()
                    else:
                        # Normal gesture handling
                        detected = swipe_gesture or temporal_gesture or circle_gesture or static_gesture

                        # Majority vote / debounce and per-gesture refractory
                        if detected:
                            self.gesture_buffer.append(detected)
                            counts = Counter(self.gesture_buffer)
                            top_gesture, top_count = counts.most_common(1)[0]
                            if top_count >= self.gesture_vote_threshold:
                                last_t = self.last_trigger_time_by_gesture.get(top_gesture, 0.0)
                                if time.time() - last_t >= self.per_gesture_refractory_s and self._gesture_cooldown_ready(top_gesture):
                                    self.last_trigger_time_by_gesture[top_gesture] = time.time()
                                    self._execute_action(top_gesture, active_app=active_app, center=center)
                                    # If resolved action is a mode, _execute_action will enter it

                        if detected:
                            cv2.putText(
                                frame,
                                f"{active_app}:{detected}",
                                (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 255, 255),
                                2,
                                cv2.LINE_AA,
                            )
                        if self.active_mode:
                            cv2.putText(
                                frame,
                                f"MODE: {self.active_mode}",
                                (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (255, 200, 0),
                                2,
                                cv2.LINE_AA,
                            )
                else:
                    self.prev_center = None
                    self.pinch_prev_dist = None
                    self.center_history.clear()

                if show_preview:
                    cv2.imshow("Gesture Control", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC to exit
                        break
                    if key in (ord('t'), ord('T')):
                        # Toggle preview text/modes if needed in future
                        pass
        finally:
            cap.release()
            cv2.destroyAllWindows()


def default_config() -> Dict[str, Dict]:
    return {
        "open_palm": {"type": "keyboard_send", "value": "media_play_pause"},
        "fist": {"type": "keyboard_send", "value": "media_play_pause"},
        "pinch": {"type": "keyboard_send", "value": "volume_mute"},
        "swipe_up": {"type": "scroll", "args": {"amount": 800}},
        "swipe_down": {"type": "scroll", "args": {"amount": -800}},
        "swipe_left": {"type": "keyboard_send", "value": "media_previous"},
        "swipe_right": {"type": "keyboard_send", "value": "media_next"},
        "point": {"type": "keyboard_hotkey", "value": "win+tab"},
        "screenshot": {"type": "keyboard_hotkey", "value": "print_screen"},
        "snip_tool": {"type": "keyboard_hotkey", "value": "win+shift+s"}
    }


def ensure_default_config(path: Path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_config(), f, indent=2)


