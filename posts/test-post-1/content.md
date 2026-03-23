# 머신러닝 기초

머신러닝은 명시적으로 프로그래밍하지 않아도 데이터로부터 패턴을 학습하는 기술입니다.

## 세 가지 학습 패러다임

### 지도학습 (Supervised Learning)

레이블이 있는 데이터로 학습. 입력 → 정답 쌍을 반복적으로 보여주어 예측 함수를 학습합니다.

- **분류(Classification)**: 스팸 메일 판별, 이미지 인식
- **회귀(Regression)**: 주가 예측, 부동산 가격 추정

```python
from sklearn.linear_model import LinearRegression
import numpy as np

X = np.array([[1], [2], [3], [4], [5]])
y = np.array([2, 4, 6, 8, 10])

model = LinearRegression()
model.fit(X, y)
print(model.predict([[6]]))  # [12.]
```

### 비지도학습 (Unsupervised Learning)

레이블 없이 데이터 구조를 스스로 파악합니다. 군집화, 차원 축소가 대표적입니다.

```python
from sklearn.cluster import KMeans

X = np.random.randn(100, 2)
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(X)
print(kmeans.labels_[:10])
```

### 강화학습 (Reinforcement Learning)

에이전트가 환경과 상호작용하며 보상을 최대화하는 정책을 학습합니다. 게임 AI, 로봇 제어에 활용됩니다.

## 모델 평가

과적합(Overfitting)을 피하려면 훈련/검증/테스트 세트를 분리해야 합니다.

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
```

## 정리

머신러닝의 핵심은 데이터 품질과 적절한 알고리즘 선택입니다. 모델 복잡도와 일반화 능력 사이의 균형을 항상 고려해야 합니다.
