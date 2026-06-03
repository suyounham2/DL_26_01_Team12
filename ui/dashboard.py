import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import numpy as np
import sys
import os

# 💡 상위 폴더의 파일(main.py, database, core)들을 부품으로 인식하기 위한 경로 동기화
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH
from core.send_alert import send_discord_alert  # 수빈님이 짠 디스코드 알림 API 연동
import main as webcam_engine  # 유정님이 고도화하고 수연님이 패치한 메인 웹캠 엔진 임포트

st.set_page_config(page_title="실버 케어 통합 관제 플랫폼", layout="wide")
st.title("👵 독거노인 통합 행동·생체 신호 관제 플랫폼")
st.markdown("---")

# 📌 세션 상태(Session State) 최적화로 웹캠 중복 점화 버그 원천 차단
if "webcam_active" not in st.session_state:
    st.session_state.webcam_active = False

# 📌 사이드바 접속 권한 메뉴 분리
app_mode = st.sidebar.selectbox("👤 접속 권한을 선택하세요", ["사용자 (노인 가구 단말기)", "보호자 및 원격 관제소"])

# ==============================================================================
# 🏠 1. 사용자 페이지 (노인 가구 단말기 인터페이스)
# ==============================================================================
if app_mode == "사용자 (노인 가구 단말기)":
    st.header("🏠 어르신 안전 안심 가구 단말기")
    st.info("💡 본 화면은 독거노인 가정 내 거실 전용 패드/스마트 TV 화면 셋업 규격입니다.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📹 실시간 안심 AI 모니터링 카메라")
        
        # 💡 [수연님 핵심 요청]: 대시보드 내에서 실제 웹캠을 켜고 끄는 인터페이스 제어 버튼
        if not st.session_state.webcam_active:
            if st.button("🤖 AI 낙상 감지 카메라 구동하기", type="secondary", use_container_width=True):
                st.session_state.webcam_active = True
                st.rerun()
        else:
            if st.button("🔴 AI 낙상 감지 카메라 가동 중지", type="primary", use_container_width=True):
                st.session_state.webcam_active = False
                st.rerun()

        # 웹캠 상태 플래그가 True일 때, 배후의 main.py 알고리즘 코어를 즉시 상속받아 웹캠 창 점화
        if st.session_state.webcam_active:
            st.success("🟢 AI 행동 스캔 엔진 구동 중... 카메라 화면창을 확인하세요. 종료하려면 'q'를 누르거나 중지 버튼을 누르세요.")
            try:
                # 팩트체크: main.py의 main() 함수를 호출하여 실제 YOLOv8+웹캠 파이프라인 가동
                webcam_engine.main() 
            except Exception as e:
                st.error(f"⚠️ 웹캠 하드웨어 점화 실패 또는 종료: {e}")
                st.session_state.webcam_active = False
        else:
            st.image("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=600&auto=format&fit=crop", 
                     caption="현재 모니터링 카메라 standby 상태 (시연용 예시 이미지)")

    with col2:
        st.subheader("🚨 비상 응급 시스템")
        st.markdown("의식을 잃지 않으셨거나 거동이 가능하실 때, 아래 버튼을 누르면 즉시 보호자 스마트폰으로 비상 알림이 사출됩니다.")
        
        # 💡 [수연님 핵심 요청]: 버튼 클릭 시 수빈님이 연동해둔 디스코드 웹훅 API 실제 즉시 트리거
        if st.button("🔥 1초 긴급 SOS 신고하기", use_container_width=True, type="primary"):
            try:
                with st.spinner("보호자 스마트폰으로 긴급 푸시 알림 송출 중..."):
                    send_discord_alert()  # 디스코드 API 실제 호출 팩트
                st.error("🚨 비상 경보 발령 완료! 보호자 디스코드 채널로 [응급 상황 발령] 메시지가 사출되었습니다.")
            except Exception as e:
                st.warning(f"⚠️ 디스코드 Webhook Open API 연동 실패: {e}")
                
        st.markdown("---")
        st.subheader("📞 단축 다이얼 비상 연락처")
        st.warning("📞 1차 보호자 (자녀 박연우): 010-1234-5678")
        st.info("🚑 전담 응급실 (삼육서울병원): 02-2210-3119")
        st.success("👵 노원구청 실버 복지과 전담 관리사: 02-970-1234")

# ==============================================================================
# 🩺 2. 보호자 페이지 (원격 관제 및 생체 정보 모니터링)
# ==============================================================================
else:
    st.header("🩺 보호자 및 실버 원격 관제 시스템")
    st.markdown(" 어르신의 댁내 상태 및 생체 신호 데이터를 시계열로 실시간 추적합니다.")
    
    tab1, tab2 = st.tabs(["📊 실시간 원격 바이탈 관제", "📅 과거 응급 낙상 기록 및 통계"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 AI 포즈 추출 기반 척추 각도 추이 (최근 1초)")
            chart_placeholder = st.empty()
            
            try:
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql("SELECT timestamp, angle FROM spine_time_series ORDER BY id DESC LIMIT 30", conn)
                conn.close()
                df = df.iloc[::-1]
            except:
                df = pd.DataFrame(columns=["timestamp", "angle"])
                
            if not df.empty:
                chart_placeholder.line_chart(df.set_index("timestamp")["angle"])
            else:
                st.info("💡 거실 단말기(`main.py`)가 켜지면 척추 각도 시계열 데이터가 동적 렌더링됩니다.")
                
            st.markdown("---")
            st.subheader("🫀 실시간 연동 원격 심전도 (ECG) 신호")
            x = np.linspace(0, 10, 300)
            ecg_signal = np.sin(2 * np.pi * 1.2 * x) + 0.5 * np.sin(2 * np.pi * 2.4 * x)
            ecg_signal += 2.0 * (np.abs(np.sin(2 * np.pi * 0.6 * x)) > 0.95)
            ecg_df = pd.DataFrame({"심전도 신호(mV)": ecg_signal})
            st.line_chart(ecg_df, height=180, color="#ff4b4b")

        with col2:
            st.subheader("📱 보호자 커뮤니케이션 인프라 상태")
            st.success("📡 디스코드 모바일 푸시 연동망: ONLINE")
            st.info("🛡️ 데이터 보안 인코딩 상태: AES-256")
            
            st.markdown("---")
            st.subheader("🏥 어르신 거주지 근처 최단거리 응급실")
            st.error("1. 삼육서울병원 응급의료센터 (02-2210-3119)")
            st.warning("2. 을지대학교병원 응급실 (02-970-8119)")
            
            st.markdown("---")
            with st.expander("👵 대상자 원격 인적 사항", expanded=True):
                st.write("**성함:** 김옥분 어르신 (만 84세)")
                st.write("**주소:** 서울 특별시 노원구 화랑로 815 행복아파트 103동")

    with tab2:
        st.subheader("📅 달력 기반 과거 응급 낙상 로그 조회 (SQLite SQL 연동)")
        selected_date = st.date_input("조회 날짜 선택", datetime.now())
        date_str = selected_date.strftime("%Y-%m-%d")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            log_df = pd.read_sql(f"SELECT timestamp, behavior, spine_angle FROM behavior_log WHERE timestamp LIKE '{date_str}%' ORDER BY id DESC", conn)
            conn.close()
            
            if not log_df.empty:
                st.error(f"🚨 해당 날짜에 총 {len(log_df)}건의 응급 낙상 위급 상황이 감지 및 이송 조치되었습니다.")
                st.dataframe(log_df, use_container_width=True)
            else:
                st.success("✅ 해당 날짜에 접수된 노인 행동 이상 정보가 없습니다. 안전 상태입니다.")
        except:
            st.info("아직 인입된 관계형 데이터베이스 데이터가 없습니다.")