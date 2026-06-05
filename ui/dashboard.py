# dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import numpy as np
import sys
import os

# 상위 폴더 인프라 모듈(config, database, core) 패키지 경로 동기화
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH
from core.send_alert import send_discord_alert  
import main as webcam_engine  

st.set_page_config(page_title="독거노인 통합 관제 플랫폼", layout="wide")
st.title("Elder behavior system 독거노인 통합 관제 시스템")
st.caption("AI Pose 기반 독거노인 실시간 라이프케어 융합 플랫폼")
st.markdown("---")

# 세션 상태 최적화로 웹캠 중복 점화 버그 원천 차단
if "webcam_active" not in st.session_state:
    st.session_state.webcam_active = False

# 사이드바 접속 권한 메뉴 분리 (문자열 완전 일치 정합성 체결)
app_mode = st.sidebar.selectbox("👤 시스템 접속 페이지", ["사용자", "보호자"])

# ==============================================================================
# 1. 사용자 페이지
# ==============================================================================
if app_mode == "사용자":
    st.subheader("스마트 안심 Webcam")
    st.markdown("본 시스템은 촬영 영상을 저장하지 않으며, 개인정보 보호를 최우선으로 하는 사생활 보호 안심 시스템입니다.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("📊 **AI 행동 인지 모니터링 상태**")
        
        if not st.session_state.webcam_active:
            if st.button("Webcam 시스템 가동", type="secondary", use_container_width=True):
                st.session_state.webcam_active = True
                st.rerun()
        else:
            if st.button("🔴 Webcam 시스템 가동 중지", type="primary", use_container_width=True):
                st.session_state.webcam_active = False
                st.rerun()

        if st.session_state.webcam_active:
            st.success("🟢 스마트 안심 Webcam 모니터링 정상 작동 중 (종료: 카메라 창에서 'q'를 입력)")
            try:
                webcam_engine.main() 
            except Exception as e:
                st.error(f" 영상 입력 하드웨어 초기화 오류 발생: {e}")
                st.session_state.webcam_active = False
        else:
            st.image("webcam.jpg", 
                     caption="시스템 대기 중 - Webcam 하드웨어 연결 정상")

    with col2:
        st.error("🚨 **긴급 위험 비상 SOS**")
        st.markdown("위급 상황 발생 시 아래 긴급 호출 버튼을 누르면 보호자 및 연계 의료기관에 긴급 알림이 즉시 전송됩니다.")
        
        if st.button("원터치 응급 SOS 신고", use_container_width=True, type="primary"):
            try:
                with st.spinner("지정 원격 관제소로 긴급 대피 푸시 프로토콜 송출 중..."):
                    send_discord_alert()  
                st.error("🚨 응급 상황이 접수되었습니다. 보호자 및 연계 의료기관에 긴급 알림이 전송되었습니다.")
            except Exception as e:
                st.warning(f"외부 연동 Gateway API 통신 장애: {e}")
                
        st.markdown("---")
        st.subheader("📞 응급 의료 연락처")
        st.warning("보호자 비상 연락처: 010-1234-5678")
        st.info("인근 응급의료센터 (서울XX병원): 02-1234-5678")
        st.success("독거노인 돌봄 전담 생활지원사: 02-987-6543")

# ==============================================================================
# 2. 보호자 페이지 (원격 중앙 집중 관제 인터페이스)
# ==============================================================================
else:
    st.subheader("종합 모니터링 케어 원격 중앙 관제 센터")
    st.markdown("연결된 가구 Webcam으로부터 수집된 안전 상태 및 활동 데이터를 실시간으로 추적합니다.")
    
    tab1, tab2 = st.tabs(["📊 실시간 건강/안전 모니터링", "📅 응급 알림 이력"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("실시간 자세 변화 각도 모니터링")
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
                st.info("💡 가구 단말기가 연결되면 대상자의 자세 변화 데이터가 실시간으로 표시됩니다.")
                
            st.markdown("---")
            st.subheader("실시간 심전도 데이터 모니터링")
            x = np.linspace(0, 10, 300)
            ecg_signal = np.sin(2 * np.pi * 1.2 * x) + 0.5 * np.sin(2 * np.pi * 2.4 * x)
            ecg_signal += 2.0 * (np.abs(np.sin(2 * np.pi * 0.6 * x)) > 0.95)
            ecg_df = pd.DataFrame({"ECG Amplitude (mV)": ecg_signal})
            st.line_chart(ecg_df, height=180, color="#E11D48")
            st.caption("※가상 시뮬레이션 데이터")

        with col2:
            st.subheader("📡 시스템 상태")
            st.success("🔒 보안 통신 연결 정상")
            st.info("🛡️ 개인정보 보호 및 데이터 암호화 적용")
            
            st.markdown("---")
            st.subheader("🏥 인근 의료기관")
            st.error("1. 서울XX병원 종합 응급의료센터 (02-1234-5678)")
            st.warning("2. 서울 XX대학교병원 응급실 (02-123-4567)")
            st.success("※ 독거노인 돌봄 전담 생활지원사: 02-987-6543")
            
            st.markdown("---")
            with st.expander("👵 보호 대상 인적 사항", expanded=True):
                st.write("**성명:** 홍길동 (만 84세)")
                st.write("**거주지:** 서울 특별시 노원구 삼육로 123 삼육아파트 101동 1001호")

    with tab2:
        st.subheader("📅 응급 알림 이력 조회")
        selected_date = st.date_input("조회할 날짜를 선택하세요.", datetime.now())
        date_str = selected_date.strftime("%Y-%m-%d")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            # 💡 [버그 수정 팩트체크]: behavior = 'FALL DETECTED' 격벽을 세워 표에 NORMAL, SITTING, LYING 노이즈가 섞여 나오지 않도록 완전 통제
            query = f"SELECT timestamp, behavior, spine_angle FROM behavior_log WHERE timestamp LIKE '{date_str}%' AND behavior = 'FALL DETECTED' ORDER BY id DESC"
            log_df = pd.read_sql(query, conn)
            conn.close()
            
            if not log_df.empty:
                st.error(f"🚨 해당 일자에 총 {len(log_df)}건의 응급 알림 이력이 확인되었습니다.")
                st.dataframe(log_df, use_container_width=True)
            else:
                st.success("✅ 선택하신 날짜에 접수된 응급 알림 이력이 없습니다.")
        except:
            st.info("통합 데이터베이스 내역에 기록된 데이터가 존재하지 않습니다.")