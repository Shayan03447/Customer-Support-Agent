# LangGraph node functions.
# Each function = one step in the agent workflow.
# Every node takes AgentState as input, returns a partial dict update.
#
# Nodes to implement:
#
# run_agent(state) → dict
#   Calls GPT-4o with current messages + system prompt + TOOL_SCHEMAS.
#   If response has tool_calls → set next_node = "execute_tools"
#   If response is final text  → set next_node = "send_reply"
#
# execute_tools(state) → dict
#   Reads tool_calls from last message in state.
#   Runs execute_tool() for each tool call.
#   Appends tool result messages to conversation.
#   If escalate_to_human was called → set next_node = "escalate"
#   Otherwise → set next_node = "run_agent" (loop back)
#
# send_reply(state) → dict
#   pilot_mode = True  → save draft to DB, notify team via Slack
#   pilot_mode = False → send via Meta API
#
# escalate(state) → dict
#   Sets human_handling = True in DB and Redis.
#   Sends Slack alert to team.
#   Sends holding message to customer via Meta API.
#
# route_after_agent(state) → str   ← routing function for conditional edge
# route_after_tools(state) → str   ← routing function for conditional edge
