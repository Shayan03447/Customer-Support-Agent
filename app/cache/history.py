# TODO (Step 4 — Redis Setup)
#
# Conversation History Cache
#
# Why cache history in Redis?
#   The agent needs the last 20 messages as context on EVERY message.
#   Loading from PostgreSQL on every message would be slow.
#   Redis serves this in <1ms vs 10-50ms from DB.
#
# Cache structure:
#   key:   "history:{conversation_id}"
#   value: JSON string of message list (last 20 messages in OpenAI format)
#   TTL:   7200 seconds (2 hours)
#   After TTL expires: reload from PostgreSQL on next request
#
# Functions to implement:
#
#   async def get_history(redis, conversation_id: str) -> list[dict] | None:
#       """Get cached message history. Returns None on cache miss."""
#
#   async def append_message(redis, conversation_id: str, message: dict, max_messages=20) -> None:
#       """
#       Append a new message to the cached history.
#       Trims to max_messages to avoid unbounded growth.
#       Resets TTL on every append.
#       """
#
#   async def invalidate(redis, conversation_id: str) -> None:
#       """Delete history cache (force reload from DB on next request)."""
