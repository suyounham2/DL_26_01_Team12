# test_alert.py
import requests
import sys
import os

# 💡 상위 폴더 및 config 인식을 위한 경로 동기화
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import DISCORD_WEBHOOK_URL

def send_discord_alert():
    data = {
        "content": "🚨 [테스트 발령] FALL DETECTED! 수연님이 대시보드 연동 테스트 중입니다."
    }

    # config.py에 적힌 DISCORD_WEBHOOK_URL 주소로 실제 요청 사출
    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json=data
    )

    print("====================================")
    print("디스코드 오픈 Open API 전송 결과 리포트")
    print("====================================")
    print("응답 상태 코드(Status Code):", response.status_code)
    
    if response.status_code == 204 or response.status_code == 200:
        print("🟢 팩트체크: 전송 성공! 디스코드 채널 알림을 확인하세요.")
    else:
        print("🔴 팩트체크: 전송 실패. config.py의 WEBHOOK_URL 주소를 확인하세요.")
    print("====================================")

# 파일이 실행될 때 함수를 강제로 즉시 트리거
if __name__ == "__main__":
    send_discord_alert()