"""
Kai Local Agent - Configuration Management
==========================================
Handles loading, saving, and validating agent configuration.
Securely stores device credentials.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


# Default configuration
DEFAULT_CONFIG = {
    "api_url": "https://kai-api-nxxv.onrender.com",  # Production Render URL
    "poll_interval": 5,  # seconds
    "heartbeat_interval": 30,  # seconds
    "device_name": None,  # Set during registration
    "device_id": None,  # Set after registration
    "auth_token": None,  # Set after registration
    "registered_at": None,
    "log_level": "INFO",
}


def get_config_path() -> Path:
    """Get the path to the config file."""
    # Store in user's home directory under .kai-agent
    config_dir = Path.home() / ".kai-agent"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from file, or create default if not exists."""
    config_path = get_config_path()
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = {**DEFAULT_CONFIG, **saved_config}
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"[CONFIG] Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set restrictive permissions on Unix-like systems (chmod 600)
        try:
            os.chmod(config_path, 0o600)
        except (OSError, AttributeError):
            pass  # Windows doesn't support chmod the same way
        
        return True
    except IOError as e:
        print(f"[CONFIG] Error saving config: {e}")
        return False


def is_registered() -> bool:
    """Check if the device is registered with valid credentials."""
    config = load_config()
    return bool(config.get("device_id") and config.get("auth_token"))


def clear_registration() -> bool:
    """Clear registration data (for re-registering or logout)."""
    config = load_config()
    config["device_id"] = None
    config["auth_token"] = None
    config["registered_at"] = None
    return save_config(config)


def update_api_url(url: str) -> bool:
    """Update the API URL (for development/testing)."""
    config = load_config()
    config["api_url"] = url.rstrip("/")
    return save_config(config)


def get_credentials() -> Optional[tuple]:
    """Get device credentials if registered. Returns (device_id, auth_token) or None."""
    config = load_config()
    device_id = config.get("device_id")
    auth_token = config.get("auth_token")
    
    if device_id and auth_token:
        return (device_id, auth_token)
    return None
