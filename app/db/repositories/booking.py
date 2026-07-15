# TODO (Step 3 — PostgreSQL Setup)
#
# Booking Repository
#
# Functions to implement:
#
#   async def create_booking(pool, data: dict) -> str:
#       """INSERT booking row. Returns booking UUID."""
#
#   async def mark_confirmation_sent(pool, booking_id: str) -> None:
#       """UPDATE bookings SET confirmation_sent = True"""
#
#   async def get_booking(pool, booking_id: str) -> dict | None:
#       """SELECT booking row by ID."""
