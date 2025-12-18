"""
Force Clear All Python Cache
============================
Run this before starting server
"""

import os
import shutil
from pathlib import Path

def clear_pycache():
    """Remove all __pycache__ directories and .pyc files"""
    base_dir = Path(__file__).parent
    
    removed_dirs = 0
    removed_files = 0
    
    # Remove __pycache__ directories
    for pycache_dir in base_dir.rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
            removed_dirs += 1
            print(f"✓ Removed: {pycache_dir}")
        except Exception as e:
            print(f"✗ Failed to remove {pycache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in base_dir.rglob('*.pyc'):
        try:
            pyc_file.unlink()
            removed_files += 1
            print(f"✓ Removed: {pyc_file}")
        except Exception as e:
            print(f"✗ Failed to remove {pyc_file}: {e}")
    
    print(f"\n✅ Cache cleared!")
    print(f"   Directories removed: {removed_dirs}")
    print(f"   Files removed: {removed_files}")
    print(f"\n🚀 Now run: python api_server.py")

if __name__ == "__main__":
    clear_pycache()
