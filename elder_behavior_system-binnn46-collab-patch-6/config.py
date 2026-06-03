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
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1511747328304873624/ibfespMBWzrqJ_Pq5YzQNiPnd-arjNFTKb-M3lCEmuEBrMc_dbRLCrU3eWCzLGggZBfD"

# =========================
# Database 설정
# =========================
DB_PATH = "database/behavior.db"

# =========================
# Log 설정
# =========================
LOG_FILE = "logs/behavior_log.csv"
