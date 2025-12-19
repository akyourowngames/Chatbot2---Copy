"""
File I/O Automation Module
Handles file search, read, write, and management operations
"""
import os
import glob
from pathlib import Path

class FileIOAutomation:
    """File operations handler"""
    
    def __init__(self):
        self.search_paths = [
            os.path.expanduser("~"),  # User home
            "C:/",  # Root (Windows)
            "/",  # Root (Unix)
        ]
    
    def search_files(self, query, file_types=None, max_results=10):
        """
        Search for files matching query
        
        Args:
            query: Search term
            file_types: List of extensions (e.g., ['.txt', '.pdf'])
            max_results: Maximum results to return
            
        Returns:
            List of file paths matching the query
        """
        results = []
        query_lower = query.lower()
        
        for search_path in self.search_paths:
            try:
                # Use glob for pattern matching
                pattern = f"**/*{query}*"
                
                for file_path in Path(search_path).rglob(f"*{query}*"):
                    if len(results) >= max_results:
                        break
                        
                    # Filter by file type if specified
                    if file_types and file_path.suffix not in file_types:
                        continue
                    
                    # Skip system/hidden files
                    if any(part.startswith('.') for part in file_path.parts):
                        continue
                        
                    results.append(str(file_path))
                    
            except (PermissionError, OSError):
                continue  # Skip inaccessible directories
                
        return results[:max_results]
    
    def read_file(self, file_path):
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
    
    def write_file(self, file_path, content):
        """Write content to file"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written successfully: {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"


# Global instance
file_io = FileIOAutomation()
