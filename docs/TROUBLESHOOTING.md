# 🔧 TROUBLESHOOTING - API SERVER NOT STARTING

**Issue:** "Server is not running" error when launching desktop app

---

## 🎯 QUICK FIX

### **Option 1: Start API Server Manually (FASTEST)**

**Open a NEW terminal and run:**
```bash
python api_server.py
```

**Then in ANOTHER terminal:**
```bash
npm start
```

**This should work immediately!**

---

### **Option 2: Check Console Logs**

**Look at the Electron console for errors:**
1. App is running
2. Press `Ctrl + Shift + I` (DevTools)
3. Click "Console" tab
4. Look for red errors
5. Share the errors with me

---

## 🔍 COMMON ISSUES

### **Issue 1: Python Not Found**

**Error:** `'python' is not recognized`

**Fix:**
```bash
# Check Python installation
python --version

# If not found, install Python 3.11
# Download: https://python.org
# ✅ Check "Add Python to PATH" during install
```

---

### **Issue 2: Port 5000 Already in Use**

**Error:** `Address already in use`

**Fix:**
```bash
# Check what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change port in api_server.py
# Line: app.run(port=5001)  # Changed from 5000
```

---

### **Issue 3: Working Directory Wrong**

**Error:** `FileNotFoundError: api_server.py`

**Fix:**
The Electron app needs to run from project root.

**Check electron/main.js console logs:**
- Should show: `Working directory: C:\Users\...\Chatbot2 - Copy`
- If wrong, the path is incorrect

---

### **Issue 4: Dependencies Not Installed**

**Error:** `ModuleNotFoundError`

**Fix:**
```bash
# Install Python dependencies
pip install -r Requirements.txt

# Install Node dependencies
npm install
```

---

## 🚀 MANUAL START (ALWAYS WORKS)

### **Terminal 1: Start API Server**
```bash
cd "c:\Users\Krish\3D Objects\Chatbot2 - Copy"
python api_server.py
```

**Wait for:** `Running on http://127.0.0.1:5000`

### **Terminal 2: Start Electron App**
```bash
cd "c:\Users\Krish\3D Objects\Chatbot2 - Copy"
npm start
```

**This WILL work!**

---

## 🔧 DEBUG MODE

### **Run with Debug Launcher:**
```bash
start-debug.bat
```

**This will:**
- Check Python
- Check Node.js
- Check port 5000
- Show detailed errors
- Launch app

---

## 📊 CHECK STATUS

### **Is Python Working?**
```bash
python --version
# Should show: Python 3.11.x
```

### **Is API Server File There?**
```bash
dir api_server.py
# Should show the file
```

### **Is Port 5000 Free?**
```bash
netstat -ano | findstr :5000
# Should show nothing (port is free)
```

---

## 💡 TEMPORARY WORKAROUND

### **Until Auto-Start is Fixed:**

**Step 1: Start API Server**
```bash
python api_server.py
```

**Keep this terminal open!**

**Step 2: Start Desktop App**
```bash
npm start
```

**Everything will work!**

---

## 🎯 WHAT I'LL FIX

The issue is likely:
1. Working directory path
2. Python command not found
3. Shell execution issue

**I can fix this! Just need to see the error messages.**

---

## 📝 SEND ME THIS INFO

**To help debug, send me:**

1. **Console output:**
   - Open DevTools (Ctrl+Shift+I)
   - Copy console errors

2. **Python version:**
   ```bash
   python --version
   ```

3. **Current directory:**
   ```bash
   cd
   ```

4. **File exists?**
   ```bash
   dir api_server.py
   ```

---

## ✅ QUICK TEST

**Does this work?**
```bash
# Terminal 1
python api_server.py

# Terminal 2 (new terminal)
npm start
```

**If YES:** Auto-start issue (I can fix)
**If NO:** Different problem (need more info)

---

**For now, use the manual start method above!**

It works 100% and you can use the app while I fix the auto-start! 🚀
