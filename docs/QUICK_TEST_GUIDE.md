# 🧪 Quick Test Guide - JARVIS v11.0

## ✅ Server Status: RUNNING
API is healthy and all modules loaded successfully!

---

## 🎵 Test 1: Music Player

### Try these commands in chat:
```
play lofi music
play shape of you
play relaxing piano music
```

### What should happen:
1. Message: "🎵 Now playing: [song name]"
2. Music downloads from YouTube (10-30 seconds first time)
3. Music plays through your speakers
4. File saved in `Data/Music/` folder

### If it doesn't work:
```bash
# Install yt-dlp
pip install yt-dlp

# Test manually
yt-dlp --version
```

---

## 🖼️ Test 2: Image Generation

### Try these commands:
```
generate image of a sunset
create image of a black panther with fire
draw a futuristic city
```

### What should happen:
1. Message: "✅ Generated realistic style image!"
2. Image appears in the chat
3. Image saved in `Data/` folder

### Check the response:
- Should show image preview
- Should have markdown format: `![Image](/data/filename.jpg)`

---

## 💻 Test 3: Python Code Execution

### Try these commands:
```
run python code: print("Hello JARVIS!")
execute: for i in range(5): print(i)
run code: import math; print(math.pi)
```

### What should happen:
1. Code executes safely
2. Output shown in formatted code block
3. Execution time displayed

### Example output:
```
✅ Code executed successfully!

**Output:**
```
Hello JARVIS!
```

⏱️ Execution time: 0.002s
```

---

## 📎 Test 4: File Upload

### Steps:
1. Click the 📎 (attach) button in chat
2. Select any file:
   - Image (JPG, PNG)
   - Code file (PY, JS)
   - Text file (TXT)
   - PDF document

### What should happen:
1. Upload progress message
2. Detailed file analysis
3. For images: Shows dimensions, format, size
4. For code: Shows line count, language
5. For PDFs: Shows page count

### Example response:
```
✅ File Uploaded & Analyzed

📄 Filename: test.jpg
📊 Type: image
💾 Size: 2.5 MB

🖼️ Image Details:
- Dimensions: 1920x1080 pixels
- Format: JPEG
- Megapixels: 2.07 MP
```

---

## 🔍 Quick Diagnostics

### Check if server is running:
```bash
curl -X GET http://localhost:5000/api/v1/health -H "X-API-Key: demo_key_12345"
```

### Expected response:
```json
{
  "modules": {
    "automation": true,
    "chat": true,
    "speech": true,
    "vision": true
  },
  "name": "JARVIS API Ultimate",
  "status": "healthy",
  "version": "7.0"
}
```

---

## 🐛 Troubleshooting

### Music not playing?
```bash
# Install yt-dlp
pip install yt-dlp

# Check pygame
pip install pygame
```

### Images not generating?
- Check `Data/` folder exists
- Check enhanced_image_gen module loaded
- Look for error messages in server console

### Code not executing?
- Check for forbidden operations (file I/O, dangerous imports)
- Code executor blocks: `import os`, `open()`, `exec()`, etc.

### File upload failing?
- Check file size (large files may timeout)
- Check `Data/Uploads/` folder exists
- Check FileAnalyzer module loaded

---

## 📊 Module Status Check

Open browser and go to:
```
http://localhost:5000/api/v1/health
```

Should show all modules as `true`:
- ✅ chat
- ✅ automation
- ✅ vision
- ✅ speech

---

## 🎯 Success Criteria

### Music Player ✅
- [ ] Downloads music from YouTube
- [ ] Plays audio through speakers
- [ ] Shows "Now playing" message
- [ ] Files saved in Data/Music/

### Image Generation ✅
- [ ] Generates images
- [ ] Displays in chat
- [ ] Shows image preview
- [ ] Files saved in Data/

### Code Execution ✅
- [ ] Runs Python code
- [ ] Shows output
- [ ] Shows execution time
- [ ] Blocks dangerous operations

### File Upload ✅
- [ ] Accepts file uploads
- [ ] Analyzes file content
- [ ] Shows detailed info
- [ ] Saves to Data/Uploads/

---

## 🎉 All Tests Passed?

If all 4 features work, you're good to go! 🚀

**Your JARVIS AI is now fully operational!**

---

## 💡 Pro Tips

1. **First music play** takes longer (download time)
2. **Subsequent plays** of same song are instant (cached)
3. **Image generation** quality depends on prompt detail
4. **Code execution** is sandboxed for safety
5. **File analysis** works best with common formats

---

**Happy testing! 😊**
