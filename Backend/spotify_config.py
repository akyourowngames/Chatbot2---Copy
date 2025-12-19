# Spotify Configuration for Backend
"""
Add these to your backend configuration file (config.py or .env):
"""

# Spotify API Credentials
SPOTIFY_CLIENT_ID = "741a5c59b58244e6bb801221101f0678"
SPOTIFY_CLIENT_SECRET = "091eace6b53b4a509dc2249a9d08ba33"

# Usage in SpotifyPlayer.py:
"""
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Initialize Spotify client
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
"""
