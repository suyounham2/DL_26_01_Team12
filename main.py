# main.py

#라이브러리
import cv2
from ultralytics import YOLO
import time
import math
import os
from collections import deque
from core.send_alert import send_discord_alert
from database.db_manager import save_behavior, create_table

from core.filters import KalmanFilter

#파일 시스템 경로
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "behavior_log.csv")

# 임계값 설정
VELOCITY_THRESHOLD = 0.04   # 떨어지는 순간의 Y축 가속도 하향 조정
FALL_ANGLE_LIMIT = 45.0     # 낙상 판단 각도
LIMIT_TIME = 1.0            # 누워있는 유지 시간 (초)
RECOVERY_ANGLE = 65.0       # 회복/복귀 각도

#영상 저장 없이 매 프레임마다 측정 값들 기록
def init_log_file():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            
            f.write("timestamp,status,raw_angle,kalman_angle,shoulder_y_velocity\n")

def save_log(status, raw_angle, kalman_angle, velocity):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{current_time},{status},{raw_angle:.2f},{kalman_angle:.2f},{velocity:.4f}\n")

#어깨, 골반 중심 좌표 / 데이터 산술 평균값과 분산값 실시간 연산
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

#시작 초기화
def main():
    init_log_file()
    create_table()
    
    print("YOLOv8 포즈 모델 로드 중...")
    yolo_pose_model = YOLO("yolov8n-pose.pt")

    kf = KalmanFilter(process_variance=1e-4, measurement_variance=2.5e-2, initial_value=90.0)

    prev_shoulder_y = None
    fall_start_time = None
    is_falling = False

    prev_angle = None
    angle_change = 0

    status_text = "NORMAL"
    alert_sent = False
    fall_angle_triggered = False
    last_saved_status = None

    # 기존 maxlen=30 -> 변경 maxlen=15 (과거 데이터 소멸 주기를 절반으로 단축)
    angle_buffer = deque(maxlen=15)
    velocity_buffer = deque(maxlen=15)

    print("웹캠 하드웨어 초기화 중...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("웹캠을 열 수 없습니다.")
        return

    print("시스템 가동 시작. 종료하려면 'q'를 누르세요.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽어오지 못했습니다.")
            break

        #모니터 좌우 반전
        frame = cv2.flip(frame, 1)

        #일시적 가림 완화
        results = yolo_pose_model.track(
            frame,
            persist=True,
            verbose=False,
            #imgsz=320
        )
        annotated_frame = results[0].plot()

        spine_angle = 90.0
        kalman_angle = 90.0
        y_velocity = 0.0

        #중심점 연산
        if results[0].keypoints is not None and len(results[0].keypoints.xyn) > 0:
            keypoints = results[0].keypoints.xyn[0]

            if len(keypoints) > 12:
                left_shoulder = keypoints[5]
                right_shoulder = keypoints[6]
                left_hip = keypoints[11]
                right_hip = keypoints[12]

                if left_shoulder[1] > 0 and right_shoulder[1] > 0:
                    center_shoulder_x = (left_shoulder[0] + right_shoulder[0]) / 2
                    center_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
                    center_hip_x = (left_hip[0] + right_hip[0]) / 2
                    center_hip_y = (left_hip[1] + right_hip[1]) / 2

                    # 1프레임당 원본 각도 계산
                    spine_angle = calculate_spine_angle(center_shoulder_x, center_shoulder_y,
                                                                        center_hip_x, center_hip_y)

                    kalman_angle = kf.update(spine_angle)

                    if prev_angle is not None:
                        angle_change = abs(kalman_angle - prev_angle)
                    else:
                        angle_change = 0

                    prev_angle = kalman_angle

                    if prev_shoulder_y is not None:
                        #1프레임당 원본 속도 계산
                        y_velocity = center_shoulder_y - prev_shoulder_y

                        #시계열 버퍼에 저장
                        angle_buffer.append(kalman_angle)
                        velocity_buffer.append(y_velocity)

                        #이동 평균, 분산 지표 추출
                        avg_angle = moving_average(angle_buffer)
                        avg_velocity = moving_average(velocity_buffer)
                        angle_var = variance(angle_buffer)
                        velocity_var = variance(velocity_buffer)

                        #print(f"각도:{kalman_angle:.1f}° | 평균속도:{avg_velocity:.4f} | 각도분산:{angle_var:.1f}")

                        #낙하 평균 속도 0.01 / 척추 각도 순간적으로 2.5도 이상 변화
                        if (
                            avg_velocity > 0.01
                            and angle_change > 2.5
                            and not is_falling
                        ):
                            fall_start_time = time.time()
                            is_falling = True
                            fall_angle_triggered = True
                            status_text = "WARNING"
                            print("[ALERT] 가속도 임계값 돌파! WARNING 진입")

                        #위험 상태 이후
                        if is_falling:
                            if (
                                fall_angle_triggered
                                and avg_angle < FALL_ANGLE_LIMIT
                                and abs(avg_velocity) < 0.01
                            ):
                                duration = time.time() - fall_start_time
                                if duration >= LIMIT_TIME:
                                    status_text = "FALL DETECTED"

                                    if not alert_sent:
                                        try:
                                            send_discord_alert()
                                        except: pass
                                        print("디스코드 알림 전송")
                                        alert_sent = True
                            else:
                                if avg_angle > RECOVERY_ANGLE:
                                    is_falling = False
                                    fall_angle_triggered = False
                                    status_text = "NORMAL"
                                    alert_sent = False
                        
                        else:
                            #print(
                                #f"avg_angle={avg_angle:.1f}, "
                                #f"angle_var={angle_var:.1f}, "
                                #f"status={status_text}"
                            #)

                            #65도 초과 normal / 45~65 sitting / 45 이하 lying
                            if avg_angle > RECOVERY_ANGLE:
                                status_text = "NORMAL"

                            elif angle_var < 150.0:
                                if FALL_ANGLE_LIMIT < avg_angle <= RECOVERY_ANGLE:
                                    status_text = "SITTING"

                                #가속도 충격 없이 눕기
                                elif avg_angle <= FALL_ANGLE_LIMIT and avg_velocity <= 0.02:
                                    status_text = "LYING"

                    prev_shoulder_y = center_shoulder_y

                    save_log(status_text, spine_angle, kalman_angle, y_velocity)

                    #데이터베이스 저장
                    if status_text != last_saved_status:
                        try:
                            save_behavior(status_text, kalman_angle)
                        except: pass
                        last_saved_status = status_text

        #그래픽 색상 매핑
        if status_text == "FALL DETECTED": text_color = (0, 0, 255)
        elif status_text == "WARNING": text_color = (0, 165, 255)
        elif status_text == "SITTING": text_color = (255, 255, 0)
        elif status_text == "LYING": text_color = (0, 255, 255)
        else: text_color = (0, 255, 0)

        #모니터 텍스트
        cv2.putText(annotated_frame, f"Status: {status_text}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
        cv2.putText(annotated_frame, f"Spine Angle: {kalman_angle:.1f} deg", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Elderly Behavior Detection System Platform", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
