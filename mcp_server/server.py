from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio, os, json
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])
server = Server("stash-mcp")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(name="add_bookmark", description="Save a bookmark",
            inputSchema={"type":"object","properties":{
                "user_id":{"type":"integer"},
                "url":{"type":"string"},
                "title":{"type":"string"},
                "tags":{"type":"string"},
                "notes":{"type":"string"}
            },"required":["user_id","url"]}),
        types.Tool(name="list_bookmarks", description="List user bookmarks",
            inputSchema={"type":"object","properties":{
                "user_id":{"type":"integer"}},"required":["user_id"]}),
        types.Tool(name="search_bookmarks", description="Search bookmarks",
            inputSchema={"type":"object","properties":{
                "user_id":{"type":"integer"},
                "query":{"type":"string"}},"required":["user_id","query"]}),
        types.Tool(name="delete_bookmark", description="Delete a bookmark",
            inputSchema={"type":"object","properties":{
                "user_id":{"type":"integer"},
                "bookmark_id":{"type":"integer"}},"required":["user_id","bookmark_id"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    uid = arguments["user_id"]  # always scoped!
    with engine.connect() as conn:
        if name == "add_bookmark":
            conn.execute(text(
                "INSERT INTO bookmarks (user_id,url,title,tags,notes) VALUES (:u,:url,:t,:tg,:n)"),
                {"u":uid,"url":arguments["url"],"t":arguments.get("title",""),
                 "tg":arguments.get("tags",""),"n":arguments.get("notes","")})
            conn.commit()
            return [types.TextContent(type="text", text="Bookmark saved.")]
        
        elif name == "list_bookmarks":
            rows = conn.execute(text(
                "SELECT id,url,title,tags,notes,created_at FROM bookmarks WHERE user_id=:u ORDER BY created_at DESC"),
                {"u":uid}).fetchall()
            return [types.TextContent(type="text", text=json.dumps([dict(r._mapping) for r in rows], default=str))]
        
        elif name == "search_bookmarks":
            q = f"%{arguments['query']}%"
            rows = conn.execute(text(
                "SELECT id,url,title,tags,notes FROM bookmarks WHERE user_id=:u AND (url ILIKE :q OR title ILIKE :q OR tags ILIKE :q OR notes ILIKE :q)"),
                {"u":uid,"q":q}).fetchall()
            return [types.TextContent(type="text", text=json.dumps([dict(r._mapping) for r in rows], default=str))]
        
        elif name == "delete_bookmark":
            conn.execute(text(
                "DELETE FROM bookmarks WHERE id=:id AND user_id=:u"),  # scoped!
                {"id":arguments["bookmark_id"],"u":uid})
            conn.commit()
            return [types.TextContent(type="text", text="Deleted.")]

if _name_ == "_main_":
    asyncio.run(stdio_server(server))