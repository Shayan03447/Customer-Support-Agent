# Tool definitions for the AI agent.
#
# TWO things to define here:
#
# 1. TOOL_SCHEMAS — list of OpenAI function schemas passed to GPT-4o
#    These tell the model what tools exist and how to call them.
#    Tools to define:
#      - get_service_price(service_name, salon_id)
#      - check_availability(salon_id, date, service_name)
#      - create_booking(salon_id, customer_name, service_name, date, time, phone, email)
#      - capture_contact(name, phone, email, sender_id)
#      - escalate_to_human(reason)
#
# 2. execute_tool(tool_name, tool_args) → str
#    Routes tool calls to the correct function.
#    Returns result as a JSON string (OpenAI tool message format).
#
#    Phase 1 (no CRM yet): use mock functions with hardcoded data
#    Phase 2 (CRM connected): replace mocks with real CRM API calls via crm/client.py
