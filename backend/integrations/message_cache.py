"""
In-Memory Message Deduplication Cache

Tracks processed message IDs to prevent replay attacks.
Uses simple in-memory dict with TTL cleanup.

For production, consider using Redis or DynamoDB for distributed systems.
"""

import time
from typing import Dict, Tuple
from threading import Lock

# In-memory cache: {message_id: (timestamp, ttl)}
_processed_messages: Dict[str, Tuple[float, int]] = {}
_cache_lock = Lock()

# Cleanup interval (seconds)
CLEANUP_INTERVAL = 60  # Clean up every minute
_last_cleanup = time.time()


def is_message_processed(message_id: str) -> bool:
    """
    Check if a message ID has been processed recently.
    
    Args:
        message_id: Unique message identifier
    
    Returns:
        bool: True if message was already processed
    """
    with _cache_lock:
        _cleanup_expired()
        
        if message_id in _processed_messages:
            timestamp, ttl = _processed_messages[message_id]
            
            # Check if still valid (not expired)
            if time.time() - timestamp < ttl:
                return True
            else:
                # Expired, remove it
                del _processed_messages[message_id]
                return False
        
        return False


def mark_message_processed(message_id: str, ttl_seconds: int = 600):
    """
    Mark a message as processed with TTL.
    
    Args:
        message_id: Unique message identifier
        ttl_seconds: Time-to-live in seconds (default: 10 minutes)
    """
    with _cache_lock:
        _processed_messages[message_id] = (time.time(), ttl_seconds)
        _cleanup_expired()


def _cleanup_expired():
    """
    Remove expired entries from cache.
    Called periodically to prevent memory bloat.
    """
    global _last_cleanup
    
    current_time = time.time()
    
    # Only cleanup if interval has passed
    if current_time - _last_cleanup < CLEANUP_INTERVAL:
        return
    
    # Remove expired entries
    expired_keys = []
    for msg_id, (timestamp, ttl) in _processed_messages.items():
        if current_time - timestamp >= ttl:
            expired_keys.append(msg_id)
    
    for key in expired_keys:
        del _processed_messages[key]
    
    _last_cleanup = current_time
    
    if expired_keys:
        from common.logger import logger
        logger.debug(f"Cleaned up {len(expired_keys)} expired message IDs from cache")


def get_cache_stats() -> dict:
    """
    Get cache statistics for monitoring.
    
    Returns:
        dict: Cache stats (size, oldest entry, etc.)
    """
    with _cache_lock:
        if not _processed_messages:
            return {'size': 0, 'oldest_age_seconds': 0}
        
        current_time = time.time()
        oldest_timestamp = min(ts for ts, _ in _processed_messages.values())
        
        return {
            'size': len(_processed_messages),
            'oldest_age_seconds': int(current_time - oldest_timestamp),
            'last_cleanup': int(current_time - _last_cleanup)
        }
