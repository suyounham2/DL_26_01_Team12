# core/filters.py

class KalmanFilter:
    def __init__(self, process_variance=1e-5, measurement_variance=1e-1, estimated_error=1.0, initial_value=90.0):
        """
        초기 물리 상수 영점 조절
        - process_variance: 시스템 자체 변동성 (낮을수록 부드러워짐)
        - measurement_variance: 웹캠의 측정 노이즈 크기 (높을수록 노이즈를 세게 필터링)
        """
        self.q = process_variance
        self.r = measurement_variance
        self.p = estimated_error
        self.x = initial_value
        self.k = 0.0

    def update(self, measurement):
        """매 프레임 들어오는 튀는 좌표를 수학적으로 예측 및 평활화"""
        # 1. 예측 업데이트 (Prediction Update)
        self.p = self.p + self.q

        # 2. 칼만 이득 연산 (Kalman Gain)
        self.k = self.p / (self.p + self.r)

        # 3. 현재 최적 추정치 보정 (Measurement Update)
        self.x = self.x + self.k * (measurement - self.x)

        # 4. 오차 공분산 업데이트
        self.p = (1.0 - self.k) * self.p

        return self.x