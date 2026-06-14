# ElderBehaviorSystem
복합 데이터 행동 분석 기반 독거노인 실시간 응급 낙상 감지 시스템입니다.

## Overview
본 시스템은 웹캠 환경에서 독거노인의 생활 행동 패턴을 실시간 모니터링하고 응급 낙상 상황에 신속하게 대응하기 위한 앱입니다.

YOLOv8-Pose 모델을 활용하여 신체 관절 좌표를 추출하고, 척추 각도 및 Y축 신체 이동 속도를 분석하여 낙상 상태를 자동 판정합니다. FALL DETECTED 상태 감지 시 비상 알림을 전송하며, 로그 분석 결과는 Streamlit 대시보드를 통해 확인할 수 있습니다.

## Features
* YOLOv8-Pose 기반 실시간 신체 관절 좌표 추출
* 척추 각도 및 신체 이동 속도 분석
* Kalman Filter 기반 노이즈 제거
* 행동 상태 라벨 분류 (NORMAL, SITTING, LYING, WARNING, FALL DETECTED)
* SQLite3 데이터베이스 저장
* Discord 실시간 알림 전송
* Streamlit 모니터링 대시보드

## Architecture
```text
Webcam 입력
      ↓
관절 좌표 추출
      ↓
척추 각도 및 이동 속도 계산
      ↓
행동 상태 판단
      ↓
SQLite 로그 저장
      ↓
Discord 알림 / Streamlit Dashboard
```

## Project Structure
```text
elder_behavior_system/
  core/
    filters.py          # Kalman Filter 기반 좌표 노이즈 필터링
    send_alert.py       # Discord API 알림 전송

  database/
    db_manager.py       # SQLite3 데이터베이스 관리

  models/
    yolov8n-pose.pt     # YOLOv8 가중치 파일

  ui/
    dashboard.py        # Streamlit 기반 실시간 대시보드

  .gitignore            
  README.md             # 프로젝트 개요
  config.py             # 시스템 전역 설정
  extract_graph.py      # 칼만 필터 적용 전후 비교 지표
  main.py               # 전체 프로세스 실행
```

## Tech Stack
* Python 3.10
* YOLOv8-Pose
* OpenCV
* Streamlit
* SQLite3
* Discord Webhook API

## How to Run
### 1. 필요한 라이브러리 설치
```bash
pip install opencv-python ultralytics streamlit
```

### 2. 낙상 감지 시스템 실행
```bash
python main.py
```

### 3. 대시보드 실행
```bash
streamlit run ui/dashboard.py
```

### 실행 환경
- Python 3.10
- 웹캠 연결
- Discord Webhook API URL 연결
