# config.py

# =========================
# YOLO 설정
# =========================
MODEL_PATH = "models/yolov8n.pt"

# =========================
# 낙상 감지 설정
# =========================
FALL_DURATION = 3  # 3초 이상 낙상 지속 시 알림

# =========================
# Discord Webhook 설정
# =========================
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1510493633009422356/wj5jwcBBS1Jn9MKeSyfPquzHo7Uwoe0CxyWnpnKFZy4hu5MGdrgppp7CKob6gmDVnpLq"

# =========================
# Database 설정
# =========================
DB_PATH = "database/behavior.db"

# =========================
# Log 설정
# =========================
LOG_FILE = "logs/behavior_log.csv"