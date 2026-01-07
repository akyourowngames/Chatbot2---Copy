"""
Kai Local Agent - Command Validation Schemas
=============================================
Defines allowed commands and validates incoming task payloads.
Commands not in the whitelist are rejected.
"""

from typing import Dict, Any, Tuple, List


# ==================== COMMAND WHITELIST ====================
# Only these commands are allowed. Each command defines:
# - required_params: List of required parameter names
# - optional_params: List of optional parameter names
# - description: Human-readable description

COMMAND_SCHEMA = {
    "open_app": {
        "required_params": ["app"],
        "optional_params": [],
        "allowed_values": {
            "app": [
                # Browsers
                "browser", "chrome", "firefox", "edge", "brave", "opera", "vivaldi", "safari",
                # Development
                "vscode", "code", "terminal", "cmd", "powershell", "postman", "docker",
                # Productivity
                "notepad", "word", "excel", "outlook", "powerpoint", "onenote", "notion", "obsidian",
                # Communication
                "teams", "slack", "discord", "zoom", "skype", "telegram", "whatsapp", "signal",
                # Media
                "spotify", "vlc", "itunes", "winamp", "obs", "audacity",
                # System
                "explorer", "calculator", "paint", "snipping", "settings", "task_manager",
                # Games
                "steam", "epicgames", "origin", "ubisoft", "gog"
            ]
        },
        "description": "Open a predefined application"
    },
    "close_app": {
        "required_params": ["app"],
        "optional_params": [],
        "allowed_values": {
            "app": [
                # Browsers
                "browser", "chrome", "firefox", "edge", "brave", "opera", "vivaldi",
                # Development
                "vscode", "code", "terminal", "cmd", "powershell", "postman", "docker",
                # Productivity
                "notepad", "word", "excel", "outlook", "powerpoint", "onenote", "notion", "obsidian",
                # Communication
                "teams", "slack", "discord", "zoom", "skype", "telegram", "whatsapp", "signal",
                # Media
                "spotify", "vlc", "itunes", "winamp", "obs", "audacity",
                # System (excluding critical)
                "calculator", "paint", "snipping",
                # Games
                "steam", "epicgames", "origin", "ubisoft", "gog"
            ]
        },
        "description": "Close a running application"
    },
    "system_control": {
        "required_params": ["action"],
        "optional_params": ["level"],
        "allowed_values": {
            "action": [
                "set_volume", "volume_up", "volume_down",
                "mute", "unmute", "toggle_mute",
                "set_brightness", "brightness_up", "brightness_down",
                "lock_screen"
            ]
        },
        "description": "Safe system controls: volume, brightness, mute, lock"
    },
    "system_status": {
        "required_params": [],
        "optional_params": [],
        "allowed_values": {},
        "description": "Report system status: CPU, RAM, uptime, OS info (read-only)"
    },
    "write_notepad": {
        "required_params": ["text"],
        "optional_params": [],
        "allowed_values": {},
        "description": "Write text into Windows Notepad (controlled, audited)"
    },
    "file_manager": {
        "required_params": ["action"],
        "optional_params": ["name", "content", "folder", "parent", "old_name", "new_name", "destination", "source_folder"],
        "allowed_values": {
            "action": [
                "create_folder", "save_file", "list_files",
                "rename_file", "move_file", "delete_file", "open_folder"
            ]
        },
        "description": "Sandboxed file operations within Kai directories only"
    },
    # "create_file": {
    #     "required_params": ["path", "content"],
    #     "optional_params": ["overwrite"],
    #     "description": "Create a file in allowed directories"
    # },
    # "run_script": {
    #     "required_params": ["script_id"],
    #     "optional_params": [],
    #     "description": "Run a predefined whitelisted script"
    # },
    # "screenshot": {
    #     "required_params": [],
    #     "optional_params": ["region"],
    #     "description": "Take a screenshot"
    # },
}


def validate_command(command: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a command against the whitelist.
    
    Args:
        command: The command name to validate
        params: The parameters for the command
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if command is allowed and valid
        - error_message: Empty string if valid, error description if not
    """
    # Check if command exists in whitelist
    if command not in COMMAND_SCHEMA:
        return False, f"Command '{command}' is not allowed. Allowed commands: {list(COMMAND_SCHEMA.keys())}"
    
    schema = COMMAND_SCHEMA[command]
    
    # Check required parameters
    for required_param in schema["required_params"]:
        if required_param not in params:
            return False, f"Missing required parameter '{required_param}' for command '{command}'"
    
    # Check for unknown parameters (prevent injection of extra params)
    all_allowed_params = schema["required_params"] + schema.get("optional_params", [])
    for param_name in params.keys():
        if param_name not in all_allowed_params:
            return False, f"Unknown parameter '{param_name}' for command '{command}'"
    
    # Validate parameter values if restrictions exist
    allowed_values = schema.get("allowed_values", {})
    for param_name, value in params.items():
        if param_name in allowed_values:
            if value not in allowed_values[param_name]:
                return False, f"Invalid value '{value}' for parameter '{param_name}'. Allowed: {allowed_values[param_name]}"
    
    return True, ""


def get_allowed_commands() -> List[str]:
    """Get list of all allowed command names."""
    return list(COMMAND_SCHEMA.keys())


def get_command_info(command: str) -> Dict[str, Any]:
    """Get schema information for a specific command."""
    return COMMAND_SCHEMA.get(command, {})
