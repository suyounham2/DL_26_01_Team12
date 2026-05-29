import cv2
from ultralytics import YOLO
import time
import math
import os
from collections import deque

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "behavior_log.csv")

# 임계값
VELOCITY_THRESHOLD = 0.08   # 낙하 속도 기준
FALL_ANGLE_LIMIT = 45.0     # 낙상 판단 각도
LIMIT_TIME = 3.0            # 누워있는 유지 시간
RECOVERY_ANGLE = 65.0       # 회복/복귀 각도

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
    yolo_pose_model = YOLO("yolov8n-pose.pt")

    prev_shoulder_y = None
    fall_start_time = None
    is_falling = False
    status_text = "NORMAL"

    # 시계열 버퍼
    angle_buffer = deque(maxlen=30)
    velocity_buffer = deque(maxlen=30)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다.")
        return

    print("YOLOv8 Pose 기반 시스템 가동 시작. 종료하려면 'q'를 누르세요.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽어오지 못했습니다.")
            break

        results = yolo_pose_model(frame, verbose=False)
        annotated_frame = results[0].plot()

        spine_angle = 90.0
        y_velocity = 0.0

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

                    spine_angle = calculate_spine_angle(center_shoulder_x, center_shoulder_y,
                                                        center_hip_x, center_hip_y)

                    if prev_shoulder_y is not None:
                        y_velocity = center_shoulder_y - prev_shoulder_y

                        # 버퍼에 값 저장
                        angle_buffer.append(spine_angle)
                        velocity_buffer.append(y_velocity)

                        # 평균값/분산 계산
                        avg_angle = moving_average(angle_buffer)
                        avg_velocity = moving_average(velocity_buffer)
                        angle_var = variance(angle_buffer)
                        velocity_var = variance(velocity_buffer)

                        # 노이즈 필터링
                        if angle_var < 0.1 and velocity_var < 0.005:

                            # STEP1: 가속도 판별
                            if avg_velocity > VELOCITY_THRESHOLD and not is_falling:
                                fall_start_time = time.time()
                                is_falling = True
                                status_text = "WARNING"

                            # STEP2: 각도, 지속 시간 판별 + 상태 머신
                            if is_falling:
                                if avg_angle < FALL_ANGLE_LIMIT and abs(avg_velocity) < 0.02:
                                    duration = time.time() - fall_start_time
                                    if duration >= LIMIT_TIME:
                                        status_text = "FALL DETECTED"
                                else:
                                    if avg_angle > RECOVERY_ANGLE:
                                        is_falling = False
                                        status_text = "NORMAL"
                            else:
                                # 상태 머신 확장
                                if avg_angle > RECOVERY_ANGLE:
                                    status_text = "NORMAL"
                                elif FALL_ANGLE_LIMIT < avg_angle <= RECOVERY_ANGLE:
                                    status_text = "SITTING"
                                elif avg_angle <= FALL_ANGLE_LIMIT:
                                    status_text = "LYING"

                        save_log(status_text, spine_angle, y_velocity)
                        prev_shoulder_y = center_shoulder_y

        # 상태별 색상 표시
        if status_text == "FALL DETECTED":
            text_color = (0, 0, 255)
        elif status_text == "WARNING":
            text_color = (0, 165, 255)
        elif status_text == "SITTING":
            text_color = (255, 255, 0)
        elif status_text == "LYING":
            text_color = (0, 255, 255)
        else:
            text_color = (0, 255, 0)

        cv2.putText(annotated_frame, f"Status: {status_text}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
        cv2.putText(annotated_frame, f"Spine Angle: {spine_angle:.1f} deg", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Elderly Behavior Detection System Platform", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
