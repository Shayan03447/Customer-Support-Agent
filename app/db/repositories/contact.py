# TODO (Step 3 — PostgreSQL Setup)
#
# Contact Repository
#
# Functions to implement:
#
#   async def upsert_contact(pool, salon_id, ig_sender_id="", fb_sender_id="",
#                             name="", phone="", email="") -> str:
#       """
#       Insert or update a contact record.
#       Returns contact_id.
#       Uses INSERT ... ON CONFLICT DO UPDATE for upsert behavior.
#       """
#
#   async def get_contact_by_sender_id(pool, sender_id: str) -> dict | None:
#       """Find contact by Instagram or Facebook sender ID."""
