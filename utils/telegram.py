#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram utility for sending trading signals
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message, image_path=None):
    """Gửi tin nhắn và ảnh qua Telegram"""
    if not TOKEN or not CHAT_ID:
        print("⚠️ Thiếu TELEGRAM_TOKEN hoặc TELEGRAM_CHAT_ID")
        return

    try:
        # Gửi tin nhắn
        msg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        response = requests.post(msg_url, data={
            'chat_id': CHAT_ID, 
            'text': message,
            'parse_mode': 'Markdown'
        })
        
        if response.status_code != 200:
            print(f"⚠️ Lỗi gửi Telegram: {response.text}")
            return

        # Gửi ảnh (nếu có)
        if image_path and os.path.exists(image_path):
            img_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            with open(image_path, 'rb') as f:
                response = requests.post(img_url, data={'chat_id': CHAT_ID}, files={'photo': f})
                
            if response.status_code != 200:
                print(f"⚠️ Lỗi gửi ảnh Telegram: {response.text}")
                
    except Exception as e:
        print(f"⚠️ Lỗi Telegram: {e}")