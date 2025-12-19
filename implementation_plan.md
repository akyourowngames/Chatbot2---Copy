# Implementation Plan - Instagram Auto-Repy & Automation

## Phase 1: Backend Core (`Backend/InstagramAuto.py`)
- [ ] Install `instagrapi` library (`pip install instagrapi`)
- [ ] Create `InstagramAutomation` class
  - [ ] Login/Session handling (save session to file to avoid re-login)
  - [ ] DM Polling loop (background thread)
  - [ ] `send_message` function
  - [ ] `get_messages` function

## Phase 2: Logic & Integration
- [ ] Create `Settings` storage (JSON file) for:
  - [ ] Auto-Reply Toggle (True/False)
  - [ ] Keywords Map (e.g., {"price": "It costs $50", "hello": "Hi there!"})
  - [ ] Smart Reply Toggle (True/False)
- [ ] Implement `process_incoming_messages` logic:
  - [ ] Check unread messages
  - [ ] Match text vs Keywords
  - [ ] If no match & Smart Reply ON -> Call LLM
  - [ ] Send response & mark read

## Phase 3: API Endpoints (`api_server.py`)
- [ ] `POST /api/instagram/login`
- [ ] `POST /api/instagram/settings` (Update keywords/toggles)
- [ ] `GET /api/instagram/status`

## Phase 4: Frontend UI (`chat.html`)
- [ ] Add "Instagram" button to Quick Actions (or a dedicated Settings Icon)
- [ ] Create **Instagram Automation Modal**:
  - [ ] Login Form (if not logged in)
  - [ ] Toggle Switch: "Auto-Reply"
  - [ ] Keyword Editor (Add/Remove pairs)
  - [ ] "Smart Reply" Checkbox
  - [ ] Log View (Recent auto-replies)
