import os, json, subprocess
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

TOOLS = [
    {"name": "add_bookmark", "description": "Save a bookmark for the user",
     "parameters": {"type": "object", "properties": {
         "url": {"type": "string"}, "title": {"type": "string"},
         "tags": {"type": "string"}, "notes": {"type": "string"}},
     "required": ["url"]}},
    {"name": "list_bookmarks", "description": "List user bookmarks",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "search_bookmarks", "description": "Search bookmarks by keyword",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": ["query"]}},
    {"name": "delete_bookmark", "description": "Delete a bookmark by ID",
     "parameters": {"type": "object", "properties": {
         "bookmark_id": {"type": "integer"}}, "required": ["bookmark_id"]}},
]

def call_mcp(tool_name: str, args: dict, user_id: int) -> str:
    args["user_id"] = user_id
    proc = subprocess.run(
        ["python", "mcp_server/server.py"],
        input=json.dumps({"tool": tool_name, "arguments": args}),
        capture_output=True, text=True, timeout=10
    )
    return proc.stdout or "Done"

def chat(messages: list, user_id: int) -> str:
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=[{"function_declarations": TOOLS}]
    )
    
    # Convert messages to Gemini format
    history = []
    for m in messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})
    
    convo = model.start_chat(history=history)
    
    hops = 0
    last_message = messages[-1]["content"]
    
    while hops < 5:
        response = convo.send_message(last_message)
        part = response.candidates[0].content.parts[0]
        
        if hasattr(part, "function_call") and part.function_call.name:
            fc = part.function_call
            args = dict(fc.args)
            result = call_mcp(fc.name, args, user_id)
            last_message = result
            hops += 1
        else:
            return part.text
    
    return "Tool call limit reached."