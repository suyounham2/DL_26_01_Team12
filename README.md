# ElderBehaviorSystem

AI Pose Estimation 기반 독거노인 실시간 라이프케어 및 응급 낙상 감지 플랫폼입니다.

## Overview

본 시스템은 저가형 단말 및 웹캠 환경에서 독거노인의 거동을 실시간 모니터링하고 응급 낙상 상황을 방어하기 위한 앱입니다.

YOLOv8-Pose 모델로 관절 좌표를 추출하고, 칼만필터 알고리즘을 통해 픽셀 노이즈를 정밀 감쇄하여 척추 각도 및 Y축 속도 기반으로 상태를 자동 판정하고 비상 경보를 사출합니다.

## Features

* YOLOv8-Pose 기반 실시간 17개 신체 키포인트 추적
* 칼만필터(Kalman Filter) 기반 픽셀 지터링 노이즈 제거
* 삼각함수(Arctangent) 기반 기하학적 척추 각도 산출
* Y축 변동 평균 속도 및 시간축 검증 기반 이중 낙상 판정
* SQLite3 데이터베이스 연동 상태 전이 트래킹 및 이력 적재
* Discord Webhook API 연동 관제소 실시간 푸시 알림

## Architecture

```text
elder_behavior_system/
  core/           # filters.py (Kalman Filter), send_alert.py (Discord API)
  ui/             # dashboard.py (Streamlit Web Dashboard)

  database/       # db_manager.py (SQLite3 integration)
```

본 시스템은 기능별 도메인이 격리된 모듈화 아키텍처로 구성됩니다.

core는 AI 관절 좌표 슬라이싱과 칼만필터 연산 및 경보 사출을 담당하고, ui는 관제사를 위한 대시보드 웹 어플리케이션을 담당합니다. 데이터베이스 계층은 database/db_manager에서 전담 관리하여 전체 프로세스 간의 데이터 구조를 일관되게 유지합니다.

##Tech Stack
* YOLOv8-Pose
* Kalman Filter
* Streamlit
* SQLite3
* Python
