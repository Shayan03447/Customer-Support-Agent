# TODO (Step 5 — Draft Approval)
#
# Draft Repository
#
# Functions to implement:
#
#   async def create_draft(pool, conversation_id, draft_text) -> str:
#       """INSERT draft row with status='pending'. Returns draft_id."""
#
#   async def get_draft(pool, draft_id: str) -> dict | None:
#       """SELECT draft by ID."""
#
#   async def approve_draft(pool, draft_id, approved_by="") -> None:
#       """UPDATE drafts SET status='approved', approved_by=..., approved_at=NOW()"""
#
#   async def update_draft_sent_text(pool, draft_id, sent_text) -> None:
#       """UPDATE drafts SET sent_text=sent_text, status='edited'"""
#
#   async def discard_draft(pool, draft_id) -> None:
#       """UPDATE drafts SET status='discarded'"""
