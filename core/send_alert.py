import requests
from config import DISCORD_WEBHOOK_URL


def send_discord_alert():

    data = {
        "content": "🚨 FALL DETECTED! 낙상이 감지되었습니다."
    }

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=data
    )

    print("전송 상태:", response.status_code)
