# TODO (Step 5 — CRM Integration)
#
# Async CRM API Client
#
# All CRM communication goes through this class.
# No other file makes direct HTTP calls to the CRM.
# This makes it easy to swap CRM providers or change endpoints in one place.
#
# When this is implemented, replace the mock functions in app/agent/tools.py
# with calls to the methods below.
#
# class CRMClient:
#
#     def __init__(self, base_url: str, api_key: str):
#         self.base_url = base_url
#         self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
#         self.client = httpx.AsyncClient(base_url=base_url, headers=self.headers, timeout=10.0)
#
#     async def get_service_price(self, salon_id: str, service_name: str) -> dict | None:
#         """
#         Returns service dict on success, None if not found (404).
#         Raises CRMTimeoutError or CRMServerError on failures.
#         """
#
#     async def check_availability(self, salon_id: str, date: str, service_name: str) -> dict:
#         """Returns available slots for the given date and service."""
#
#     async def create_booking(self, booking_data: dict) -> dict:
#         """Creates booking, returns booking_id and confirmation details."""
#
#     async def upsert_contact(self, contact_data: dict) -> str:
#         """Creates or updates a contact. Returns crm_contact_id."""
#
#     async def log_conversation(self, data: dict) -> None:
#         """Saves full conversation transcript and metadata."""
#
#     async def update_lead_status(self, lead_id: str, status: str) -> None:
#         """Updates lead stage: new → interested → qualified → booked | escalated"""
#
# Error handling contract:
#   - 404 Not Found  → return None (agent will escalate)
#   - 500 / Timeout  → raise exception (agent will escalate)
#   - Never return partial or guessed data
