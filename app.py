from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import smtplib
import random
from datetime import datetime
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

app = Flask(__name__)

# ================= BASIC CONFIG =================
YOUR_WEB_APP_NAME = os.getenv("WEBAPPNAME", "xyzapp")
CURRENT_YEAR = str(datetime.now().year)   # MUST be string
TEMPLATE_PATH = os.getcwd()  + "\\Templates\\template1.html"
REMOVE_WATERMARK = False

# ================= API KEYS =================
VALID_API_KEYS = {
    "sk-apinow-tbfgenrated1": {"user": "demo"},
    "sk-apinow-tbfgenratedpro": {"user": "pro"}
}

def verify_api_key(key: str):
    return VALID_API_KEYS.get(key)

# ================= AUTH DECORATOR =================
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")

        if not auth.startswith("Bearer "):
            return jsonify({
                "error": {
                    "message": "Missing API key",
                    "type": "authentication_error"
                }
            }), 401

        api_key = auth.replace("Bearer ", "").strip()
        key_data = verify_api_key(api_key)

        if not key_data:
            return jsonify({
                "error": {
                    "message": "Invalid API key",
                    "type": "authentication_error"
                }
            }), 401

        request.api_user = key_data["user"]
        return f(*args, **kwargs)

    return decorated

# ================= RATE LIMIT =================
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per hour"]
)

# ================= SMTP CONFIG =================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", GMAIL_EMAIL)

# ================= SECURITY CONFIG =================
OTP_EXPIRY_SECONDS = 300
MAX_ATTEMPTS = 5
LOCK_TIME = 600
RESEND_COOLDOWN = 60

IP_MAX_ATTEMPTS = 10
IP_BLOCK_TIME = 60

# ================= STORES (IN-MEMORY) =================
otp_store = {}
ip_store = {}

# ================= HTML TEMPLATE =================
def load_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

def apply_template_changes(template: str) -> str:
    template = template.replace("{{APP_NAME}}", YOUR_WEB_APP_NAME)
    template = template.replace("{{YEAR}}", CURRENT_YEAR)

    if REMOVE_WATERMARK:
        template = template.replace(
            "MailOTP Guard — made with ❤️ by TechBitForge",
            ""
        )

    return template  # ❗ FIX: missing return

HTML_TEMPLATE = apply_template_changes(load_template(TEMPLATE_PATH))

# ================= IP BLOCK SYSTEM =================
def is_ip_blocked(ip):
    record = ip_store.get(ip)
    if not record:
        return False

    if time.time() > record["blocked_until"]:
        ip_store.pop(ip)
        return False

    return True

def register_ip_failure(ip):
    now = time.time()
    record = ip_store.setdefault(ip, {
        "attempts": 0,
        "blocked_until": 0
    })

    record["attempts"] += 1
    if record["attempts"] >= IP_MAX_ATTEMPTS:
        record["blocked_until"] = now + IP_BLOCK_TIME

# ================= SEND EMAIL =================
def send_email(email, otp):
    html = HTML_TEMPLATE.replace("{{OTP_CODE}}", otp)

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = email
    msg["Subject"] = f"{YOUR_WEB_APP_NAME} OTP Verification"
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(GMAIL_EMAIL, APP_PASSWORD)
        server.send_message(msg)

# ================= SEND OTP =================
@app.route("/send-otp", methods=["POST"])
@require_api_key
@limiter.limit("5 per minute")
def send_otp():
    ip = request.remote_addr

    if is_ip_blocked(ip):
        return jsonify({"error": "IP blocked for 1 minute"}), 429

    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        register_ip_failure(ip)
        return jsonify({"error": "Email required"}), 400

    now = time.time()
    otp = str(random.randint(100000, 999999))

    otp_store[email] = {
        "otp": otp,
        "expires": now + OTP_EXPIRY_SECONDS,
        "attempts": 0,
        "locked_until": 0,
        "last_sent": now
    }

    try:
        send_email(email, otp)
        return jsonify({"message": "OTP sent successfully"})
    except Exception as e:
        register_ip_failure(ip)
        return jsonify({"error": "Failed to send email"}), 500

# ================= RESEND OTP =================
@app.route("/resend-otp", methods=["POST"])
@require_api_key
@limiter.limit("3 per minute")
def resend_otp():
    ip = request.remote_addr

    if is_ip_blocked(ip):
        return jsonify({"error": "IP blocked for 1 minute"}), 429

    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        register_ip_failure(ip)
        return jsonify({"error": "Email required"}), 400

    record = otp_store.get(email)
    if not record:
        return jsonify({"error": "OTP not requested"}), 400

    now = time.time()

    if record["locked_until"] > now:
        return jsonify({"error": "Account locked"}), 429

    if now - record["last_sent"] < RESEND_COOLDOWN:
        return jsonify({
            "error": "Please wait before resending OTP",
            "retry_after": int(RESEND_COOLDOWN - (now - record["last_sent"]))
        }), 429

    otp = str(random.randint(100000, 999999))

    record.update({
        "otp": otp,
        "expires": now + OTP_EXPIRY_SECONDS,
        "attempts": 0,
        "last_sent": now
    })

    try:
        send_email(email, otp)
        return jsonify({"message": "OTP resent successfully"})
    except Exception:
        register_ip_failure(ip)
        return jsonify({"error": "Failed to resend OTP"}), 500

# ================= VERIFY OTP =================
@app.route("/verify-otp", methods=["POST"])
@require_api_key
@limiter.limit("10 per minute")
def verify_otp():
    ip = request.remote_addr

    if is_ip_blocked(ip):
        return jsonify({"error": "IP blocked for 1 minute"}), 429

    data = request.get_json(silent=True) or {}
    email = data.get("email")
    user_otp = data.get("otp")

    if not email or not user_otp:
        register_ip_failure(ip)
        return jsonify({"error": "Missing fields"}), 400

    record = otp_store.get(email)
    if not record:
        register_ip_failure(ip)
        return jsonify({"error": "OTP not found"}), 400

    now = time.time()

    if record["locked_until"] > now:
        return jsonify({"error": "Account locked"}), 429

    if now > record["expires"]:
        otp_store.pop(email)
        return jsonify({"error": "OTP expired"}), 400

    if record["otp"] != user_otp:
        record["attempts"] += 1
        register_ip_failure(ip)

        if record["attempts"] >= MAX_ATTEMPTS:
            record["locked_until"] = now + LOCK_TIME
            return jsonify({"error": "Account locked for 10 minutes"}), 429

        return jsonify({
            "error": "Invalid OTP",
            "remaining_attempts": MAX_ATTEMPTS - record["attempts"]
        }), 400

    otp_store.pop(email)
    return jsonify({"message": "OTP verified successfully"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
