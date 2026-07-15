# TODO (Step 4 — Redis Setup)
#
# Session Store
#
# What a session is:
#   Fast lookup of key conversation state for an incoming sender.
#   Avoids a PostgreSQL query on every single message.
#
# Session structure stored in Redis:
#   key:   "session:{sender_id}"
#   value: JSON string of:
#     {
#       "salon_id": "salon_abc",
#       "conversation_id": "uuid-xxx",
#       "human_handling": false,
#       "pilot_mode": true,
#       "last_active": "2026-07-14T14:30:00Z"
#     }
#   TTL:   86400 seconds (24 hours)
#
# Functions to implement:
#
#   async def get_session(redis, sender_id: str) -> dict | None:
#       """
#       Get session from Redis.
#       Returns None if session doesn't exist (new customer or expired).
#       """
#
#   async def set_session(redis, sender_id: str, session_data: dict) -> None:
#       """Save or update session. Always reset TTL to 24 hours."""
#
#   async def update_human_handling(redis, sender_id: str, value: bool) -> None:
#       """Update just the human_handling flag in the session."""
#
#   async def delete_session(redis, sender_id: str) -> None:
#       """Remove session entirely (e.g., conversation resolved)."""
