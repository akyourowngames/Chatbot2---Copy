# 🚀 JARVIS v8.0 - QUICK REFERENCE GUIDE

## 📋 QUICK START

### 1. Restart API Server (Important!)
```bash
# Stop current server (Ctrl+C if running)
# Then start:
python api_server.py
```

The server will auto-load all new modules!

---

## 💬 NATURAL LANGUAGE COMMANDS

### Document Creation:
```
"create a PDF about [topic]"
"generate a PowerPoint on [topic]"
"make a report about [topic]"
```

### Image Generation:
```
"create a [description] in [style] style"
"generate an HD image of [description]"
"make variations of [description]"
```

**Available Styles:**
realistic, anime, oil_painting, watercolor, sketch, 3d_render, cyberpunk, fantasy, minimalist, vintage, comic, pixel_art

### Information:
```
"what's the weather in [city]"
"get news about [topic]"
"what's the price of [crypto/stock]"
```

### Entertainment:
```
"tell me a joke"
"tell me a fact"
"give me a quote"
```

### Memory:
```
"remember that [fact]"
"what do you remember about [topic]"
```

### Media Control:
```
"play [song/video] on YouTube"
```

---

## 🔌 NEW API ENDPOINTS

### Documents:
```
POST /api/v1/documents/pdf
POST /api/v1/documents/powerpoint
POST /api/v1/documents/report
```

### Images:
```
POST /api/v1/images/generate
POST /api/v1/images/generate/hd
POST /api/v1/images/generate/variations
GET  /api/v1/images/styles
GET  /api/v1/images/list
```

---

## 📝 EXAMPLE REQUESTS

### Create PDF:
```javascript
fetch('/api/v1/documents/pdf', {
  method: 'POST',
  headers: {
    'X-API-Key': 'demo_key_12345',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My Document',
    content: [
      {type: 'heading', text: 'Chapter 1'},
      {type: 'paragraph', text: 'Content here...'},
      {type: 'bullet', text: 'Point 1'},
      {type: 'spacer'}
    ]
  })
})
```

### Generate Image:
```javascript
fetch('/api/v1/images/generate', {
  method: 'POST',
  headers: {
    'X-API-Key': 'demo_key_12345',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: 'beautiful sunset over mountains',
    style: 'anime',
    num_images: 1
  })
})
```

### Create PowerPoint:
```javascript
fetch('/api/v1/documents/powerpoint', {
  method: 'POST',
  headers: {
    'X-API-Key': 'demo_key_12345',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My Presentation',
    slides: [
      {
        title: 'Introduction',
        content: ['Point 1', 'Point 2', 'Point 3']
      },
      {
        title: 'Conclusion',
        content: ['Summary', 'Next steps']
      }
    ]
  })
})
```

---

## 🎨 IMAGE STYLES REFERENCE

| Style | Description |
|-------|-------------|
| **realistic** | Photorealistic, professional photography |
| **anime** | Japanese anime/manga style |
| **oil_painting** | Classical oil painting |
| **watercolor** | Soft watercolor art |
| **sketch** | Pencil sketch, hand-drawn |
| **3d_render** | 3D rendered, Unreal Engine |
| **cyberpunk** | Neon lights, futuristic |
| **fantasy** | Magical, ethereal |
| **minimalist** | Clean, simple, modern |
| **vintage** | Retro, nostalgic |
| **comic** | Comic book style |
| **pixel_art** | 8-bit retro gaming |

---

## 📄 DOCUMENT CONTENT TYPES

### PDF/Report Content Blocks:
```javascript
{type: 'heading', text: 'Your Heading'}
{type: 'paragraph', text: 'Your paragraph text...'}
{type: 'bullet', text: 'Bullet point'}
{type: 'spacer'}  // Adds vertical space
{type: 'pagebreak'}  // New page
```

### PowerPoint Slide Layouts:
```javascript
{
  title: 'Slide Title',
  content: ['Point 1', 'Point 2', 'Point 3'],
  layout: 'content'  // or 'title'
}
```

---

## 🔥 POWER TIPS

### 1. Combine Features:
```
"create a PDF about AI and generate an image in cyberpunk style"
```

### 2. Use Memory:
```
"remember that I prefer anime style images"
// Later:
"generate a cat" → Uses anime style automatically
```

### 3. Batch Operations:
```javascript
// Generate multiple images in different styles
for (const style of ['anime', 'realistic', 'cyberpunk']) {
  await generateImage('sunset', style);
}
```

### 4. Custom Templates:
```javascript
// Create reusable document templates
const reportTemplate = {
  title: 'Weekly Report',
  content: [
    {type: 'heading', text: 'Summary'},
    {type: 'paragraph', text: '...'},
    {type: 'heading', text: 'Details'},
    // ... more sections
  ]
};
```

---

## 🐛 TROUBLESHOOTING

### Issue: New features not working
**Solution:** Restart the API server
```bash
python api_server.py
```

### Issue: PDF/PowerPoint not generating
**Solution:** Check dependencies
```bash
pip install reportlab python-pptx
```

### Issue: Images not generating
**Solution:** Check internet connection (Pollinations AI requires internet)

### Issue: Chat commands not recognized
**Solution:** Use exact phrases from examples above

---

## 📊 FEATURE CHECKLIST

✅ Document Generation (PDF, PowerPoint, Reports)  
✅ Enhanced Image Generation (12 styles)  
✅ Natural Language Commands (20+ types)  
✅ Weather & News Integration  
✅ Market Data (Crypto & Stocks)  
✅ YouTube Control  
✅ Memory System  
✅ Entertainment (Jokes, Facts, Quotes)  
✅ Cache Performance Monitoring  
✅ 70+ API Endpoints  

---

## 🎯 COMMON USE CASES

### Student:
```
"create a PDF about photosynthesis"
"generate a diagram in sketch style"
"remember that my exam is on Friday"
```

### Professional:
```
"create a business report about Q4"
"generate a logo in minimalist style"
"make a PowerPoint for the meeting"
```

### Developer:
```
"create API documentation PDF"
"generate UI mockup in 3d_render style"
"make a presentation about our stack"
```

### Creator:
```
"generate artwork in cyberpunk style"
"create variations of my character"
"make a comic page in comic style"
```

---

## 📚 DOCUMENTATION FILES

- **`UPGRADE_V8.md`** - Complete upgrade guide
- **`UPGRADE_COMPLETE_V8.md`** - Completion summary
- **`QUICK_REFERENCE.md`** - This file
- **`API_DOCUMENTATION.md`** - Full API reference
- **`INTEGRATION_COMPLETE.md`** - Integration guide

---

## 🚀 READY TO GO!

Your JARVIS v8.0 is now the **MOST ADVANCED AI ASSISTANT** available!

**Start creating amazing things! 🎉**
