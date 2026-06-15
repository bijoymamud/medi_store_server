import os
import json
from typing import Any, Optional

class Cache:
    def __init__(self):
        self._local_cache = {}
        self._redis = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                self._redis = redis.from_url(redis_url, decode_responses=True)
                print("Redis cache client initialized.")
            except Exception as e:
                print(f"Failed to initialize Redis client: {e}. Using in-memory fallback cache.")

    def get(self, key: str) -> Optional[Any]:
        if self._redis:
            try:
                data = self._redis.get(key)
                return json.loads(data) if data else None
            except Exception as e:
                print(f"Redis get key failed: {e}")
                return None
        return self._local_cache.get(key)

    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        if self._redis:
            try:
                self._redis.set(key, json.dumps(value), ex=expire_seconds)
                return
            except Exception as e:
                print(f"Redis set key failed: {e}")
        self._local_cache[key] = value

    def delete(self, key: str):
        if self._redis:
            try:
                self._redis.delete(key)
                return
            except Exception as e:
                print(f"Redis delete key failed: {e}")
        if key in self._local_cache:
            del self._local_cache[key]

cache_client = Cache()
