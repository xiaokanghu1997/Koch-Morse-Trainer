"""
Koch 统计窗口
显示学习统计数据和图表

Author: xiaokanghu1997
Date: 2025-11-11
Version: 1.4.0
"""

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
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
from Config import config


class StatisticsWindow(QWidget):
    """统计数据展示窗口"""

    DARK_TITLE_BAR_COLOR = 0x00202020  # 深色模式标题栏颜色
    LIGHT_TITLE_BAR_COLOR = 0x00F3F3F3  # 浅色模式标题栏颜色

    def __init__(self, stats_manager, is_dark_theme=False):
        """
        初始化统计窗口

        Args:
            stats_manager: 传入的统计数据管理器
            is_dark_theme: 是否应用深色主题
        """
        super().__init__()
        self.stats_manager = stats_manager
        self.is_dark_theme = is_dark_theme

        self.setWindowTitle("Statistics")
        self.setBaseSize(900, 600)
        self.set_windows_title_bar_color(is_dark_theme)  # 初始化为浅色标题栏
        self.update_window_icon(is_dark_theme)
        self.toggle_theme(is_dark_theme)
        self.toggle_transparency(False)

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
        self.hbox11.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.hbox12 = QHBoxLayout()
        self.hbox12.addWidget(BodyLabel("Total practice time:"))
        total_time = self.stats_manager.get_overall_stats().get("total_practice_time")
        self.label_total_time = StrongBodyLabel(f"{total_time} minutes")
        self.hbox12.addWidget(self.label_total_time)
        self.hbox12.addSpacing(20)
        self.hbox12.addWidget(BodyLabel("Total practice count:"))
        total_count = self.stats_manager.get_overall_stats().get("total_practice_count")
        self.label_total_count = StrongBodyLabel(f"{total_count}")
        self.hbox12.addWidget(self.label_total_count)
        self.hbox12.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.hbox1.addLayout(self.hbox11)
        self.hbox1.addLayout(self.hbox12)

    def _setup_row2(self):
        """设置统计图表区域"""
        self.hbox2 = QHBoxLayout()

        self.figure, self.ax1 = plt.subplots(figsize=(8, 5))
        self.ax2 = self.ax1.twinx()  # 双Y轴

        # 设置图表样式
        self.ax1.set_ylabel("Accuracy (%)", color="tab:blue")
        self.ax1.tick_params(axis="y", labelcolor="tab:blue")
        self.ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax1.grid(True, linestyle="--", alpha=0.5)

        self.ax2.set_ylabel("Practice Count", color="tab:orange")
        self.ax2.tick_params(axis="y", labelcolor="tab:orange")
        self.ax2.yaxis.set_major_locator(MaxNLocator(integer=True))

        self.fig_canvas = FigureCanvas(self.figure)
        self.hbox2.addWidget(self.fig_canvas)

        self.update_chart()

    def update_chart(self):
        """根据选择更新统计图表"""

        if self.combo_lessons.currentIndex() == 0:
            self.plot_all_courses()
        else:
            self.plot_single_course(self.combo_lessons.currentText())

        self.fig_canvas.draw()

    def plot_all_courses(self):
        """绘制所有已学课程的总结统计图"""
        lessons_index = self.stats_manager.get_overall_stats().get("practiced_lesson_numbers")
        lessons_index = [int(num) for num in lessons_index[1:]]  # 跳过“所有已学课程”
        accuracies = []
        counts = []
        
        for num in lessons_index:  # 跳过“所有已学课程”
            lesson_data = self.stats_manager.get_lesson_stats(num)
            accuracies.append(int(lesson_data.get("average_accuracy", 0)))
            counts.append(int(lesson_data.get("practice_count", 0)))

        self.ax1.clear()
        self.ax2.clear()


        self.ax1.set_xlabel("Courses")
        self.ax1.set_ylabel("Accuracy (%)", color="tab:blue")
        self.ax1.plot(lessons_index, accuracies, color="tab:blue", marker="o")
        self.ax1.tick_params(axis="y", labelcolor="tab:blue")
        self.ax1.grid(True, linestyle="--", alpha=0.5)
        self.ax1.tick_params(axis="x")

        self.ax2.set_ylabel("Practice Count", color="tab:orange")
        self.ax2.bar(lessons_index, counts, color="tab:orange", alpha=0.7)
        self.ax2.tick_params(axis="y", labelcolor="tab:orange")

    def plot_single_course(self, lesson_name):
        """绘制单一课程的详细统计图"""
        lesson_data = self.stats_manager.get_lesson_stats(lesson_name)
        if not lesson_data:
            self.ax1.clear()
            self.ax2.clear()
            return

        history = lesson_data.get("accuracy_history", [])
        timestamps = [record["timestamp"] for record in history]
        accuracies = [record["accuracy"] for record in history]
        counts = range(1, len(history) + 1)

        self.ax1.clear()
        self.ax2.clear()

        self.ax1.set_title(f"{lesson_name} Details")
        self.ax1.set_xlabel("Practice History")
        self.ax1.set_ylabel("Accuracy (%)", color="tab:blue")
        self.ax1.plot(timestamps, accuracies, color="tab:blue", marker="o")
        self.ax1.tick_params(axis="y", labelcolor="tab:blue")
        self.ax1.grid(True, linestyle="--", alpha=0.5)
        self.ax1.tick_params(axis="x", rotation=45)

        self.ax2.set_ylabel("Practice Count", color="tab:orange")
        self.ax2.bar(timestamps, counts, color="tab:orange", alpha=0.7)
        self.ax2.tick_params(axis="y", labelcolor="tab:orange")

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
        else:  # 浅色主题
            setTheme(Theme.LIGHT)
            self.setStyleSheet("QWidget { background-color: #f3f3f3; }")
            self.set_windows_title_bar_color(False)
            self.update_window_icon(False)
    
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

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from Statistics import stats_manager
    import sys

    app = QApplication(sys.argv)

    stats_window = StatisticsWindow(stats_manager, is_dark_theme=False)
    stats_window.show()

    sys.exit(app.exec())