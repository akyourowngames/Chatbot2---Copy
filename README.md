# 🚀 KAI OS - Beast Mode AI Assistant

<div align="center">

![KAI OS](https://img.shields.io/badge/KAI%20OS-Beast%20Mode-8b5cf6?style=for-the-badge&logo=lightning&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-00ff88?style=for-the-badge)

**Your Premium AI Operating System with Advanced Automation**

[Features](#-features) • [Quick Start](#-quick-start) • [Commands](#-commands) • [API](#-api-reference)

</div>

---

## ✨ Features

### 🧠 AI Intelligence
- **Multi-Model Support**: Gemini Pro, GPT-4, Claude integration
- **Contextual Memory**: Remembers conversations and learns preferences
- **Smart Predictions**: AI-powered command suggestions

### ⚡ System Control (Beast Mode)
- **PC Diagnostics**: CPU, RAM, disk, battery monitoring
- **Window Management**: Grid layout, split screen, focus mode
- **System Optimization**: Temp cleanup, process management
- **Power Control**: Shutdown, restart, sleep, hibernate

### 🎵 Media & Entertainment
- **Music Player**: YouTube streaming, queue, volume control
- **Video Player**: YouTube search, VLC integration, watch history
- **Voice Control**: Speech-to-text, text-to-speech

### 🌐 Productivity Tools
- **Translator**: 46+ languages with auto-detection
- **Math Solver**: Natural language calculations, equations
- **Code Executor**: Sandboxed Python execution
- **Web Scraper**: Fast markdown extraction

### 📱 Social Automation
- **Instagram**: DMs, follow/unfollow, post, search
- **WhatsApp**: Messages, groups, calls
- **Email**: Draft, send, templates

### 🎮 Advanced Features
- **Gesture Control**: Face tracking, wink clicks, nose cursor
- **Smart Workflows**: Automated task sequences
- **Live Data**: Crypto, stocks, weather, news

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Electron)
- Chrome browser

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/kai-os.git
cd kai-os

# Install Python dependencies
pip install -r Requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env and add your API keys

# Start the server
python api_server.py
```

### Access the Interface
- **Dashboard**: Open `Frontend/dashboard.html` in browser
- **Chat**: Open `Frontend/chat.html` in browser
- **API**: `http://localhost:5000/api/v1`

---

## 💬 Commands

### System
| Command | Description |
|---------|-------------|
| `system stats` | Show CPU, RAM, disk usage |
| `optimize system` | Clean temp files, free memory |
| `grid windows` | Arrange windows in grid |
| `split screen` | Side-by-side window layout |
| `screenshot` | Take a screenshot |

### Media
| Command | Description |
|---------|-------------|
| `play music [song]` | Play music from YouTube |
| `pause music` | Pause playback |
| `play video [query]` | Play YouTube video |
| `volume [0-100]` | Set volume level |

### Productivity
| Command | Description |
|---------|-------------|
| `translate [text] to [language]` | Translate text |
| `calculate [expression]` | Math calculation |
| `15 percent of 250` | Natural language math |
| `solve x^2 - 5x + 6 = 0` | Solve equations |

### Data
| Command | Description |
|---------|-------------|
| `bitcoin price` | Get crypto prices |
| `weather in [city]` | Get weather info |
| `news about [topic]` | Get latest news |

---

## 🔌 API Reference

### Base URL
```
http://localhost:5000/api/v1
```

### Authentication
```http
X-API-Key: demo_key_12345
```

### Endpoints

#### Chat
```http
POST /chat
Content-Type: application/json

{
  "query": "your message here"
}
```

#### System Stats
```http
GET /system/detailed_stats
```

#### Image Generation
```http
POST /image/generate
Content-Type: application/json

{
  "prompt": "a futuristic city"
}
```

---

## 📁 Project Structure

```
kai-os/
├── api_server.py          # Main Flask API server
├── main.py                # Standalone entry point
├── Backend/               # Core modules
│   ├── MusicPlayer.py     # Beast Mode music
│   ├── VideoPlayer.py     # YouTube integration
│   ├── Translator.py      # 46+ languages
│   ├── MathSolver.py      # Natural language math
│   ├── CodeExecutor.py    # Sandboxed execution
│   ├── UltimatePCControl.py  # System controls
│   ├── WindowManager.py   # Window management
│   └── JarvisGesture.py   # Face/gesture control
├── Frontend/              # Web interfaces
│   ├── dashboard.html     # Beast Mode dashboard
│   └── chat.html          # Chat interface
├── Data/                  # Runtime data
├── Config/                # Configuration files
└── docs/                  # Documentation
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# AI Models
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# API Security
API_KEY=demo_key_12345
DEVELOPER_API_KEY=demo_key_12345

# Optional Services
WEATHER_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
```

---

## 🎨 Beast Mode Features

### Dashboard Widgets
- 📊 Real-time system stats
- 🎵 Music player with search
- 🎬 Video player
- 🌐 Translator
- 🔢 Calculator
- 🌤️ Weather
- 📈 Markets
- 🧠 Memory system

### Chat Quick Actions
- 💡 Capabilities guide
- 🚀 Productivity workflows
- 📊 Live market data
- 🎨 AI image generation
- ⚡ System controls
- 🎵 Music playback
- 🌐 Translation
- 🔢 Math solving

---

## 📝 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<div align="center">

**Built with ❤️ by the KAI OS Team**

[⬆ Back to Top](#-kai-os---beast-mode-ai-assistant)

</div>
# Chatbot2---Copy
# Chatbot2---Copy
