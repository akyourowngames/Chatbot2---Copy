"""
📊 LOGGING SYSTEM — The Operation Tracker 📈
Comprehensive logging system for tracking web scraping operations, performance, and errors.
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import time
from collections import defaultdict, deque
import traceback
from contextlib import contextmanager

@dataclass
class LogConfig:
    """Configuration for logging system"""
    log_level: str = "INFO"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True
    json_format: bool = True
    performance_tracking: bool = True
    error_tracking: bool = True
    operation_tracking: bool = True
    log_rotation: bool = True
    log_retention_days: int = 30
    real_time_monitoring: bool = True
    metrics_collection: bool = True

@dataclass
class OperationMetrics:
    """Metrics for tracking operations"""
    operation_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    urls_processed: int = 0
    bytes_downloaded: int = 0
    pages_scraped: int = 0
    errors_encountered: int = 0
    retries_made: int = 0
    metadata: Dict[str, Any] = None

class WebScrapingLogger:
    """
    📊 Advanced logging system for web scraping operations
    """
    
    def __init__(self, config: LogConfig = None):
        self.config = config or LogConfig()
        self.log_dir = Path(self.config.log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Thread-safe collections for metrics
        self.lock = threading.Lock()
        self.operation_metrics: Dict[str, OperationMetrics] = {}
        self.error_log: deque = deque(maxlen=1000)
        self.performance_log: deque = deque(maxlen=1000)
        self.url_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'success_count': 0,
            'error_count': 0,
            'total_time': 0.0,
            'last_accessed': None
        })
        
        # Initialize loggers
        self._setup_loggers()
        
        # Start background cleanup
        if self.config.log_rotation:
            self._start_cleanup_thread()
    
    def _setup_loggers(self):
        """Setup different loggers for different purposes"""
        
        # Main logger
        self.main_logger = logging.getLogger('web_scraper')
        self.main_logger.setLevel(getattr(logging, self.config.log_level))
        
        # Clear existing handlers
        self.main_logger.handlers.clear()
        
        # Console handler
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.main_logger.addHandler(console_handler)
        
        # File handlers
        if self.config.file_output:
            # General log file
            general_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'web_scraper.log',
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            general_handler.setLevel(getattr(logging, self.config.log_level))
            self.main_logger.addHandler(general_handler)
            
            # Error log file
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'errors.log',
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            self.main_logger.addHandler(error_handler)
            
            # Performance log file
            if self.config.performance_tracking:
                perf_handler = logging.handlers.RotatingFileHandler(
                    self.log_dir / 'performance.log',
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count
                )
                perf_handler.setLevel(logging.INFO)
                self.main_logger.addHandler(perf_handler)
        
        # JSON formatter for structured logging
        if self.config.json_format:
            self.json_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / 'structured.json',
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            self.json_handler.setLevel(getattr(logging, self.config.log_level))
            self.json_handler.setFormatter(JsonFormatter())
            self.main_logger.addHandler(self.json_handler)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with optional metadata"""
        self.main_logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with optional metadata"""
        self.main_logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, exception: Exception = None, **kwargs):
        """Log error message with optional exception"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        
        self.main_logger.error(message, extra=kwargs)
        
        # Track error
        if self.config.error_tracking:
            self._track_error(message, exception, kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with optional metadata"""
        self.main_logger.debug(message, extra=kwargs)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        if self.config.performance_tracking:
            kwargs.update({
                'operation': operation,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            self.main_logger.info(f"Performance: {operation} took {duration:.2f}s", extra=kwargs)
            
            # Track in performance log
            with self.lock:
                self.performance_log.append({
                    'operation': operation,
                    'duration': duration,
                    'timestamp': datetime.now(),
                    'metadata': kwargs
                })
    
    def start_operation(self, operation_id: str, operation_type: str, **metadata) -> OperationMetrics:
        """Start tracking an operation"""
        metrics = OperationMetrics(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        with self.lock:
            self.operation_metrics[operation_id] = metrics
        
        self.log_info(f"Started operation: {operation_type}", 
                     operation_id=operation_id, **metadata)
        
        return metrics
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     error_message: str = None, **updates):
        """End tracking an operation"""
        with self.lock:
            if operation_id in self.operation_metrics:
                metrics = self.operation_metrics[operation_id]
                metrics.end_time = datetime.now()
                metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
                metrics.success = success
                metrics.error_message = error_message
                
                # Apply updates
                for key, value in updates.items():
                    if hasattr(metrics, key):
                        setattr(metrics, key, value)
                
                # Log completion
                if success:
                    self.log_info(f"Completed operation: {metrics.operation_type}",
                                operation_id=operation_id,
                                duration=metrics.duration,
                                **metrics.metadata)
                else:
                    self.log_error(f"Failed operation: {metrics.operation_type}",
                                 operation_id=operation_id,
                                 duration=metrics.duration,
                                 error_message=error_message,
                                 **metrics.metadata)
                
                # Track URL stats
                if 'url' in metrics.metadata:
                    self._update_url_stats(metrics.metadata['url'], success, metrics.duration)
    
    def log_url_access(self, url: str, success: bool, duration: float, **metadata):
        """Log URL access with performance metrics"""
        self._update_url_stats(url, success, duration)
        
        if success:
            self.log_info(f"Successfully accessed: {url}", 
                         url=url, duration=duration, **metadata)
        else:
            self.log_error(f"Failed to access: {url}", 
                          url=url, duration=duration, **metadata)
    
    def log_scraping_result(self, url: str, success: bool, content_length: int = 0, **metadata):
        """Log scraping result"""
        if success:
            self.log_info(f"Scraped content from: {url}", 
                         url=url, content_length=content_length, **metadata)
        else:
            self.log_error(f"Failed to scrape: {url}", 
                          url=url, **metadata)
    
    def log_retry_attempt(self, url: str, attempt: int, max_attempts: int, error: str):
        """Log retry attempt"""
        self.log_warning(f"Retry attempt {attempt}/{max_attempts} for: {url}",
                        url=url, attempt=attempt, max_attempts=max_attempts, error=error)
    
    def log_rate_limit(self, url: str, retry_after: int):
        """Log rate limiting"""
        self.log_warning(f"Rate limited for: {url}, retry after {retry_after}s",
                        url=url, retry_after=retry_after)
    
    def log_proxy_switch(self, old_proxy: str, new_proxy: str, reason: str):
        """Log proxy switching"""
        self.log_info(f"Switched proxy: {old_proxy} -> {new_proxy}, reason: {reason}",
                     old_proxy=old_proxy, new_proxy=new_proxy, reason=reason)
    
    def log_ai_processing(self, operation: str, model: str, duration: float, **metadata):
        """Log AI processing operations"""
        self.log_performance(f"AI_{operation}", duration, model=model, **metadata)
    
    def _track_error(self, message: str, exception: Exception, metadata: Dict):
        """Track error for analysis"""
        with self.lock:
            self.error_log.append({
                'message': message,
                'exception': str(exception) if exception else None,
                'timestamp': datetime.now(),
                'metadata': metadata
            })
    
    def _update_url_stats(self, url: str, success: bool, duration: float):
        """Update URL statistics"""
        with self.lock:
            stats = self.url_stats[url]
            if success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            stats['total_time'] += duration
            stats['last_accessed'] = datetime.now()
    
    def _start_cleanup_thread(self):
        """Start background thread for log cleanup"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self._cleanup_old_logs()
                except Exception as e:
                    self.log_error("Error in cleanup thread", e)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.log_retention_days)
            
            for log_file in self.log_dir.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.log_info(f"Cleaned up old log file: {log_file}")
        
        except Exception as e:
            self.log_error("Failed to cleanup old logs", e)
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation statistics"""
        with self.lock:
            total_operations = len(self.operation_metrics)
            successful_operations = sum(1 for m in self.operation_metrics.values() if m.success)
            failed_operations = total_operations - successful_operations
            
            avg_duration = 0
            if self.operation_metrics:
                durations = [m.duration for m in self.operation_metrics.values() if m.duration]
                avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'failed_operations': failed_operations,
                'success_rate': successful_operations / total_operations if total_operations > 0 else 0,
                'average_duration': avg_duration,
                'total_urls_processed': sum(m.urls_processed for m in self.operation_metrics.values()),
                'total_bytes_downloaded': sum(m.bytes_downloaded for m in self.operation_metrics.values()),
                'total_errors': sum(m.errors_encountered for m in self.operation_metrics.values())
            }
    
    def get_url_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get URL statistics"""
        with self.lock:
            return dict(self.url_stats)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        with self.lock:
            if not self.error_log:
                return {'total_errors': 0, 'recent_errors': []}
            
            error_types = defaultdict(int)
            recent_errors = []
            
            for error in list(self.error_log)[-10:]:  # Last 10 errors
                recent_errors.append({
                    'message': error['message'],
                    'timestamp': error['timestamp'].isoformat(),
                    'exception': error['exception']
                })
                
                if error['exception']:
                    error_types[error['exception']] += 1
            
            return {
                'total_errors': len(self.error_log),
                'error_types': dict(error_types),
                'recent_errors': recent_errors
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        with self.lock:
            if not self.performance_log:
                return {'total_operations': 0, 'average_duration': 0}
            
            operations = defaultdict(list)
            
            for perf in self.performance_log:
                operations[perf['operation']].append(perf['duration'])
            
            summary = {}
            for op, durations in operations.items():
                summary[op] = {
                    'count': len(durations),
                    'average_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations)
                }
            
            return summary
    
    def export_logs(self, output_file: str = None) -> str:
        """Export logs to JSON file"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"web_scraper_logs_{timestamp}.json"
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'operation_stats': self.get_operation_stats(),
                'url_stats': self.get_url_stats(),
                'error_summary': self.get_error_summary(),
                'performance_summary': self.get_performance_summary(),
                'config': asdict(self.config)
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.log_info(f"Exported logs to: {output_file}")
            return output_file
            
        except Exception as e:
            self.log_error("Failed to export logs", e)
            return ""
    
    @contextmanager
    def operation_context(self, operation_id: str, operation_type: str, **metadata):
        """Context manager for operation tracking"""
        metrics = self.start_operation(operation_id, operation_type, **metadata)
        
        try:
            yield metrics
            self.end_operation(operation_id, success=True)
        except Exception as e:
            self.end_operation(operation_id, success=False, error_message=str(e))
            raise

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

# Global logger instance
_global_logger = None

def get_logger(config: LogConfig = None) -> WebScrapingLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = WebScrapingLogger(config)
    return _global_logger

def setup_logging(config: LogConfig = None) -> WebScrapingLogger:
    """Setup logging system"""
    return get_logger(config)

# Convenience functions
def log_info(message: str, **kwargs):
    """Quick info logging"""
    get_logger().log_info(message, **kwargs)

def log_error(message: str, exception: Exception = None, **kwargs):
    """Quick error logging"""
    get_logger().log_error(message, exception, **kwargs)

def log_performance(operation: str, duration: float, **kwargs):
    """Quick performance logging"""
    get_logger().log_performance(operation, duration, **kwargs)

# Example usage
if __name__ == "__main__":
    # Test logging system
    config = LogConfig(
        log_level="DEBUG",
        console_output=True,
        file_output=True,
        performance_tracking=True,
        error_tracking=True
    )
    
    logger = WebScrapingLogger(config)
    
    # Test basic logging
    logger.log_info("Testing info logging", test_param="value")
    logger.log_warning("Testing warning logging")
    logger.log_error("Testing error logging", ValueError("Test error"))
    
    # Test operation tracking
    with logger.operation_context("test_op_1", "test_operation", url="https://example.com") as metrics:
        time.sleep(0.1)  # Simulate work
        metrics.urls_processed = 1
        metrics.bytes_downloaded = 1024
    
    # Test performance logging
    logger.log_performance("test_performance", 0.5, operation_type="test")
    
    # Test URL logging
    logger.log_url_access("https://example.com", True, 1.2)
    logger.log_scraping_result("https://example.com", True, 2048)
    
    # Test stats
    print("\n📊 Operation Stats:")
    print(json.dumps(logger.get_operation_stats(), indent=2))
    
    print("\n📊 URL Stats:")
    print(json.dumps(logger.get_url_stats(), indent=2))
    
    print("\n📊 Error Summary:")
    print(json.dumps(logger.get_error_summary(), indent=2))
    
    print("\n📊 Performance Summary:")
    print(json.dumps(logger.get_performance_summary(), indent=2))
    
    # Export logs
    export_file = logger.export_logs()
    print(f"\n📊 Logs exported to: {export_file}")
    
    print("\n📊 Logging System initialized successfully!")
