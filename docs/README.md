# JARVIS AI Assistant 🤖

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

> Premium AI assistant with advanced automation, WhatsApp integration, and cloud database

## ✨ Features

- 🧠 **Advanced AI** - Powered by Groq LLM
- 📱 **WhatsApp Automation** - Send messages, make calls
- ☁️ **Cloud Database** - Supabase integration
- 🎤 **Voice Control** - Speech recognition & synthesis
- 🖼️ **Image Generation** - AI-powered image creation
- 📁 **File Analysis** - Analyze documents, images, code
- 🌐 **Web Automation** - Chrome, YouTube control
- ⚙️ **System Control** - PC automation, gestures
- 📊 **Analytics Dashboard** - Usage tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js (for Electron app)
- WhatsApp Web account
- Supabase account (free tier)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "Chatbot2 - Copy"
```

2. **Install Python dependencies**
```bash
pip install -r Requirements.txt
```

3. **Install WhatsApp & Supabase**
```powershell
.\scripts\install_whatsapp_supabase.ps1
```

4. **Set up Supabase database**
- Go to https://supabase.com
- Run SQL from `config/supabase_schema.sql`

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

6. **Start the server**
```bash
python api_server.py
```

7. **Open the UI**
- Web: Open `chat.html` in browser
- Desktop: `npm start`

## 📚 Documentation

- **[Setup Guide](docs/setup/DEPLOYMENT_GUIDE.md)** - Detailed installation
- **[API Documentation](docs/api/API_DOCUMENTATION.md)** - API reference
- **[Features Guide](docs/features/)** - Feature documentation
- **[Upgrade History](docs/upgrades/)** - Version history

## 🎯 Usage Examples

### Chat Interface
```
User: "Send WhatsApp to John: Meeting at 3pm"
JARVIS: "✅ Message sent to John"

User: "Generate image of sunset over mountains"
JARVIS: "🖼️ Generating image..."

User: "What's on my screen?"
JARVIS: "📸 Analyzing screen..."
```

### API
```python
import requests

# Send WhatsApp message
response = requests.post('http://localhost:5000/api/v1/whatsapp/send', 
    headers={'X-API-Key': 'demo_key_12345'},
    json={'phone': '+1234567890', 'message': 'Hello!'})
```

## 🏗️ Project Structure

```
├── Backend/          # Python modules
├── Frontend/         # Web UI
├── Data/             # Runtime data
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── config/           # Configuration
├── api_server.py     # Main API server
└── main.py           # Entry point
```

## 🔧 Configuration

### Environment Variables (.env)
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
```

### API Key
Default: `demo_key_12345` (change in production)

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🆘 Support

- **Issues**: [GitHub Issues](issues)
- **Documentation**: [docs/](docs/)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🎉 Acknowledgments

- Groq for LLM API
- Supabase for cloud database
- pywhatkit for WhatsApp automation

---

**Made with ❤️ by the JARVIS Team**
