# 🤖 KAI - Advanced AI Assistant

An ultra-modern, voice-activated AI assistant integrated with your entire digital life. Now featuring a **SaaS Productivity Suite** to manage your work directly from the chat.

## 🌟 New Features: SaaS Productivity Suite
Unlocked "Beast Mode" integrations with premium UI cards:

- **🎨 Figma**: Browse recent design files and mockups.
- **📝 Notion**: Search your workspace pages and databases.
- **💬 Slack**: View channels and send messages to your team.
- **📋 Trello**: visual board summaries and card tracking.
- **📅 Google Calendar**: Timeline view of your upcoming schedule.

## 🛠️ Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/akyourowngames/Chatbot2.git
   cd Chatbot2
   ```

2. **Install Dependencies**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd Frontend
   npm install
   ```

3. **Configure Environment**
   Create a `.env` file in the root directory and add your keys:
   ```env
   # Core
   OPENAI_API_KEY=sk-...
   
   # SaaS Suite (Optional - System runs in Mock Mode without them)
   FIGMA_ACCESS_TOKEN=figd_...
   NOTION_API_KEY=ntn_...
   SLACK_BOT_TOKEN=xoxb-...
   TRELLO_API_KEY=...
   TRELLO_TOKEN=...
   GOOGLE_CALENDAR_CREDENTIALS=path/to/creds.json
   ```

4. **Run the System**
   ```bash
   # Terminal 1: Backend
   python api_server.py
   
   # Terminal 2: Frontend
   cd Frontend
   npm run dev
   ```

## 🧪 Commands to Test

Try these prompts to see the new capabilities in action:

### 💼 Productivity
- **Figma**: *"Show my recent Figma files"* or *"Figma projects"*
- **Notion**: *"Search Notion for 'Roadmap'"* or *"Find notes about meeting"*
- **Slack**: *"List Slack channels"* or *"Send message 'Hello Team' to general"*
- **Trello**: *"Show my Trello boards"*
- **Calendar**: *"What are my upcoming events?"* or *"Check my schedule"*

### 🌐 Utilities
- **Weather**: *"Weather in Tokyo"* (Displays live atmospheric card)
- **News**: *"Latest AI news"* or *"Hacker News top stories"*
- **Finance**: *"Bitcoin price"* or *"AAPL stock"*
- **System**: *"System stats"* (Sci-fi CPU/RAM telemetry)
- **Space**: *"NASA APOD"* (Astronomy Picture of the Day)
- **Code**: *"Show GitHub repos for torvalds"*

## 🚀 Future Roadmap
- [ ] AI Thinking Mode (Chain-of-thought visualization)
- [ ] Enhanced Voice Interaction (Real-time interruption)
- [ ] Deep Research Agent
