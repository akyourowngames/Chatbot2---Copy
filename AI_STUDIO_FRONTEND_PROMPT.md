# 🎨 AI Studio Frontend Development Prompt
## KAI OS - Frontend Integration Guide

> **IMPORTANT**: This file contains ONLY logic, API integration patterns, and technical instructions. AI Studio is responsible for UI/UX design. Backend (Python/API) is handled separately by Antigravity.

---

## 📡 API Configuration

### Base URLs
```javascript
// Toggle between local and cloud deployment
const USE_CLOUD_API = true; // Set to false for local development

const API_URL = USE_CLOUD_API
    ? 'https://kai-api-nxxv.onrender.com/api/v1'  // Cloud (Render)
    : 'http://localhost:5000/api/v1';             // Local development

const BASE_URL = USE_CLOUD_API
    ? 'https://kai-api-nxxv.onrender.com'
    : 'http://localhost:5000';
```

### Authentication
```javascript
// API Key Management (use session storage)
function getApiKey() {
    let key = sessionStorage.getItem('kai_api_key');
    if (!key) {
        key = 'demo_key_12345'; // Default for local dev
        sessionStorage.setItem('kai_api_key', key);
    }
    return key;
}

// Include in every API request header
headers: {
    'X-API-Key': getApiKey(),
    'Content-Type': 'application/json'
}
```

---

## 🔌 Core API Endpoints

### 1. Health Check
```javascript
// Check API connection status
const healthUrl = USE_CLOUD_API 
    ? `${BASE_URL}/health` 
    : `${API_URL}/status`;

const response = await fetch(healthUrl, {
    method: 'GET',
    mode: 'cors',
    signal: AbortSignal.timeout(10000)  // 10s timeout for cold starts
});
```

**Use Case**: Display connection status badge (Connected/Offline)

---

### 2. Chat Endpoint (PRIMARY)
```javascript
// POST /api/v1/chat
const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: userMessage  // User's input text
    })
});

const data = await response.json();
```

**Response Format**:
```json
{
    "response": "AI text response",
    "type": "text|spotify|stream|pdf|scrape|code_execution|video_summary|screenshot",
    "command_executed": true/false,
    
    // Additional fields based on type:
    "spotify": {
        "embed_url": "https://open.spotify.com/embed/...",
        "name": "Track name",
        "external_url": "https://open.spotify.com/track/..."
    },
    "music": {
        "embed_url": "YouTube embed URL",
        "title": "Stream title"
    },
    "pdf_url": "/data/pdfs/...",
    "scrape_result": {
        "title": "Page title",
        "url": "Source URL",
        "content": "Markdown content"
    },
    "code": {
        "code": "Python code",
        "output": "Execution output"
    }
}
```

---

### 3. Image Generation
```javascript
// POST /api/v1/image/generate
const response = await fetch(`${API_URL}/image/generate`, {
    method: 'POST',
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        prompt: "a futuristic city at sunset"
    })
});

const data = await response.json();
// data.images = ["/data/Images/image_xyz.png"]
```

**Response**:
```json
{
    "status": "success",
    "images": [
        "/data/Images/generated_image.png"
    ]
}
```

**Image URL Construction**:
```javascript
const fullImageUrl = imageUrl.startsWith('http') 
    ? imageUrl 
    : `${BASE_URL}${imageUrl}`;
```

---

### 4. System Stats (for dashboard widgets)
```javascript
// GET /api/v1/system/detailed_stats
const response = await fetch(`${API_URL}/system/detailed_stats`, {
    headers: { 'X-API-Key': API_KEY }
});

const stats = await response.json();
```

**Response**: CPU, RAM, disk, network, battery metrics

---

### 5. Translation
```javascript
// POST /api/v1/translate
const response = await fetch(`${API_URL}/translate`, {
    method: 'POST',
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        text: "Hello world",
        target_lang: "es"  // Spanish
    })
});
```

---

### 6. Math Solver
```javascript
// POST /api/v1/math/solve
const response = await fetch(`${API_URL}/math/solve`, {
    method: 'POST',
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        expression: "15 percent of 250"
    })
});
```

---

### 7. Firebase Authentication (Optional)
```javascript
// POST /api/v1/auth/signup
// POST /api/v1/auth/login
// POST /api/v1/auth/logout
// GET /api/v1/auth/verify

// Include JWT token in authenticated requests:
headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'X-API-Key': API_KEY
}
```

---

## 🎯 Smart Command Detection (Frontend Pre-processing)

### Music vs Stream Detection
```javascript
// Differentiate between Spotify music and live streams
const streamKeywords = ['radio', 'station', 'stream', 'live', 'broadcast', 'news', 'channel'];

let processedMessage = message;
const lowerMsg = message.toLowerCase();

if (lowerMsg.startsWith('play ')) {
    const query = lowerMsg.substring(5);
    
    // Stream request?
    if (streamKeywords.some(kw => query.includes(kw))) {
        processedMessage = `stream ${query}`;
    }
    // Music request
    else {
        processedMessage = `spotify ${query}`;
    }
}

// Send processedMessage to API
fetch(`${API_URL}/chat`, {
    body: JSON.stringify({ query: processedMessage })
});
```

---

## 🎨 Response Type Handlers

### 1. Spotify Player
**When**: `data.type === 'spotify'`

```javascript
if (data.type === 'spotify' && data.spotify && data.spotify.embed_url) {
    // Create Spotify iframe embed
    const iframe = `
        <iframe 
            src="${data.spotify.embed_url}" 
            width="100%" 
            height="152" 
            frameborder="0" 
            allowtransparency="true" 
            allow="encrypted-media">
        </iframe>
    `;
    
    // Display with track name and external link
    // data.spotify.name, data.spotify.external_url
}
```

---

### 2. Live Stream Player (Radio/TV)
**When**: `data.type === 'stream'`

```javascript
if (data.type === 'stream' && data.music && data.music.embed_url) {
    // Create YouTube iframe for live streams
    const iframe = `
        <iframe 
            src="${data.music.embed_url}" 
            class="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
        </iframe>
    `;
    
    // Show "LIVE" indicator with red dot
}
```

---

### 3. PDF Preview
**When**: `data.type === 'pdf_capture'` or `data.type === 'pdf'`

```javascript
if (data.type === 'pdf_capture' && data.pdf_url) {
    const pdfUrl = data.pdf_url.startsWith('http') 
        ? data.pdf_url 
        : `${BASE_URL}${data.pdf_url}`;
    
    // Display PDF card with:
    // - Thumbnail (if available): data.thumbnail_url
    // - Title: data.title
    // - Download button
    // - Open in new tab button
}
```

---

### 4. Web Scrape Result
**When**: `data.type === 'scrape'`

```javascript
if (data.type === 'scrape' && data.scrape_result) {
    // Display as styled card:
    // - Title: data.scrape_result.title
    // - URL: data.scrape_result.url
    // - Content: data.scrape_result.content (markdown formatted)
    // - Use formatMessage() to render markdown
}
```

---

### 5. Code Execution
**When**: `data.type === 'code_execution'`

```javascript
if (data.type === 'code_execution' && data.code) {
    // Display code block with syntax highlighting
    // - Code: data.code.code
    // - Output: data.code.output
    // - Use Prism.js for syntax highlighting
}
```

---

### 6. Video Summary
**When**: `data.type === 'video_summary'`

```javascript
if (data.type === 'video_summary') {
    // Display:
    // - Video title: data.title
    // - Thumbnail: data.thumbnail
    // - Summary: data.summary
    // - Key points: data.key_points (array)
}
```

---

### 7. Screenshot Capture
**When**: `data.type === 'screenshot'`

```javascript
if (data.type === 'screenshot' && data.screenshot_url) {
    const fullUrl = data.screenshot_url.startsWith('http')
        ? data.screenshot_url
        : `${BASE_URL}${data.screenshot_url}`;
    
    // Display as image message
}
```

---

## 📝 Message Formatting

### Markdown to HTML
```javascript
function formatMessage(text) {
    // Convert markdown to HTML
    // Support:
    // - **bold**, *italic*, `code`
    // - # Headers
    // - - Lists
    // - ```code blocks```
    // - [links](url)
    // - ![images](url)
    
    // Use a markdown library or implement basic parsing
    return htmlContent;
}
```

### Image URL Extraction
```javascript
// Extract image URLs from response text
const imageUrlRegex = /!\[.*?\]\((.*?)\)|(?:http:\/\/localhost:5000)?\/data\/(?:Images\/)?([^\s\)]+\.(?:jpg|jpeg|png|gif|webp))/gi;

let match;
while ((match = imageUrlRegex.exec(responseText)) !== null) {
    const imageUrl = match[1] || `/data/Images/${match[2]}`;
    const fullUrl = imageUrl.startsWith('http') 
        ? imageUrl 
        : `${BASE_URL}${imageUrl}`;
    
    // Display image
}
```

---

## 🗣️ Voice Features

### Voice Input (Web Speech API)
```javascript
function toggleVoice() {
    if (!('webkitSpeechRecognition' in window)) {
        alert('Voice input not supported in your browser');
        return;
    }
    
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('messageInput').value = transcript;
    };
    
    recognition.onerror = (event) => {
        console.error('Voice recognition error:', event.error);
        // Fallback to server-side recognition if needed
        // POST /api/v1/voice/recognize
    };
    
    recognition.start();
}
```

### Text-to-Speech
```javascript
function speakResponse(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        speechSynthesis.speak(utterance);
    }
}
```

---

## 📊 Chat History Management

### Save to Local Storage (Offline Mode)
```javascript
function saveChatHistory(userMessage, aiResponse) {
    const history = JSON.parse(localStorage.getItem('kai_chat_history') || '[]');
    history.push({
        timestamp: Date.now(),
        user: userMessage,
        assistant: aiResponse,
        conversation_id: currentChatId
    });
    localStorage.setItem('kai_chat_history', JSON.stringify(history));
}
```

### Save to Firebase (Authenticated Users)
```javascript
async function saveMessageToFirebase(userMessage, aiResponse) {
    if (!window.authClient || !window.authClient.isAuthenticated()) {
        return;
    }
    
    const token = window.authClient.getToken();
    
    await fetch(`${API_URL}/chat/save`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            conversation_id: currentChatId,
            user_message: userMessage,
            ai_response: aiResponse,
            timestamp: Date.now()
        })
    });
}
```

### Load Chat History
```javascript
// GET /api/v1/chat/history?conversation_id=xxx
async function loadChatHistory(conversationId) {
    const response = await fetch(
        `${API_URL}/chat/history?conversation_id=${conversationId}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-API-Key': API_KEY
            }
        }
    );
    
    const messages = await response.json();
    // Render messages in UI
}
```

### Delete Conversation
```javascript
// DELETE /api/v1/chat/delete?conversation_id=xxx
async function deleteConversation(conversationId) {
    await fetch(
        `${API_URL}/chat/delete?conversation_id=${conversationId}`,
        {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-API-Key': API_KEY
            }
        }
    );
}
```

---

## 🎮 Quick Actions

### Pre-defined Actions
```javascript
const quickActions = {
    music: "play lofi beats",
    image: "generate image of a sunset",
    search: "search for latest tech news",
    translate: "translate hello to spanish",
    pdf: "generate a report about AI",
    radio: "play BBC news radio",
    scrape: "scrape https://example.com",
    capture: "capture https://example.com as pdf",
    workflow: "show available workflows"
};

function quickAction(action) {
    const message = quickActions[action];
    if (message) {
        sendQuickMessage(message);
    }
}
```

---

## ⚡ Real-time Features

### Connection Status Monitoring
```javascript
async function checkConnection() {
    try {
        const healthUrl = USE_CLOUD_API 
            ? `${BASE_URL}/health` 
            : `${API_URL}/status`;
            
        const res = await fetch(healthUrl, {
            method: 'GET',
            mode: 'cors',
            signal: AbortSignal.timeout(10000)
        });
        
        if (res.ok) {
            updateStatusBadge('connected');
        } else {
            updateStatusBadge('offline');
        }
    } catch (e) {
        updateStatusBadge('offline');
    }
}

// Check every 30 seconds
setInterval(checkConnection, 30000);
```

### Typing Indicator
```javascript
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-' + Date.now();
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="thinking-bar"></div>
            <span>Intelligence Processing...</span>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    return typingDiv.id;
}

function removeTypingIndicator(id) {
    document.getElementById(id)?.remove();
}
```

---

## 🎨 UI State Management

### Message Display Pattern
```javascript
function addMessage(role, content) {
    // role: 'user' | 'assistant'
    
    // 1. Create message container
    const messageDiv = document.createElement('div');
    
    // 2. Add avatar (user icon or AI icon)
    // 3. Add content bubble
    // 4. Format content with markdown
    // 5. Add action buttons (copy, regenerate) for assistant
    // 6. Scroll to bottom smoothly
}
```

### Loading States
```javascript
// Show loading before API call
const typingId = addTypingIndicator();

try {
    const response = await fetch(API_URL + '/chat', {...});
    const data = await response.json();
    
    // Remove loading
    removeTypingIndicator(typingId);
    
    // Display response
    addMessage('assistant', data.response);
} catch (error) {
    removeTypingIndicator(typingId);
    addMessage('assistant', 'Connection error. Please try again.');
}
```

---

## 🔒 Security Best Practices

1. **Never hardcode API keys** - Use session storage or environment variables
2. **Validate all user inputs** before sending to API
3. **Sanitize HTML** when displaying user/AI content
4. **Use HTTPS** in production
5. **Implement CORS** properly
6. **Rate limit** client-side to prevent spam

---

## 📱 Responsive Considerations

1. **Mobile-first design**
2. **Touch-friendly buttons** (min 44x44px)
3. **Hamburger menu** for sidebar on mobile
4. **Responsive embed players** (aspect-ratio CSS)
5. **Lazy load images** for performance

---

## 🎯 File Upload (Vision Features)

### Upload File
```javascript
// POST /api/v1/upload
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'X-API-Key': API_KEY
    },
    body: formData
});

const data = await response.json();
// data.file_url, data.file_id
```

### Analyze Image (Florence-2 Vision)
```javascript
// POST /api/v1/analyze
const response = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        image_url: uploadedImageUrl,
        task: 'caption'  // or 'ocr', 'object_detection'
    })
});

const analysis = await response.json();
// analysis.result, analysis.description
```

---

## 🚀 Performance Tips

1. **Debounce input** to reduce API calls
2. **Cache responses** for repeated queries
3. **Lazy load chat history** (pagination)
4. **Optimize images** before upload
5. **Use Web Workers** for heavy processing
6. **Implement virtual scrolling** for long chats

---

## 📦 Required Libraries

### Already Included in chat.html:
- **Tailwind CSS** - Utility-first styling
- **Prism.js** - Code syntax highlighting
- **Google Fonts** - Inter, JetBrains Mono

### Recommended:
- **Marked.js** or **markdown-it** - Markdown parsing
- **DOMPurify** - XSS protection for HTML sanitization
- **date-fns** - Date formatting

---

## 🎨 Styling Tokens (from chat.html)

```css
/* Glass morphism */
.glass-panel {
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Message bubbles */
.user-bubble {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.assistant-bubble {
    background: rgba(31, 41, 55, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Accent colors */
--accent-500: #8b5cf6;
--accent-600: #7c3aed;
```

---

## 🔄 Example: Complete Chat Flow

```javascript
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 1. Hide welcome screen
    document.getElementById('welcome')?.classList.add('hidden');
    
    // 2. Display user message
    addMessage('user', message);
    input.value = '';
    
    // 3. Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        // 4. Send to API
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: message })
        });
        
        const data = await response.json();
        
        // 5. Remove typing indicator
        removeTypingIndicator(typingId);
        
        // 6. Display AI response
        addMessage('assistant', data.response);
        
        // 7. Handle special response types
        if (data.type === 'spotify' && data.spotify) {
            addSpotifyPlayer('assistant', data.spotify);
        }
        if (data.type === 'stream' && data.music) {
            addStreamPlayer('assistant', data.music);
        }
        // ... other types
        
        // 8. Save to history
        saveChatHistory(message, data.response);
        
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('assistant', 'Connection error. Please try again.');
    }
}
```

---

## 📋 Checklist for New Features

When adding a new frontend feature:

- [ ] Define API endpoint (or request backend to create)
- [ ] Create request function with proper headers
- [ ] Handle loading/error states
- [ ] Parse and validate response
- [ ] Create UI component for response
- [ ] Add to message display logic
- [ ] Test on mobile and desktop
- [ ] Update this documentation

---

## 🆘 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| CORS error | Check CORS_ALLOWED_ORIGINS in backend .env |
| 401 Unauthorized | Verify API_KEY matches backend |
| Embed not loading | Check protocol (file:// vs http://) |
| Image not displaying | Verify full URL with BASE_URL prefix |
| Slow response | Check cold start timeout (10s) |
| Voice not working | Check browser support (Chrome/Edge) |

---

## 📞 Backend Coordination

**When you need backend changes:**
1. Request new API endpoint in this format:
   - Method: GET/POST/DELETE
   - Path: /api/v1/feature_name
   - Request body schema
   - Response schema

2. Antigravity will implement and update this doc

**Current backend capabilities:**
- ✅ Chat with AI models (Gemini, GPT, Claude)
- ✅ Image generation
- ✅ Spotify integration
- ✅ Live stream player
- ✅ Web scraping
- ✅ PDF capture
- ✅ Translation
- ✅ Math solving
- ✅ Code execution
- ✅ Video summarization
- ✅ System stats
- ✅ Firebase auth
- ✅ File upload/download
- ✅ Florence-2 vision analysis

---

## 🎓 Final Notes

1. **Focus on UX/UI design** - Backend handles all heavy lifting
2. **Keep frontend lightweight** - Avoid complex business logic
3. **Follow chat.html patterns** - Consistency is key
4. **Test with both local and cloud APIs**
5. **Mobile-first, always**

**Questions?** Ask Antigravity for backend clarifications!

---

*Last Updated: 2025-12-19*
*Version: 1.0*
*Maintained by: Antigravity (Backend) + AI Studio (Frontend)*
