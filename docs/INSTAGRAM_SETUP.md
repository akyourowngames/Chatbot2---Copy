# 🔐 Instagram Credentials Setup

## How to Enable Natural Language Instagram Commands

Currently, Instagram works via **direct API calls only**. To enable natural language commands like "login to instagram as krish", you need to:

### Option 1: Store Credentials (Not Recommended for Security)

Create a file `Data/instagram_credentials.json`:
```json
{
    "username": "your_instagram_username",
    "password": "your_instagram_password"
}
```

### Option 2: Use Direct API Calls (Recommended)

**Open browser console (F12) and run:**

```javascript
// Store credentials in browser session
const INSTAGRAM_CREDS = {
    username: 'your_username',
    password: 'your_password'
};

// Helper function to login
async function instagramLogin() {
    const response = await fetch('http://localhost:5000/api/v1/instagram/login', {
        method: 'POST',
        headers: {
            'X-API-Key': 'demo_key_12345',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(INSTAGRAM_CREDS)
    });
    const data = await response.json();
    console.log(data);
    return data;
}

// Login
await instagramLogin();

// Now you can use other commands
async function searchUsers(query) {
    const response = await fetch('http://localhost:5000/api/v1/instagram/search-users', {
        method: 'POST',
        headers: {
            'X-API-Key': 'demo_key_12345',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({query, limit: 20})
    });
    return await response.json();
}

// Search
const users = await searchUsers('photographer');
console.log(users);
```

### Option 3: Create a Simple UI

Add buttons to chat.html for Instagram actions. This is the cleanest approach.

---

## Why Natural Language Doesn't Work Yet

The current system needs:
1. **Credential Storage** - Where to store Instagram username/password
2. **SmartTrigger Integration** - Connect patterns to API calls  
3. **Chat Intelligence** - Parse commands and call appropriate endpoints

**For now, use direct API calls in browser console!**

---

## Quick Commands (Browser Console)

```javascript
// After login, you can use these:

// Search users
fetch('http://localhost:5000/api/v1/instagram/search-users', {
    method: 'POST',
    headers: {'X-API-Key': 'demo_key_12345', 'Content-Type': 'application/json'},
    body: JSON.stringify({query: 'tech', limit: 10})
}).then(r => r.json()).then(console.log);

// Follow user
fetch('http://localhost:5000/api/v1/instagram/follow', {
    method: 'POST',
    headers: {'X-API-Key': 'demo_key_12345', 'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'some_user'})
}).then(r => r.json()).then(console.log);

// Get followers
fetch('http://localhost:5000/api/v1/instagram/followers?limit=50', {
    headers: {'X-API-Key': 'demo_key_12345'}
}).then(r => r.json()).then(console.log);
```

---

**The backend is ready! Just use API calls for now.** 🚀
