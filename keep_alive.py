import time
import requests

BOT_URL = "https://bulk-thumb.onrender.com"  # Replace with your Render bot URL

while True:
    try:
        response = requests.get(BOT_URL)
        print(f"Keep-alive ping sent. Status: {response.status_code}")
    except Exception as e:
        print(f"Keep-alive failed: {e}")

    time.sleep(300)  # Ping every 5 minutes
