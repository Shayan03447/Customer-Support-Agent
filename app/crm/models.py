# TODO (Step 5 — CRM Integration)
#
# Pydantic models for CRM request and response payloads.
# Using Pydantic ensures that malformed CRM responses are caught early.
#
# Models to create:
#
#   class PriceResponse(BaseModel):
#       found: bool
#       service_name: str
#       price: float | None
#       currency: str = "USD"
#       duration_hours: float | None
#       includes_hair: bool = False
#
#   class AvailabilityResponse(BaseModel):
#       available: bool
#       date: str
#       slots: list[str]
#
#   class BookingRequest(BaseModel):
#       salon_id: str
#       customer_name: str
#       service_name: str
#       date: str
#       time: str
#       phone: str = ""
#       email: str = ""
#
#   class BookingResponse(BaseModel):
#       success: bool
#       booking_id: str
#       confirmation_code: str
#       deposit_amount: float
#       deposit_link: str
#
#   class ContactRequest(BaseModel):
#       salon_id: str
#       name: str
#       phone: str = ""
#       email: str = ""
#       ig_sender_id: str = ""
#       fb_sender_id: str = ""
#
#   class ConversationLog(BaseModel):
#       contact_id: str
#       salon_id: str
#       channel: str
#       lead_status: str
#       service_interest: str
#       transcript: list[dict]
#       booking_id: str | None = None
