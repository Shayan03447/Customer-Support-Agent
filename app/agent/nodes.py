from openai import OpenAI
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import build_system_prompt
from app.agent.tools import TOOL_SCHEMAS

_client=None

def _get_client()-> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client

def run_agent(state: AgentState)-> dict:
    client = _get_client()
    system_prompt= {
        "role": "system",
        "content": build_system_prompt(state["salon_config"]),
    }
    full_messages = [system_prompt] + state["messages"]

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages= full_messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
    )
    assistant_message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason

    if finish_reason == "tool_calls" and assistant_message.tool_calls:
        tool_calls_data = [
            {
                "id": tool_call.id,
                "type":"function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in assistant_message.tool_calls
        ]

        new_message = {
            "role":"assistant",
            "content": assistant_message.content,
            "tool_calls": tool_calls_data,
        }

        return {
            "messages": state["messages"]+ [new_message],
            "next_node": "execute_tools",
        }
    
    final_text =  assistant_message.content or ""
    new_message = {
        "role": "assistant",
        "content": final_text,
    }

    return {
        "messages": state["messages"] + [new_message],
        "final_response": final_text,
        "next_node": "send_reply",
    }


        