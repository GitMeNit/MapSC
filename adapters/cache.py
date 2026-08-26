import time
import requests
import requests_cache
from typing import Dict, Any, Optional
from functools import wraps

# Setup persistent SQLite cache for all requests
requests_cache.install_cache('supply_chain_cache', expire_after=86400) # 24 hours
#
class RateLimiter:
    """Simple rate limiter to respect API boundaries."""
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        # records the timestamps of the api calls 
        self.timestamps = []

    def wait(self):
        
        now = time.time() # current time
        self.timestamps = [t for t in self.timestamps if now - t < self.period]
        if len(self.timestamps) >= self.calls:
            #if no of time stamps are greaetr than the allowed calls, then sleep for the remaining time
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.timestamps.append(time.time())

def rate_limited(calls: int, period: int = 1):
    limiter = RateLimiter(calls, period)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        return wrapper
    return decorator

class BaseAPIClient:
    """Shared HTTP client with caching already injected via requests_cache."""
    
    @rate_limited(calls=5, period=1) # Default fallback: 5 calls per second
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response