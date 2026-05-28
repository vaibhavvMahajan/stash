import os, json, subprocess
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

TOOLS = [
    {"type": "function", "function": {"name": "add_bookmark",
     "description": "Save a bookmark. Always call this when user wants to save a URL.",
     "parameters": {"type": "object", "properties": {
         "url": {"type": "string"}, "title": {"type": "string"},
         "tags": {"type": "string"}, "notes": {"type": "string"}},
     "required": ["url"]}}},
    {"type": "function", "function": {"name": "list_bookmarks",
     "description": "List all bookmarks for the user.",
     "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "search_bookmarks",
     "description": "Search bookmarks by keyword or tag.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "delete_bookmark",
     "description": "Delete a bookmark by ID.",
     "parameters": {"type": "object", "properties": {
         "bookmark_id": {"type": "integer"}}, "required": ["bookmark_id"]}}},
]

def call_mcp(tool_name: str, args: dict, user_id: int) -> str:
    args = args or {}  # guard against None
    args["user_id"] = user_id
    proc = subprocess.run(
        ["python", "mcp_server/server.py"],
        input=json.dumps({"tool": tool_name, "arguments": args}),
        capture_output=True, text=True, timeout=10,
    )
    print("MCP stdout:", repr(proc.stdout))   # <-- add this
    return proc.stdout.strip() or "Done"

def chat(messages: list, user_id: int) -> str:
    msgs = [
        {"role": "system", "content": "You are Stash, a bookmark manager AI. You MUST use tools whenever the user wants to save, list, search, or delete bookmarks. Never refuse to save a URL."}
    ] + list(messages)

    for _ in range(5):
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=msgs,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        msgs.append(msg)

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")  # guard against empty
            result = call_mcp(tc.function.name, args, user_id)

    return "Tool call limit reached."