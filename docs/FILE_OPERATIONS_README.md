# 🗂️ Advanced File Operations Module

## Overview

The Advanced File Operations module provides comprehensive file management capabilities for KAI automation. It supports both keyboard shortcuts (Ctrl+C, Ctrl+V, etc.) and direct file system operations with natural language command parsing.

---

## Features

| Category | Features |
|----------|----------|
| **Keyboard** | Select All, Copy, Cut, Paste, Delete, Undo, Redo, Rename, New Folder |
| **File System** | Copy, Move, Delete, Rename, Create, Read, Write, Search |
| **Batch Ops** | Wildcards (*.txt), Pattern matching, Recursive operations |
| **Smart** | Natural language parsing, Folder aliases, Operation history |

---

## Quick Start

### Python Usage

```python
from Backend.BasicFileOps import file_ops, execute

# Keyboard shortcuts
file_ops.select_all()
file_ops.copy()
file_ops.paste()

# File operations
file_ops.copy_file("report.txt", "~/Documents")
file_ops.move_file("*.jpg", "~/Pictures")
file_ops.delete_file("old_folder")
file_ops.create_folder("~/Projects/NewApp")

# Natural language
execute("copy report.txt to Documents")
execute("move all images to Pictures")
execute("search for python in Documents")
```

### Voice Commands (via KAI)

```
"Copy this file to Documents"
"Move all jpg files to Pictures"
"Delete the old folder permanently"
"Create folder called Projects"
"Search for python files"
"Select all and copy"
"Open Downloads folder"
```

---

## API Endpoints

### POST `/api/v1/file/execute`
Execute a file operation command.

**Request:**
```json
{
  "command": "copy report.txt to Documents"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Copied to /Users/john/Documents/report.txt"
}
```

### POST `/api/v1/file/copy`
Copy file(s) to destination.

```json
{
  "source": "report.txt",
  "destination": "~/Documents"
}
```

### POST `/api/v1/file/move`
Move file(s) to destination.

```json
{
  "source": "*.jpg",
  "destination": "~/Pictures"
}
```

### POST `/api/v1/file/delete`
Delete file(s) or folder.

```json
{
  "path": "old_folder",
  "permanent": false
}
```

### POST `/api/v1/file/create`
Create file or folder.

```json
{
  "path": "~/Projects/NewApp",
  "type": "folder"
}
```
or
```json
{
  "path": "~/Documents/notes.txt",
  "type": "file",
  "content": "Hello World"
}
```

### GET `/api/v1/file/list`
List files in directory.

```
GET /api/v1/file/list?path=~/Documents&pattern=*.txt
```

### GET `/api/v1/file/search`
Search for files.

```
GET /api/v1/file/search?pattern=report&path=~/Documents&content=true
```

### GET `/api/v1/file/info`
Get file information.

```
GET /api/v1/file/info?path=~/Documents/report.txt
```

### POST `/api/v1/file/open`
Open folder in file explorer.

```json
{
  "path": "~/Downloads"
}
```

### Keyboard Shortcuts

```
POST /api/v1/file/shortcut
{
  "action": "select_all" | "copy" | "cut" | "paste" | "delete" | "undo" | "redo"
}
```

---

## Folder Aliases

Shorthand names for common folders:

| Alias | Path |
|-------|------|
| `desktop` | ~/Desktop |
| `documents` | ~/Documents |
| `downloads` | ~/Downloads |
| `pictures` | ~/Pictures |
| `videos` | ~/Videos |
| `music` | ~/Music |
| `home` | ~ |
| `temp` | %TEMP% |
| `current` / `here` | Current directory |

**Example:**
```python
file_ops.copy_file("report.txt", "documents")
# Copies to ~/Documents/report.txt
```

---

## Batch Operations

### Wildcards
```python
# Copy all .txt files
file_ops.copy_file("*.txt", "~/Backup")

# Delete all .tmp files
file_ops.delete_file("*.tmp")

# Move all images
file_ops.move_file("*.jpg *.png", "~/Pictures")
```

### Recursive
```python
# Search recursively
file_ops.search_files("config", "~/Projects", search_content=True)

# List all Python files
file_ops.list_files("~/Code", "*.py", recursive=True)
```

---

## Natural Language Commands

The module parses natural language into file operations:

| Command | Action |
|---------|--------|
| "copy file.txt to Documents" | `copy_file("file.txt", "documents")` |
| "move all jpg to Pictures" | `move_file("*.jpg", "pictures")` |
| "delete old_folder" | `delete_file("old_folder")` |
| "delete file permanently" | `delete_file("file", permanent=True)` |
| "rename report to final_report" | `rename_file("report", "final_report")` |
| "create folder Projects" | `create_folder("Projects")` |
| "list files in Downloads" | `list_files("downloads")` |
| "search for python" | `search_files("python")` |
| "open folder Documents" | `open_folder("documents")` |
| "select all" | Keyboard Ctrl+A |
| "copy" | Keyboard Ctrl+C |
| "paste" | Keyboard Ctrl+V |

---

## Integration with SmartTrigger

The SmartTrigger automatically detects file commands:

```python
from Backend.SmartTrigger import smart_trigger

trigger, command, confidence = smart_trigger.detect("copy report to Documents")
# trigger = "file"
# command = "copy report to Documents"
```

**Detected Keywords:**
- create, delete, copy, move, rename
- file, folder, directory
- list, search, find
- select all, cut, paste, undo, redo
- documents, downloads, desktop, pictures

---

## Operation History

Track recent operations for undo support:

```python
# Get last 10 operations
history = file_ops.get_history(10)

# Clear history
file_ops.clear_history()
```

---

## Requirements

**Required:**
- Python 3.7+
- Standard library (os, shutil, glob)

**Optional (for keyboard shortcuts):**
- `pyautogui` - Keyboard automation
- `keyboard` - Alternative keyboard control
- `pyperclip` - Clipboard access
- `send2trash` - Recycle bin support

Install optional dependencies:
```bash
pip install pyautogui pyperclip send2trash
```

---

## Examples

### Organize Downloads

```python
from Backend.BasicFileOps import file_ops

# Move images to Pictures
file_ops.move_file("~/Downloads/*.jpg", "~/Pictures")
file_ops.move_file("~/Downloads/*.png", "~/Pictures")

# Move documents
file_ops.move_file("~/Downloads/*.pdf", "~/Documents")
file_ops.move_file("~/Downloads/*.docx", "~/Documents")

# Clean up temp files
file_ops.delete_file("~/Downloads/*.tmp")
```

### Backup Project

```python
# Copy entire project folder
file_ops.copy_file("~/Projects/MyApp", "~/Backup/MyApp_backup")
```

### Search & Organize

```python
# Find all Python files
results = file_ops.search_files("*.py", "~/Code", max_results=50)

# Find files containing "TODO"
results = file_ops.search_files("TODO", "~/Projects", search_content=True)
```

---

## Error Handling

All functions return a dict with status:

```python
result = file_ops.copy_file("nonexistent.txt", "~/Documents")

if result["status"] == "success":
    print(f"Done: {result['message']}")
else:
    print(f"Error: {result['message']}")
```

---

*Advanced File Operations Module v2.0*  
*Part of KAI Automation System*
