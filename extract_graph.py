# extract_graph.py
import os
import pandas as pd
import matplotlib.pyplot as plt

LOG_FILE = os.path.join("logs", "behavior_log.csv")
OUTPUT_IMAGE = "kalman_comparison.png"

def generate_comparison_chart():
    if not os.path.exists(LOG_FILE):
        print(f"❌ [에러] {LOG_FILE} 파일이 없습니다. 먼저 logs 폴더의 behavior_log.csv를 완전히 삭제하고 main.py를 재가동하세요.")
        return

    try:
        df = pd.read_csv(LOG_FILE, encoding="utf-8")
        
        if df.empty:
            print("❌ [알림] 로그 파일이 비어 있습니다.")
            return
            
        # PPT 가독성이 가장 훌륭한 최신 120 프레임 구간 슬라이싱 추출
        plot_df = df.tail(120).copy()
        
        # 정량적 데이터 정적 분산 노이즈 감쇄 성능 계산 팩트
        raw_var = plot_df['raw_angle'].var()
        kalman_var = plot_df['kalman_angle'].var()
        reduction = ((raw_var - kalman_var) / raw_var) * 100 if raw_var > 0 else 0
        
        print("\n📊 ==================================================")
        print("📈 [수연님 졸작 PPT 제출용 정량 지표 데이터 보고서]")
        print(f"   - 보정 전 원본 각도 분산 (Raw Variance)  : {raw_var:.4f}")
        print(f"   - 보정 후 칼만 각도 분산 (Clean Variance): {kalman_var:.4f}")
        print(f"   - ⚡ 하드웨어 지터링 오차율 정밀 감쇄율     : {reduction:.1f}%")
        print("====================================================\n")

        # 고해상도 300 DPI 매트플롯 레이어 가동
        plt.figure(figsize=(10, 4.5), dpi=300)
        
        # 🔴 보정 전 튀는 라인 (빨간색 투명 대시선)
        plt.plot(plot_df['raw_angle'].values, label=f'Raw Spine Angle (Noise Var: {raw_var:.2f})', 
                 color='#F43F5E', linestyle='--', alpha=0.5, linewidth=1.5)
        
        # 🟢 보정 후 부드러운 정품 라인 (초록색 실선)
        plt.plot(plot_df['kalman_angle'].values, label=f'Kalman Filtered Angle (Clean Var: {kalman_var:.2f})', 
                 color='#10B981', linestyle='-', alpha=1.0, linewidth=2.5)
        
        plt.title('Real-time Jittering Noise Optimization (Kalman Filter Integration)', fontsize=12, fontweight='bold', pad=12)
        plt.xlabel('Time Frames (30fps Stream)', fontsize=9, labelpad=8)
        plt.ylabel('Spine Angle (Degree)', fontsize=9, labelpad=8)
        plt.grid(True, linestyle=':', alpha=0.5)
        plt.legend(loc='upper right', fontsize=9, frameon=True, shadow=True)
        
        plt.tight_layout()
        plt.savefig(OUTPUT_IMAGE)
        plt.close()
        
        print(f"🎯 [성공] PPT용 슬라이드 오버랩 차트 '{OUTPUT_IMAGE}' 저장 마감 완료.")
        
    except Exception as e:
        print(f"❌ [에러] 지표 렌더링 파이프라인 결함: {e}")

if __name__ == "__main__":
    generate_comparison_chart()