import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL_ID")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHANNEL,
    "text": "🎉 <b>Sheger Football Prediction Channel is officially Connected!</b> 🇪🇹⚽",
    "parse_mode": "HTML",
}

res = requests.post(url, json=payload)
print("Telegram Status Code:", res.status_code)
print("Telegram Response:", res.text)
