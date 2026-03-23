# OpenCV로 시작하는 컴퓨터 비전

OpenCV는 실시간 이미지/영상 처리를 위한 오픈소스 라이브러리입니다. C++로 작성되었지만 Python 바인딩이 강력합니다.

## 설치 및 기본 입출력

```bash
pip install opencv-python-headless  # GUI 없는 서버 환경
pip install opencv-python           # GUI 포함
```

```python
import cv2
import numpy as np

# 이미지 읽기 (BGR 순서!)
img = cv2.imread('photo.jpg')
print(img.shape)  # (height, width, channels)

# BGR → RGB 변환 (matplotlib 표시용)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# 저장
cv2.imwrite('output.jpg', img)
```

## 이미지 전처리

### 리사이즈와 크롭

```python
# 리사이즈
resized = cv2.resize(img, (640, 480))
# 비율 유지
h, w = img.shape[:2]
scale = 640 / w
resized = cv2.resize(img, (640, int(h * scale)))

# 크롭 — NumPy 슬라이싱
roi = img[100:300, 50:250]  # [y1:y2, x1:x2]
```

### 색상 공간 변환

```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# HSV로 색상 범위 마스킹 (빨간 물체 감지 예시)
lower_red = np.array([0, 120, 70])
upper_red = np.array([10, 255, 255])
mask = cv2.inRange(hsv, lower_red, upper_red)
```

## 엣지 검출

```python
# Canny 엣지
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blurred, threshold1=50, threshold2=150)
```

## 윤곽선(Contour) 찾기

```python
contours, hierarchy = cv2.findContours(
    edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)

# 면적으로 필터링
large_contours = [c for c in contours if cv2.contourArea(c) > 1000]

# 그리기
output = img.copy()
cv2.drawContours(output, large_contours, -1, (0, 255, 0), 2)
```

## 영상에서 실시간 처리

```python
cap = cv2.VideoCapture(0)  # 웹캠 (파일 경로도 가능)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 프레임 처리
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    cv2.imshow('Edges', edges)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## 딥러닝 모델 연동

OpenCV DNN 모듈로 ONNX 모델을 직접 실행할 수 있습니다.

```python
net = cv2.dnn.readNetFromONNX('model.onnx')

blob = cv2.dnn.blobFromImage(
    img, scalefactor=1/255.0, size=(640, 640), swapRB=True
)
net.setInput(blob)
outputs = net.forward()
```

PyTorch에서 학습한 모델을 ONNX로 내보내면 OpenCV에서 바로 추론 가능합니다. GPU 의존성 없이 경량 배포할 때 유용합니다.
