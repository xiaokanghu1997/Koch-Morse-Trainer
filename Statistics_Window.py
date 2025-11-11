"""
Koch 统计窗口
显示学习统计数据和图表

Author: xiaokanghu1997
Date: 2025-11-11
Version: 1.4.0
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt


class StatisticsWindow(QMainWindow):
    """统计数据展示窗口"""

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

        self.setWindowTitle("Statistics - Koch Morse Trainer")
        self.setFixedSize(900, 650)

        self.setup_ui()

    def setup_ui(self):
        """设置统计窗口的用户界面"""
        container = QWidget()
        layout = QVBoxLayout(container)

        # 设置顶部区域：统计信息和课程选择
        self.setup_header(layout)

        # 设置图表区域
        self.setup_chart(layout)

        self.setCentralWidget(container)

    def setup_header(self, layout):
        """顶部区域：统计信息和课程选择"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # 总练习时长
        self.label_total_time = QLabel("Total Practice Time: 0m 0s")
        self.label_total_time.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(self.label_total_time)

        # 总练习次数
        self.label_total_count = QLabel("Total Practice Count: 0")
        self.label_total_count.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(self.label_total_count)

        # 空白伸缩
        header_layout.addStretch(1)

        # 下拉框
        self.label_combo = QLabel("Select Lesson:")
        header_layout.addWidget(self.label_combo)

        self.combo_lessons = QComboBox()
        self.combo_lessons.addItem("All Learned Courses")
        self.refresh_combo_items()
        self.combo_lessons.currentIndexChanged.connect(self.update_chart)
        header_layout.addWidget(self.combo_lessons)

        layout.addLayout(header_layout)

    def setup_chart(self, layout):
        """设置统计图表区域"""
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
        layout.addWidget(self.fig_canvas)

        self.update_chart()

    def refresh_combo_items(self):
        """刷新下拉框中的选项"""
        self.combo_lessons.clear()
        self.combo_lessons.addItem("All Learned Courses")
        for lesson_name in self.stats_manager.data.get("lessons", {}):
            self.combo_lessons.addItem(lesson_name)

    def update_chart(self):
        """根据选择更新统计图表"""
        selected_lesson = self.combo_lessons.currentText()

        if selected_lesson == "All Learned Courses":
            self.plot_all_courses()
        else:
            self.plot_single_course(selected_lesson)

        self.fig_canvas.draw()

    def plot_all_courses(self):
        """绘制所有已学课程的总结统计图"""
        lessons = self.stats_manager.data.get("lessons", {})
        lesson_names = list(lessons.keys())[:40]  # 最多显示40个课程

        accuracies = [lessons[lesson]["average_accuracy"] for lesson in lesson_names]
        counts = [lessons[lesson]["practice_count"] for lesson in lesson_names]

        self.ax1.clear()
        self.ax2.clear()

        self.ax1.set_title("All Learned Courses")
        self.ax1.set_xlabel("Courses")
        self.ax1.set_ylabel("Accuracy (%)", color="tab:blue")
        self.ax1.plot(lesson_names, accuracies, color="tab:blue", marker="o")
        self.ax1.tick_params(axis="y", labelcolor="tab:blue")
        self.ax1.grid(True, linestyle="--", alpha=0.5)
        self.ax1.tick_params(axis="x", rotation=45)

        self.ax2.set_ylabel("Practice Count", color="tab:orange")
        self.ax2.bar(lesson_names, counts, color="tab:orange", alpha=0.7)
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