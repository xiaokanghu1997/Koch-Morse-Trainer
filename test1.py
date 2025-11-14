import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

# 示例数据
x = np.arange(10)
y = np.random.randint(1, 10, size=10)

fig, ax = plt.subplots()

# 绘制柱状图
bars = ax.bar(x, y, color='skyblue', edgecolor='black')

# 创建高亮条（初始不可见）
highlight = Rectangle((0,0), width=0, height=0, facecolor='orange', edgecolor='red', alpha=0.6)
ax.add_patch(highlight)
highlight.set_visible(False)

# 创建提示框
annot = ax.annotate("",
                    xy=(0, 0),
                    xytext=(8, 8),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", fc="w", alpha=0.8),
                    arrowprops=None)
annot.set_visible(False)

def update_annot(i, event, offset=20):
    bar = bars[i]
    x_bar = bar.get_x() + bar.get_width() / 2
    y_bar = bar.get_height()

    y_mouse = event.ydata
    y_mouse = max(0, min(y_mouse, y_bar))  # 限制提示框不超过柱子顶部
    # 根据鼠标位置设置偏移方向
    if event.x < fig.bbox.width / 2:
        dx = offset
        ha = 'left'
        x_bar = bar.get_x() + bar.get_width() / 2
    else:
        dx = -offset
        ha = 'right'
        x_bar = bar.get_x() - bar.get_width() / 2

    annot.xy = (x_bar, y_mouse)
    annot.set_text(f"x={x[i]}\nyy={y[i]}")
    annot.set_position((dx, 0))
    annot.set_ha('left')
    annot.set_va('center')

    # 设置高亮条位置和大小
    highlight.set_x(bar.get_x())
    highlight.set_y(0)
    highlight.set_width(bar.get_width())
    highlight.set_height(bar.get_height())
    highlight.set_visible(True)

def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        for i, bar in enumerate(bars):
            cont, _ = bar.contains(event)
            if cont:
                update_annot(i, event)
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
        if vis:
            annot.set_visible(False)
            highlight.set_visible(False)
            fig.canvas.draw_idle()

# 鼠标悬停事件
fig.canvas.mpl_connect("motion_notify_event", hover)

plt.show()
