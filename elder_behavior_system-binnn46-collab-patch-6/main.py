import cv2
from ultralytics import YOLO
import time
import math
import os
from collections import deque
from core.send_alert import send_discord_alert
from database.db_manager import save_behavior, save_time_series

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "behavior_log.csv")

# 📊 [물리 임계값 최적화 선언] 구조적 충돌을 방지하는 정밀 가이드라인
VELOCITY_THRESHOLD = 0.018   # 낙하 충격으로 인정할 순간 Y축 하강 속도
FALL_ANGLE_LIMIT = 45.0     # 완전 수평 상태 인정 각도
LIMIT_TIME = 2.5            # 낙상 확정 전 대기 검증 시간 (초)
RECOVERY_ANGLE = 65.0       # 정상 상태 복귀 각도

def init_log_file():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("timestamp,status,spine_angle,shoulder_y_velocity\n")

def save_log(status, angle, velocity):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{current_time},{status},{angle:.2f},{velocity:.4f}\n")

def calculate_spine_angle(sx, sy, hx, hy):
    dx = abs(hx - sx)
    dy = abs(hy - sy)
    if dx == 0:
        return 90.0
    return math.degrees(math.atan(dy / dx))

def moving_average(buffer):
    return sum(buffer) / len(buffer) if buffer else 0.0

def variance(buffer):
    mean = moving_average(buffer)
    return sum((x - mean) ** 2 for x in buffer) / len(buffer) if buffer else 0.0

def main():
    init_log_file()
    
    print("⏳ YOLOv8 포즈 추적 신경망 로드 중...")
    yolo_pose_model = YOLO("models/yolov8n-pose.pt")

    prev_shoulder_y = None
    fall_start_time = None
    is_falling = False
    status_text = "NORMAL"
    alert_sent = False

    angle_buffer = deque(maxlen=30)
    velocity_buffer = deque(maxlen=30)

    print("⏳ 비디오 캡처 레이어 디바이스 점화 중...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return

    print("🚀 실시간 행동 양식 관제 파이프라인 가동. 시스템 종료: 'q'")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        results = yolo_pose_model(frame, verbose=False)
        annotated_frame = results[0].plot()

        if results[0].keypoints is None or len(results[0].keypoints.xyn) == 0:
            cv2.imshow("Elderly Behavior Detection System Platform", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            continue

        keypoints = results[0].keypoints.xyn[0]

        if len(keypoints) > 12:
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            left_hip = keypoints[11]
            right_hip = keypoints[12]

            if left_shoulder[1] > 0 and right_shoulder[1] > 0 and left_hip[1] > 0 and right_hip[1] > 0:
                center_shoulder_x = (left_shoulder[0] + right_shoulder[0]) / 2
                center_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
                center_hip_x = (left_hip[0] + right_hip[0]) / 2
                center_hip_y = (left_hip[1] + right_hip[1]) / 2

                spine_angle = calculate_spine_angle(center_shoulder_x, center_shoulder_y, center_hip_x, center_hip_y)
                y_velocity = center_shoulder_y - prev_shoulder_y if prev_shoulder_y is not None else 0.0

                angle_buffer.append(spine_angle)
                velocity_buffer.append(y_velocity)

                avg_angle = float(moving_average(angle_buffer))
                avg_velocity = float(moving_average(velocity_buffer))
                angle_var = float(variance(angle_buffer))
                velocity_var = float(variance(velocity_buffer))

                try:
                    save_time_series(avg_angle, avg_velocity, angle_var, velocity_var)
                except:
                    pass

                # ------------------------------------------------------------------
                # ⚙️ 구조 혁신 상태 머신 Core (WARNING vs LYING 모순 해결)
                # ------------------------------------------------------------------
                
                # STEP 1: 고속 하강 이벤트 발생 시 위험 추적(is_falling) 강제 온
                if (y_velocity > VELOCITY_THRESHOLD or avg_velocity > 0.012) and status_text != "FALL DETECTED":
                    if not is_falling:
                        fall_start_time = time.time()
                        is_falling = True
                        status_text = "WARNING"
                        print("🚨 [초동 감지] 급격한 자유낙하 가속도 감지 ➡️ WARNING")

                # STEP 2: 실시간 상태 전이 분기 가이드라인
                if status_text == "FALL DETECTED":
                    # 낙상 확정 상태에서는 일어서기 전까지 낙상 유지
                    if avg_angle > RECOVERY_ANGLE:
                        status_text = "NORMAL"
                        is_falling = False
                        alert_sent = False
                
                elif is_falling:
                    # WARNING 상태에서 바닥 안착 여부 검증
                    if avg_angle < FALL_ANGLE_LIMIT:
                        # 💡 핵심 패치: 쿵 떨어졌으나 정지해 있다면 낙상 진행, 계속 움직임이 크다면 충격 노이즈 혹은 정상 눕기로 필터링
                        if abs(avg_velocity) < 0.025:
                            duration = time.time() - fall_start_time
                            if duration >= LIMIT_TIME:
                                status_text = "FALL DETECTED"
                        else:
                            # 누웠으나 각도 분산이 안정적이고 가속도가 빠지지 않는다면 LYING 상태로 완화 유도
                            if angle_var < 15.0:
                                status_text = "LYING"
                                is_falling = False
                    else:
                        # 떨어지는 도중 다시 몸을 추스르고 일어난 경우
                        if avg_angle > RECOVERY_ANGLE:
                            status_text = "NORMAL"
                            is_falling = False
                
                else:
                    # STEP 3: 정적/평시 상태 분류 (가속도 충격이 없는 일상적인 움직임)
                    if angle_var < 20.0:
                        if avg_angle > RECOVERY_ANGLE:
                            status_text = "NORMAL"
                        elif FALL_ANGLE_LIMIT < avg_angle <= RECOVERY_ANGLE:
                            status_text = "SITTING"
                        elif avg_angle <= FALL_ANGLE_LIMIT:
                            status_text = "LYING"

                prev_shoulder_y = center_shoulder_y
                try:
                    save_log(status_text, spine_angle, y_velocity)
                except:
                    pass

        # UI 가시성 컬러 매핑
        if status_text == "FALL DETECTED": text_color = (0, 0, 255)
        elif status_text == "WARNING": text_color = (0, 165, 255)
        elif status_text == "SITTING": text_color = (255, 255, 0)
        elif status_text == "LYING": text_color = (0, 255, 255)
        else: text_color = (0, 255, 0)

        cv2.putText(annotated_frame, f"Status: {status_text}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
        cv2.putText(annotated_frame, f"Spine Angle: {spine_angle:.1f} deg", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Elderly Behavior Detection System Platform", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty("Elderly Behavior Detection System Platform", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()