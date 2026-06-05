import sqlite3
from datetime import datetime
from config import DB_PATH

def connect_db():
    return sqlite3.connect(DB_PATH)

def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    # 1. [기존 인프라 유지] 최종 낙상 이벤트 발생 시 기록할 사건 기록 테이블
    # main.py의 호출 규격(상태 텍스트, 정제된 각도)에 맞추어 컬럼 명칭을 공학적으로 동기화
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS behavior_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        behavior TEXT,
        spine_angle REAL
    )
    """)

    # 2. 🔥 [수연님 대시보드 전용 신규 인프라] 실시간 초당 30프레임 시계열 원시 데이터 누적 테이블
    # 매초 출렁이는 각도, 속도, 분산 지표를 적재하여 실시간 꺾은선 그래프(st.line_chart)의 소스로 활용
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spine_time_series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        angle REAL,
        velocity REAL,
        angle_var REAL,
        velocity_var REAL
    )
    """)

    conn.commit()
    conn.close()

def save_behavior(behavior, spine_angle):
    """최종 낙상 확정(FALL DETECTED) 시 디스코드 알림과 동시에 단 1회 호출되는 사건 적재 함수"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO behavior_log (timestamp, behavior, spine_angle)
    VALUES (?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        behavior,
        spine_angle
    ))

    conn.commit()
    conn.close()

def save_time_series(angle, velocity, angle_var, velocity_var):
    """💡 [수연님 요청 반영]: 웹캠이 구동되는 동안 초당 30번씩 시계열 통계 수치를 논스톱 누적하는 함수"""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO spine_time_series (timestamp, angle, velocity, angle_var, velocity_var)
    VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # 밀리초(ms) 단위까지 정밀 기록하여 시계열 순서 보장
        angle,
        velocity,
        angle_var,
        velocity_var
    ))

    conn.commit()
    conn.close()

# 파일이 최초로 로드되거나 임포트될 때 가동에 필요한 테이블들을 안전하게 자동 자동 생성
create_table()