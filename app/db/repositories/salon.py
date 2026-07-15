# TODO (Step 3 — PostgreSQL Setup)
#
# Salon Repository
#
# Functions to implement:
#
#   async def get_salon_by_page_id(pool, page_id: str) -> dict | None:
#       """
#       Look up salon config by Meta page_id.
#       Returns full salon_config dict or None if page not registered.
#       Used by every incoming webhook to identify which salon it belongs to.
#       """
#
#   async def get_salon_by_id(pool, salon_id: str) -> dict | None:
#       """Look up salon by its salon_id."""
#
#   async def list_active_salons(pool) -> list[dict]:
#       """Get all salons where active = True."""
#
#   async def update_pilot_mode(pool, salon_id: str, pilot_mode: bool) -> None:
#       """
#       Toggle pilot mode for a salon.
#       pilot_mode = True  → agent drafts, team approves before sending
#       pilot_mode = False → agent sends directly
#       """
