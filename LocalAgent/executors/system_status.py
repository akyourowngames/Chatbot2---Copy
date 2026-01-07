"""
Kai Local Agent - System Status Executor
=========================================
Read-only executor that safely collects system information.

Collects:
- CPU usage percentage
- RAM usage (used, total, percentage)
- System uptime
- Operating system details

Security: No shell commands, no file modifications, no elevated permissions.
Uses only psutil and platform modules for reliable cross-platform support.
"""

import platform
import time
from datetime import datetime, timedelta
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .base import BaseExecutor


class SystemStatusExecutor(BaseExecutor):
    """
    Read-only executor for collecting system status information.
    No parameters accepted - returns a fixed set of safe metrics.
    """
    
    @property
    def command_name(self) -> str:
        return "system_status"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect and return system status information.
        
        Args:
            params: Empty dict (no parameters for this command)
        
        Returns:
            Dict with system status data
        """
        if not PSUTIL_AVAILABLE:
            return {
                "status": "error",
                "message": "psutil module not available. Install with: pip install psutil"
            }
        
        try:
            # Collect system metrics
            status_data = {
                "cpu": self._get_cpu_info(),
                "memory": self._get_memory_info(),
                "uptime": self._get_uptime_info(),
                "system": self._get_system_info(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Create a human-readable summary
            cpu_percent = status_data["cpu"]["percent"]
            mem_percent = status_data["memory"]["percent"]
            uptime_str = status_data["uptime"]["formatted"]
            
            summary = f"CPU: {cpu_percent}% | RAM: {mem_percent}% | Uptime: {uptime_str}"
            
            return {
                "status": "success",
                "message": summary,
                "data": status_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to collect system status: {str(e)}"
            }
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU usage information."""
        # Get CPU percent with a small interval for accuracy
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        return {
            "percent": cpu_percent,
            "cores_physical": cpu_count,
            "cores_logical": cpu_count_logical
        }
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get RAM usage information."""
        mem = psutil.virtual_memory()
        
        return {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "percent": mem.percent
        }
    
    def _get_uptime_info(self) -> Dict[str, Any]:
        """Get system uptime information."""
        boot_time = psutil.boot_time()
        boot_datetime = datetime.fromtimestamp(boot_time)
        uptime_seconds = time.time() - boot_time
        uptime_delta = timedelta(seconds=int(uptime_seconds))
        
        # Format uptime nicely
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            formatted = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            formatted = f"{hours}h {minutes}m"
        else:
            formatted = f"{minutes}m"
        
        return {
            "boot_time": boot_datetime.isoformat(),
            "uptime_seconds": int(uptime_seconds),
            "formatted": formatted
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get operating system information."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "hostname": platform.node()
        }
