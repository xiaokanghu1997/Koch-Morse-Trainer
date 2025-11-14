"""
Koch 统计窗口
显示学习统计数据和图表

Author: xiaokanghu1997
Date: 2025-11-11
Version: 1.4.0
"""

import warnings
from ctypes import windll, byref, sizeof, c_int
from datetime import datetime

from PySide6 import QtGui
from PySide6.QtCore import Qt, QUrl, QSettings, QTimer, QSize
from PySide6.QtGui import QShortcut, QKeySequence, QIcon, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QLabel, QComboBox

from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, ComboBox, ProgressBar, 
    PushButton, TextEdit, setTheme, Theme, SwitchButton, FluentIcon
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
from Config import config


class StatisticsWindow(QWidget):
    """统计数据展示窗口"""

    DARK_TITLE_BAR_COLOR = 0x00202020  # 深色模式标题栏颜色
    LIGHT_TITLE_BAR_COLOR = 0x00F3F3F3  # 浅色模式标题栏颜色

    def __init__(self, stats_manager, is_dark_theme=False, is_transparent=False):
        """
        初始化统计窗口

        Args:
            stats_manager: 传入的统计数据管理器
            is_dark_theme: 是否应用深色主题
        """
        super().__init__()
        self.stats_manager = stats_manager

        self.setWindowTitle("Statistics")
        self.setFixedSize(822, 358)
        self.toggle_theme(is_dark_theme)
        self.toggle_transparency(is_transparent)

        # 用于悬停提示的变量
        self.annot = None
        self.highlight_line = None
        self.highlight_bar = None

        self.setup_ui()

    def setup_ui(self):
        """设置统计窗口的用户界面"""
        self.layout_main = QVBoxLayout(self)

        self._setup_row1()
        self._setup_row2()

        self.layout_main.addLayout(self.hbox1)
        self.layout_main.addLayout(self.hbox2)

    def _setup_row1(self):
        """顶部区域：统计信息和课程选择"""
        self.hbox1 = QHBoxLayout()

        self.hbox11 = QHBoxLayout()
        self.hbox11.addWidget(BodyLabel("Select lesson:"))
        self.combo_lessons = ComboBox()
        self.combo_lessons.setFixedSize(160, 30)
        self.combo_lessons.setMaxVisibleItems(5)
        lesson_names = self.stats_manager.get_overall_stats().get("practiced_lesson_names")
        self.combo_lessons.addItems(lesson_names)
        self.combo_lessons.currentIndexChanged.connect(self.update_chart)
        self.hbox11.addWidget(self.combo_lessons)
        self.hbox111 = QHBoxLayout()
        self.hbox11.addLayout(self.hbox111)

        self.hbox11.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.hbox12 = QHBoxLayout()
        self.hbox12.addWidget(BodyLabel("Total practice time:"))
        self.label_total_time = StrongBodyLabel()
        self.hbox12.addWidget(self.label_total_time)
        self.hbox12.addSpacing(10)
        self.hbox12.addWidget(BodyLabel("Total practice count:"))
        self.label_total_count = StrongBodyLabel()
        self.hbox12.addWidget(self.label_total_count)
        self.hbox12.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.hbox1.addLayout(self.hbox11)
        self.hbox1.addLayout(self.hbox12)

    def resizeEvent(self, event):
        """窗口大小改变时更新显示"""
        super().resizeEvent(event)
        if hasattr(self, 'label_window_size'):
            self.label_window_size.setText(f"Size: {self.width()}x{self.height()}")

    def _setup_row2(self):
        """设置统计图表区域"""
        self.hbox2 = QHBoxLayout()

        self.figure = plt.figure(figsize=(8, 3), dpi=100)

        class HighQualityCanvas(FigureCanvas):
            def paintEvent(self, event):
                painter = QtGui.QPainter(self)
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
                painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)
                painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
                painter.end()
                super().paintEvent(event)
    
        self.fig_canvas = HighQualityCanvas(self.figure)
        self.fig_canvas.mpl_connect("motion_notify_event", self.on_hover)

        self.hbox2.addWidget(self.fig_canvas)
        self.update_chart()

    def update_chart(self):
        """根据选择更新统计图表"""
        if self.combo_lessons.currentIndex() == 0:
            total_time = self.stats_manager.get_overall_stats().get("total_practice_time")
            total_count = self.stats_manager.get_overall_stats().get("total_practice_count")
            self.clear_layout(self.hbox111)
            self.combo_mode = None
        else:
            lesson_id = self.combo_lessons.currentIndex()
            total_time = self.stats_manager.get_lesson_stats(lesson_id).get("practice_time")
            total_count = self.stats_manager.get_lesson_stats(lesson_id).get("practice_count")

            # 显示统计模式选择（重新创建 widgets）
            self.clear_layout(self.hbox111)
            self.combo_mode = None
            self.hbox111.addWidget(BodyLabel("Statistic by:"))  # 重新创建
        
            # 重新创建或重用 combo_mode
            if not hasattr(self, 'combo_mode') or self.combo_mode is None:
                self.combo_mode = ComboBox()
                self.combo_mode.setFixedSize(90, 30)
                self.combo_mode.setMaxVisibleItems(5)
                self.combo_mode.addItems(["Default", "Hour", "Day", "Month", "Year"])
                self.combo_mode.currentIndexChanged.connect(self.mode_changed)
            self.hbox111.addWidget(self.combo_mode)
        
        self.plot(self.combo_lessons.currentIndex())
        self.label_total_time.setText(self.stats_manager.format_time(total_time))
        self.label_total_count.setText(f"{total_count}")
        self.fig_canvas.draw()
    
    @staticmethod
    def clear_layout(layout: QHBoxLayout):
        """
        清除布局中的所有控件
        
        Args:
            layout: 要清空的布局对象
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def mode_changed(self):
        """统计模式改变时更新图表"""
        self.plot(self.combo_lessons.currentIndex())
        self.fig_canvas.draw()
    
    def plot(self, index):
        """根据索引绘制相应的统计图表"""
        self.figure.clf()      # 清除整个图形

        self.annot = None
        self.highlight_line = None
        self.highlight_bar = None

        self.legend_ax = self.figure.add_axes([0.056, 0.94, 1, 0.06])
        self.legend_ax.axis('off')
        self.legend_ax.set_navigate(False)  # 禁用图例轴的交互功能

        self.figure.set_tight_layout(False)
        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        if index == 0:
            self.ax1.set_position([0.065, 0.15, 0.885, 0.72])
            self.ax2.set_position([0.065, 0.15, 0.885, 0.72])

            avg_accuracy = self.stats_manager.get_overall_stats().get("average_accuracy")
            lessons_index = self.stats_manager.get_overall_stats().get("practiced_lesson_numbers")
            lessons_index = [int(num) for num in lessons_index[1:]]  # 跳过“所有已学课程”
            accuracies = []
            counts = []
        
            for num in lessons_index:  # 跳过“所有已学课程”
                lesson_data = self.stats_manager.get_lesson_stats(num)
                accuracies.append(float(lesson_data.get("average_accuracy", 0)))
                counts.append(int(lesson_data.get("practice_count", 0)))
            
            x = lessons_index
            self.ax1.set_xlabel("Lesson ID", labelpad=6)
            self.ax1.set_xlim(0.5, 40.5)
            self.ax1.set_xticks(range(1, 41))
            self.ax1.set_xticklabels([str(i).zfill(2) for i in range(1, 41)])
        else:
            self.ax1.set_position([0.065, 0.205, 0.885, 0.665])
            self.ax2.set_position([0.065, 0.205, 0.885, 0.665])
        
            lesson_data = self.stats_manager.get_lesson_stats(index)
            if not lesson_data:
                self.ax1.clear()
                self.ax2.clear()
                return

            avg_accuracy = lesson_data.get("average_accuracy")
            # 获取聚合模式
            mode = self.combo_mode.currentText()

            if mode == "Default":
                # 原始数据（逐次练习）
                history = lesson_data.get("accuracy_history", [])
                timestamps = [datetime.strptime(record["timestamp"], "%Y-%m-%dT%H:%M:%S") for record in history]
                formatted = [dt.strftime("%m-%d\n%H:%M") for dt in timestamps]
                accuracies = [record["accuracy"] for record in history]
                counts = list(range(1, len(history) + 1))
            else:
                # 按时间聚合
                formatted, accuracies, counts = self.stats_manager.aggregate_by_time_period(index, mode)
                if not formatted:  # 如果没有数据
                    self.ax1.clear()
                    self.ax2.clear()
                    return
                if mode != "Hour":
                    self.ax1.set_position([0.065, 0.15, 0.885, 0.72])
                    self.ax2.set_position([0.065, 0.15, 0.885, 0.72])

            x = list(range(1, len(formatted) + 1))
            self.ax1.set_xlabel("Practice Time", labelpad=6)
            self.ax1.set_xlim(0.5, len(formatted) + 0.5)
            self.ax1.set_xticks(x)
            self.ax1.set_xticklabels(formatted)

        if self.is_dark_theme:
            line_color = "#C8B5FC"       # 浅紫色（深色背景下更亮）
            bar_color = "#4A9B8E"        # 深青色（深色背景下调暗）
            threshold_color = "#F86D6B"  # 保持红色
            edge_color = "#CCABF4"      # 深色边框
            h_line_color = "#721ED9"      # 深紫色
            h_bar_color = "#92E0D3"       # 浅青色
        else:
            line_color = "#721ED9"       # 深紫色（浅色背景下）
            bar_color = "#92E0D3"        # 浅青色（浅色背景下）
            threshold_color = "#F86D6B"  # 保持红色
            edge_color = "#9465CE"       # 浅色边框
            h_line_color = "#C8B5FC"      # 浅紫色#AFA4F4
            h_bar_color = "#4A9B8E"       # 深青色
        
        # 设置左轴
        self.ax1.tick_params(axis="both", direction="in", width=1, zorder=3, pad=5)
        self.ax1.tick_params(axis="x", which="both", bottom=False)
        line = self.ax1.plot(x, accuracies, color=line_color, marker="o", markersize=4, linewidth=1, zorder=3, clip_on=False)
        self.ax1.set_ylabel("Accuracy (%)", labelpad=6)  # 添加颜色参数
        self.ax1.set_ylim(0, 100)  # 设置Y轴范围为0-100%
        self.ax1.set_yticks(range(0, 101, 10))  # 设置Y轴刻度
        self.ax1.set_yticklabels([f"{i}" for i in range(0, 101, 10)])  # 设置Y轴刻度标签为百分比

        self.ax1.spines["left"].set_linewidth(1)
        self.ax1.spines["left"].set_zorder(3)
        self.ax1.spines["right"].set_linewidth(1)
        self.ax1.spines["bottom"].set_linewidth(1)
        self.ax1.spines["top"].set_visible(False)

        # 设置右轴
        self.ax2.tick_params(axis="both", direction="in", width=1, zorder=5)
        bar = self.ax2.bar(x, counts, color=bar_color, zorder=2)
        hline1 = self.ax2.hlines(y=90, xmin=0, xmax=1, color=threshold_color, linestyles="--", linewidth=1, zorder=2, transform=self.ax1.get_yaxis_transform(), clip_on=False)
        hline2 = self.ax2.hlines(y=float(avg_accuracy), xmin=0, xmax=1, color=line_color, linestyles="--", linewidth=1, zorder=2, transform=self.ax1.get_yaxis_transform(), clip_on=False)
        self.ax2.set_ylabel("Practice Count", labelpad=6)  # 添加右轴标签和颜色
        self.ax2.yaxis.set_label_position("right")  # 将右轴标签位置设置为右侧
        self.ax2.set_ylim(0, 20)  # 设置右轴Y轴范围
        self.ax2.set_yticks(range(0, 21, 2))  # 设置右轴Y轴刻度
        self.ax2.set_yticklabels([f"{i}" for i in range(0, 21, 2)])  # 设置右轴Y轴刻度标签

        self.ax2.grid(axis="y", linestyle="--", linewidth=1, zorder=0)

        self.ax2.spines["right"].set_linewidth(1)
        self.ax2.spines["right"].set_zorder(2)
        self.ax2.spines["top"].set_visible(False)

        self.line_plot = line[0]
        self.bar_plot = bar
        self.highlight_line = self.ax1.plot(
            [], [], 
            color=h_line_color, 
            marker='o', 
            markersize=6,
            markeredgecolor=edge_color,
            markeredgewidth=1.5, 
            linewidth=1, 
            zorder=4, 
            clip_on=False
        )[0]
        self.highlight_bar = Rectangle((0,0), width=0, height=0, color=h_bar_color, zorder=2)
        self.ax2.add_patch(self.highlight_bar)
        self.highlight_bar.set_visible(False)

        if hasattr(self, 'annot_config'):
            self.annot = self.ax1.annotate(
                "",
                xy=(0, 0),
                xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor=self.annot_config['bg_color'],
                    edgecolor=self.annot_config['edge_color'],
                    linewidth=self.annot_config['edge_width'],
                    alpha=self.annot_config['bg_alpha']
                ),
                arrowprops=None,
                zorder=10,
                fontfamily=self.annot_config['font_family'],
                fontsize=self.annot_config['font_size'],
                color=self.annot_config['font_color']
            )
        else:
            # 回退到默认配置
            self.annot = self.ax1.annotate(
                "",
                xy=(0, 0),
                xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(boxstyle="round", alpha=0.8),
                arrowprops=None,
                zorder=10
            )
        self.annot.set_visible(False)

        handles = [line[0], hline2, hline1, bar]
        labels = ["Accuracy", f"Average Accuracy: {avg_accuracy:.2f}%", "Accuracy Threshold: 90%", "Practice Count"]
        self.legend_ax.clear()
        self.legend_ax.axis('off')
        self.legend_ax.legend(handles, labels, ncol=4, framealpha=1, loc="upper left")

        self.ax1.set_zorder(4)
        self.ax2.set_zorder(3)
        self.ax1.patch.set_visible(False)

        ax3 = self.figure.add_axes(self.ax1.get_position(), frameon=False) 
        ax3.tick_params(axis="y", which="both", left=False, labelleft=False)
        ax3.tick_params(axis="x", which="both", bottom=True, labelbottom=False, direction="in", width=1)
        ax3.set_xlim(self.ax1.get_xlim())
        ax3.set_xticks(self.ax1.get_xticks())
    

    # ==================== 主题与透明度设置 ====================
    
    def toggle_transparency(self, checked: bool):
        """
        切换窗口透明度
        
        Args:
            checked: True为透明，False为不透明
        """
        self.setWindowOpacity(0.1 if checked else 1.0)

    def update_window_icon(self, dark_mode: bool):
        """
        根据主题更新窗口图标

        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        try:
            if dark_mode:
                icon_path = config.get_logo_path('dark')  # 深色模式图标路径
            else:
                icon_path = config.get_logo_path('light')  # 浅色模式图标路径

            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # 如果图标文件不存在，使用默认图标
                self.setWindowIcon(FluentIcon.MUSIC.icon())
        except (OSError, AttributeError):
            # 发生错误时使用默认图标
            self.setWindowIcon(FluentIcon.MUSIC.icon())
    
    def toggle_theme(self, checked: bool):
        """
        切换浅色/深色主题
        
        Args:
            checked: True为深色主题，False为浅色主题
        """
        if checked:  # 深色主题
            setTheme(Theme.DARK)
            self.setStyleSheet("QWidget { background-color: #202020; }")
            self.set_windows_title_bar_color(True)
            self.update_window_icon(True)
            self.apply_matplotlib_theme(True)
        else:  # 浅色主题
            setTheme(Theme.LIGHT)
            self.setStyleSheet("QWidget { background-color: #f3f3f3; }")
            self.set_windows_title_bar_color(False)
            self.update_window_icon(False)
            self.apply_matplotlib_theme(False)
    
    def set_windows_title_bar_color(self, dark_mode: bool):
        """
        设置Windows标题栏颜色（仅Windows 11有效）
        同时禁用标题栏过渡动画，使主题切换更流畅
        
        Args:
            dark_mode: True为深色标题栏，False为浅色标题栏
        """
        try:
            hwnd = int(self.winId())
            
            # 设置深色/浅色模式
            dwmwa_use_immersive_dark_mode = 20
            value = c_int(1 if dark_mode else 0)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, dwmwa_use_immersive_dark_mode, byref(value), sizeof(value)
            )
            
            # 设置标题栏颜色
            dwmwa_caption_color = 35
            color_value = c_int(
                self.DARK_TITLE_BAR_COLOR if dark_mode else self.LIGHT_TITLE_BAR_COLOR
            )
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, dwmwa_caption_color, byref(color_value), sizeof(color_value)
            )
            
            # 禁用标题栏过渡动画，使切换更即时
            dwmwa_transitions_forcedisabled = 3
            disable_transitions = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, dwmwa_transitions_forcedisabled,
                byref(disable_transitions), sizeof(disable_transitions)
            )
        except (OSError, AttributeError):
            # 非Windows系统或API调用失败时忽略
            pass

    def apply_matplotlib_theme(self, dark_mode: bool):
        """
        应用 matplotlib 主题
    
        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        if dark_mode:
            plt.rcParams.update({
                # 背景色
                'figure.facecolor': '#202020',
                'axes.facecolor': '#202020',
                'savefig.facecolor': '#202020',
            
                # 文字和标签
                'text.color': '#FFFFFF',
                'axes.labelcolor': '#FFFFFF',
                'axes.edgecolor': '#FFFFFF',
            
                # 刻度
                'xtick.color': '#FFFFFF',
                'ytick.color': '#FFFFFF',
            
                # 网格
                'grid.color': '#444444',
                'grid.alpha': 0.5,
                'grid.linestyle': '--',
            
                # 边框
                'axes.linewidth': 1,

                # 字体
                'font.family': 'Segoe UI',  # 或 'SimHei', 'Arial' 等
                'font.size': 10.5,                    # 全局字号
                'axes.labelsize': 10.5,               # 坐标轴标签字号
                'axes.titlesize': 10.5,               # 标题字号
                'xtick.labelsize': 9.5,               # x轴刻度标签字号
                'ytick.labelsize': 9.5,               # y轴刻度标签字号
                'legend.fontsize': 9.5,               # 图例字号

                # 抗锯齿设置
                'lines.antialiased': True,
                'patch.antialiased': True,
                'text.antialiased': True
            })

            # 提示框配置（深色主题）
            self.annot_config = {
                'font_family': 'Segoe UI',
                'font_size': 9.5,
                'font_color': '#FFFFFF',
                'bg_color': '#2D2D2D',      # 深色背景
                'bg_alpha': 0.95,           # 背景透明度
                'edge_color': '#555555',    # 边框颜色
                'edge_width': 1             # 边框宽度
            }
        else:
            plt.rcParams.update({
                # 背景色
                'figure.facecolor': '#F3F3F3',
                'axes.facecolor': '#F3F3F3',
                'savefig.facecolor': '#F3F3F3',
            
                # 文字和标签
                'text.color': '#000000',
                'axes.labelcolor': '#000000',
                'axes.edgecolor': '#000000',
            
                # 刻度
                'xtick.color': '#000000',
                'ytick.color': '#000000',
            
                # 网格
                'grid.color': '#CCCCCC',
                'grid.alpha': 0.3,
                'grid.linestyle': '--',
            
                # 边框
                'axes.linewidth': 1,

                # 字体
                'font.family': 'Segoe UI',  # 或 'SimHei', 'Arial' 等
                'font.size': 10.5,                    # 全局字号
                'axes.labelsize': 10.5,               # 坐标轴标签字号
                'axes.titlesize': 10.5,               # 标题字号
                'xtick.labelsize': 9.5,               # x轴刻度标签字号
                'ytick.labelsize': 9.5,               # y轴刻度标签字号
                'legend.fontsize': 9.5,               # 图例字号

                # 抗锯齿设置
                'lines.antialiased': True,
                'patch.antialiased': True,
                'text.antialiased': True
            })
            # 提示框配置（浅色主题）
            self.annot_config = {
                'font_family': 'Segoe UI',
                'font_size': 9.5,
                'font_color': '#000000',
                'bg_color': '#FFFFFF',      # 浅色背景
                'bg_alpha': 0.95,           # 背景透明度
                'edge_color': '#CCCCCC',    # 边框颜色
                'edge_width': 1             # 边框宽度
            }
        self.is_dark_theme = dark_mode
    
    def on_hover(self, event):
        """
        鼠标悬停事件处理
        显示折线图点和柱状图的详细信息
        """
        if not hasattr(self, 'annot') or self.annot is None:
            return

        vis = self.annot.get_visible()
        # 检查鼠标是否在坐标轴内
        if event.inaxes == self.ax1 or event.inaxes == self.ax2:
            # 检查折线图的点
            if hasattr(self, 'line_plot'):
                cont, ind = self.line_plot.contains(event)
                if cont:
                    self._update_line_annot(ind, event)
                    return
            # 检查柱状图的柱
            if hasattr(self, 'bar_plot'):
                for i, bar in enumerate(self.bar_plot):
                    cont, _ = bar.contains(event)
                    if cont:
                        self._update_bar_annot(i, event)
                        return
        
            # 鼠标不在任何对象上，隐藏提示
            if vis:
                self.annot.set_visible(False)
                if self.highlight_line:
                    self.highlight_line.set_visible(False)
                if self.highlight_bar:
                    self.highlight_bar.set_visible(False)
                self.fig_canvas.draw_idle()
        elif vis:
            # 鼠标离开坐标轴，隐藏提示
            self.annot.set_visible(False)
            if self.highlight_line:
                self.highlight_line.set_visible(False)
            if self.highlight_bar:
                self.highlight_bar.set_visible(False)
            self.fig_canvas.draw_idle()

    def _update_line_annot(self, ind, event, offset=10):
        """
        更新折线图点的提示框
        """
        i = ind["ind"][0]
    
        # 获取数据
        if self.combo_lessons.currentIndex() == 0:
            lesson_id = int(self.ax1.get_xticks()[i])
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            lesson_name = lesson_data.get("lesson_name")
            accuracy = lesson_data.get("average_accuracy", 0)
            text = f"Lesson {lesson_name}\nAccuracy: {accuracy:.1f}%"
        else:
            lesson_id = self.combo_lessons.currentIndex()
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            history = lesson_data.get("accuracy_history", [])
            if i < len(history):
                record = history[i]
                timestamp = record["timestamp"]
                accuracy = record["accuracy"]
                # 格式化时间
                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                time_str = dt.strftime("%Y-%m-%d %H:%M")
                text = f"Time: {time_str}\nAccuracy: {accuracy:.1f}%\nPractice #{i+1}"
    
        # 获取坐标
        xdata = self.line_plot.get_xdata()
        ydata = self.line_plot.get_ydata()
        self.annot.xy = (xdata[i], ydata[i])
        self.annot.set_text(text)
    
        # 根据鼠标位置调整提示框位置
        if event.x > self.figure.bbox.width / 2:
            dx = -offset
            ha = 'right'
        else:
            dx = offset
            ha = 'left'
        if event.y > self.figure.bbox.height / 2:
            dy = -offset
            va = 'top'
        else:
            dy = offset
            va = 'bottom'
    
        self.annot.set_position((dx, dy))
        self.annot.set_ha(ha)
        self.annot.set_va(va)
        self.annot.set_visible(True)
    
        # 高亮点
        self.highlight_line.set_data([xdata[i]], [ydata[i]])
        self.highlight_line.set_visible(True)
    
        # 隐藏柱状图高亮
        if self.highlight_bar:
            self.highlight_bar.set_visible(False)
    
        self.fig_canvas.draw_idle()

    def _update_bar_annot(self, i, event, offset=15):
        """
        更新柱状图柱的提示框
        """
        bar = self.bar_plot[i]
    
        # 获取数据
        if self.combo_lessons.currentIndex() == 0:
            lesson_id = int(self.ax1.get_xticks()[i])
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            lesson_name = lesson_data.get("lesson_name")
            count = lesson_data.get("practice_count")
            text = f"Lesson {lesson_name}\nPractice Count: {count}"
        else:
            count = int(bar.get_height())
            text = f"Practice #{i+1}\nCount: {count}"
    
        # 设置提示框位置
        y_mouse = event.ydata
    
        # 根据鼠标位置调整提示框
        if event.x < self.figure.bbox.width / 2:
            dx = offset
            x_bar = bar.get_x() + bar.get_width() / 2
        else:
            dx = -offset
            x_bar = bar.get_x() - bar.get_width() / 2
    
        self.annot.xy = (x_bar, y_mouse)
        self.annot.set_text(text)
        self.annot.set_position((dx, 0))
        self.annot.set_ha('left')
        self.annot.set_va('center')
        self.annot.set_visible(True)
        # 高亮柱
        self.highlight_bar.set_x(bar.get_x())
        self.highlight_bar.set_y(0)
        self.highlight_bar.set_width(bar.get_width())
        self.highlight_bar.set_height(bar.get_height())
        self.highlight_bar.set_visible(True)
    
        # 隐藏折线图高亮
        if self.highlight_line:
            self.highlight_line.set_visible(False)
    
        self.fig_canvas.draw_idle()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from Statistics import stats_manager
    import sys

    app = QApplication(sys.argv)

    stats_window = StatisticsWindow(stats_manager, is_dark_theme=True, is_transparent=False)
    stats_window.show()

    sys.exit(app.exec())