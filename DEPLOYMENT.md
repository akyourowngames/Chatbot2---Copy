# 🚀 KAI OS - Deployment Guide

This guide covers how to deploy KAI OS for production use.

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have completed the following:

- [ ] ✅ **API Keys configured** - At least one AI API key (Gemini, Groq, or OpenAI)
- [ ] ✅ **Security keys set** - Strong `API_KEY`, `DEVELOPER_API_KEY`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY`
- [ ] ✅ **CORS origins configured** - Only allow your trusted domains
- [ ] ✅ **Firebase/Supabase configured** (if using cloud features)
- [ ] ✅ **All tests passing** - Run `python -m pytest tests/`
- [ ] ✅ **No hardcoded secrets** - Use environment variables only

---

## 🔧 Configuration

### Step 1: Create Production Environment File

```bash
# Copy the template
copy .env.production.template .env

# Edit and fill in your actual values
notepad .env
```

### Step 2: Generate Secure Keys

Run these Python commands to generate secure random keys:

```python
# Generate API keys (64 characters)
import secrets
print("API_KEY:", secrets.token_hex(32))
print("DEVELOPER_API_KEY:", secrets.token_hex(32))

# Generate JWT secret (128 characters)
print("JWT_SECRET_KEY:", secrets.token_hex(64))

# Generate Fernet encryption key
from cryptography.fernet import Fernet
print("ENCRYPTION_KEY:", Fernet.generate_key().decode())
```

### Step 3: Configure CORS Origins

In your `.env` file, set allowed origins:

```env
# For Electron desktop app only
CORS_ALLOWED_ORIGINS=file://

# For web deployment
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# For local testing (not recommended for production)
CORS_ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
```

---

## 🖥️ Deployment Options

### Option 1: Windows Desktop (Local)

For running as a desktop application:

```batch
# Production mode with Waitress WSGI server
start-production.bat

# Or manually:
pip install waitress
set FLASK_ENV=production
python -c "from waitress import serve; from api_server import app; serve(app, host='0.0.0.0', port=5000, threads=4)"
```

### Option 2: Docker Container

For containerized deployment:

```bash
# Build the image
docker build -t kai-os .

# Run with environment file
docker run -d \
  --name kai-os \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/Data:/app/Data \
  kai-os

# Or using Docker Compose
docker-compose up -d
```

### Option 3: Linux Server (Gunicorn)

For Linux VPS or cloud servers:

```bash
# Install dependencies
pip install -r Requirements.txt
pip install gunicorn

# Run with Gunicorn
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --threads 2 \
         --timeout 120 \
         api_server:app
```

### Option 4: Cloud Platforms

#### Railway/Render/Fly.io

Create a `Procfile`:
```
web: gunicorn api_server:app --bind 0.0.0.0:$PORT --workers 4
```

#### AWS EC2 / DigitalOcean

1. Set up an Ubuntu server
2. Install Python 3.11+
3. Clone your repository
4. Install dependencies: `pip install -r Requirements.txt`
5. Use systemd service for auto-restart (see below)

---

## 🔒 Security Best Practices

### 1. NEVER Expose Demo Keys
```env
# ❌ BAD - Never use in production
API_KEY=demo_key_12345

# ✅ GOOD - Use strong random keys
API_KEY=a1b2c3d4e5f6...64_random_characters...
```

### 2. Use HTTPS in Production

Configure a reverse proxy (Nginx/Caddy) with SSL:

```nginx
# Nginx example
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Rate Limiting

Rate limiting is automatically enabled in production:
- **Auth endpoints**: 10 requests/minute
- **Chat endpoints**: 30 requests/minute  
- **Image generation**: 5 requests/minute
- **Default**: 60 requests/minute

### 4. Security Headers

The following headers are automatically added:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (in production)

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:5000/health
# Returns: {"status":"ok"}

curl http://localhost:5000/api/v1/health
# Returns: {"status":"healthy","version":"13.0",...}
```

### Logs

```bash
# View logs
tail -f logs/kai_os.log

# Docker logs
docker logs -f kai-os
```

### Systemd Service (Linux)

Create `/etc/systemd/system/kai-os.service`:

```ini
[Unit]
Description=KAI OS API Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/kai-os
EnvironmentFile=/opt/kai-os/.env
ExecStart=/usr/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 api_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kai-os
sudo systemctl start kai-os
```

---

## 🔥 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `CORS error` | Check `CORS_ALLOWED_ORIGINS` in `.env` |
| `401 Unauthorized` | Verify `API_KEY` matches between client and server |
| `Rate limit exceeded` | Wait 60 seconds or adjust rate limits |
| `Firebase error` | Check `FIREBASE_CREDENTIALS_PATH` exists |
| `Module not found` | Run `pip install -r Requirements.txt` |

### Validate Configuration

```python
# Run to validate your config
python -c "from Config.production import validate_config; validate_config()"
```

---

## 📦 Electron Desktop Build

To build the Electron desktop app:

```bash
# Install Node dependencies
npm install

# Build for Windows
npm run build:win

# Build for macOS
npm run build:mac

# Build for Linux
npm run build:linux
```

The built app will be in the `dist/` folder.

---

## 🎉 You're Ready!

Once deployed, your KAI OS instance will be available at:
- **API**: `http://your-server:5000/api/v1`
- **Dashboard**: `http://your-server:5000/Frontend/dashboard.html`
- **Chat**: `http://your-server:5000/Frontend/chat.html`

For support, check the `docs/` folder or open an issue on GitHub.
