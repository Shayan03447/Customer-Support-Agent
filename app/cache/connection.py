# TODO (Step 4 — Redis Setup)
#
# Redis Connection
#
# How to implement:
#
#   import redis.asyncio as aioredis
#   from app.config import settings
#
#   _redis: aioredis.Redis | None = None
#
#   async def init_redis() -> None:
#       """Call once at app startup in app/main.py lifespan."""
#       global _redis
#       _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
#
#   def get_redis() -> aioredis.Redis:
#       if _redis is None:
#           raise RuntimeError("Redis not initialized")
#       return _redis
#
#   async def close_redis() -> None:
#       if _redis:
#           await _redis.aclose()
#
# decode_responses=True means Redis returns strings instead of bytes.
# This makes working with JSON data much easier.
