import resend, os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ["RESEND_API_KEY"]
SENDER = "onboarding@resend.dev"

def send_welcome_email(to: str):
    resend.Emails.send({"from": SENDER, "to": to,
        "subject": "Welcome to Stash!",
        "html": "<h1>Welcome to Stash 🔖</h1><p>Start saving bookmarks with your AI co-pilot.</p>"})

def send_reset_email(to: str, token: str):
    base = os.environ.get("BASE_URL", "http://localhost:8000")
    link = f"{base}/reset-password?token={token}"
    resend.Emails.send({"from": SENDER, "to": to,
        "subject": "Reset your Stash password",
        "html": f"<p>Click to reset (valid 1 hour): <a href='{link}'>{link}</a></p>"})