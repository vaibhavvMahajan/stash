import bcrypt, secrets
from datetime import datetime, timedelta
from sqlalchemy import text
from .database import engine
from .mailer import send_welcome_email, send_reset_email

def signup(email: str, password: str):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with engine.connect() as conn:
        result = conn.execute(text(
            "INSERT INTO users (email,password_hash) VALUES (:e,:p) RETURNING id"),
            {"e":email,"p":hashed})
        conn.commit()
        user_id = result.fetchone()[0]
    send_welcome_email(email)
    return user_id

def login(email: str, password: str):
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT id,password_hash FROM users WHERE email=:e"),{"e":email}).fetchone()
    if not row: return None
    if bcrypt.checkpw(password.encode(), row.password_hash.encode()):
        return row.id
    return None

def create_reset_token(email: str):
    with engine.connect() as conn:
        user = conn.execute(text("SELECT id FROM users WHERE email=:e"),{"e":email}).fetchone()
        if not user: return
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        conn.execute(text(
            "INSERT INTO password_reset_tokens (user_id,token,expires_at) VALUES (:u,:t,:e)"),
            {"u":user.id,"t":token,"e":expires})
        conn.commit()
    send_reset_email(email, token)

def reset_password(token: str, new_password: str) -> bool:
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT user_id FROM password_reset_tokens WHERE token=:t AND expires_at>NOW() AND used=FALSE"),
            {"t":token}).fetchone()
        if not row: return False
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        conn.execute(text("UPDATE users SET password_hash=:p WHERE id=:u"),
            {"p":hashed,"u":row.user_id})
        conn.execute(text("UPDATE password_reset_tokens SET used=TRUE WHERE token=:t"),{"t":token})
        conn.commit()
    return True