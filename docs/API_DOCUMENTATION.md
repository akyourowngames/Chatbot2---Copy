# JARVIS API Server - Complete API Documentation

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication
All endpoints require an API key in the header:
```
X-API-Key: demo_key_12345
```

---

## 📋 Table of Contents
1. [Core Chat & AI](#core-chat--ai)
2. [Speech & Audio](#speech--audio)
3. [Vision & Images](#vision--images)
4. [Automation & Control](#automation--control)
5. [Memory System](#memory-system)
6. [Advanced Integrations](#advanced-integrations)
7. [YouTube Automation](#youtube-automation)
8. [Chrome Automation](#chrome-automation)
9. [Web Scraping](#web-scraping)
10. [System & Utils](#system--utils)
11. [Cache Management](#cache-management)

---

## 🤖 Core Chat & AI

### Chat with AI
**POST** `/chat`
```json
{
  "query": "What's the weather like?"
}
```
**Response:**
```json
{
  "query": "What's the weather like?",
  "response": "AI response here...",
  "command_executed": false
}
```

### Health Check
**GET** `/health`
```json
{
  "status": "healthy",
  "version": "7.0",
  "name": "JARVIS API Ultimate",
  "modules": {
    "chat": true,
    "automation": true,
    "vision": true,
    "speech": true
  }
}
```

---

## 🎤 Speech & Audio

### Speech Recognition (Listen)
**POST** `/speech/recognize`
```json
{
  "status": "success",
  "text": "recognized speech text"
}
```

### Text-to-Speech
**POST** `/speech/synthesize`
```json
{
  "text": "Hello, how are you?",
  "mode": "play"  // or "file"
}
```
**Response (file mode):**
```json
{
  "status": "success",
  "url": "/data/speech.mp3",
  "timestamp": 1234567890
}
```

### Voice Level
**GET** `/voice/level`
```json
{
  "status": "success",
  "level": 0.75
}
```

---

## 👁️ Vision & Images

### Vision Analysis
**POST** `/vision/analyze`
```json
{
  "query": "What do you see on screen?"
}
```
**Response:**
```json
{
  "status": "success",
  "result": "Description of what's on screen..."
}
```

### Generate Image
**POST** `/image/generate`
```json
{
  "prompt": "a beautiful sunset over mountains"
}
```
**Response:**
```json
{
  "status": "success",
  "images": [
    "/data/a_beautiful_sunset1.jpg",
    "/data/a_beautiful_sunset2.jpg"
  ]
}
```

---

## ⚙️ Automation & Control

### Execute Automation
**POST** `/automation/execute`
```json
{
  "commands": ["open notepad", "shutdown in 60"]
}
```

### Run Workflow
**POST** `/workflow/run`
```json
{
  "workflow": "morning_routine"
}
```

### Gesture Control
**POST** `/gestures/control`
```json
{
  "action": "start"  // or "stop"
}
```

---

## 🧠 Memory System

### Facts
**GET** `/memory/facts?query=python`
**POST** `/memory/facts`
```json
{
  "fact": "User prefers Python over JavaScript",
  "category": "preferences"
}
```

### Preferences
**GET** `/memory/preferences`
**POST** `/memory/preferences`
```json
{
  "key": "favorite_language",
  "value": "Python"
}
```

### Projects
**GET** `/memory/projects`
**POST** `/memory/projects`
```json
{
  "name": "AI Assistant",
  "description": "Building JARVIS-level AI"
}
```

### Get Context
**POST** `/memory/context`
```json
{
  "query": "How's my project going?"
}
```

### Memory Summary
**GET** `/memory/summary`
```json
{
  "status": "success",
  "summary": "Memory Summary:\n- 15 facts stored\n- 5 preferences\n- 3 projects\n- 100 conversations"
}
```

---

## 🌐 Advanced Integrations

### Weather
**GET** `/integrations/weather?city=London`
```json
{
  "status": "success",
  "weather": "22°C, Partly Cloudy"
}
```

### Weather Forecast
**GET** `/integrations/forecast?city=London&days=3`

### News
**GET** `/integrations/news?topic=technology&limit=5`
```json
{
  "status": "success",
  "news": [
    {"title": "...", "url": "...", "source": "..."}
  ]
}
```

### Cryptocurrency Price
**GET** `/integrations/crypto?symbol=bitcoin`
```json
{
  "status": "success",
  "crypto": "Bitcoin: $98,450"
}
```

### Stock Price
**GET** `/integrations/stock?symbol=AAPL`
```json
{
  "status": "success",
  "stock": "AAPL: $185.50"
}
```

### Inspirational Quote
**GET** `/integrations/quote`
```json
{
  "status": "success",
  "quote": "The only way to do great work is to love what you do. - Steve Jobs"
}
```

### Random Joke
**GET** `/integrations/joke`
```json
{
  "status": "success",
  "joke": "Why did the programmer quit his job? Because he didn't get arrays!"
}
```

### Random Fact
**GET** `/integrations/fact`
```json
{
  "status": "success",
  "fact": "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that's still edible."
}
```

### Word Definition
**GET** `/integrations/define?word=serendipity`
```json
{
  "status": "success",
  "definition": "The occurrence of events by chance in a happy or beneficial way."
}
```

### IP Information
**GET** `/integrations/ip`
```json
{
  "status": "success",
  "ip_info": {
    "ip": "123.45.67.89",
    "country": "United States",
    "city": "New York"
  }
}
```

---

## 📺 YouTube Automation

### Control YouTube
**POST** `/youtube/control`
```json
{
  "action": "search",
  "query": "lofi hip hop"
}
```
**Actions:** `search`, `play`, `pause`, `next`, `previous`

---

## 🌐 Chrome Automation

### Control Chrome
**POST** `/chrome/control`
```json
{
  "action": "search",
  "target": "artificial intelligence"
}
```
**Actions:** `start`, `search`, `open`, `command`

---

## 🕷️ Web Scraping

### Scrape Website
**POST** `/scrape`
```json
{
  "url": "https://example.com"
}
```
**Response:**
```json
{
  "status": "success",
  "url": "https://example.com",
  "data": {
    "title": "Example Domain",
    "content": "...",
    "links": []
  }
}
```

---

## 🖥️ System & Utils

### System Statistics
**GET** `/system/stats`
```json
{
  "status": "success",
  "stats": {
    "cpu": "45%",
    "memory": "8GB/16GB",
    "disk": "500GB/1TB"
  }
}
```

### Detailed System Stats
**GET** `/system/detailed_stats`

### System Control
**POST** `/system/control`
```json
{
  "action": "shutdown"  // or "restart", "lock", "screenshot"
}
```

### AI Predictions
**GET** `/predictions`
```json
{
  "status": "success",
  "predictions": ["Task 1", "Task 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}
```

### Window Management
**GET** `/windows/list`
**POST** `/windows/switch`
```json
{
  "app": "Chrome"
}
```

### Wake Word Status
**GET** `/status`
```json
{
  "status": "Available...",
  "wake_word_detected": false
}
```

**POST** `/status/reset`

---

## 💾 Cache Management

### Cache Statistics
**GET** `/cache/stats`
```json
{
  "status": "success",
  "stats": {
    "total_queries": 1500,
    "cache_hits": 450,
    "cache_misses": 1050,
    "hit_rate": 0.30,
    "avg_time_saved": 1.5
  }
}
```

### Clear Cache
**POST** `/cache/clear`
```json
{
  "status": "success",
  "message": "Cache cleared"
}
```

---

## 🔄 Realtime Data

### Live Data (Crypto, Weather)
**GET** `/data/live`
```json
{
  "status": "success",
  "bitcoin": "$98,000",
  "weather": "22°C ☀️ (Local)"
}
```

### Realtime Search
**POST** `/search/realtime`
```json
{
  "query": "latest AI news"
}
```

---

## 📝 Reminders

### Get Reminders
**GET** `/reminders`

### Set Reminder
**POST** `/reminders`
```json
{
  "text": "Call mom",
  "time": "2024-12-15 14:30:00"
}
```

---

## 📊 Usage Examples

### JavaScript/Electron Example
```javascript
const API_KEY = 'demo_key_12345';
const BASE_URL = 'http://localhost:5000/api/v1';

async function chat(query) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({ query })
  });
  return await response.json();
}

// Usage
const result = await chat("What's the weather?");
console.log(result.response);
```

### Python Example
```python
import requests

API_KEY = 'demo_key_12345'
BASE_URL = 'http://localhost:5000/api/v1'

def chat(query):
    response = requests.post(
        f'{BASE_URL}/chat',
        headers={'X-API-Key': API_KEY},
        json={'query': query}
    )
    return response.json()

# Usage
result = chat("Tell me a joke")
print(result['response'])
```

---

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   python api_server.py
   ```

2. **Test the API:**
   ```bash
   curl -X GET http://localhost:5000/api/v1/health \
     -H "X-API-Key: demo_key_12345"
   ```

3. **Chat with JARVIS:**
   ```bash
   curl -X POST http://localhost:5000/api/v1/chat \
     -H "X-API-Key: demo_key_12345" \
     -H "Content-Type: application/json" \
     -d '{"query": "Hello JARVIS"}'
   ```

---

## 📌 Notes

- All endpoints return JSON responses
- Error responses include an `error` field with details
- Most endpoints return a `status` field ("success" or error code)
- The server runs on port 5000 by default
- CORS is enabled for all origins (for Electron app compatibility)

---

## 🎯 New Features Added

The following features have been **newly integrated** into the API:

✅ **Contextual Memory System** - Remember facts, preferences, and projects  
✅ **Response Caching** - Smart caching for faster responses  
✅ **Advanced Integrations** - Weather, News, Crypto, Stocks, Quotes, Jokes, Facts  
✅ **YouTube Automation** - Full playback control  
✅ **Chrome Automation** - Browser control via API  
✅ **Web Scraping** - Extract data from any website  
✅ **Word Definitions** - Dictionary lookup  
✅ **IP Information** - Geolocation data  

All backend features are now fully accessible via the API! 🎉
