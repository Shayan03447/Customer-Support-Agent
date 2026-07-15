# AgentState — the shared context dictionary that flows through every LangGraph node.
#
# Fields to define here:
#   messages         → list of OpenAI-format message dicts (conversation history)
#   sender_id        → customer's Meta user ID
#   channel          → "instagram_dm" | "facebook_messenger" | "test_cli"
#   salon_id         → which salon this conversation belongs to
#   salon_config     → dict loaded from DB: name, address, hours, policies
#   conversation_id  → UUID of the PostgreSQL conversations row
#   human_handling   → bool: if True, agent stops — human takes over
#   pilot_mode       → bool: if True, agent drafts reply but does not send
#   final_response   → the text reply to send to customer
#   escalation_reason → why escalation was triggered
#   booking_details  → populated when create_booking tool succeeds
#   next_node        → internal routing hint for conditional edges

from argparse import OPTIONAL
from typing import TypedDict, Optional

class AgentState(TypedDict):
    message: list
    sender_id: Optional[str]
    channel: Optional[str]
    salon_id: Optional[str]
    salon_config: Optional[dict]
    conversation_id: Optional[str]
    human_handling: Optional[bool]
    pilot_mode: Optional[bool]
    final_response: Optional[str]
    escalation_reason : Optional[str]
    booking_details: Optional[dict]
    next_node: Optional[str]
    
