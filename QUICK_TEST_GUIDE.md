# 🚀 KAI OS - Quick Test Guide

## ✅ Beast Mode is Active!

This guide helps you quickly test all KAI OS features.

---

## 🏃 Quick Start

```bash
# 1. Start the server
python api_server.py

# 2. Open in browser
# Dashboard: http://localhost:5000/Frontend/dashboard.html
# Chat: http://localhost:5000/Frontend/chat.html
```

---

## 💬 Chat Commands

### System Control
```
system stats        → CPU, RAM, disk usage
optimize system     → Clean temp files
grid windows        → Arrange windows in grid
split screen        → Side-by-side layout
screenshot          → Take screenshot
```

### Media
```
play music lofi beats    → Play music
pause music              → Pause playback
play video python tutorial  → Play YouTube video
volume 50                → Set volume
```

### Productivity
```
translate hello to spanish     → Translation
calculate 15 percent of 250    → Math (= 37.5)
solve x^2 - 5x + 6 = 0         → Quadratic solver
convert 100 celsius to fahrenheit  → Unit conversion
```

### Data
```
bitcoin price        → Crypto prices
weather in london    → Weather info
news about tech      → Latest news
```

### Creative
```
generate image of a futuristic city  → AI image
```

---

## 🔧 API Testing (Browser Console)

Press F12, go to Console, paste:

```javascript
// Test connection
fetch('http://localhost:5000/api/v1/status', {
    headers: {'X-API-Key': 'demo_key_12345'}
}).then(r => r.json()).then(console.log);

// Send a message
fetch('http://localhost:5000/api/v1/chat', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({query: 'system stats'})
}).then(r => r.json()).then(console.log);

// Get system stats
fetch('http://localhost:5000/api/v1/system/detailed_stats', {
    headers: {'X-API-Key': 'demo_key_12345'}
}).then(r => r.json()).then(console.log);
```

---

## 📸 Instagram API

```javascript
// Check status
fetch('http://localhost:5000/api/v1/instagram/status', {
    headers: {'X-API-Key': 'demo_key_12345'}
}).then(r => r.json()).then(console.log);

// Login
fetch('http://localhost:5000/api/v1/instagram/login', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'YOUR_USERNAME',
        password: 'YOUR_PASSWORD'
    })
}).then(r => r.json()).then(console.log);
```

---

## ✅ Expected Results

| Feature | Status | Notes |
|---------|--------|-------|
| System Stats | ✅ Working | Shows CPU, RAM, disk |
| Math Solver | ✅ Working | Natural language math |
| Translator | ✅ Working | 46+ languages |
| Music Player | ✅ Working | YouTube streaming |
| Video Player | ✅ Working | YouTube search |
| Image Gen | ✅ Working | AI image creation |
| Gestures | ✅ Working | Face/nose tracking |
| Instagram | ✅ API Ready | Requires login |
| WhatsApp | ✅ Working | Messages/calls |

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Check Python version
python --version  # Need 3.11+

# Check dependencies
pip install -r Requirements.txt
```

### Connection error
- Make sure server is running on port 5000
- Check firewall settings
- Verify API key matches

### YouTube search fails
- Uses fallback to open browser directly
- Install yt-dlp: `pip install yt-dlp`

---

## 📝 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/status` | GET | Server status |
| `/api/v1/chat` | POST | Send message |
| `/api/v1/system/detailed_stats` | GET | System stats |
| `/api/v1/image/generate` | POST | Generate image |
| `/api/v1/instagram/status` | GET | Instagram status |

---

**The server is ready! Start chatting!** 🎉
