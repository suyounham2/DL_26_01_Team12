import cv2
from ultralytics import YOLO
import time
import math
import os
from collections import deque
from core.send_alert import send_discord_alert
from database.db_manager import save_behavior

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "behavior_log.csv")

# 임계값 설정 (현실적인 웹캠 픽셀 좌표계 기준 반영)
VELOCITY_THRESHOLD = 0.02   # 쾅 떨어지는 순간의 Y축 가속도 하향 조정 (포착력 극대화)
FALL_ANGLE_LIMIT = 45.0     # 낙상 판단 각도
LIMIT_TIME = 3.0            # 누워있는 유지 시간 (초)
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
    
    print("⏳ YOLOv8 포즈 모델 로드 중...")
    yolo_pose_model = YOLO("yolov8n-pose.pt")

    prev_shoulder_y = None
    fall_start_time = None
    is_falling = False
    status_text = "NORMAL"
    alert_sent = False

    # 시계열 버퍼 (최근 1초치 데이터 저축 공간)
    angle_buffer = deque(maxlen=30)
    velocity_buffer = deque(maxlen=30)

    # 윈도우 드라이버 호환성을 위해 백엔드 설정 강제 추가
    print("⏳ 웹캠 하드웨어 초기화 중...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다.")
        return

    print("🚀 시스템 가동 시작. 종료하려면 'q'를 누르세요.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽어오지 못했습니다.")
            break

        # 실시간 관제 모니터링을 위한 좌우 반전
        frame = cv2.flip(frame, 1)

       #일시적 가림 및 조도 변화 환경에서의 추적 안정성 향상(persist=True 옵션 활용하여 동일 인물의 객체 ID 유지)
        results = yolo_pose_model.track(
            frame,
            persist=True,
            verbose=False
)
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

                # 키포인트 유효성 검사 및 중심점 연산
                if left_shoulder[1] > 0 and right_shoulder[1] > 0:
                    center_shoulder_x = (left_shoulder[0] + right_shoulder[0]) / 2
                    center_shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2
                    center_hip_x = (left_hip[0] + right_hip[0]) / 2
                    center_hip_y = (left_hip[1] + right_hip[1]) / 2

                    # 1프레임당 원본 각도 계산
                    spine_angle = calculate_spine_angle(center_shoulder_x, center_shoulder_y,
                                                        center_hip_x, center_hip_y)

                    if prev_shoulder_y is not None:
                        # 1프레임당 원본 속도 계산
                        y_velocity = center_shoulder_y - prev_shoulder_y

                        # 시계열 버퍼에 실시간 적재
                        angle_buffer.append(spine_angle)
                        velocity_buffer.append(y_velocity)

                        # 이동 평균 및 분산 지표 추출
                        avg_angle = moving_average(angle_buffer)
                        avg_velocity = moving_average(velocity_buffer)
                        angle_var = variance(angle_buffer)
                        velocity_var = variance(velocity_buffer)

                        # 실시간 수치 모니터링용 터미널 프린트
                        print(f"📊 각도:{spine_angle:.1f}° | 평균속도:{avg_velocity:.4f} | 각도분산:{angle_var:.1f}")

                        # ------------------------------------------------------------------
                        # 🔥 [대수술 완료된 고도화 판정 로직 인터페이스]
                        # ------------------------------------------------------------------
                        
                        # 💡 가속도 판별(STEP 1)은 거대한 분산 수치에 막히지 않도록 필터 바깥에서 생으로 잡습니다.
                        if avg_velocity > VELOCITY_THRESHOLD and not is_falling:
                            fall_start_time = time.time()
                            is_falling = True
                            status_text = "WARNING"
                            print("🚨 [ALERT] 가속도 임계값 돌파! WARNING 진입")

                        # STEP 2: 위험 징후 감지 후 지속 시간 및 각도 검증
                        if is_falling:
                            # 넘어지는 와중에는 데이터가 튀므로, 오직 바닥 충돌 후 '가로 각도'와 '정지 상태(속도 안정)'만 체크합니다.
                            if avg_angle < FALL_ANGLE_LIMIT and abs(avg_velocity) < 0.01:
                                duration = time.time() - fall_start_time
                                if duration >= LIMIT_TIME:
                                    status_text = "FALL DETECTED"

                                    if not alert_sent:
                                        send_discord_alert()

                                        save_behavior(
                                            status_text,
                                            spine_angle
                                        )
                                        print("📱 디스코드 알림 전송")
                                        alert_sent = True
                            else:
                                # 완전히 몸을 세워 다시 일어났을 때만 낙상 추적 해제
                                if avg_angle > RECOVERY_ANGLE:
                                    is_falling = False
                                    status_text = "NORMAL"
                                    alert_sent = False
                        
                        else:
                            # 💡 분산 필터(노이즈 방어)는 평온하게 가만히 움직이는 일상 상태를 나눌 때만 가두어 작동시킵니다.
                            if angle_var < 15.0:
                                if avg_angle > RECOVERY_ANGLE:
                                    status_text = "NORMAL"
                                elif FALL_ANGLE_LIMIT < avg_angle <= RECOVERY_ANGLE:
                                    status_text = "SITTING"
                                elif avg_angle <= FALL_ANGLE_LIMIT:
                                    status_text = "LYING"

                    # 매 프레임 좌표 동기화와 로그 저장은 끊김이 없도록 최하단 샌드박스에 배치합니다.
                    prev_shoulder_y = center_shoulder_y
                    save_log(status_text, spine_angle, y_velocity)
                    
                    

        # 상태별 가시성 확보를 위한 UI 색상 맵핑
        if status_text == "FALL DETECTED":
            text_color = (0, 0, 255)      # 위험 상황: 빨간색
        elif status_text == "WARNING":
            text_color = (0, 165, 255)    # 낙하 감지: 주황색
        elif status_text == "SITTING":
            text_color = (255, 255, 0)    # 일상 행동: 하늘색
        elif status_text == "LYING":
            text_color = (0, 255, 255)    # 안정한 누움: 노란색
        else:
            text_color = (0, 255, 0)      # 평시 보행: 초록색

        # 모니터 렌더링 텍스트 출력
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
