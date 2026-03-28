import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# 1. 다크 테마 설정 (가장 먼저)
# ==========================================
plt.style.use('dark_background')

# 공통 matplotlib 설정
plt.rcParams.update({
    'font.family': 'sans-serif',
    'axes.unicode_minus': False,
    'font.size': 11,
    'axes.labelcolor': 'white',
    'text.color': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'axes.edgecolor': '#666666',
    'grid.color': '#444444',
    'grid.alpha': 0.25,
    'legend.facecolor': '#1a1a1a',
    'legend.edgecolor': '#666666',
    'legend.labelcolor': 'white',
})

# ==========================================
# 2. 색상 및 설정 정의
# ==========================================
C_RED = '#FF3333'
C_MAGENTA = '#FF00FF'
C_DEEPBLUE = '#1F51FF'
C_GRID = '#444444'
BG_COLOR = '#0d0d0d'

FOLDER_NAME = "nn_distortion_steps"

# 저장할 폴더 생성
if not os.path.exists(FOLDER_NAME):
    os.makedirs(FOLDER_NAME)

# ==========================================
# 3. 기본 데이터 및 함수 정의
# ==========================================
x_range = np.linspace(-3, 3, 200)

def sigmoid(x):
    """Sigmoid 활성화 함수"""
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))  # 오버플로우 방지

def setup_ax(ax, title, xlabel="Input (x)", ylabel="Output"):
    """다크 테마 축 설정 함수"""
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='white')
    ax.set_xlabel(xlabel, fontsize=11, color='white')
    ax.set_ylabel(ylabel, fontsize=11, color='white')
    
    ax.grid(True, color=C_GRID, linestyle='--', linewidth=0.5, alpha=0.25)
    ax.set_xlim(-3, 3)
    
    # 축 테두리 스타일
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#666666')
    ax.spines['bottom'].set_color('#666666')
    
    # 틱 스타일
    ax.tick_params(colors='white', labelsize=10)

def save_fig(step_num, title):
    """다크 테마 맞춤 저장 함수"""
    fig = plt.gcf()
    fig.patch.set_facecolor(BG_COLOR)
    
    filename = f"{FOLDER_NAME}/step_{step_num}_{title.lower().replace(' ', '_')}.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=150, facecolor=BG_COLOR, edgecolor='none', bbox_inches='tight')
    print(f"✓ 이미지 저장: {filename}")
    plt.close()

# ==============================================================================
# STEP 1: 입력 신호 시각화 (Input Layer)
# 직선 신호 y = 2x + 3
# ==============================================================================
print("📊 Step 1 생성 중...")
fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor(BG_COLOR)

y_input = 2 * x_range + 3
ax.plot(x_range, y_input, color=C_DEEPBLUE, linewidth=3.5, label='Input Signal: y = 2x + 3', zorder=2)

setup_ax(ax, "Step 1: Input Linear Signal", ylabel="y = 2x + 3")
ax.set_ylim(-4, 10)
ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
ax.fill_between(x_range, y_input, alpha=0.1, color=C_DEEPBLUE)

save_fig(1, "input_signal")


# ==============================================================================
# STEP 2: 첫 번째 은닉층의 왜곡 (Hidden Layer 1)
# 직선이 가중치/편향을 만나 부드럽게 구부러짐 (여러 노드)
# ==============================================================================
print("📊 Step 2 생성 중...")
fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor(BG_COLOR)

# 세 개의 노드로 다양한 변환
# 노드 1: 약한 왜곡
z1 = 1.0 * x_range + 1.0
a1 = sigmoid(z1)

# 노드 2: 중간 왜곡
z2 = 2.5 * x_range + 0.0
a2 = sigmoid(z2)

# 노드 3: 강한 경사 및 반전
z3 = -4.0 * x_range + 2.0
a3 = sigmoid(z3)

# 시각화
ax.plot(x_range, a1, color=C_RED, linewidth=2.5, alpha=0.7, 
        linestyle='--', label='Node 1: σ(x + 1)', zorder=2)
ax.plot(x_range, a2, color=C_RED, linewidth=3.5, alpha=1.0, 
        label='Node 2: σ(2.5x)', zorder=3)
ax.plot(x_range, a3, color=C_RED, linewidth=2.5, alpha=0.7, 
        linestyle=':', label='Node 3: σ(-4x + 2)', zorder=2)

setup_ax(ax, "Step 2: Hidden Layer 1 (First Distortion)", ylabel="Activation σ(z)")
ax.set_ylim(-0.05, 1.05)
ax.axhline(0, color='white', linestyle='-', linewidth=0.5, alpha=0.2)
ax.axhline(1, color='white', linestyle='-', linewidth=0.5, alpha=0.2)
ax.legend(loc='best', fontsize=10, framealpha=0.9)

save_fig(2, "hidden_layer_1")


# ==============================================================================
# STEP 3: 두 번째 은닉층의 중첩 왜곡 (Hidden Layer 2)
# 구부러진 선들을 다시 모아 더 복잡하게 찌그러뜨림
# ==============================================================================
print("📊 Step 3 생성 중...")
fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor(BG_COLOR)

# 이전 층의 출력을 가중치로 조합
# h2_z = W1*a1 + W2*a2 + W3*a3 + b
h2_z1 = (5.0 * a1) + (-6.0 * a2) + (2.0 * a3) - 1.0
h2_z2 = (-3.0 * a1) + (4.0 * a2) + (3.0 * a3) - 2.5

# 2차 활성화 함수 통과
h2_a1 = sigmoid(h2_z1)
h2_a2 = sigmoid(h2_z2)

# 시각화: 훨씬 더 복잡해진 곡선
ax.plot(x_range, h2_a1, color=C_MAGENTA, linewidth=3.5, alpha=0.9, 
        label='Complex Curve A', zorder=2)
ax.plot(x_range, h2_a2, color=C_MAGENTA, linewidth=2.5, alpha=0.6, 
        linestyle='--', label='Complex Curve B', zorder=2)

# 배경 채우기
ax.fill_between(x_range, h2_a1, alpha=0.1, color=C_MAGENTA)

setup_ax(ax, "Step 3: Hidden Layer 2 (Complex Distortion)", ylabel="Activation σ(z)")
ax.set_ylim(-0.05, 1.05)
ax.axhline(0, color='white', linestyle='-', linewidth=0.5, alpha=0.2)
ax.axhline(1, color='white', linestyle='-', linewidth=0.5, alpha=0.2)
ax.legend(loc='best', fontsize=10, framealpha=0.9)

save_fig(3, "hidden_layer_2")


# ==============================================================================
# STEP 4: 실제 MLP 학습 후 결정 경계 시각화
# ==============================================================================
print("📊 Step 4 생성 중...")

# ── 1. XOR 데이터 ──
X = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=float)
y = np.array([[0],[1],[1],[0]], dtype=float)

# ── 2. MLP 초기화 (2 → 4 → 1) ──
np.random.seed(42)
W1 = np.random.randn(2, 4) * 1.5
b1 = np.zeros((1, 4))
W2 = np.random.randn(4, 1) * 1.5
b2 = np.zeros((1, 1))

lr = 0.5

# ── 3. 학습 (5000 에폭) ──
for _ in range(5000):
    # Forward
    z1 = X @ W1 + b1
    a1 = sigmoid(z1)
    z2 = a1 @ W2 + b2
    a2 = sigmoid(z2)

    # Backward
    dL_da2 = a2 - y
    dL_dz2 = dL_da2 * a2 * (1 - a2)
    dL_dW2 = a1.T @ dL_dz2
    dL_db2 = dL_dz2.sum(axis=0, keepdims=True)

    dL_da1 = dL_dz2 @ W2.T
    dL_dz1 = dL_da1 * a1 * (1 - a1)
    dL_dW1 = X.T @ dL_dz1
    dL_db1 = dL_dz1.sum(axis=0, keepdims=True)

    W2 -= lr * dL_dW2
    b2 -= lr * dL_db2
    W1 -= lr * dL_dW1
    b1 -= lr * dL_db1

# 학습 결과 확인
z1 = X @ W1 + b1;  a1 = sigmoid(z1)
z2 = a1 @ W2 + b2; preds = sigmoid(z2)
print("학습 결과:", np.round(preds.flatten(), 3), "→ 정답:", y.flatten().astype(int))

# ── 4. 결정 경계 시각화 ──
fig, ax = plt.subplots(figsize=(8, 5)) 
fig.patch.set_facecolor(BG_COLOR)

xx, yy = np.meshgrid(np.linspace(-0.2, 1.2, 400),
                     np.linspace(-0.2, 1.2, 400))
grid = np.c_[xx.ravel(), yy.ravel()]

# 학습된 MLP로 예측
g_a1 = sigmoid(grid @ W1 + b1)
g_out = sigmoid(g_a1 @ W2 + b2).reshape(xx.shape)

# 배경 확률 색칠
ax.contourf(xx, yy, g_out, levels=50, cmap='RdBu_r', alpha=0.4, zorder=1)

# 결정 경계선 (0.5 등고선)
ax.contour(xx, yy, g_out, levels=[0.5], colors=[C_MAGENTA], linewidths=3.5, zorder=3)

# XOR 데이터 포인트
xor_labels = np.array([0, 1, 1, 0])
ax.scatter(X[xor_labels==0, 0], X[xor_labels==0, 1],
           color='white', edgecolors='#888888', s=400, linewidth=2.5,
           zorder=5, label='Class 0 (False)')
ax.scatter(X[xor_labels==1, 0], X[xor_labels==1, 1],
           color='#111111', edgecolors='white', s=400, linewidth=2.5,
           zorder=5, label='Class 1 (True)')

# ── 범례 설정 (그래프 밖으로 이동) ──
from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([0],[0], color=C_MAGENTA, linewidth=3, label='Decision Boundary (p=0.5)'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='white',
           markeredgecolor='#888888', markersize=10, label='Class 0 (False)'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='#111111',
           markeredgecolor='white', markersize=10, label='Class 1 (True)'),
], 
    loc='upper left', 
    bbox_to_anchor=(1.05, 1), # 그래프 오른쪽(1.05) 상단(1)에 배치
    borderaxespad=0., 
    fontsize=10, 
    framealpha=0.95, 
    edgecolor='#666666'
)

# ── 축 및 스타일 설정 (순서 중요!) ──
setup_ax(ax, "Step 4: Output Layer", xlabel="Input X₁", ylabel="Input X₂")

# setup_ax 내부의 set_xlim(-3, 3)을 다시 XOR 범위로 덮어씌웁니다.
ax.set_xticks([0, 0.5, 1])
ax.set_yticks([0, 0.5, 1])
ax.set_xlim(-0.2, 1.2)
ax.set_ylim(-0.2, 1.2)
ax.set_aspect('equal')
ax.grid(True, color='#333333', linestyle='-', linewidth=1, alpha=0.3)

save_fig(4, "output_xor")