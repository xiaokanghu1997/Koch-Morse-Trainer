import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# 示例数据
x = np.linspace(0, 10, 30)
y = np.sin(x)

fig, ax = plt.subplots()
points = ax.plot(x, y, 'o', picker=5, markersize=6)[0]
highlight = ax.plot([], [], 'o', color='red', markersize=6)[0]

# 创建提示框
annot = ax.annotate("",
                    xy=(0, 0),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", fc="w", alpha=0.8),
                    arrowprops=None)
annot.set_visible(False)

def update_annot(ind, event, offset=8):
    i = ind["ind"][0]
    annot.xy = (x[i], y[i])
    annot.set_text(f"x={x[i]:.2f}\ny={y[i]:.2f}")

    # 根据鼠标位置设置偏移方向
    if event.x > fig.bbox.width / 2:
        dx = -offset
        ha = 'right'
    else:
        dx = offset
        ha = 'left'
    if event.y > fig.bbox.height / 2:
        dy = -offset
        va = 'top'
    else:
        dy = offset
        va = 'bottom'

    annot.set_position((dx, dy))
    annot.set_ha(ha)
    annot.set_va(va)

    highlight.set_data([x[i]], [y[i]])

def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = points.contains(event)
        if cont:
            update_annot(ind, event)
            annot.set_visible(True)
            highlight.set_visible(True)
            fig.canvas.draw_idle()
        elif vis:
            annot.set_visible(False)
            highlight.set_visible(False)
            fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", hover)
plt.show()
