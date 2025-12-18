"""
Performance Optimizer - Beast Mode (Central Nervous System)
============================================================
The brain behind KAI's speed. Manages caching, threading, and resource health.
"""

import time
import functools
import json
import os
import hashlib
from typing import Any, Callable, Dict
from datetime import datetime
import threading

class PerformanceOptimizer:
    def __init__(self):
        self.cache_dir = os.path.join("Data", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.stats = {
            "start_time": time.time(),
            "calls": 0,
            "hits": 0,
        }
        self._lock = threading.Lock()

    def cache_beast(self, ttl: int = 3600):
        """God-level caching decorator"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.stats["calls"] += 1
                
                # Dynamic Cache Key
                key_str = f"{func.__name__}:{args}:{kwargs}"
                key = hashlib.md5(key_str.encode()).hexdigest()
                cache_path = os.path.join(self.cache_dir, f"{key}.json")
                
                # Check Validity
                if os.path.exists(cache_path):
                    try:
                        with open(cache_path, 'r') as f:
                            data = json.load(f)
                        if time.time() - data['t'] < ttl:
                            self.stats["hits"] += 1
                            return data['v']
                    except: pass
                
                # Execute and Cache
                result = func(*args, **kwargs)
                try:
                    with open(cache_path, 'w') as f:
                        json.dump({'t': time.time(), 'v': result}, f)
                except: pass
                return result
            return wrapper
        return decorator

    def get_beast_metrics(self) -> Dict:
        uptime = time.time() - self.stats["start_time"]
        hit_rate = (self.stats["hits"] / max(1, self.stats["calls"])) * 100
        return {
            "uptime_sec": int(uptime),
            "total_calls": self.stats["calls"],
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "active_threads": threading.active_count()
        }

    def clean_slate(self):
        """Wipe all temporary cache"""
        for f in os.listdir(self.cache_dir):
            try: os.remove(os.path.join(self.cache_dir, f))
            except: pass
        return "Cache cleared"

# Global instance
performance_optimizer = PerformanceOptimizer()
cache = performance_optimizer.cache_beast
