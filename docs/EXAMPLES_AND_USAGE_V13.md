# 🎯 JARVIS v13.0 - Complete Examples & Usage Guide
## All Features with Real Examples

---

## 🎨 **1. IMAGE GENERATION - AUTO-DISPLAY** ✨

### Problem FIXED!
Images now automatically display in chat - no need to open manually!

### How to Use:

**Method 1: Direct Command**
```
You: generate image of a sunset over mountains
JARVIS: ✅ Generated image!
[Image automatically displays in chat]
```

**Method 2: Create Image**
```
You: create image cyberpunk city at night
JARVIS: ✅ Generated image!
[Image automatically displays in chat]
```

**What Changed:**
- ✅ Images auto-detect from response
- ✅ Displays inline in chat
- ✅ No manual opening needed
- ✅ Works with markdown format too

---

## 📸 **2. INSTAGRAM AUTOMATION - ENHANCED** 🚀

### NEW FEATURES ADDED:
- ✅ Like posts
- ✅ Comment on posts
- ✅ Follow/unfollow users
- ✅ Get followers/following lists
- ✅ Search users
- ✅ Get user posts
- ✅ Auto-reply to DMs

### Complete Examples:

#### **A. Login to Instagram**
```javascript
fetch('http://localhost:5000/api/v1/instagram/login', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'your_username',
        password: 'your_password'
    })
}).then(r => r.json()).then(console.log);
```

**Response:**
```json
{
    "status": "success",
    "message": "Logged in as your_username",
    "username": "your_username"
}
```

---

#### **B. Send Direct Message**
```javascript
fetch('http://localhost:5000/api/v1/instagram/send-message', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'friend_username',
        message: 'Hey! Check out this cool AI assistant 🤖'
    })
}).then(r => r.json()).then(console.log);
```

---

#### **C. Get Your Messages**
```javascript
fetch('http://localhost:5000/api/v1/instagram/messages?limit=20', {
    headers: {
        'X-API-Key': 'demo_key_12345'
    }
}).then(r => r.json()).then(data => {
    console.log(`You have ${data.count} conversations`);
    data.messages.forEach(msg => {
        console.log(`From: ${msg.users.join(', ')}`);
        console.log(`Last message: ${msg.last_message.text}`);
        console.log(`Unread: ${msg.unread}`);
    });
});
```

---

#### **D. Start Real-Time Monitoring**
```javascript
// Monitor for new DMs every 30 seconds
fetch('http://localhost:5000/api/v1/instagram/start-monitoring', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        interval: 30
    })
}).then(r => r.json()).then(console.log);
```

---

#### **E. Like a Post** ⭐ NEW!
```javascript
fetch('http://localhost:5000/api/v1/instagram/like-post', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        media_id: '1234567890123456789'
    })
}).then(r => r.json()).then(console.log);
```

---

#### **F. Comment on Post** 💬 NEW!
```javascript
fetch('http://localhost:5000/api/v1/instagram/comment-post', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        media_id: '1234567890123456789',
        comment: 'Amazing photo! 🔥'
    })
}).then(r => r.json()).then(console.log);
```

---

#### **G. Follow a User** ➕ NEW!
```javascript
fetch('http://localhost:5000/api/v1/instagram/follow', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'cool_account'
    })
}).then(r => r.json()).then(console.log);
```

---

#### **H. Get Followers List** 👥 NEW!
```javascript
// Get your own followers
fetch('http://localhost:5000/api/v1/instagram/followers?limit=50', {
    headers: {
        'X-API-Key': 'demo_key_12345'
    }
}).then(r => r.json()).then(data => {
    console.log(`You have ${data.count} followers`);
    data.followers.forEach(follower => {
        console.log(`@${follower.username} - ${follower.full_name}`);
        if (follower.is_verified) console.log('✓ Verified');
    });
});

// Get someone else's followers
fetch('http://localhost:5000/api/v1/instagram/followers?username=celebrity&limit=100', {
    headers: {
        'X-API-Key': 'demo_key_12345'
    }
}).then(r => r.json()).then(console.log);
```

---

#### **I. Search Users** 🔍 NEW!
```javascript
fetch('http://localhost:5000/api/v1/instagram/search-users', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: 'tech influencer',
        limit: 20
    })
}).then(r => r.json()).then(data => {
    console.log(`Found ${data.count} users`);
    data.users.forEach(user => {
        console.log(`@${user.username} - ${user.follower_count} followers`);
        console.log(`Private: ${user.is_private}, Verified: ${user.is_verified}`);
    });
});
```

---

#### **J. Get User's Posts** 📱 NEW!
```javascript
fetch('http://localhost:5000/api/v1/instagram/user-posts', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'photographer_account',
        limit: 12
    })
}).then(r => r.json()).then(data => {
    console.log(`User has ${data.count} recent posts`);
    data.posts.forEach(post => {
        console.log(`Caption: ${post.caption.substring(0, 50)}...`);
        console.log(`Likes: ${post.like_count}, Comments: ${post.comment_count}`);
        console.log(`Posted: ${post.taken_at}`);
    });
});
```

---

#### **K. Post a Photo**
```javascript
fetch('http://localhost:5000/api/v1/instagram/post-photo', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        image_path: 'C:/Users/Krish/Pictures/sunset.jpg',
        caption: 'Beautiful sunset today! 🌅 #photography #nature'
    })
}).then(r => r.json()).then(console.log);
```

---

#### **L. Post a Story**
```javascript
fetch('http://localhost:5000/api/v1/instagram/post-story', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        image_path: 'C:/Users/Krish/Pictures/story.jpg'
    })
}).then(r => r.json()).then(console.log);
```

---

#### **M. Auto-Reply Setup** 🤖 NEW!
```javascript
// Set up auto-replies for common questions
fetch('http://localhost:5000/api/v1/instagram/auto-reply', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        keywords: {
            "price": "Thanks for asking! Please check our website for pricing.",
            "hours": "We're open Monday-Friday, 9 AM - 5 PM.",
            "location": "We're located in downtown. DM for exact address!",
            "hello": "Hi there! How can I help you today?"
        },
        enable: true
    })
}).then(r => r.json()).then(console.log);
```

---

## 💬 **3. NATURAL LANGUAGE EXAMPLES**

### Use JARVIS in Chat:

```
You: login to instagram as myusername
JARVIS: [Logs in and confirms]

You: send instagram dm to john saying "hey what's up"
JARVIS: ✅ Message sent to @john

You: check my instagram messages
JARVIS: You have 5 unread messages from...

You: start monitoring instagram dms
JARVIS: ✅ Monitoring started (checking every 30s)

You: follow user techguru on instagram
JARVIS: ✅ Now following @techguru

You: search instagram for "photographers in NYC"
JARVIS: Found 20 users: [list]

You: get posts from user travelblogger
JARVIS: [Shows recent 12 posts with stats]

You: like the latest post from celebrity
JARVIS: ✅ Post liked

You: post this image to instagram with caption "sunset vibes"
JARVIS: ✅ Photo posted successfully
```

---

## 🌐 **4. WEBSITE AUTOMATION EXAMPLES**

### Scrape a Website:
```python
from Backend.WebsiteAutomation import website_automation

# Start browser
website_automation.start_browser(headless=True)

# Scrape news site
result = website_automation.scrape_page('https://news.ycombinator.com')

if result['status'] == 'success':
    data = result['data']
    print(f"Title: {data['title']}")
    print("\nTop Headlines:")
    for heading in data['headings']['h1'][:10]:
        print(f"- {heading}")

website_automation.close_browser()
```

### Monitor Price Changes:
```python
# Start browser
website_automation.start_browser(headless=True)

# Navigate to product
website_automation.navigate('https://amazon.com/product/123')

# Monitor price for 5 minutes
result = website_automation.monitor_element(
    selector='.price',
    interval=30,  # Check every 30 seconds
    duration=300  # For 5 minutes
)

# Check changes
for change in result['changes']:
    print(f"Price changed: {change['old_value']} → {change['new_value']}")
```

### Fill a Form:
```python
website_automation.start_browser()
website_automation.navigate('https://example.com/contact')

# Fill form
website_automation.fill_form({
    '#name': 'John Doe',
    '#email': 'john@example.com',
    '#message': 'Hello from JARVIS!'
})

# Submit
website_automation.click_element('#submit-button')
website_automation.screenshot('form_submitted.png')
```

---

## 📱 **5. WHATSAPP AUTOMATION**

### Send Message:
```javascript
fetch('http://localhost:5000/api/v1/whatsapp/send', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        phone: '+1234567890',
        message: 'Hello from JARVIS!',
        instant: true
    })
}).then(r => r.json()).then(console.log);
```

### Send to Group:
```javascript
fetch('http://localhost:5000/api/v1/whatsapp/send-group', {
    method: 'POST',
    headers: {
        'X-API-Key': 'demo_key_12345',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        group: 'Family Group',
        message: 'Good morning everyone! ☀️'
    })
}).then(r => r.json()).then(console.log);
```

---

## 🎯 **6. COMBINED AUTOMATION EXAMPLES**

### Example 1: Instagram + Image Generation
```
You: generate image of a futuristic city
JARVIS: ✅ Generated image!
[Image displays]

You: post this to instagram with caption "AI generated art"
JARVIS: ✅ Posted to Instagram feed
```

### Example 2: Monitor Instagram + Auto-Reply
```javascript
// Set up monitoring with auto-reply
await fetch('http://localhost:5000/api/v1/instagram/auto-reply', {
    method: 'POST',
    headers: {'X-API-Key': 'demo_key_12345', 'Content-Type': 'application/json'},
    body: JSON.stringify({
        keywords: {
            "support": "Thanks for reaching out! Our support team will respond within 24 hours.",
            "pricing": "Check our website for current pricing: example.com/pricing"
        },
        enable: true
    })
});

await fetch('http://localhost:5000/api/v1/instagram/start-monitoring', {
    method: 'POST',
    headers: {'X-API-Key': 'demo_key_12345', 'Content-Type': 'application/json'},
    body: JSON.stringify({interval: 30})
});

// Now JARVIS will auto-reply to DMs containing those keywords!
```

### Example 3: Cross-Platform Posting
```
You: generate image of a sunset
JARVIS: ✅ Generated!
[Image displays]

You: post this to instagram and send to whatsapp group "Friends"
JARVIS: ✅ Posted to Instagram
✅ Sent to WhatsApp group "Friends"
```

---

## 🚀 **7. QUICK START CHECKLIST**

### For Instagram:
- [ ] Login to Instagram
- [ ] Test sending a DM
- [ ] Start monitoring
- [ ] Try liking a post
- [ ] Search for users
- [ ] Get your followers

### For Image Generation:
- [ ] Generate an image
- [ ] Check it displays automatically
- [ ] Generate another with different prompt

### For Website Automation:
- [ ] Scrape a news site
- [ ] Take a screenshot
- [ ] Fill a form

---

## 💡 **8. PRO TIPS**

### Instagram:
1. **Session Persistence**: Login once, session saves automatically
2. **Monitoring**: Start monitoring to get real-time DM notifications
3. **Auto-Reply**: Set up keywords for common questions
4. **Rate Limiting**: Don't spam - Instagram has limits
5. **Search Smart**: Use specific keywords for better results

### Image Generation:
1. **Be Specific**: "cyberpunk city at night" > "city"
2. **Auto-Display**: Images show automatically now!
3. **Multiple Images**: Can generate multiple at once

### Website Automation:
1. **Headless Mode**: Faster for scraping
2. **Screenshots**: Great for debugging
3. **Monitor Elements**: Perfect for price tracking

---

## 📊 **9. FEATURE COMPARISON**

| Feature | Before | Now |
|---------|--------|-----|
| Image Display | Manual open | Auto-display ✅ |
| Instagram DMs | Basic | Enhanced ✅ |
| Like Posts | ❌ | ✅ |
| Comments | ❌ | ✅ |
| Follow Users | ❌ | ✅ |
| Search Users | ❌ | ✅ |
| Get Posts | ❌ | ✅ |
| Auto-Reply | ❌ | ✅ |
| Followers List | ❌ | ✅ |

---

## 🎉 **10. WHAT'S NEW IN v13.0**

✅ **Image Generation**: Auto-display in chat  
✅ **Instagram**: 8 new features added  
✅ **Better UX**: No manual opening needed  
✅ **More Examples**: Complete usage guide  
✅ **Enhanced Automation**: Cross-platform support  

---

**Ready to automate everything! 🚀**

**Version:** 13.0  
**Date:** December 12, 2024  
**Status:** ✅ Production Ready
