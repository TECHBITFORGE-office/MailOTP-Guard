# 🔐 MailOTP Guard

A **secure, lightning-fast OTP-based email authentication system** built with Flask. Perfect for protecting your apps while keeping things smooth for your users.  

---

## 🚀 Features
- ✉️ **Email OTP Login** – Simple, secure, password-free access.  
- 🎨 **HTML Email Templates** – Beautiful OTP emails that actually look professional.  
- ⏱️ **OTP Expiry** – OTPs expire in 5 minutes to stay extra secure.  
- 🔄 **Resend OTP Cooldown** – No spamming allowed!  
- 🛡️ **Brute-force Protection** – Blocks attackers before they can break in.  
- 🚫 **Temporary IP Blocking** – Blocks suspicious IPs for 1 minute.  
- 🔑 **Environment-based Secrets** – Keep your credentials safe.  
- ☁️ **Cloudflare / Cloud Email Support** – Professional email handling made easy.  

---

## 🧱 Tech Stack
- Python 🐍  
- Flask ⚡  
- SMTP (Gmail) 📧  
- dotenv 🌿  

---

## 📦 Installation

### Windows
1. Install Git: [https://git-scm.com/download/win](https://git-scm.com/download/win)  
2. Run the `.exe` and follow the prompts.

### Linux Distros

**Ubuntu / Debian / Linux Mint**
```bash
sudo apt update
sudo apt install git -y
```
**Fedora**
```bash
sudo dnf install git -y
```
**CentOS / RHEL**
```bash
sudo yum install git -y
# For CentOS 8 / RHEL 8+
sudo dnf install git -y
```
**Arch Linux / Manjaro**
```bash
sudo pacman -Sy git
```
**openSUSE**
```bash
sudo zypper install git -y
```
### Check your Git installation:
```bash
git --version
```
### Clone the repo and install dependencies:
```bash
git clone https://github.com/TECHBITFORGE-office/MailOTP-Guard.git
cd EmailOTP-Auth-Service
pip install flask Flask-Limiter python-dotenv
```
### 🔑 Environment Variables

Edit your `.env` file:
```bash
GMAIL_EMAIL=yourgmail@gmail.com
APP_PASSWORD=your_app_password
FROM_EMAIL=your_business_mail
WEBAPPNAME= YOUR_WEB_APP_NAME
```
### 📬 How to Get a Free Business Email
You can create a professional-style email with Cloudflare Email Routing:
1. Go to Cloudflare Dashboard and add your domain (e.g., xyz.com).

2. Enable Email Routing in your domain settings.

3. Create a custom email (like login@xyz.com) and forward it to your Gmail.

4. Use this as your FROM_EMAIL in `.env`.

5. Congrats! You now have a free business email to send OTPs. 🎉

### ▶ Run Server
```bash
python app.py
```
Server runs at http://localhost:5000

## 📡 API Endpoints

1. Send OTP – `POST /send-otp`
2. Resend OTP – `POST /resend-otp`
3. Verify OTP –`POST /verify-otp`

## 🛡️ Security Highlights

1. OTP expires in 5 minutes ⏱️
2. IP blocking after multiple failed attempts 🚫
3. Automatic unblock after 1 minute 🔓
4. In-memory storage (upgrade to Redis in production)

## ⚠️ Production Notes

1. Swap in Redis for scalable storage
2. Always use HTTPS
3. Consider putting behind Cloudflare / reverse proxy for extra protection

### MailOTP Guard makes authentication safe, fast, and professional — all without sacrificing simplicity. 💌

