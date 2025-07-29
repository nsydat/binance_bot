# utils/telegram.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message, image_path=None):
    if not TOKEN or not CHAT_ID:
        return

    # Gửi tin nhắn
    msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(msg_url, data={'chat_id': CHAT_ID, 'text': message})

    # Gửi ảnh (nếu có)
    if image_path and os.path.exists(image_path):
        img_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(image_path, 'rb') as f:
            requests.post(img_url, data={'chat_id': CHAT_ID}, files={'photo': f})