import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def send_telegram_message(chat_id: int, text: str):
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM SEND ERROR: TELEGRAM_BOT_TOKEN is missing")
        return {"ok": False, "error": "missing_token"}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        print("TELEGRAM SEND STATUS:", resp.status_code)
        print("TELEGRAM SEND RESPONSE:", resp.text)
        return {"ok": resp.ok, "status_code": resp.status_code, "body": resp.text}
    except Exception as e:
        print("TELEGRAM SEND EXCEPTION:", repr(e))
        return {"ok": False, "error": repr(e)}