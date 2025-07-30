# dashboard/app.py
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime

app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# Dữ liệu toàn cục
bot_status = {
    "is_running": True,
    "last_signal": None,
    "total_signals": 0,
    "signals_last_hour": 0,
    "uptime": "00:00:00",
    "config": {
        "symbol": "DOGEUSDT",
        "interval": "5m",
        "active_strategies": ["EMA_VWAP", "RSI_DIVERGENCE", "SUPERTREND_ATR"]
    },
    "log": []
}

def log(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    entry = f"[{timestamp}] {message}"
    bot_status['log'].append(entry)
    bot_status['log'] = bot_status['log'][-100:]
    # Gửi log realtime
    socketio.emit('log_update', {'log': entry})

# API: Trả về trạng thái
@app.route('/status')
def get_status():
    return bot_status

# Socket: Gửi cập nhật realtime
def emit_update():
    socketio.emit('status_update', bot_status)

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('status_update', bot_status)

@socketio.on('stop_bot')
def handle_stop():
    bot_status['is_running'] = False
    log("🛑 Bot đã bị dừng từ dashboard")
    emit_update()

@socketio.on('start_bot')
def handle_start():
    bot_status['is_running'] = True
    log("✅ Bot đã được bật từ dashboard")
    emit_update()

@socketio.on('update_config')
def handle_config(data):
    bot_status['config'].update(data)
    log(f"⚙️ Cấu hình đã cập nhật: {data}")
    emit_update()

@app.route('/')
def index():
    return render_template('index.html')