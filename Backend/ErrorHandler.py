"""
Centralized Error Handler - User-Friendly Error Management
==========================================================
Provides consistent error handling across all JARVIS modules
"""

import logging
import traceback
from datetime import datetime
from typing import Optional, Callable, Any
import os

class ErrorHandler:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup logging
        log_file = os.path.join(self.log_dir, f"jarvis_{datetime.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('JARVIS')
    
    def handle_error(self, error: Exception, context: str = "", user_friendly: bool = True) -> str:
        """
        Handle an error and return user-friendly message
        
        Args:
            error: The exception that occurred
            context: Context where error occurred (e.g., "Image Analysis")
            user_friendly: Whether to return user-friendly message
            
        Returns:
            Error message string
        """
        # Log full error details
        self.logger.error(f"Error in {context}: {str(error)}")
        self.logger.error(traceback.format_exc())
        
        if user_friendly:
            return self._get_user_friendly_message(error, context)
        else:
            return str(error)
    
    def _get_user_friendly_message(self, error: Exception, context: str) -> str:
        """Generate user-friendly error message"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Common error patterns
        if "rate limit" in error_msg.lower():
            return f"API rate limit reached. Please wait a moment and try again."
        
        elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            return f"API authentication issue. Please check your API keys in .env file."
        
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            return f"Network connection issue. Please check your internet connection."
        
        elif "file not found" in error_msg.lower() or "no such file" in error_msg.lower():
            return f"File not found. Please check the file path and try again."
        
        elif "permission" in error_msg.lower():
            return f"Permission denied. Please run with appropriate permissions."
        
        elif "timeout" in error_msg.lower():
            return f"Operation timed out. Please try again."
        
        elif "import" in error_msg.lower() or "module" in error_msg.lower():
            return f"Missing dependency. Please install required packages: pip install -r requirements.txt"
        
        else:
            return f"{context} error: {error_msg[:100]}"
    
    def safe_execute(self, func: Callable, *args, context: str = "", default_return: Any = None, **kwargs) -> Any:
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            *args: Function arguments
            context: Context description
            default_return: Value to return on error
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or default_return on error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = self.handle_error(e, context)
            self.logger.error(f"Safe execution failed: {error_msg}")
            return default_return
    
    def log_info(self, message: str):
        """Log informational message"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_silent(self, error: Exception = None, context: str = "", message: str = ""):
        """
        Log error silently (to file only, no console output)
        Use this to replace bare 'except: pass' statements
        """
        if error:
            log_msg = f"[SILENT] {context}: {type(error).__name__}: {str(error)[:200]}"
        else:
            log_msg = f"[SILENT] {context}: {message}"
        
        # Write directly to log file without console
        try:
            log_file = os.path.join(self.log_dir, f"jarvis_{datetime.now().strftime('%Y%m%d')}.log")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - JARVIS - SILENT - {log_msg}\n")
        except:
            pass  # Last resort - don't crash on logging failure
    
    def log_debug(self, message: str):
        """Log debug message (file only)"""
        self.logger.debug(message)
    
    def wrap_silent(self, func: Callable, context: str = "", default: Any = None):
        """
        Decorator/wrapper for functions that should fail silently but log
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.log_silent(e, context)
                return default
        return wrapper


# Global instance
error_handler = ErrorHandler()

if __name__ == "__main__":
    # Test error handler
    try:
        raise ValueError("Test error")
    except Exception as e:
        print(error_handler.handle_error(e, "Test Context"))
