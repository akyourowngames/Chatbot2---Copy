# 🎯 JARVIS v12.0 - Quick Start Guide
## Get Started in 5 Minutes!

---

## 🚀 Installation

### Step 1: Install Dependencies
```bash
# Navigate to project directory
cd "c:\Users\Krish\3D Objects\Chatbot2 - Copy"

# Install Instagram automation
pip install instagrapi

# Install website automation (if needed)
pip install selenium beautifulsoup4 webdriver-manager
```

### Step 2: Restart API Server
```bash
# Stop current server (Ctrl+C in terminal)
# Start fresh
python api_server.py
```

### Step 3: Open Chat Interface
- Open `chat.html` in your browser
- Or navigate to `http://localhost:3000`

---

## 📸 Using Image Analysis (FIXED!)

### Upload an Image
1. Click the 📎 (paperclip) button in chat
2. Select an image file
3. Wait for upload and analysis
4. See results in chat:
   - Image preview
   - AI description
   - OCR text (if any)
   - Processing time

### Example Output:
```
✅ File Uploaded Successfully

📄 Filename: sunset.jpg
📊 Type: image
💾 Size: 2.5 MB

🤖 AI Vision Analysis:

**Description:** A beautiful sunset over the ocean with orange and pink clouds

📝 Text Detected in Image:
"Summer Vacation 2024"

⚙️ Processing: BLIP-VQA, 1250ms
```

---

## 📱 Instagram Automation

### Login to Instagram
```javascript
// In browser console or via API
fetch('http://localhost:5000/api/v1/instagram/login', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'your_instagram_username',
        password: 'your_password'
    })
}).then(r => r.json()).then(console.log);
```

### Send a DM
```javascript
fetch('http://localhost:5000/api/v1/instagram/send-message', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'friend_username',
        message: 'Hey! This is sent from JARVIS AI 🤖'
    })
}).then(r => r.json()).then(console.log);
```

### Check Your Messages
```javascript
fetch('http://localhost:5000/api/v1/instagram/messages?limit=10', {
    headers: {
        'X-API-Key': 'demo_key_12345'
    }
}).then(r => r.json()).then(console.log);
```

### Start Monitoring (Auto-check for new DMs)
```javascript
fetch('http://localhost:5000/api/v1/instagram/start-monitoring', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        interval: 30  // Check every 30 seconds
    })
}).then(r => r.json()).then(console.log);
```

### Post a Photo
```javascript
fetch('http://localhost:5000/api/v1/instagram/post-photo', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        image_path: 'C:/path/to/image.jpg',
        caption: 'Posted by JARVIS AI! 🤖✨ #AI #Automation'
    })
}).then(r => r.json()).then(console.log);
```

---

## 🌐 Website Automation

### Python Usage
```python
from Backend.WebsiteAutomation import website_automation

# Start browser
website_automation.start_browser(headless=False)

# Navigate to a website
website_automation.navigate('https://example.com')

# Click a button
website_automation.click_element('#login-button')

# Fill a form
website_automation.type_text('#email', 'user@example.com')
website_automation.type_text('#password', 'password123')

# Take screenshot
website_automation.screenshot('example_page.png')

# Scrape page content
data = website_automation.scrape_page()
print(data['title'])
print(data['headings'])

# Close browser
website_automation.close_browser()
```

### Scrape a News Website
```python
# Start browser
website_automation.start_browser(headless=True)

# Scrape news
result = website_automation.scrape_page('https://news.ycombinator.com')

if result['status'] == 'success':
    data = result['data']
    print(f"Title: {data['title']}")
    print(f"\nTop Headlines:")
    for i, heading in enumerate(data['headings']['h1'][:5], 1):
        print(f"{i}. {heading}")
    
    print(f"\nTop Links:")
    for link in data['links'][:10]:
        print(f"- {link['text']}: {link['href']}")

# Close
website_automation.close_browser()
```

### Monitor Price Changes
```python
# Start browser
website_automation.start_browser(headless=True)

# Navigate to product page
website_automation.navigate('https://example-shop.com/product/123')

# Monitor price element for 5 minutes
result = website_automation.monitor_element(
    selector='.price',
    interval=10,  # Check every 10 seconds
    duration=300  # For 5 minutes
)

# Check for changes
if result['changes']:
    print("Price changed!")
    for change in result['changes']:
        print(f"{change['timestamp']}: {change['old_value']} -> {change['new_value']}")

website_automation.close_browser()
```

---

## 💬 WhatsApp Automation

### Send a Message
```javascript
fetch('http://localhost:5000/api/v1/whatsapp/send', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        phone: '+1234567890',  // Include country code
        message: 'Hello from JARVIS!',
        instant: true
    })
}).then(r => r.json()).then(console.log);
```

### Send to Group
```javascript
fetch('http://localhost:5000/api/v1/whatsapp/send-group', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        group: 'My Group Name',
        message: 'Hello everyone!'
    })
}).then(r => r.json()).then(console.log);
```

---

## 🎨 Using in Chat

### Natural Language Commands

**Image Analysis:**
```
You: "Analyze this image" [attach image]
JARVIS: [Shows image + AI analysis + OCR text]
```

**Instagram:**
```
You: "Send Instagram DM to john saying hello"
JARVIS: [Sends DM via Instagram]

You: "Check my Instagram messages"
JARVIS: [Shows recent DMs]

You: "Post this image to Instagram with caption 'Beautiful sunset'"
JARVIS: [Posts to Instagram feed]
```

**Website Automation:**
```
You: "Scrape news from example.com"
JARVIS: [Scrapes and shows headlines]

You: "Take screenshot of google.com"
JARVIS: [Opens browser, takes screenshot]

You: "Monitor price on amazon.com/product/123"
JARVIS: [Monitors for price changes]
```

**WhatsApp:**
```
You: "Send WhatsApp message to +1234567890 saying hello"
JARVIS: [Sends via WhatsApp Web]

You: "Send to WhatsApp group 'Family' saying good morning"
JARVIS: [Sends to group]
```

---

## 🔑 API Keys

Default API key for testing:
```
X-API-Key: demo_key_12345
```

For production, update in `api_server.py`:
```python
API_KEYS = {
    "your_secure_key_here": {"name": "Your Name", "tier": "pro"}
}
```

---

## 🐛 Common Issues & Solutions

### Issue: Image analysis not showing
**Solution:**
1. Open browser console (F12)
2. Look for errors
3. Check if VQA service loaded in terminal
4. Verify file uploaded successfully

### Issue: Instagram login failed
**Solution:**
1. Verify account via Instagram app first
2. Disable 2FA temporarily
3. Check username/password
4. Look for checkpoint/challenge messages

### Issue: Website automation - ChromeDriver not found
**Solution:**
```bash
pip install webdriver-manager
```

### Issue: WhatsApp not sending
**Solution:**
1. Ensure WhatsApp Web is logged in
2. Check phone number format (+countrycode)
3. Verify internet connection

---

## 📊 Monitoring & Logs

### Check API Server Logs
Look for these messages in terminal:
```
[OK] Instagram Automation loaded
[OK] File Analyzer loaded
[OK] VQA Service loaded
[Instagram] Logged in as username
[Website] Browser started successfully
```

### Check Browser Console
Press F12 in browser and look for:
```
[FILE UPLOAD] Response: {success: true, ...}
```

---

## 🎯 Quick Commands

### Test Image Analysis
1. Open chat
2. Click 📎
3. Upload any image
4. See analysis in chat ✅

### Test Instagram
```javascript
// Quick test in browser console
fetch('http://localhost:5000/api/v1/instagram/status', {
    headers: {'X-API-Key': 'demo_key_12345'}
}).then(r => r.json()).then(console.log);
```

### Test Website Automation
```python
from Backend.WebsiteAutomation import website_automation
print(website_automation.get_status())
```

---

## 🚀 Next Steps

1. **Explore Features**
   - Try image analysis with different images
   - Login to Instagram and send a test DM
   - Scrape your favorite website
   - Send a WhatsApp message

2. **Customize**
   - Add your own automation scripts
   - Create custom workflows
   - Integrate with other services

3. **Build**
   - Create auto-reply bots
   - Build monitoring dashboards
   - Automate repetitive tasks

---

## 📚 Documentation

- **Full Feature List:** `COMPLETE_FEATURE_SUMMARY_V12.md`
- **Detailed Upgrade Guide:** `V12_COMPLETE_UPGRADE.md`
- **API Documentation:** `API_DOCUMENTATION.md`
- **Troubleshooting:** Check terminal logs and browser console

---

## 💡 Pro Tips

1. **Image Analysis:**
   - Use clear, well-lit images for best results
   - OCR works best with printed text
   - Supported formats: JPG, PNG, GIF, WebP

2. **Instagram:**
   - Login once, session persists
   - Start monitoring for real-time notifications
   - Use auto-caption for images

3. **Website Automation:**
   - Use headless mode for faster scraping
   - Monitor elements for price tracking
   - Take screenshots for debugging

4. **WhatsApp:**
   - Keep WhatsApp Web logged in
   - Use instant=true for immediate sending
   - Bulk send for multiple contacts

---

**Need Help?**
- Check logs in terminal
- Open browser console (F12)
- Review documentation files
- Test with simple examples first

**Happy Automating! 🎉**
