# ElderBehaviorSystem

복합 데이터 행동 분석 기반 독거노인 실시간 응급 낙상 감지 시스템입니다.

## Overview

본 시스템은 웹캠 환경에서 독거노인의 생활 행동 패턴을 실시간 모니터링하고 응급 낙상 상황을 방어하기 위한 앱입니다.

YOLOv8-Pose 모델을 활용하여 신체 관절 좌표를 추출하고, 척추 각도 및 Y축 신체 이동 속도를 분석하여 낙상 상태를 자동 판정합니다. 응급 상황 발생 시 비상 알림을 전송하며, 로그 분석 결과는 Stramlit 대시보드를 통해 확인할 수 있습니다.

## Features

* YOLOv8-Pose 기반 실시간 관절 추적
* 척추 각도 및 신체 이동 속도 분석
* Kalman Filter 기반 노이즈 제거
* 5단계 행동 상태 분류
  (NORMAL, SITTING, LYING, WARNING, FALL DETECTED)
* SQLite 데이터베이스 저장
* Discord 실시간 알림 전송
* Streamlit 모니터링 대시보드

## Architecture

```text
Webcam Input
      ↓
YOLOv8-Pose
      ↓
관절 좌표 추출
      ↓
척추 각도 및 이동 속도 계산
      ↓
행동 상태 분류
      ↓
SQLite 저장
      ↓
Discord 알림 / Streamlit Dashboard
```

본 시스템은 웹캠 영상을 입력받아 YOLOv8-Pose를 통해 관절 좌표를 추출하고,
척추 각도와 신체 이동 속도를 계산하여 사용자의 상태를 판단합니다.

판단된 상태는 SQLite 데이터베이스에 저장되며,
Streamlit 대시보드에서 실시간으로 확인할 수 있습니다.

또한 FALL DETECTED 상태가 감지되면 Discord Webhook API를 통해 보호자에게 즉시 알림을 전송합니다.

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
* Python
* YOLOv8-Pose
* OpenCV
* Streamlit
* SQLite3
* Discord Webhook API

## How to Run
### 1. 저장소 클론

```bash
git clone https://github.com/사용자명/ElderBehaviorSystem.git
cd ElderBehaviorSystem
```

### 2. 필요한 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 3. 낙상 감지 시스템 실행

```bash
python main.py
```

### 4. 대시보드 실행

```bash
streamlit run ui/dashboard.py
```

### 실행 환경

- Python 3.10 이상
- 웹캠 연결 필수
- Discord Webhook URL 설정 필요

낙상(FALL DETECTED) 상태가 감지되면 Discord 알림이 자동으로 전송됩니다.
