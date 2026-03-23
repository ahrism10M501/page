# 딥러닝과 신경망

딥러닝은 머신러닝의 하위 분야로, 여러 층의 신경망을 통해 복잡한 패턴을 학습합니다.

## 퍼셉트론부터 딥러닝까지

단일 퍼셉트론은 선형 분리 가능한 문제만 풀 수 있습니다. 여러 층을 쌓은 MLP(Multi-Layer Perceptron)는 비선형 문제를 해결합니다.

## 역전파 알고리즘

신경망 학습의 핵심. 출력 오차를 체인룰(chain rule)로 역방향으로 전파해 각 가중치의 기울기를 계산합니다.

```python
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.layers(x)

model = SimpleNet()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
```

## 활성화 함수

| 함수 | 특징 | 주요 사용처 |
|------|------|------------|
| ReLU | 기울기 소실 완화 | 은닉층 |
| Sigmoid | 출력 0~1 | 이진 분류 출력 |
| Softmax | 다중 클래스 확률 | 다중 분류 출력 |
| GELU | Transformer 계열 | 언어 모델 |

## 과적합 방지 기법

- **Dropout**: 학습 시 랜덤하게 뉴런 비활성화
- **Batch Normalization**: 각 레이어 입력을 정규화
- **Weight Decay (L2 정규화)**: 큰 가중치에 패널티

```python
class RegularizedNet(nn.Module):
    def __init__(self, dropout=0.3):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(784, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 10)
        )
```

## PyTorch vs TensorFlow

두 프레임워크 모두 강력하지만, 연구에서는 PyTorch의 동적 그래프가 디버깅이 용이해 선호됩니다. 프로덕션 배포는 TensorFlow/Keras의 생태계가 강점입니다.
