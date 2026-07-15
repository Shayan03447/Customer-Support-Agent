# Interactive CLI test script.
#
# Run this to test the agent in the terminal without Meta API or CRM.
# Only OpenAI API key needed.
#
# Usage: python scripts/test_agent.py
#
# What to implement here:
#   1. Load .env (dotenv)
#   2. Define DEMO_SALON dict (mock salon config — replaces DB in early phase)
#   3. Run a while loop:
#        - input("You: ")
#        - Build AgentState with conversation_history + salon_config
#        - agent_graph.invoke(state)
#        - Print result["final_response"]
#        - Append user message + agent reply to conversation_history (multi-turn)
#   4. Handle escalation (human_handling = True)
#   5. Handle "reset" command to clear history
#   6. Handle "quit" to exit
