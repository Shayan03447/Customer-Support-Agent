# LangGraph graph definition — assembles all nodes and edges.
#
# Graph structure:
#
#   START
#     ↓
#   run_agent ──────────────────────────► execute_tools
#     ▲                                         │
#     └─────────────────────────────────────────┘ (loop back)
#     │
#     │ (final reply ready)
#     ▼
#   send_reply ──► END
#
#     │ (escalate_to_human tool called)
#     ▼
#   escalate ──► END
#
# To implement:
#   1. Create StateGraph(AgentState)
#   2. add_node() for each node function
#   3. set_entry_point("run_agent")
#   4. add_conditional_edges("run_agent", route_after_agent, {...})
#   5. add_conditional_edges("execute_tools", route_after_tools, {...})
#   6. add_edge("send_reply", END)
#   7. add_edge("escalate", END)
#   8. graph.compile() → agent_graph
#
# Export: agent_graph (compiled graph, reused across all requests)
