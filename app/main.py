from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .database import init_db
from . import auth
from .chat import chat

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup(): init_db()

def get_user(request: Request):
    return request.cookies.get("user_id")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    uid = get_user(request)
    if not uid: return RedirectResponse("/login")
    return templates.TemplateResponse(request, "chat.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html")

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_page(request: Request):
    return templates.TemplateResponse(request, "forgot.html")

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_page(request: Request):
    return templates.TemplateResponse(request, "reset.html")

@app.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    uid = auth.signup(email, password)
    r = RedirectResponse("/", status_code=302)
    r.set_cookie("user_id", str(uid), httponly=True)
    return r

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    uid = auth.login(email, password)
    if not uid: return RedirectResponse("/login?error=1", status_code=302)
    r = RedirectResponse("/", status_code=302)
    r.set_cookie("user_id", str(uid), httponly=True)
    return r

@app.post("/api/chat")
async def api_chat(request: Request):
    uid = get_user(request)
    if not uid: return {"error": "Not authenticated"}
    body = await request.json()
    messages = body.get("messages", [])
    reply = chat(messages, int(uid))
    return {"reply": reply}

@app.get("/logout")
async def logout():
    r = RedirectResponse("/login")
    r.delete_cookie("user_id")
    return r

@app.post("/forgot-password")
async def forgot_password(email: str = Form(...)):
    auth.create_reset_token(email)
    return RedirectResponse("/login?reset=sent", status_code=302)

@app.post("/reset-password")
async def reset_password(token: str = Form(...), password: str = Form(...)):
    ok = auth.reset_password(token, password)
    return RedirectResponse("/login?reset=done" if ok else "/login?reset=fail", status_code=302)