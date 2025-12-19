# Spotify Configuration for KAI Chatbot

## Credentials
- **Client ID**: 741a5c59b58244e6bb801221101f0678
- **Client Secret**: 091eace6b53b4a509dc2249a9d08ba33

## Backend Integration

Add these to your backend `config.py` or `.env`:

```python
SPOTIFY_CLIENT_ID = "741a5c59b58244e6bb801221101f0678"
SPOTIFY_CLIENT_SECRET = "091eace6b53b4a509dc2249a9d08ba33"
```

## Features
- All "play" commands now route to Spotify
- Simple iframe embed player
- No YouTube music (removed)
- Streams still use YouTube for radio/news/live
