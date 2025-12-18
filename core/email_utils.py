import smtplib
import os
import random
import time
from email.mime.text import MIMEText
from email.header import Header

# 内存中存储验证码: { "email": { "code": "123456", "expires": timestamp } }
_VERIFICATION_STORE = {}

def clean_expired_codes():
    """清理过期验证码"""
    now = time.time()
    expired = [email for email, data in _VERIFICATION_STORE.items() if now > data['expires']]
    for email in expired:
        del _VERIFICATION_STORE[email]

def generate_and_store_code(email: str) -> str:
    """生成6位验证码并存储，有效期5分钟"""
    clean_expired_codes()
    code = str(random.randint(100000, 999999))
    _VERIFICATION_STORE[email] = {
        "code": code,
        "expires": time.time() + 300  # 5分钟有效期
    }
    return code

def verify_code(email: str, code: str) -> bool:
    """验证验证码是否正确且未过期"""
    clean_expired_codes()
    data = _VERIFICATION_STORE.get(email)
    if not data:
        return False
    if data['code'] == code:
        del _VERIFICATION_STORE[email] # 验证成功后立即失效
        return True
    return False

def send_verification_email(to_email: str) -> bool:
    """发送验证邮件"""
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT", "465")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not all([smtp_server, smtp_user, smtp_password]):
        print("[-] SMTP configuration missing")
        return False

    code = generate_and_store_code(to_email)
    
    content = f"您的 MegaCite 注册验证码是：{code}，有效期 5 分钟。"
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = smtp_user
    message['To'] = to_email
    message['Subject'] = Header("MegaCite 注册验证码", 'utf-8')

    try:
        if smtp_port == "465":
            server = smtplib.SMTP_SSL(smtp_server, 465)
        else:
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], message.as_string())
        server.quit()
        print(f"[+] Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[-] Failed to send email: {e}")
        return False