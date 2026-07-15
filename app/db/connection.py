# TODO (Step 3 — PostgreSQL Setup)
#
# asyncpg Connection Pool
#
# Why asyncpg instead of psycopg2?
# FastAPI is async. asyncpg is a fully async PostgreSQL driver.
# Using a sync driver (psycopg2) would block the event loop on every DB query.
#
# How to implement:
#
#   import asyncpg
#   from app.config import settings
#
#   _pool: asyncpg.Pool | None = None
#
#   async def init_db_pool() -> None:
#       """Call this once at application startup in app/main.py lifespan."""
#       global _pool
#       _pool = await asyncpg.create_pool(
#           dsn=settings.database_url,
#           min_size=2,
#           max_size=10,
#       )
#
#   async def get_db() -> asyncpg.Pool:
#       """FastAPI dependency — use with Depends(get_db) in route handlers."""
#       if _pool is None:
#           raise RuntimeError("Database pool not initialized")
#       return _pool
#
#   async def close_db_pool() -> None:
#       """Call this at application shutdown in app/main.py lifespan."""
#       if _pool:
#           await _pool.close()
