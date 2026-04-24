import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import os

# ==========================================
# 1. 다크 테마 설정
# ==========================================
plt.style.use('dark_background')
plt.rcParams.update({
    'font.family': 'NanumGothic',
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
# 2. 색상 및 공통 설정
# ==========================================
C_RED     = '#FF3333'
C_MAGENTA = '#FF00FF'
C_BLUE    = '#1F51FF'
C_CYAN    = '#00CFFF'
C_YELLOW  = '#FFD700'
C_GREEN   = '#39FF14'
C_GRID    = '#444444'
BG_COLOR  = '#0d0d0d'

FOLDER = "post_graphs"
os.makedirs(FOLDER, exist_ok=True)

def setup_ax(ax, title, xlabel="x", ylabel="y"):
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='white')
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(True, color=C_GRID, linestyle='--', linewidth=0.5, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#666666')
    ax.spines['bottom'].set_color('#666666')
    ax.tick_params(colors='white', labelsize=10)

def save_fig(name):
    fig = plt.gcf()
    fig.patch.set_facecolor(BG_COLOR)
    path = f"{FOLDER}/{name}.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150, facecolor=BG_COLOR, edgecolor='none', bbox_inches='tight')
    print(f"✓ 저장: {path}")
    plt.close()


# ==============================================================================
# GRAPH 1: scatter(실제 데이터) + y=x 직선 (Loss 개념 도입)
# x=[1,2,3,4,5], y=[3,5,7,9,11]  /  모델: y_pred = x
# ==============================================================================
print("📊 Graph 1: Loss 개념 - scatter + y=x 직선")
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor(BG_COLOR)

x_data = np.array([1, 2, 3, 4, 5], dtype=float)
y_data = np.array([3, 5, 7, 9, 11], dtype=float)
x_line = np.linspace(0.5, 5.5, 200)
y_pred_line = x_line  # 모델: y = x

ax.plot(x_line, y_pred_line, color=C_BLUE, linewidth=2.5,
        label='모델 예측: y = x', zorder=2)
ax.scatter(x_data, y_data, color=C_RED, s=120, zorder=5,
           edgecolors='white', linewidths=1.2, label='실제 데이터')

setup_ax(ax, "실제 데이터 vs 모델 예측", xlabel="x", ylabel="y")
ax.set_xlim(0.2, 6.0)
ax.set_ylim(0, 13)
ax.legend(fontsize=11, framealpha=0.9)

save_fig("graph1_loss_intro")


# ==============================================================================
# GRAPH 2: 잔차(Residual) 시각화
# 실제 y와 예측 y=x 사이의 수직 거리
# ==============================================================================
print("📊 Graph 2: 잔차(Residual) 시각화")
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor(BG_COLOR)

y_pred_at_data = x_data  # 모델 y=x 에서의 예측값
residuals = y_data - y_pred_at_data

ax.plot(x_line, y_pred_line, color=C_BLUE, linewidth=2.5,
        label='모델 예측: y = x', zorder=2)
ax.scatter(x_data, y_data, color=C_RED, s=120, zorder=6,
           edgecolors='white', linewidths=1.2, label='실제 데이터')

# 잔차 수직선 및 라벨
for xi, yi_true, yi_pred, res in zip(x_data, y_data, y_pred_at_data, residuals):
    ax.plot([xi, xi], [yi_pred, yi_true],
            color=C_YELLOW, linewidth=2.0, linestyle='--', zorder=4)
    ax.annotate(f'오차={res:.0f}',
                xy=(xi, (yi_true + yi_pred) / 2),
                xytext=(xi + 0.15, (yi_true + yi_pred) / 2),
                color=C_YELLOW, fontsize=9.5,
                va='center')

# 예측 점 (모델이 찍는 위치)
ax.scatter(x_data, y_pred_at_data, color=C_BLUE, s=80, zorder=5,
           edgecolors='white', linewidths=1.0, label='모델 예측값')

setup_ax(ax, "잔차(Residual): 실제값 - 예측값", xlabel="x", ylabel="y")
ax.set_xlim(0.2, 6.5)
ax.set_ylim(0, 13)
ax.legend(fontsize=10, framealpha=0.9)

save_fig("graph2_residuals")


# ==============================================================================
# GRAPH 3: y = x² 곡선 + 각 점의 접선 (Gradient 시각화)
# ==============================================================================
print("📊 Graph 3: y=x² 기울기(접선) 시각화")
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor(BG_COLOR)

x_curve = np.linspace(-3, 3, 300)
y_curve = x_curve ** 2

ax.plot(x_curve, y_curve, color=C_CYAN, linewidth=3.0,
        label='$f(x) = x^2$', zorder=2)

# 접선 그릴 점들
tangent_points = [-2.0, -1.0, 0.0, 1.0, 2.0]
colors_t = [C_RED, C_MAGENTA, C_GREEN, C_MAGENTA, C_RED]
dx_span = 1.2

for xp, col in zip(tangent_points, colors_t):
    yp = xp ** 2
    slope = 2 * xp  # dy/dx = 2x
    x_t = np.array([xp - dx_span, xp + dx_span])
    y_t = yp + slope * (x_t - xp)

    ax.plot(x_t, y_t, color=col, linewidth=1.8,
            linestyle='--', alpha=0.85, zorder=3)
    ax.scatter([xp], [yp], color=col, s=100, zorder=6,
               edgecolors='white', linewidths=1.0)

    # 기울기 값 표시 (0이 아닌 점만)
    if xp != 0:
        offset_x = 0.15 if xp > 0 else -0.15
        ha = 'left' if xp > 0 else 'right'
        ax.annotate(f"기울기={slope:.0f}",
                    xy=(xp, yp), xytext=(xp + offset_x, yp + 0.8),
                    color=col, fontsize=9, ha=ha)
    else:
        ax.annotate("기울기=0\n(최솟값!)",
                    xy=(0, 0), xytext=(0.2, 1.5),
                    color=C_GREEN, fontsize=9.5,
                    arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.5))

setup_ax(ax, "기울기(Gradient): 어느 방향으로 내려갈까?",
         xlabel="가중치 w", ylabel="Loss = $w^2$")
ax.set_xlim(-3.2, 3.2)
ax.set_ylim(-0.5, 9.5)
ax.legend(fontsize=11, framealpha=0.9)
ax.axhline(0, color='white', linewidth=0.5, alpha=0.3)

save_fig("graph3_gradient_tangent")


# ==============================================================================
# GRAPH 4: 학습률(lr) 비교 — 너무 클 때 / 적당 / 너무 작을 때
# Loss landscape: f(w) = w² 위에서 경사하강법 스텝 시각화
# ==============================================================================
print("📊 Graph 4: 학습률 비교")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.patch.set_facecolor(BG_COLOR)

w_curve = np.linspace(-4, 4, 300)
loss_curve = w_curve ** 2

configs = [
    {"lr": 1.9,  "title": "학습률이 너무 크면\n(lr = 1.9)", "color": C_RED,    "steps": 8},
    {"lr": 0.3,  "title": "학습률이 적당하면\n(lr = 0.3)", "color": C_GREEN,  "steps": 8},
    {"lr": 0.02, "title": "학습률이 너무 작으면\n(lr = 0.02)", "color": C_YELLOW, "steps": 8},
]

for ax, cfg in zip(axes, configs):
    ax.plot(w_curve, loss_curve, color=C_CYAN, linewidth=2.5, label='Loss = w²', zorder=2)

    # 경사하강 시뮬레이션
    w = 3.0
    ws = [w]
    for _ in range(cfg["steps"]):
        grad = 2 * w
        w = w - cfg["lr"] * grad
        ws.append(w)
        if abs(w) > 10:  # 발산 방지
            break

    ws = np.array(ws)
    ls = ws ** 2

    # 스텝 화살표
    for i in range(len(ws) - 1):
        ax.annotate("",
                    xy=(ws[i+1], ls[i+1]),
                    xytext=(ws[i], ls[i]),
                    arrowprops=dict(arrowstyle='->', color=cfg["color"],
                                    lw=2.0, mutation_scale=15))

    ax.scatter(ws[:len(ws)], ls[:len(ws)],
               color=cfg["color"], s=80, zorder=5,
               edgecolors='white', linewidths=1.0)

    # 시작점 강조
    ax.scatter([ws[0]], [ls[0]], color='white', s=130, zorder=6,
               edgecolors=cfg["color"], linewidths=2.0, label='시작점')

    ax.set_title(cfg["title"], fontsize=12, fontweight='bold',
                 color='white', pad=12)
    ax.set_xlabel("가중치 w", fontsize=10)
    ax.set_ylabel("Loss", fontsize=10)
    ax.set_xlim(-4.5, 4.5)
    ax.set_ylim(-0.5, 16)
    ax.grid(True, color=C_GRID, linestyle='--', linewidth=0.5, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#666666')
    ax.spines['bottom'].set_color('#666666')
    ax.tick_params(colors='white', labelsize=9)
    ax.legend(fontsize=9, framealpha=0.9)

plt.suptitle("학습률(Learning Rate)에 따른 경사하강법 비교",
             fontsize=14, fontweight='bold', color='white', y=1.02)

save_fig("graph4_learning_rate_comparison")


# ==============================================================================
# GRAPH 5: epoch에 따른 Loss 수렴 곡선
# 실제 경사하강법 코드 실행 결과 (y=2x+1 선형회귀)
# ==============================================================================
print("📊 Graph 5: Loss 수렴 곡선")
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.patch.set_facecolor(BG_COLOR)

# 데이터 및 학습
x_d = np.array([1, 2, 3, 4, 5], dtype=float)
y_d = np.array([3, 5, 7, 9, 11], dtype=float)

lrs = [0.1, 0.01, 0.001]
colors_lr = [C_GREEN, C_CYAN, C_YELLOW]
epochs = 300

# ── 왼쪽: lr별 loss 곡선 ──
ax_loss = axes[0]
for lr_val, col in zip(lrs, colors_lr):
    w, b = 0.0, 0.0
    loss_hist = []
    for _ in range(epochs):
        y_hat = w * x_d + b
        loss = np.mean((y_hat - y_d) ** 2)
        loss_hist.append(loss)
        dw = np.mean(2 * (y_hat - y_d) * x_d)
        db = np.mean(2 * (y_hat - y_d))
        w -= lr_val * dw
        b -= lr_val * db
    ax_loss.plot(range(epochs), loss_hist, color=col, linewidth=2.2,
                 label=f'lr = {lr_val}')

setup_ax(ax_loss, "Epoch별 Loss 변화", xlabel="Epoch", ylabel="MSE Loss")
ax_loss.legend(fontsize=10, framealpha=0.9)
ax_loss.set_xlim(0, epochs)
ax_loss.set_ylim(bottom=0)

# ── 오른쪽: lr=0.01로 학습된 가중치/편향 수렴 곡선 ──
ax_wb = axes[1]
w, b = 0.0, 0.0
w_hist, b_hist = [], []
for _ in range(epochs):
    y_hat = w * x_d + b
    dw = np.mean(2 * (y_hat - y_d) * x_d)
    db = np.mean(2 * (y_hat - y_d))
    w -= 0.01 * dw
    b -= 0.01 * db
    w_hist.append(w)
    b_hist.append(b)

ax_wb.plot(range(epochs), w_hist, color=C_CYAN, linewidth=2.2, label='w (가중치)')
ax_wb.plot(range(epochs), b_hist, color=C_MAGENTA, linewidth=2.2, label='b (편향)')
ax_wb.axhline(2.0, color=C_CYAN, linewidth=1.0, linestyle=':', alpha=0.5, label='정답 w=2')
ax_wb.axhline(1.0, color=C_MAGENTA, linewidth=1.0, linestyle=':', alpha=0.5, label='정답 b=1')

setup_ax(ax_wb, "가중치·편향 수렴 (lr=0.01)", xlabel="Epoch", ylabel="값")
ax_wb.legend(fontsize=9.5, framealpha=0.9)
ax_wb.set_xlim(0, epochs)

plt.suptitle("경사하강법: 학습 과정 시각화",
             fontsize=14, fontweight='bold', color='white', y=1.02)

save_fig("graph5_loss_convergence")

print("\n✅ 모든 그래프 생성 완료!")
print(f"📁 저장 위치: ./{FOLDER}/")