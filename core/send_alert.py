import requests
from config import DISCORD_WEBHOOK_URL


def send_discord_alert():

    data = {
        "content": "🚨 보호 대상자에게서 낙상 의심 상황이 감지되었습니다. 즉시 상태를 확인해주세요."
    }

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=data
    )

    print("전송 상태:", response.status_code)
