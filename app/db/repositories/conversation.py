# TODO (Step 3 — PostgreSQL Setup)
#
# Conversation Repository
#
# All SQL queries for the conversations and messages tables live here.
# No raw SQL in agent nodes or API handlers — always go through a repository.
#
# Functions to implement:
#
#   async def create_conversation(pool, sender_id, channel, salon_id) -> str:
#       """Insert a new conversation row. Returns conversation_id (UUID)."""
#
#   async def get_conversation(pool, sender_id, salon_id) -> dict | None:
#       """Find existing conversation for this sender + salon combo."""
#
#   async def set_human_handling(pool, conversation_id, value: bool) -> None:
#       """UPDATE conversations SET human_handling = value WHERE id = conversation_id"""
#
#   async def update_lead_status(pool, conversation_id, status: str) -> None:
#       """UPDATE conversations SET lead_status = status"""
#
#   async def save_message(pool, conversation_id, role, content, tool_name=None) -> None:
#       """INSERT into messages table — saves every message for transcript."""
#
#   async def get_message_history(pool, conversation_id, limit=20) -> list[dict]:
#       """SELECT last N messages for this conversation."""
