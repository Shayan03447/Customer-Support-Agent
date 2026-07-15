import json
import uuid

# Mock CRM Data
MOCK_SERVICES={
    "box braids": {
        "price":180,
        "currency":"USD",
        "duration_hours":4,
        "includes_hair": True,
    },
    "knotless braids":{
        "price":220,
        "currency":"USD",
        "duration_hours": 5,
        "includes_hair": True,
    },
    "cornrows":{
        "price": 80,
        "currency":"USD",
        "duration_hours":2,
        "includes_hair": False,
    },
    "senegalese twists":{
        "price": 200,
        "currency":"USD",
        "duration_hours":5,
        "includes_hair":True,
    },
    "locs retwist":{
        "price":120,
        "currency":"USD",
        "duration_hours":3,
        "includes_hair":False
    },

}
MOCK_SLOTS= ["9:00 AM", "11:00 AM", "1:00 PM", "3:00 PM", "5:00 PM"]

# TOOL_SCHEMAS
TOOL_SCHEMAS=[
    {
        "type":"function",
        "function":{
            "name":"get_service_price",
            "description":"Fetch price of a service from CRM. ALWAYS call this before quoting any price.",
            "parameters":{
                "type":"object",
                "properties":{
                    "service_name":{"type":"string"},
                    "salon_id":{"type":"string"},
                },
                "required":["service_name","salon_id"],
            },
        },
    },

    {
        "type":"function",
        "function":{
            "name":"check_availability",
            "description":"check available slots for a date and service.",
            "parameters":{
                "type":"object",
                "properties":{
                    "salon_id":{"type":"string"},
                    "date":{"type":"string"},
                    "service_name":{"type":"string"},
                },
                "required":["salon_id","date","service_name"],
            },
        },
    },

    {
        "type":"function",
        "function":{
            "name": "create_booking",
            "description": "create booking. only when you have: name, service, date, time, and phone or email.",
            "parameters":{
                "type":"object",
                "properties":{
                    "salon_id":{"type":"string"},
                    "customer_name":{"type":"string"},
                    "service_name":{"type":"string"},
                    "date":{"type":"string"},
                    "time":{"type":"string"},
                    "phone":{"type":"string"},
                    "email":{"type":"string"},
                },
                "required":["salon_id","customer_name","service_name","date","time"],
            },
        },
    },

    {
        "type":"function",
        "function":{
            "name":"escalate_to_human",
            "description":"Transfer to human. Call when: price not found, customer wants a person, customer is upset, or you are not confident.",
            "parameters":{
                "type":"object",
                "properties": {
                    "reason": {"type":"string"},
                },
                "required":["reason"],
            },
        },
    },
]

# Mock Functions + execute_tool()

def _get_service_price(service_name: str, salon_id: str)-> dict:
    key=service_name.lower().strip()
    service=MOCK_SERVICES.get(key)
    if service:
        return {"found":True, "service_name": service_name, **service}
    return {"found":False, "service_name": service_name, "price": None, "error": "not_found"}

def _check_availability(salon_id: str, date: str, service_name: str)-> dict:
     return {"available":True, "date": date, "slots": MOCK_SLOTS}

def _create_booking(salon_id: str, customer_name: str, service_name: str, date: str, time: str, phone: str = "", email: str = "")-> dict:
    booking_id=f"BK-{str(uuid.uuid4())[:8].upper()}"
    return {
        "success":True,
        "booking_id":booking_id,
        "customer_name": customer_name,
        "service_name": service_name,
        "date": date,
        "time": time,
        "deposit_amount": 30,
        "deposit_link": f"https://yourbookingapp.com/deposit/{booking_id}",
    }

def _escalate_to_human(reason: str)-> dict:
    return {"success": True, "reason":reason}

def execute_tool(tool_name: str, tool_args: dict)-> str:
    tool_map={
        "get_service_price": lambda: _get_service_price(**tool_args),
        "check_availability": lambda: _check_availability(**tool_args),
        "create_booking": lambda: _create_booking(**tool_args),
        "escalate_to_human": lambda: _escalate_to_human(**tool_args),
    }
    executor = tool_map.get(tool_name)
    if not executor:
        return json.dumps({"error":f"Unknown tool: {tool_name}"})
    return json.dumps(executor())