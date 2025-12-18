# Firebase Setup Guide for AI Assistant

## 🔥 Complete Firebase Configuration Guide

This guide will walk you through setting up Firebase for your AI assistant's backend persistence system.

---

## Step 1: Create Firebase Project

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com/
   - Sign in with your Google account

2. **Create New Project**
   - Click "Add project"
   - Enter project name (e.g., "ai-assistant-backend")
   - Click "Continue"
   - Disable Google Analytics (optional, you can enable later)
   - Click "Create project"
   - Wait for project creation to complete

---

## Step 2: Enable Firestore Database

1. **Navigate to Firestore**
   - In Firebase Console, click "Firestore Database" in left sidebar
   - Click "Create database"

2. **Choose Security Rules**
   - Select "Start in **production mode**" (we'll add custom rules)
   - Click "Next"

3. **Select Location**
   - Choose a location close to your users (e.g., `us-central1`)
   - Click "Enable"
   - Wait for database creation

4. **Set Security Rules**
   - Go to "Rules" tab
   - Replace with these rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection - only server can write
    match /users/{userId} {
      allow read, write: if false; // Server-side only
    }
    
    // User-scoped collections - server-side only
    match /{collection}/{userId}/{collection}/{document=**} {
      allow read, write: if false; // Server-side only with Firebase Admin SDK
    }
    
    // Offline queue - server-side only
    match /offline_queue/{userId} {
      allow read, write: if false; // Server-side only
    }
  }
}
```

   - Click "Publish"

---

## Step 3: Enable Firebase Authentication

1. **Navigate to Authentication**
   - Click "Authentication" in left sidebar
   - Click "Get started"

2. **Enable Email/Password**
   - Go to "Sign-in method" tab
   - Click "Email/Password"
   - Enable "Email/Password"
   - Click "Save"

3. **Enable Google Sign-In (Optional)**
   - Click "Google"
   - Enable "Google"
   - Enter project support email
   - Click "Save"

---

## Step 4: Enable Firebase Storage

1. **Navigate to Storage**
   - Click "Storage" in left sidebar
   - Click "Get started"

2. **Set Security Rules**
   - Choose "Start in **production mode**"
   - Click "Next"

3. **Select Location**
   - Use same location as Firestore
   - Click "Done"

---

## Step 5: Get Firebase Credentials

### 5.1: Download Service Account Key

1. **Go to Project Settings**
   - Click gear icon (⚙️) next to "Project Overview"
   - Click "Project settings"

2. **Navigate to Service Accounts**
   - Click "Service accounts" tab
   - Click "Generate new private key"
   - Click "Generate key"
   - **Save the JSON file** to your project directory

3. **Rename and Move File**
   - Rename file to `firebase-credentials.json`
   - Move to your project root: `Chatbot2 - Copy/firebase-credentials.json`
   - **IMPORTANT:** Add to `.gitignore` to keep it private!

### 5.2: Get Project Configuration

1. **Get Project ID**
   - In Project Settings → General tab
   - Copy "Project ID" (e.g., `ai-assistant-12345`)

2. **Get Storage Bucket**
   - In Project Settings → General tab
   - Scroll to "Your apps" section
   - Copy "Storage bucket" (e.g., `ai-assistant-12345.appspot.com`)

---

## Step 6: Configure Environment Variables

1. **Copy .env.example to .env**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** and add your Firebase credentials:

```bash
# Firebase Project Configuration
FIREBASE_PROJECT_ID=your-actual-project-id
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# JWT Secrets - Generate random values
JWT_SECRET_KEY=generate_random_64_char_hex_string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption Key - Generate using Fernet
ENCRYPTION_KEY=generate_fernet_key_here
```

3. **Generate Secrets** (run in Python):

```python
# Generate JWT Secret
import secrets
print("JWT_SECRET_KEY:", secrets.token_hex(64))

# Generate Encryption Key
from cryptography.fernet import Fernet
print("ENCRYPTION_KEY:", Fernet.generate_key().decode())
```

---

## Step 7: Update FirebaseStorage.py

Check if `Backend/FirebaseStorage.py` loads credentials correctly:

```python
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase
cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
cred = credentials.Certificate(cred_path)

firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

db = firestore.client()
```

---

## Step 8: Test Firebase Connection

1. **Create test script** (`test_firebase.py`):

```python
from Backend.FirebaseStorage import get_firebase_storage
from Backend.FirebaseAuth import FirebaseAuth
from Backend.FirebaseDAL import FirebaseDAL

# Test Firebase connection
print("Testing Firebase connection...")

storage = get_firebase_storage()
if storage and storage.db:
    print("✅ Firebase connected successfully!")
    
    # Test authentication
    auth = FirebaseAuth(storage.db)
    print("✅ FirebaseAuth initialized")
    
    # Test DAL
    dal = FirebaseDAL(storage.db)
    print("✅ FirebaseDAL initialized")
    
    print("\n🎉 All Firebase components working!")
else:
    print("❌ Firebase connection failed. Check credentials.")
```

2. **Run test**:
   ```bash
   python test_firebase.py
   ```

---

## Step 9: Start Using Firebase

1. **Start API Server**
   ```bash
   python api_server.py
   ```

2. **Test Authentication Endpoint**
   ```bash
   # Signup
   curl -X POST http://localhost:5000/api/v1/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!"}'
   
   # Login
   curl -X POST http://localhost:5000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!"}'
   ```

3. **Check Firebase Console**
   - Go to Authentication → Users
   - You should see your test user!

---

## 🔒 Security Checklist

- [ ] Firebase credentials file (`firebase-credentials.json`) is in `.gitignore`
- [ ] `.env` file is in `.gitignore`
- [ ] JWT_SECRET_KEY is randomly generated (64+ characters)
- [ ] ENCRYPTION_KEY is properly generated with Fernet
- [ ] Firestore security rules are set to server-side only
- [ ] Firebase project has billing enabled (for production use)

---

## 📁 File Structure

```
Chatbot2 - Copy/
├── .env                          # Your actual credentials (NEVER commit!)
├── .env.example                  # Template (safe to commit)
├── firebase-credentials.json     # Firebase service account (NEVER commit!)
├── .gitignore                    # Should include .env and firebase-credentials.json
├── Backend/
│   ├── FirebaseStorage.py        # Firebase initialization
│   ├── FirebaseAuth.py            # Authentication system
│   ├── FirebaseDAL.py             # Data access layer
│   ├── SecurityManager.py         # JWT & encryption
│   └── RealtimeSync.py            # WebSocket server
└── static/
    └── js/
        └── auth-client.js         # Frontend auth client
```

---

## 🚨 Troubleshooting

### Error: "Could not load credentials"
- Check `FIREBASE_CREDENTIALS_PATH` in `.env`
- Verify `firebase-credentials.json` exists
- Ensure file path is correct (relative to project root)

### Error: "Permission denied"
- Check Firestore security rules
- Ensure using Firebase Admin SDK (server-side)
- Verify service account has proper permissions

### Error: "Invalid JWT"
- Check `JWT_SECRET_KEY` is set in `.env`
- Ensure secret key is the same across server restarts
- Verify token hasn't expired

### Error: "Firebase app already initialized"
- Only initialize Firebase once
- Check for duplicate initialization in code

---

## 🎯 Quick Start Commands

```bash
# 1. Generate secrets
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(64))"
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env with your Firebase credentials
# (Add the values from Firebase Console)

# 4. Test connection
python test_firebase.py

# 5. Start server
python api_server.py
```

---

## ✅ Verification

After setup, verify everything works:

1. **Firebase Console** shows:
   - ✅ Firestore database created
   - ✅ Authentication enabled
   - ✅ Storage bucket created

2. **API Server** shows:
   - ✅ `[OK] Firebase Auth & DAL loaded`
   - ✅ Server starts without errors

3. **Test Signup/Login** works:
   - ✅ Can create new user
   - ✅ Can login and get JWT token
   - ✅ User appears in Firebase Console

---

## 📚 Additional Resources

- **Firebase Documentation:** https://firebase.google.com/docs
- **Firestore Guide:** https://firebase.google.com/docs/firestore
- **Firebase Admin SDK:** https://firebase.google.com/docs/admin/setup
- **Security Rules:** https://firebase.google.com/docs/firestore/security/get-started

---

## 🎉 You're All Set!

Once you complete these steps, your AI assistant will have:
- ✅ Persistent cloud storage
- ✅ User authentication
- ✅ Real-time sync
- ✅ Secure data encryption
- ✅ Scalable backend infrastructure

**Need help?** Check the troubleshooting section or review the walkthrough.md for implementation details.
