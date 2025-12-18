"""
KAI VOICE ASSISTANT — English Only
===================================
Translates any language to English, responds in English
"""

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTextEdit, QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtGui import (QPainter, QColor, QPen, QRadialGradient, QBrush, QLinearGradient, QFont)
from PyQt5.QtCore import (Qt, QTimer, QPoint, pyqtSignal, QDateTime)
import sys
import math
import threading
import random
import requests
from dotenv import dotenv_values

try:
    import speech_recognition as sr
    HAS_SPEECH = True
except:
    HAS_SPEECH = False

try:
    from vosk import Model, KaldiRecognizer
    import json
    import wave
    import pyaudio
    HAS_VOSK = True
except:
    HAS_VOSK = False

try:
    import psutil
    HAS_PSUTIL = True
except:
    HAS_PSUTIL = False

# Porcupine disabled - using Vosk/manual wake word
HAS_PORCUPINE = False


env = dotenv_values(".env")
ASSISTANT = env.get("Assistantname", "KAI")
USER_NAME = env.get("Username", "User")
API_URL = "http://localhost:5000/api/v1"
API_KEY = "demo_key_12345"


# ==================== SMART COMMAND ROUTER ====================

class SmartRouter:
    """
    Intent-based command router - executes common commands directly without LLM.
    Only falls back to LLM for complex/conversational queries.
    """
    
    # Command patterns for intent detection
    INTENTS = {
        "screenshot": ["screenshot", "capture screen", "take picture", "screen capture", "snap screen"],
        "time": ["what time", "current time", "time now", "tell me the time", "what's the time"],
        "date": ["what date", "today's date", "what day", "current date", "today is"],
        "open_app": ["open", "launch", "start", "run"],
        "close_app": ["close", "exit", "quit", "kill"],
        "search": ["search for", "google", "look up", "find online", "search"],
        "weather": ["weather", "temperature", "forecast", "how hot", "how cold"],
        "volume_up": ["volume up", "louder", "increase volume", "turn up"],
        "volume_down": ["volume down", "quieter", "decrease volume", "turn down"],
        "mute": ["mute", "silence", "no sound"],
        "play_music": ["play music", "play song", "music please"],
        "stop_music": ["stop music", "pause music", "stop playing"],
        "system_info": ["cpu usage", "memory usage", "battery", "system status", "how much ram"],
        "hello": ["hello kai", "hi kai", "hey kai", "good morning kai", "good afternoon kai"],
        "thanks": ["thank you", "thanks kai", "appreciate"],
        "bye": ["bye kai", "goodbye kai", "see you kai"],
        # FILE OPERATIONS - Execute keyboard shortcuts
        "select_all": ["select all", "select everything", "ctrl a"],
        "copy": ["copy this", "copy that", "copy it", "ctrl c"],
        "cut": ["cut this", "cut that", "ctrl x"],
        "paste": ["paste this", "paste that", "paste it", "ctrl v"],
        "undo": ["undo", "undo that", "ctrl z"],
        "redo": ["redo", "redo that", "ctrl y"],
        "delete": ["delete everything", "delete all", "delete files", "remove everything", "remove all", "clear all"],
    }
    
    # Known apps for extraction
    APPS = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "gmail": "https://gmail.com",
        "chrome": "chrome",
        "spotify": "spotify",
        "discord": "discord",
        "whatsapp": "whatsapp",
        "telegram": "telegram",
        "notepad": "notepad",
        "calculator": "calc",
        "settings": "ms-settings:",
        "file explorer": "explorer",
        "files": "explorer",
        "downloads": "explorer shell:Downloads",
        "documents": "explorer shell:Documents",
        "cmd": "cmd",
        "terminal": "wt",
        "vscode": "code",
        "code": "code",
    }
    
    @classmethod
    def detect_intent(cls, text):
        """Detect intent from text - FIXED: only match at START of text or as full phrase"""
        text_lower = text.lower().strip()
        
        for intent, patterns in cls.INTENTS.items():
            for pattern in patterns:
                # Pattern must be at START of text, or preceded by a word boundary
                if text_lower.startswith(pattern):
                    return intent
                # Or check if it's a complete phrase (not substring)
                if f" {pattern}" in f" {text_lower}" and (
                    text_lower.endswith(pattern) or 
                    f"{pattern} " in text_lower or
                    text_lower == pattern
                ):
                    return intent
        return None
    
    @classmethod
    def extract_app(cls, text):
        """Extract app name from text"""
        text_lower = text.lower()
        for app_name, app_cmd in cls.APPS.items():
            if app_name in text_lower:
                return app_name, app_cmd
        return None, None
    
    @classmethod
    def extract_search_query(cls, text):
        """Extract search query from text"""
        text_lower = text.lower()
        for trigger in ["search for", "google", "look up", "find online", "search"]:
            if trigger in text_lower:
                idx = text_lower.find(trigger) + len(trigger)
                query = text[idx:].strip()
                if query:
                    return query
        return text
    
    @classmethod
    def execute(cls, text):
        """
        Execute command if it matches a known intent.
        Returns (handled: bool, response: str)
        """
        import subprocess
        import os
        from datetime import datetime
        
        intent = cls.detect_intent(text)
        
        if not intent:
            return False, None
        
        try:
            # Screenshot
            if intent == "screenshot":
                import pyautogui
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                path = os.path.join(os.path.expanduser("~"), "Pictures", filename)
                pyautogui.screenshot(path)
                return True, f"Screenshot saved to {filename}"
            
            # Time
            elif intent == "time":
                now = datetime.now()
                return True, f"It's {now.strftime('%I:%M %p')}"
            
            # Date
            elif intent == "date":
                now = datetime.now()
                return True, f"Today is {now.strftime('%A, %B %d, %Y')}"
            
            # Open App
            elif intent == "open_app":
                app_name, app_cmd = cls.extract_app(text)
                if app_cmd:
                    if app_cmd.startswith("http"):
                        import webbrowser
                        webbrowser.open(app_cmd)
                    else:
                        subprocess.Popen(app_cmd, shell=True)
                    return True, f"Opening {app_name}"
                return False, None
            
            # Close App
            elif intent == "close_app":
                app_name, _ = cls.extract_app(text)
                if app_name:
                    os.system(f'taskkill /f /im {app_name}.exe 2>nul')
                    return True, f"Closing {app_name}"
                return False, None
            
            # Search
            elif intent == "search":
                query = cls.extract_search_query(text)
                import webbrowser
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return True, f"Searching for {query}"
            
            # Weather (opens weather)
            elif intent == "weather":
                import webbrowser
                webbrowser.open("https://www.google.com/search?q=weather")
                return True, "Opening weather forecast"
            
            # Volume Up
            elif intent == "volume_up":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.1), None)
                return True, "Volume increased"
            
            # Volume Down
            elif intent == "volume_down":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                current = volume.GetMasterVolumeLevelScalar()
                volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.1), None)
                return True, "Volume decreased"
            
            # Mute
            elif intent == "mute":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMute(1, None)
                return True, "Sound muted"
            
            # System Info
            elif intent == "system_info":
                if HAS_PSUTIL:
                    cpu = psutil.cpu_percent()
                    mem = psutil.virtual_memory().percent
                    bat = psutil.sensors_battery()
                    bat_str = f"{bat.percent}%" if bat else "AC power"
                    return True, f"CPU is at {cpu}%, memory at {mem}%, battery at {bat_str}"
                return True, "System monitoring not available"
            
            # Hello
            elif intent == "hello":
                greetings = ["Hello! How can I help you?", "Hey there! What can I do for you?", 
                            "Hi! Ready to assist!", "Hello! I'm listening."]
                import random
                return True, random.choice(greetings)
            
            # Thanks
            elif intent == "thanks":
                responses = ["You're welcome!", "Happy to help!", "Anytime!", "No problem!"]
                import random
                return True, random.choice(responses)
            
            # Bye
            elif intent == "bye":
                return True, "Goodbye! Have a great day!"
            
            # File Operations - Keyboard Shortcuts
            elif intent == "select_all":
                import pyautogui
                pyautogui.hotkey('ctrl', 'a')
                return True, "Selected all"
            
            elif intent == "copy":
                import pyautogui
                pyautogui.hotkey('ctrl', 'c')
                return True, "Copied to clipboard"
            
            elif intent == "cut":
                import pyautogui
                pyautogui.hotkey('ctrl', 'x')
                return True, "Cut to clipboard"
            
            elif intent == "paste":
                import pyautogui
                pyautogui.hotkey('ctrl', 'v')
                return True, "Pasted from clipboard"
            
            elif intent == "undo":
                import pyautogui
                pyautogui.hotkey('ctrl', 'z')
                return True, "Undone"
            
            elif intent == "redo":
                import pyautogui
                pyautogui.hotkey('ctrl', 'y')
                return True, "Redone"
            
            elif intent == "delete":
                import pyautogui
                # First select all, then delete
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('delete')
                return True, "Deleted selected items. Use Ctrl+Z to undo if this was a mistake."
        
        except Exception as e:
            return True, f"Sorry, I couldn't do that: {str(e)[:50]}"
        
        return False, None



def speak(text):
    """Smart TTS - speaks short text fully, summarizes long text"""
    def _speak():
        try:
            import pyttsx3
            e = pyttsx3.init()
            # Better voice settings
            voices = e.getProperty('voices')
            if voices and len(voices) > 1:
                e.setProperty('voice', voices[1].id)
            e.setProperty('rate', 170)
            e.setProperty('volume', 1.0)
            
            text_clean = str(text).strip()
            
            # Short response - speak it all
            if len(text_clean) < 150:
                e.say(text_clean)
            else:
                # Long response - speak first sentence/part + tell user to read
                # Find first sentence end
                end_marks = ['. ', '! ', '? ', '\n']
                first_end = len(text_clean)
                for mark in end_marks:
                    pos = text_clean.find(mark)
                    if pos > 20 and pos < first_end:
                        first_end = pos + 1
                
                # Get first part (max 120 chars)
                first_part = text_clean[:min(first_end, 120)]
                
                # Speak first part + notification
                e.say(first_part)
                e.say("The rest is on your screen.")
            
            e.runAndWait()
        except Exception as ex:
            print(f"TTS Error: {ex}")
    
    threading.Thread(target=_speak, daemon=True).start()


class Reactor(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 320)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(35)
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 0.25
        self.wave = [0.0] * 48
        self.status = "idle"
        self.color = QColor(70, 140, 220)
    
    def set_status(self, s):
        self.status = str(s).lower() if s else "idle"
        if "listen" in self.status:
            self.color = QColor(70, 190, 120)
        elif "speak" in self.status:
            self.color = QColor(95, 155, 235)
        elif "think" in self.status:
            self.color = QColor(145, 105, 215)
        else:
            self.color = QColor(70, 140, 220)
    
    def _tick(self):
        self.angle = (self.angle + 0.55) % 360
        self.pulse += self.pulse_dir
        if self.pulse >= 14 or self.pulse <= 0:
            self.pulse_dir *= -1
        if "listen" in self.status:
            self.wave.pop(0)
            self.wave.append(random.uniform(0.35, 1.0))
        else:
            self.wave.pop(0)
            self.wave.append(max(0, self.wave[-1] - 0.04) if self.wave else 0)
        self.update()
    
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        sz = min(self.width(), self.height())
        sc = sz / 380.0
        cx, cy = self.width() // 2, self.height() // 2
        c = self.color
        
        g = QRadialGradient(cx, cy, int(165 * sc))
        g.setColorAt(0, Qt.transparent)
        g.setColorAt(0.55, QColor(c.red(), c.green(), c.blue(), 18))
        g.setColorAt(1, Qt.transparent)
        p.setBrush(QBrush(g))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPoint(cx, cy), int(165 * sc), int(165 * sc))
        
        if any(w > 0.06 for w in self.wave):
            p.save()
            p.translate(cx, cy)
            for i, lv in enumerate(self.wave):
                if lv > 0.03:
                    a = (i / len(self.wave)) * 360
                    r = math.radians(a)
                    r1, r2 = int(118 * sc), int((118 + lv * 32) * sc)
                    p.setPen(QPen(QColor(c.red(), c.green(), c.blue(), int(145 * lv)), int(2.2 * sc)))
                    p.drawLine(int(r1 * math.cos(r)), int(r1 * math.sin(r)), int(r2 * math.cos(r)), int(r2 * math.sin(r)))
            p.restore()
        
        p.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 40), int(2 * sc)))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPoint(cx, cy), int(128 * sc), int(128 * sc))
        
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        for i in range(12):
            r = math.radians(i * 30)
            al = int(30 + 22 * math.sin(math.radians(i * 30 + self.angle * 2)))
            p.setPen(QPen(QColor(c.red(), c.green(), c.blue(), al), int(2.5 * sc)))
            p.drawLine(int(108 * sc * math.cos(r)), int(108 * sc * math.sin(r)), int(123 * sc * math.cos(r)), int(123 * sc * math.sin(r)))
        p.restore()
        
        for rr, aa in [(95, 28), (74, 22), (54, 17)]:
            p.setPen(QPen(QColor(c.red(), c.green(), c.blue(), int(aa + self.pulse * 0.45)), sc))
            p.drawEllipse(QPoint(cx, cy), int(rr * sc), int(rr * sc))
        
        cr = int((42 + self.pulse * 0.28) * sc)
        cg = QRadialGradient(cx, cy, cr + int(14 * sc))
        cg.setColorAt(0, QColor(255, 255, 255, 230))
        cg.setColorAt(0.28, QColor(c.red(), c.green(), c.blue(), 125))
        cg.setColorAt(0.65, QColor(c.red(), c.green(), c.blue(), 25))
        cg.setColorAt(1, Qt.transparent)
        p.setBrush(QBrush(cg))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPoint(cx, cy), cr + int(10 * sc), cr + int(10 * sc))
        p.setBrush(QBrush(QColor(255, 255, 255, 245)))
        p.drawEllipse(QPoint(cx, cy), int(8 * sc), int(8 * sc))


class Stat(QWidget):
    def __init__(self, icon, title):
        super().__init__()
        self.setFixedHeight(48)
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(8)
        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 16px;")
        ic.setFixedWidth(22)
        ly.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(0)
        lb = QLabel(title)
        lb.setStyleSheet("color: #5A8AB8; font-size: 9px; font-weight: 600;")
        col.addWidget(lb)
        self.val = QLabel("--")
        self.val.setStyleSheet("color: #D8E8F8; font-size: 18px; font-weight: 700;")
        col.addWidget(self.val)
        ly.addLayout(col)
        ly.addStretch()
    
    def set(self, v, u=""):
        self.val.setText(f"{v}{u}")


class Cap(QWidget):
    def __init__(self, icon, title):
        super().__init__()
        self.setFixedHeight(32)
        ly = QHBoxLayout(self)
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(8)
        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 14px;")
        ic.setFixedWidth(20)
        ly.addWidget(ic)
        lb = QLabel(title)
        lb.setStyleSheet("color: #8AB0D0; font-size: 11px; font-weight: 500;")
        ly.addWidget(lb)
        ly.addStretch()


class ActBtn(QPushButton):
    def __init__(self, icon, label):
        super().__init__()
        self.setFixedSize(68, 60)
        self.setCursor(Qt.PointingHandCursor)
        ly = QVBoxLayout(self)
        ly.setContentsMargins(4, 8, 4, 5)
        ly.setSpacing(4)
        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("font-size: 20px; background: transparent;")
        ly.addWidget(ic)
        lb = QLabel(label)
        lb.setAlignment(Qt.AlignCenter)
        lb.setStyleSheet("color: #7898B5; font-size: 8px; font-weight: 600; background: transparent;")
        ly.addWidget(lb)
        self.setStyleSheet("QPushButton { background: rgba(28, 42, 60, 0.7); border: none; border-radius: 10px; } QPushButton:hover { background: rgba(45, 70, 100, 0.85); }")


class Chat(QTextEdit):
    sig = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(130)
        self.setStyleSheet("QTextEdit { background: rgba(14, 20, 30, 0.8); color: #B5C8D8; font-family: 'Segoe UI'; font-size: 11px; border: none; border-radius: 8px; padding: 8px; } QScrollBar:vertical { width: 4px; background: transparent; } QScrollBar::handle:vertical { background: rgba(70, 100, 140, 0.5); border-radius: 2px; }")
        self.sig.connect(self._add)
    
    def _add(self, h):
        self.append(h)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def add(self, sender, txt, user=False):
        c = "#6090B0" if user else "#50A080"
        t = QDateTime.currentDateTime().toString("hh:mm")
        i = "👤" if user else "🤖"
        self.sig.emit(f'<span style="color:#4A5A68;font-size:8px;">{t}</span> <span style="color:{c};font-weight:600;">{i} {sender}</span>: <span style="color:#B8C8D8;">{str(txt)}</span>')


class Dashboard(QMainWindow):
    sig_chat = pyqtSignal(str, str, bool)
    sig_status = pyqtSignal(str)
    sig_reactor = pyqtSignal(str)
    sig_btn = pyqtSignal(str, bool)
    sig_reset_ui = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()
        
        self.busy = False
        self.expanded_log = False
        
        self.cw = QWidget()
        self.setCentralWidget(self.cw)
        
        # Main Layout
        self.main_layout = QHBoxLayout(self.cw)
        self.main_layout.setContentsMargins(35, 28, 35, 28)
        self.main_layout.setSpacing(28)
        
        # --- LEFT PANEL ---
        self.left_container = QWidget()
        left = QVBoxLayout(self.left_container)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(4)
        
        lbl1 = QLabel("⚡ SYSTEM")
        lbl1.setStyleSheet("color: #4A88B5; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        left.addWidget(lbl1)
        left.addSpacing(6)
        self.cpu = Stat("🔲", "CPU")
        self.ram = Stat("💾", "MEMORY")
        self.pwr = Stat("🔋", "POWER")
        self.net = Stat("📶", "NETWORK")
        left.addWidget(self.cpu)
        left.addWidget(self.ram)
        left.addWidget(self.pwr)
        left.addWidget(self.net)
        left.addSpacing(16)
        lbl2 = QLabel("🧠 CAPABILITIES")
        lbl2.setStyleSheet("color: #4A88B5; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        left.addWidget(lbl2)
        left.addSpacing(4)
        for i, t in [("🎙️", "Voice Control"), ("🌐", "Web Search"), ("📱", "App Control"), ("📝", "Smart Tasks")]:
            left.addWidget(Cap(i, t))
        left.addStretch()
        self.main_layout.addWidget(self.left_container, 1)
        
        # --- CENTER PANEL ---
        self.center_container = QWidget()
        center = QVBoxLayout(self.center_container)
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(12)
        
        hdr = QHBoxLayout()
        logo = QLabel(f"⚡ {ASSISTANT.upper()}")
        logo.setStyleSheet("color: #4A92C5; font-size: 17px; font-weight: 700; letter-spacing: 3px;")
        self.stat_lbl = QLabel("● ONLINE")
        self.stat_lbl.setStyleSheet("color: #50B585; font-size: 10px; font-weight: 600;")
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet("color: #5A6878; font-size: 18px; font-weight: 300;")
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet("color: #404855; font-size: 9px;")
        close = QPushButton("✕")
        close.setFixedSize(24, 24)
        close.setStyleSheet("color: #506070; background: transparent; font-size: 14px; border: none;")
        close.clicked.connect(self.close)
        tb = QVBoxLayout()
        tb.setSpacing(0)
        tb.addWidget(self.time_lbl, alignment=Qt.AlignRight)
        tb.addWidget(self.date_lbl, alignment=Qt.AlignRight)
        hdr.addWidget(logo)
        hdr.addSpacing(10)
        hdr.addWidget(self.stat_lbl)
        hdr.addStretch()
        hdr.addLayout(tb)
        hdr.addSpacing(10)
        hdr.addWidget(close)
        center.addLayout(hdr)
        
        self.reactor = Reactor()
        center.addWidget(self.reactor, stretch=1)
        
        self.voice_lbl = QLabel("")
        self.voice_lbl.setAlignment(Qt.AlignCenter)
        self.voice_lbl.setStyleSheet("color: #5A7588; font-size: 11px;")
        center.addWidget(self.voice_lbl)
        
        self.btn = QPushButton("🎤  TAP TO SPEAK")
        self.btn.setFixedSize(190, 42)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.on_btn)
        self._btn_off()
        center.addWidget(self.btn, alignment=Qt.AlignCenter)
        
        hint = QLabel("Say 'Hey KAI' or press SPACE  •  ESC to exit")
        hint.setStyleSheet("color: #3A4550; font-size: 8px;")
        center.addWidget(hint, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.center_container, 3)
        
        # --- RIGHT PANEL ---
        self.right_container = QWidget()
        right = QVBoxLayout(self.right_container)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(6)
        
        # Quick Actions Section (Collapsible)
        self.quick_actions_widget = QWidget()
        qa_layout = QVBoxLayout(self.quick_actions_widget)
        qa_layout.setContentsMargins(0, 0, 0, 0)
        qa_layout.setSpacing(6)
        
        lbl3 = QLabel("⚡ QUICK ACTIONS")
        lbl3.setStyleSheet("color: #4A88B5; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        qa_layout.addWidget(lbl3)
        
        grid = QGridLayout()
        grid.setSpacing(6)
        acts = [("📷", "Screenshot", "take a screenshot"), ("🔍", "Search", "open google"), ("🌤", "Weather", "what's the weather"), ("📧", "Email", "open gmail"), ("📁", "Files", "open downloads"), ("⚙️", "Settings", "open settings")]
        for i, (ic, lb, cm) in enumerate(acts):
            b = ActBtn(ic, lb)
            b.clicked.connect(lambda _, c=cm: self.action(c))
            grid.addWidget(b, i // 3, i % 3)
        qa_layout.addLayout(grid)
        qa_layout.addSpacing(8)
        right.addWidget(self.quick_actions_widget)
        
        # Chat Section
        chat_header = QHBoxLayout()
        lbl4 = QLabel("💬 CONVERSATION")
        lbl4.setStyleSheet("color: #4A88B5; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        chat_header.addWidget(lbl4)
        chat_header.addStretch()
        
        # Expand Button
        self.expand_btn = QPushButton("⛶")
        self.expand_btn.setFixedSize(20, 20)
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setToolTip("Toggle Full Log")
        self.expand_btn.setStyleSheet("color: #4A88B5; background: transparent; border: none; font-size: 14px;")
        self.expand_btn.clicked.connect(self.toggle_log_view)
        chat_header.addWidget(self.expand_btn)
        
        right.addLayout(chat_header)
        
        self.chat = Chat()
        # Default height
        self.chat.setMaximumHeight(130)
        right.addWidget(self.chat)
        
        # Try Saying Section (Collapsible)
        self.try_saying_widget = QWidget()
        ts_layout = QVBoxLayout(self.try_saying_widget)
        ts_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl5 = QLabel("💡 TRY SAYING")
        lbl5.setStyleSheet("color: #4A88B5; font-size: 10px; font-weight: 700; letter-spacing: 2px;")
        ts_layout.addSpacing(8)
        ts_layout.addWidget(lbl5)
        for cmd in ['"Open YouTube"', '"What\'s the weather?"', '"Take a screenshot"']:
            l = QLabel(cmd)
            l.setStyleSheet("color: #6888A8; font-size: 10px; font-style: italic;")
            ts_layout.addWidget(l)
        
        right.addWidget(self.try_saying_widget)
        right.addStretch()
        
        self.main_layout.addWidget(self.right_container, 2)
        
        # Signals
        self.sig_chat.connect(lambda s, t, u: self.chat.add(s, t, u))
        self.sig_status.connect(lambda t: self.voice_lbl.setText(t))
        self.sig_reactor.connect(lambda s: self.reactor.set_status(s))
        self.sig_btn.connect(self._update_btn)
        
        self.t1 = QTimer()
        self.t1.timeout.connect(self._time)
        self.t1.start(1000)
        self.t2 = QTimer()
        self.t2.timeout.connect(self._stats)
        self.t2.start(2000)
        self._time()
        self._stats()
        
        # Wake word listener
        self.wake_active = True
        self.wake_words = ["kai", "kay", "hey kai", "ok kai", "hello kai", "hi kai", "jarvis", "hey jarvis"]
        
        if HAS_SPEECH:
            self.chat.add(ASSISTANT, "Ready! Say 'Hey KAI' or press SPACE to speak.")
            self._start_wake_listener()
        else:
            self.chat.add(ASSISTANT, "Speech not available. Use Quick Actions.")
            
        self.sig_reset_ui.connect(self._reset_ui_slot)
    
    def toggle_log_view(self):
        """Toggle between compact sidebar chat and full-screen log"""
        self.expanded_log = not self.expanded_log
        
        if self.expanded_log:
            # Hide specific elements
            self.left_container.hide()
            self.center_container.hide()
            self.quick_actions_widget.hide()
            self.try_saying_widget.hide()
            
            # Expand chat
            self.chat.setMaximumHeight(16777215) # Max int
            self.expand_btn.setText("🗕")
            self.expand_btn.setToolTip("Restore View")
        else:
            # specific elements
            self.left_container.show()
            self.center_container.show()
            self.quick_actions_widget.show()
            self.try_saying_widget.show()
            
            # Restore chat size
            self.chat.setMaximumHeight(130)
            self.expand_btn.setText("⛶")
            self.expand_btn.setToolTip("Toggle Full Log")
    
    def _start_wake_listener(self):
        """Start background wake word detection - Porcupine preferred"""
        
        # PRIORITY 1: Porcupine (Premium, most reliable - "Hello Kai")
        if HAS_PORCUPINE:
            try:
                self._start_porcupine_wake_listener()
                return
            except Exception as e:
                print(f"[WAKE] Porcupine failed: {e}")
        
        # PRIORITY 2: Vosk (Offline, fuzzy matching)
        if HAS_VOSK:
            try:
                import os
                model_path = os.path.join(os.path.dirname(__file__), "..", "models", "vosk", "vosk-model-small-en-us-0.15")
                if not os.path.exists(model_path):
                    model_path = "models/vosk/vosk-model-small-en-us-0.15"
                
                if os.path.exists(model_path):
                    print(f"[WAKE] Loading Vosk model from: {model_path}")
                    vosk_model = Model(model_path)
                    print("[WAKE] ✓ Vosk model loaded - INSTANT wake word!")
                    self._start_vosk_wake_listener(vosk_model)
                    return
                else:
                    print(f"[WAKE] Vosk model not found at {model_path}")
            except Exception as e:
                print(f"[WAKE] Vosk init error: {e}")
        
        # PRIORITY 3: Google (Slowest, needs network)
        print("[WAKE] Using Google Speech (slower, needs network)")
        self._start_google_wake_listener()
    
    def _start_porcupine_wake_listener(self):
        """Porcupine-based wake word - MOST RELIABLE"""
        def porcupine_loop():
            porcupine = None
            pa = None
            audio_stream = None
            try:
                porcupine = pvporcupine.create(
                    access_key=PORCUPINE_KEY,
                    keyword_paths=[PORCUPINE_KEYWORD]
                )
                
                pa = pyaudio.PyAudio()
                audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length
                )
                
                print(f"[WAKE] 🎯 Porcupine listening for 'Hello Kai' (sample_rate={porcupine.sample_rate})")
                self.sig_status.emit("Say 'Hello Kai'...")
                
                while self.wake_active:
                    if self.busy:
                        import time
                        time.sleep(0.05)
                        continue
                    
                    try:
                        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                        
                        keyword_index = porcupine.process(pcm)
                        
                        if keyword_index >= 0:
                            print("[WAKE] 🎯 PORCUPINE DETECTED: Hello Kai!")
                            self.sig_reactor.emit("listening")
                            self.sig_status.emit("Listening...")
                            self._listen_once(extended=True)
                    except IOError:
                        pass
                        
            except Exception as e:
                print(f"[WAKE] Porcupine error: {e}")
            finally:
                if audio_stream:
                    audio_stream.close()
                if pa:
                    pa.terminate()
                if porcupine:
                    porcupine.delete()
        
        threading.Thread(target=porcupine_loop, daemon=True).start()
    
    def _start_vosk_wake_listener(self, vosk_model):
        """Vosk-based wake word - INSTANT OFFLINE with fuzzy matching"""
        def vosk_loop():
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                           input=True, frames_per_buffer=4000)
            stream.start_stream()
            
            rec = KaldiRecognizer(vosk_model, 16000)
            print("[WAKE] Vosk listening started (offline, instant)")
            
            # Wake word patterns with fuzzy matching
            exact_patterns = [
                "kai", "kay", "jarvis", "hey kai", "hey kay", "hey jarvis",
                "ok kai", "okay kai", "hi kai", "hello kai", "ok jarvis"
            ]
            
            # Partial match prefixes (word must START with these)
            partial_prefixes = ["kai", "kay", "jar", "jarv"]
            
            # Common Vosk mishearings
            kai_variants = [
                "chi", "kye", "ky", "cai", "tie kai", "the kai", "a kai", "high",
                "service", "harvest", "davis", "travis", "javis", "garbage", 
                "office", "target", "drivers", "chavez", "artist", "nervous"
            ]
            
            def is_wake_word(text):
                # Check if text contains wake word with fuzzy matching
                words = text.split()
                
                # 1. Exact pattern match
                for pattern in exact_patterns:
                    if pattern in text:
                        return True, pattern
                
                # 2. Check variants
                for variant in kai_variants:
                    if variant in text:
                        return True, variant
                
                # 3. Partial prefix match
                for word in words:
                    for prefix in partial_prefixes:
                        if word.startswith(prefix) and len(word) <= len(prefix) + 3:
                            return True, word
                
                return False, None
            
            while self.wake_active:
                if self.busy:
                    import time
                    time.sleep(0.05)
                    continue
                
                try:
                    data = stream.read(4000, exception_on_overflow=False)
                    
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").lower().strip()
                        
                        if text:
                            # Visual Feedback (Important for debugging)
                            self.sig_status.emit(f"Heard: {text}")
                            
                            # Use fuzzy matching function
                            matched, pattern = is_wake_word(text)
                            
                            if matched:
                                print(f"[WAKE] *** MATCH: '{text}' -> {pattern} ***")
                                
                                # Reset visuals
                                self.sig_reactor.emit("listening")
                                self.sig_status.emit("Listening...")
                                
                                # Stop streaming temporarily or just listen once
                                self._listen_once(extended=True)
                            else:
                                # Clear "Heard: ..." after a moment if no match
                                QTimer.singleShot(1500, lambda: self.sig_status.emit(""))
                                
                                # Get command after wake word
                                command = ""
                                for wake in ["kai", "kay", "jarvis", "chi", "kye"]:
                                    if wake in text:
                                        idx = text.find(wake) + len(wake)
                                        command = text[idx:].strip()
                                        break
                                
                                if command and len(command) > 2:
                                    self.sig_chat.emit(USER_NAME, command, True)
                                    self.sig_reactor.emit("listening")
                                    threading.Thread(target=lambda c=command: self._process_command(c), daemon=True).start()
                                else:
                                    self.sig_status.emit("Yes? Speak now...")
                                    self.sig_reactor.emit("listening")
                                    threading.Thread(target=lambda: self._listen_once(extended=True), daemon=True).start()
                                
                except Exception as e:
                    import time
                    time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
        
        threading.Thread(target=vosk_loop, daemon=True).start()
    
    def _start_google_wake_listener(self):
        """Google-based wake word (fallback, slower)"""
        def wake_loop():
            rec = sr.Recognizer()
            rec.energy_threshold = 400
            rec.dynamic_energy_threshold = True
            rec.pause_threshold = 0.4
            
            print("[WAKE] Google wake word listener started")
            
            while self.wake_active:
                if self.busy:
                    import time
                    time.sleep(0.1)
                    continue
                
                try:
                    with sr.Microphone() as mic:
                        rec.adjust_for_ambient_noise(mic, duration=0.1)
                        try:
                            audio = rec.listen(mic, timeout=2, phrase_time_limit=2)
                        except sr.WaitTimeoutError:
                            continue
                    
                    try:
                        text = rec.recognize_google(audio).lower()
                        print(f"[WAKE] Heard: {text}")
                        
                        for wake in self.wake_words:
                            if wake in text:
                                print(f"[WAKE] *** MATCH: {wake} ***")
                                idx = text.find(wake) + len(wake)
                                command = text[idx:].strip()
                                
                                if command and len(command) > 2:
                                    self.sig_chat.emit(USER_NAME, command, True)
                                    self._process_command(command)
                                else:
                                    self.sig_status.emit("Yes? Speak now...")
                                    self._listen_once(extended=True)
                                break
                                
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        import time
                        time.sleep(1)
                        
                except:
                    import time
                    time.sleep(0.2)
        
        threading.Thread(target=wake_loop, daemon=True).start()
    
    def _process_command(self, text):
        """Process command after wake word"""
        self.busy = True
        self.sig_btn.emit("🎤  PROCESSING...", True)
        self.sig_reactor.emit("thinking")
        
        # Translate if needed
        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source='auto', target='en').translate(text)
            display_text = translated if translated else text
        except:
            display_text = text
        
        threading.Thread(target=lambda: self._call_api(display_text), daemon=True).start()
    
    def _btn_off(self):
        self.btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(50,88,140,0.85), stop:1 rgba(65,108,165,0.85)); color: #B0C8E0; font-size: 11px; font-weight: 600; letter-spacing: 1px; border: none; border-radius: 21px; } QPushButton:hover { background: rgba(60,105,160,0.95); }")
    
    def _btn_on(self):
        self.btn.setStyleSheet("QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(50,170,105,0.9), stop:1 rgba(65,190,120,0.9)); color: #D0FFD8; font-size: 11px; font-weight: 600; letter-spacing: 1px; border: none; border-radius: 21px; } QPushButton:hover { background: rgba(60,185,115,0.95); }")
    
    def _update_btn(self, text, active):
        self.btn.setText(text)
        if active:
            self._btn_on()
        else:
            self._btn_off()
    
    def _time(self):
        n = QDateTime.currentDateTime()
        self.time_lbl.setText(n.toString("hh:mm:ss"))
        self.date_lbl.setText(n.toString("dddd, MMMM d, yyyy"))
    
    def _stats(self):
        if HAS_PSUTIL:
            try:
                self.cpu.set(f"{psutil.cpu_percent():.0f}", "%")
                self.ram.set(f"{psutil.virtual_memory().percent:.0f}", "%")
                b = psutil.sensors_battery()
                self.pwr.set(f"{b.percent:.0f}" if b else "AC", "%" if b else "")
                self.net.set("●", " OK")
            except:
                pass
    
    def on_btn(self):
        """Handle button click - single listen"""
        if self.busy:
            return
        if not HAS_SPEECH:
            self.chat.add(ASSISTANT, "Speech recognition not available!")
            return
        self._listen_once()
    
    def _listen_once(self, extended=False):
        """Listen for ONE phrase. extended=True for wake word (longer timeout)"""
        self.busy = True
        self.sig_btn.emit("🎤  LISTENING...", True)
        self.sig_reactor.emit("listening")
        self.sig_status.emit("Speak now..." if extended else "Speak...")
        
        def do_listen():
            try:
                rec = sr.Recognizer()
                rec.energy_threshold = 400
                rec.dynamic_energy_threshold = False
                rec.pause_threshold = 0.8 if extended else 0.5  # More time to pause
                rec.phrase_threshold = 0.2
                rec.non_speaking_duration = 0.4
                
                with sr.Microphone() as mic:
                    rec.adjust_for_ambient_noise(mic, duration=0.2)
                    
                    # Extended timeout for wake word triggered listening
                    timeout = 10 if extended else 5
                    phrase_limit = 20 if extended else 10
                    
                    print(f"[LISTEN] Waiting {timeout}s for speech...")
                    audio = rec.listen(mic, timeout=timeout, phrase_time_limit=phrase_limit)
                
                self.sig_status.emit("Got it...")
                self.sig_reactor.emit("thinking")
                
                text = rec.recognize_google(audio)
                
                if text and text.strip():
                    display_text = text
                    if not all(ord(c) < 128 for c in text):
                        try:
                            from deep_translator import GoogleTranslator
                            display_text = GoogleTranslator(source='auto', target='en').translate(text) or text
                        except:
                            pass
                    
                    self.sig_chat.emit(USER_NAME, display_text, True)
                    self._call_api(display_text)
                else:
                    self.sig_status.emit("Didn't catch that")
                    self._reset()
            
            except sr.WaitTimeoutError:
                self.sig_status.emit("Say something after wake word" if extended else "Tap to speak")
                self._reset()
            except sr.UnknownValueError:
                self.sig_status.emit("Didn't understand")
                self._reset()
            except sr.RequestError:
                self.sig_status.emit("Network error")
                self._reset()
            except Exception as e:
                print(f"[LISTEN] Error: {e}")
                self.sig_status.emit("Mic error")
                self._reset()
        
        threading.Thread(target=do_listen, daemon=True).start()
    
    def _reset(self):
        self.busy = False
        self.sig_btn.emit("🎤  TAP TO SPEAK", False)
        self.sig_reactor.emit("idle")
        self.sig_reset_ui.emit()

    def _reset_ui_slot(self):
        QTimer.singleShot(2000, lambda: self.sig_status.emit(""))
    
    def action(self, cmd):
        if self.busy:
            return
        self.chat.add(USER_NAME, cmd, True)
        self.busy = True
        self.reactor.set_status("thinking")
        self.voice_lbl.setText("Processing...")
        threading.Thread(target=lambda: self._call_api(cmd), daemon=True).start()
    
    def _call_api(self, q):
        try:
            # Try SmartRouter first (direct execution without LLM)
            handled, response = SmartRouter.execute(q)
            
            if handled and response:
                # Direct execution succeeded!
                self.sig_chat.emit(ASSISTANT, response, False)
                self.sig_reactor.emit("speaking")
                self.sig_status.emit("Done!")
                self.sig_status.emit("Done!")
                speak(response)
                
                # Reset UI state
                self.sig_reactor.emit("idle")
                self.busy = False
                self.sig_btn.emit("🎤  TAP TO SPEAK", False)
                self.sig_reset_ui.emit()
            else:
                # Fall back to LLM for complex queries
                # Call Flask API with USER context for better intelligence
                print(f"[API] Sending query: {q}")
                import json
                payload = {
                    "query": q,
                    "user_id": USER_NAME,  # Pass username as ID to maintain context
                    "stream": False
                }
                
                try:
                    r = requests.post(f"{API_URL}/chat", headers={"X-API-Key": API_KEY, "Content-Type": "application/json"}, json=payload, timeout=25)
                    if r.status_code == 200:
                        ans = r.json().get("response", "Sorry, error.")
                    else:
                        print(f"[API] Error {r.status_code}: {r.text}")
                        ans = f"Server error: {r.status_code}"
                except requests.exceptions.Timeout:
                    ans = "Server timed out."
                except Exception as e:
                    print(f"[API] Connection failed: {e}")
                    ans = "Could not connect to server."
                
                # Speak full response in expanded mode, or summarized in compact
                self.sig_chat.emit(ASSISTANT, ans, False)
                
                # If short or expanded mode, speak all. logic handled in speak()
                # actually speak() truncates. Let's send full text to speak()
                # speak() logic needs to know if we are in expanded mode? 
                # No, the user said "when full window of log there should be no rest of text on screen"
                # which implies they want to read it.
                # But they also want intelligent output.
                
                self.sig_reactor.emit("speaking")
                speak(ans)
                
                # Reset state
                self.sig_reactor.emit("idle")
                self.sig_status.emit("")
                self.busy = False
                self.sig_btn.emit("🎤  TAP TO SPEAK", False)
                
        except Exception as e:
            self.sig_chat.emit("System", f"Error: {str(e)[:40]}", False)
            self._reset()
    
    def paintEvent(self, e):
        p = QPainter(self)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor(11, 17, 26))
        g.setColorAt(0.5, QColor(15, 23, 34))
        g.setColorAt(1, QColor(9, 15, 23))
        p.fillRect(self.rect(), g)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_Space:
            self.on_btn()
    
    def closeEvent(self, e):
        self.wake_active = False  # Stop wake word listener
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))
    Dashboard().show()
    sys.exit(app.exec_())
