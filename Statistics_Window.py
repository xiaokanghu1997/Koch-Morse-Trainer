"""
Koch 统计窗口
显示学习统计数据和图表

Author: xiaokanghu1997
Date: 2025-11-11
Version: 1.1.0
"""

from ctypes import windll, byref, sizeof, c_int
from datetime import datetime
from typing import Optional

from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, ComboBox, 
    setTheme, Theme, FluentIcon
)

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.container import BarContainer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from Config import config


class StatisticsWindow(QWidget):
    """
    统计数据展示窗口
    
    使用matplotlib绘制统计图表，支持:
    - 全局统计(所有课程)
    - 单课程统计
    - 多种时间聚合模式(小时/天/月/年)
    - 交互式悬停提示
    - 深色/浅色主题切换
    """
    
    # ==================== 常量定义 ====================
    DARK_TITLE_BAR_COLOR = 0x00202020   # 深色模式标题栏颜色 RGB(32, 32, 32)
    LIGHT_TITLE_BAR_COLOR = 0x00F3F3F3  # 浅色模式标题栏颜色 RGB(243, 243, 243)
    
    # ==================== 类型注解 - UI控件 ====================
    layout_main: QVBoxLayout            # 主布局
    hbox1: QHBoxLayout                  # 第一行布局
    hbox11: QHBoxLayout                 # 课程选择区
    hbox111: QHBoxLayout                # 统计模式选择区
    hbox12: QHBoxLayout                 # 统计信息显示区
    hbox2: QHBoxLayout                  # 第二行布局(图表)
    
    combo_lessons: ComboBox             # 课程选择下拉框
    combo_mode: Optional[ComboBox]      # 统计模式下拉框(动态创建)
    label_total_time: StrongBodyLabel   # 总练习时长标签
    label_total_count: StrongBodyLabel  # 总练习次数标签
    
    figure: plt.Figure                  # matplotlib图形对象
    fig_canvas: FigureCanvas            # 图形画布
    legend_ax: plt.Axes                 # 图例坐标轴
    ax1: plt.Axes                       # 主坐标轴(左Y轴-准确率)
    ax2: plt.Axes                       # 副坐标轴(右Y轴-练习次数)
    
    line_plot: plt.Line2D               # 准确率折线图
    bar_plot: BarContainer              # 练习次数柱状图
    highlight_line: plt.Line2D          # 悬停高亮折线
    highlight_bar: Rectangle            # 悬停高亮柱状图
    annot: plt.Annotation               # 悬停提示框
    
    # ==================== 类型注解 - 状态变量 ====================
    stats_manager: any                  # 统计管理器实例
    is_dark_theme: bool                 # 是否为深色主题
    annot_config: dict                  # 提示框配置
    
    def __init__(
        self, 
        stats_manager, 
        is_dark_theme: bool = False, 
        is_transparent: bool = False
    ):
        """
        初始化统计窗口
        
        Args:
            stats_manager: 统计数据管理器实例
            is_dark_theme: 是否应用深色主题
            is_transparent: 是否应用透明效果
        """
        super().__init__()
        self.stats_manager = stats_manager
        
        # 设置窗口基础属性
        self.setWindowTitle("Statistics")
        self.setFixedSize(822, 358)
        
        # 应用主题和透明度
        self.toggle_theme(is_dark_theme)
        self.toggle_transparency(is_transparent)
        
        # 初始化悬停提示相关变量
        self.annot = None
        self.highlight_line = None
        self.highlight_bar = None
        
        # 设置用户界面
        self.setup_ui()
    
    # ==================== 界面布局 ====================
    
    def setup_ui(self) -> None:
        """
        设置统计窗口的用户界面
        
        布局结构:
        - 第一行: 课程选择 + 统计模式选择 + 统计信息
        - 第二行: 统计图表
        """
        self.layout_main = QVBoxLayout(self)
        
        self._setup_row1()  # 顶部控制栏
        self._setup_row2()  # 图表区域
        
        self.layout_main.addLayout(self.hbox1)
        self.layout_main.addLayout(self.hbox2)
    
    def _setup_row1(self) -> None:
        """
        第一行: 统计信息和课程选择
        
        包含:
        - 左侧: 课程选择下拉框 + 统计模式选择(动态显示)
        - 右侧: 总练习时长和总练习次数
        """
        self.hbox1 = QHBoxLayout()
        
        # ========== 左侧: 课程选择区 ==========
        self.hbox11 = QHBoxLayout()
        self.hbox11.addWidget(BodyLabel("Select lesson:"))
        
        # 课程选择下拉框
        self.combo_lessons = ComboBox()
        self.combo_lessons.setFixedSize(160, 30)
        self.combo_lessons.setMaxVisibleItems(5)
        lesson_names = self.stats_manager.get_overall_stats().get("practiced_lesson_names")
        self.combo_lessons.addItems(lesson_names)
        self.combo_lessons.currentIndexChanged.connect(self.update_chart)
        self.hbox11.addWidget(self.combo_lessons)
        
        # 统计模式选择区(动态创建)
        self.hbox11.addSpacing(10)
        self.hbox111 = QHBoxLayout()
        self.hbox11.addLayout(self.hbox111)
        self.hbox11.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # ========== 右侧: 统计信息显示 ==========
        self.hbox12 = QHBoxLayout()
        self.hbox12.addWidget(BodyLabel("Total practice time:"))
        self.label_total_time = StrongBodyLabel()
        self.hbox12.addWidget(self.label_total_time)
        self.hbox12.addSpacing(10)
        self.hbox12.addWidget(BodyLabel("Total practice count:"))
        self.label_total_count = StrongBodyLabel()
        self.hbox12.addWidget(self.label_total_count)
        self.hbox12.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合左右两侧
        self.hbox1.addLayout(self.hbox11)
        self.hbox1.addLayout(self.hbox12)
    
    def _setup_row2(self) -> None:
        """
        第二行: 统计图表区域
        
        使用matplotlib绘制双Y轴图表:
        - 左Y轴: 准确率折线图
        - 右Y轴: 练习次数柱状图
        """
        self.hbox2 = QHBoxLayout()
        
        # 创建matplotlib图形
        self.figure = plt.figure(figsize=(8, 3), dpi=100)
        
        # 自定义高质量画布(启用抗锯齿)
        class HighQualityCanvas(FigureCanvas):
            def paintEvent(self, event):
                painter = QtGui.QPainter(self)
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
                painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)
                painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
                painter.end()
                super().paintEvent(event)
        
        self.fig_canvas = HighQualityCanvas(self.figure)
        
        # 连接鼠标悬停事件
        self.fig_canvas.mpl_connect("motion_notify_event", self.on_hover)
        
        self.hbox2.addWidget(self.fig_canvas)
        
        # 初始化图表
        self.update_chart()
    
    # ==================== 图表更新方法 ====================
    
    def update_chart(self) -> None:
        """
        根据选择更新统计图表
        
        处理两种情况:
        1. 全局统计(索引0): 显示所有课程的统计对比
        2. 单课程统计: 显示该课程的练习历史
        """
        if self.combo_lessons.currentIndex() == 0:
            # ========== 全局统计模式 ==========
            total_time = self.stats_manager.get_overall_stats().get("total_practice_time")
            total_count = self.stats_manager.get_overall_stats().get("total_practice_count")
            
            # 隐藏统计模式选择
            self.clear_layout(self.hbox111)
            self.combo_mode = None
        else:
            # ========== 单课程统计模式 ==========
            lesson_id = self.combo_lessons.currentIndex()
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            total_time = lesson_data.get("practice_time")
            total_count = lesson_data.get("practice_count")
            
            # 显示统计模式选择
            self.clear_layout(self.hbox111)
            self.combo_mode = None
            self.hbox111.addWidget(BodyLabel("Statistic by:"))
            
            # 创建统计模式下拉框
            if not hasattr(self, 'combo_mode') or self.combo_mode is None:
                self.combo_mode = ComboBox()
                self.combo_mode.setFixedSize(90, 30)
                self.combo_mode.setMaxVisibleItems(5)
                self.combo_mode.addItems(["Default", "Hour", "Day", "Month", "Year"])
                self.combo_mode.currentIndexChanged.connect(self.mode_changed)
            self.hbox111.addWidget(self.combo_mode)
        
        # 绘制图表
        self.plot(self.combo_lessons.currentIndex())
        
        # 更新统计信息
        self.label_total_time.setText(self.stats_manager.format_time(total_time))
        self.label_total_count.setText(f"{total_count}")
        
        # 刷新画布
        self.fig_canvas.draw()
    
    def mode_changed(self) -> None:
        """
        统计模式改变时更新图表
        
        当用户切换时间聚合模式(小时/天/月/年)时触发
        """
        self.plot(self.combo_lessons.currentIndex())
        self.fig_canvas.draw()
    
    # ==================== 图表绘制方法 ====================
    
    def plot(self, index: int) -> None:
        """
        根据索引绘制相应的统计图表
        
        Args:
            index: 课程索引
                - 0: 绘制全局统计(所有课程对比)
                - 其他: 绘制单课程历史统计
        """
        # 清除现有图表
        self.figure.clf()
        
        # 重置交互元素
        self.annot = None
        self.highlight_line = None
        self.highlight_bar = None
        
        # 创建图例区域
        self.legend_ax = self.figure.add_axes([0.056, 0.94, 1, 0.06])
        self.legend_ax.axis('off')
        self.legend_ax.set_navigate(False)  # 禁用图例轴的交互功能
        
        # 创建主坐标轴
        self.figure.set_tight_layout(False)
        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        
        if index == 0:
            # ========== 绘制全局统计 ==========
            self._plot_global_statistics()
        else:
            # ========== 绘制单课程统计 ==========
            self._plot_lesson_statistics(index)
        
        # 应用通用样式
        self._apply_plot_style()
    
    def _plot_global_statistics(self) -> None:
        """
        绘制全局统计图表(所有课程对比)
        
        X轴: 课程编号(01-40)
        左Y轴: 平均准确率
        右Y轴: 练习次数
        """
        # 设置坐标轴位置
        self.ax1.set_position([0.065, 0.15, 0.886, 0.72])
        self.ax2.set_position([0.065, 0.15, 0.886, 0.72])
        
        # 获取数据
        avg_accuracy = self.stats_manager.get_overall_stats().get("average_accuracy")
        lessons_index = self.stats_manager.get_overall_stats().get("practiced_lesson_numbers")
        lessons_index = [int(num) for num in lessons_index[1:]]  # 跳过"所有已学课程"
        
        accuracies = []
        counts = []
        
        for num in lessons_index:
            lesson_data = self.stats_manager.get_lesson_stats(num)
            accuracies.append(float(lesson_data.get("average_accuracy", 0)))
            counts.append(int(lesson_data.get("practice_count", 0)))
        
        # X轴设置
        x = lessons_index
        self.ax1.set_xlabel("Lesson ID", labelpad=6)
        self.ax1.set_xlim(0.5, 40.5)
        self.ax1.set_xticks(range(1, 41))
        self.ax1.set_xticklabels([str(i).zfill(2) for i in range(1, 41)])
        
        # 存储数据用于绘制
        self._draw_plot_elements(x, accuracies, counts, avg_accuracy)
    
    def _plot_lesson_statistics(self, lesson_id: int) -> None:
        """
        绘制单课程统计图表(练习历史)
        
        Args:
            lesson_id: 课程编号
        """
        lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
        if not lesson_data:
            self.ax1.clear()
            self.ax2.clear()
            return
        
        avg_accuracy = lesson_data.get("average_accuracy")
        
        # 获取聚合模式
        mode = self.combo_mode.currentText() if self.combo_mode else "Default"
        
        if mode == "Default":
            # ========== 原始数据(逐次练习) ==========
            history = lesson_data.get("accuracy_history", [])
            timestamps = [
                datetime.strptime(record["timestamp"], "%Y-%m-%dT%H:%M:%S") 
                for record in history
            ]
            formatted = [dt.strftime("%m-%d\n%H:%M") for dt in timestamps]
            accuracies = [record["accuracy"] for record in history]
            counts = list(range(1, len(history) + 1))
            
            # 设置坐标轴位置
            self.ax1.set_position([0.065, 0.198, 0.886, 0.67])
            self.ax2.set_position([0.065, 0.198, 0.886, 0.67])
        else:
            # ========== 按时间聚合 ==========
            formatted, accuracies, counts = self.stats_manager.aggregate_by_time_period(
                lesson_id, mode
            )
            if not formatted:  # 如果没有数据
                self.ax1.clear()
                self.ax2.clear()
                return
            
            # 根据模式调整坐标轴位置
            if mode != "Hour":
                self.ax1.set_position([0.065, 0.15, 0.886, 0.72])
                self.ax2.set_position([0.065, 0.15, 0.886, 0.72])
            else:
                self.ax1.set_position([0.065, 0.198, 0.886, 0.67])
                self.ax2.set_position([0.065, 0.198, 0.886, 0.67])
        
        # X轴设置
        x = list(range(1, len(formatted) + 1))
        self.ax1.set_xlabel("Practice Time", labelpad=6)
        self.ax1.set_xlim(0.5, len(formatted) + 0.5)
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels(formatted)
        
        # 绘制图表元素
        self._draw_plot_elements(x, accuracies, counts, avg_accuracy)
    
    def _draw_plot_elements(
        self, 
        x: list, 
        accuracies: list, 
        counts: list, 
        avg_accuracy: float
    ) -> None:
        """
        绘制图表的核心元素(折线图、柱状图、阈值线等)
        
        Args:
            x: X轴数据
            accuracies: 准确率数据
            counts: 练习次数数据
            avg_accuracy: 平均准确率
        """
        # 根据主题选择颜色
        if self.is_dark_theme:
            line_color = "#C8B5FC"       # 浅紫色(折线)
            bar_color = "#4A9B8E"        # 深青色(柱状图)
            threshold_color = "#F86D6B"  # 红色(阈值线)
            edge_color = "#CCABF4"       # 深色边框
            h_line_color = "#721ED9"     # 深紫色(高亮折线)
            h_bar_color = "#92E0D3"      # 浅青色(高亮柱)
            grid_color = "#444444"       # 深色网格线
            grid_alpha = 0.5
        else:
            line_color = "#721ED9"       # 深紫色(折线)
            bar_color = "#92E0D3"        # 浅青色(柱状图)
            threshold_color = "#F86D6B"  # 红色(阈值线)
            edge_color = "#9465CE"       # 浅色边框
            h_line_color = "#C8B5FC"     # 浅紫色(高亮折线)
            h_bar_color = "#4A9B8E"      # 深青色(高亮柱)
            grid_color = "#CCCCCC"       # 浅色网格线
            grid_alpha = 0.3
        
        # ========== 左轴(准确率) ==========
        self.ax1.tick_params(axis="both", direction="in", width=1, zorder=3, pad=5)
        self.ax1.tick_params(axis="x", which="both", bottom=False)
        line = self.ax1.plot(
            x, accuracies, 
            color=line_color, 
            marker="o", 
            markersize=4, 
            linewidth=1, 
            zorder=3, 
            clip_on=False
        )
        self.ax1.set_ylabel("Accuracy (%)", labelpad=6)
        self.ax1.set_ylim(0, 100)
        self.ax1.set_yticks(range(0, 101, 10))
        self.ax1.set_yticklabels([f"{i}" for i in range(0, 101, 10)])
        
        self.ax1.spines["left"].set_linewidth(1)
        self.ax1.spines["left"].set_zorder(3)
        self.ax1.spines["right"].set_linewidth(1)
        self.ax1.spines["bottom"].set_linewidth(1)
        self.ax1.spines["top"].set_visible(False)
        
        # ========== 右轴(练习次数) ==========
        self.ax2.tick_params(axis="both", direction="in", width=1, zorder=5)
        bar = self.ax2.bar(x, counts, color=bar_color, zorder=0.5)
        
        # 阈值线(90%准确率)
        hline1 = self.ax2.hlines(
            y=90, xmin=0, xmax=1, 
            color=threshold_color, 
            linestyles="--", 
            linewidth=1, 
            zorder=1, 
            transform=self.ax1.get_yaxis_transform(), 
            clip_on=False
        )
        
        # 平均准确率线
        hline2 = self.ax2.hlines(
            y=float(avg_accuracy), xmin=0, xmax=1, 
            color=line_color, 
            linestyles="--", 
            linewidth=1, 
            zorder=1, 
            transform=self.ax1.get_yaxis_transform(), 
            clip_on=False
        )
        
        self.ax2.set_ylabel("Practice Count", labelpad=6)
        self.ax2.yaxis.set_label_position("right")
        self.ax2.set_ylim(0, 20)
        self.ax2.set_yticks(range(0, 21, 2))
        self.ax2.set_yticklabels([f"{i}" for i in range(0, 21, 2)])
        
        self.ax2.hlines(
            y=range(0, 21, 2), xmin=0, xmax=1,
            color=grid_color,
            alpha=grid_alpha,
            linestyle="--",
            linewidth=1,
            zorder=0,
            transform=self.ax2.get_yaxis_transform(),
            clip_on=False
        )
        
        self.ax2.spines["right"].set_linewidth(1)
        self.ax2.spines["right"].set_zorder(5)
        self.ax2.spines["top"].set_visible(False)
        
        # 存储绘图对象
        self.line_plot = line[0]
        self.bar_plot = bar
        
        # ========== 创建高亮元素 ==========
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
        
        self.highlight_bar = Rectangle((0, 0), width=0, height=0, color=h_bar_color, zorder=0.5)
        self.ax2.add_patch(self.highlight_bar)
        self.highlight_bar.set_visible(False)
        
        # ========== 创建悬停提示框 ==========
        if hasattr(self, 'annot_config'):
            self.annot = self.ax1.annotate(
                "",
                xy=(0, 0),
                xytext=(0, 0),
                textcoords="offset points",
                ha="left",
                va="center",
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
                xytext=(0, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                bbox=dict(boxstyle="round", alpha=0.8),
                arrowprops=None,
                zorder=10
            )
        self.annot.set_visible(False)
        
        # ========== 创建图例 ==========
        handles = [line[0], hline2, hline1, bar]
        labels = [
            "Accuracy", 
            f"Average Accuracy: {avg_accuracy:.2f}%", 
            "Accuracy Threshold: 90%", 
            "Practice Count"
        ]
        self.legend_ax.clear()
        self.legend_ax.axis('off')
        self.legend_ax.legend(handles, labels, ncol=4, framealpha=1, loc="upper left")
        
        # 设置图层顺序
        self.ax1.set_zorder(4)
        self.ax2.set_zorder(3)
        self.ax1.patch.set_visible(False)
        
        # ========== 添加底部刻度线 ==========
        ax3 = self.figure.add_axes(self.ax1.get_position(), frameon=False)
        ax3.tick_params(axis="y", which="both", left=False, labelleft=False)
        ax3.tick_params(axis="x", which="both", bottom=True, labelbottom=False, direction="in", width=1)
        ax3.set_xlim(self.ax1.get_xlim())
        ax3.set_xticks(self.ax1.get_xticks())
    
    def _apply_plot_style(self) -> None:
        """
        应用绘图样式(预留方法，用于未来扩展)
        """
        pass
    
    # ==================== 交互事件处理 ====================
    
    def on_hover(self, event) -> None:
        """
        鼠标悬停事件处理
        
        当鼠标悬停在折线图点或柱状图柱上时，显示详细信息
        
        Args:
            event: matplotlib鼠标事件对象
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
    
    def _update_line_annot(self, ind: dict, event, offset: int = 10) -> None:
        """
        更新折线图点的提示框
        
        Args:
            ind: 包含索引信息的字典
            event: 鼠标事件对象
            offset: 提示框偏移量(像素)
        """
        i = ind["ind"][0]
        
        # 获取数据
        if self.combo_lessons.currentIndex() == 0:
            # 全局统计模式
            lesson_id = int(self.ax1.get_xticks()[i])
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            lesson_name = lesson_data.get("lesson_name")
            accuracy = lesson_data.get("average_accuracy", 0)
            text = f"Lesson {lesson_name}\nAccuracy: {accuracy:.2f}%"
        else:
            # 单课程统计模式
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
                text = f"Time: {time_str}\nAccuracy: {accuracy:.2f}%"
        
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
    
    def _update_bar_annot(self, i: int, event, offset: int = 10) -> None:
        """
        更新柱状图柱的提示框
        
        Args:
            i: 柱的索引
            event: 鼠标事件对象
            offset: 提示框偏移量(像素)
        """
        bar = self.bar_plot[i]
        
        # 获取数据
        if self.combo_lessons.currentIndex() == 0:
            # 全局统计模式
            lesson_id = int(self.ax1.get_xticks()[i])
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            lesson_name = lesson_data.get("lesson_name")
            count = lesson_data.get("practice_count")
            text = f"Lesson {lesson_name}\nPractice Count: {count}"
        else:
            # 单课程统计模式
            count = int(bar.get_height())
            text = f"Practice Count: {count}"
        
        # 提取柱子的边界
        x_left = bar.get_x()  # 柱子的左边界
        x_right = x_left + bar.get_width()  # 柱子的右边界
        y_mouse = event.ydata  # 鼠标的 y 坐标

        # 根据提示框宽度计算中心点偏移的位置
        ax_bbox = self.ax1.get_window_extent(self.fig_canvas.renderer)
        mid_x = (ax_bbox.x0 + ax_bbox.x1) / 2

        # 根据鼠标的位置判断提示框的位置和对齐方式
        if event.x < mid_x:  # 鼠标在图中央左侧
            x_annot = x_right
            xytext = (offset, 0)
            ha = "left"
        else:  # 鼠标在图中央右侧
            x_annot = x_left
            xytext = (-offset, 0)
            ha = "right"

        # 更新提示框属性
        self.annot.xy = (x_annot, y_mouse)
        self.annot.set_text(text)
        self.annot.set_ha(ha)
        self.annot.set_va("center")
        self.annot.set_position(xytext)
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
    
    # ==================== 辅助方法 ====================
    
    @staticmethod
    def clear_layout(layout: QHBoxLayout) -> None:
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
    
    # ==================== 主题与透明度设置 ====================
    
    def toggle_transparency(self, checked: bool) -> None:
        """
        切换窗口透明度
        
        Args:
            checked: True为透明，False为不透明
        """
        self.setWindowOpacity(0.1 if checked else 1.0)
    
    def update_window_icon(self, dark_mode: bool) -> None:
        """
        根据主题更新窗口图标
        
        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        try:
            if dark_mode:
                icon_path = config.get_logo_path('dark')
            else:
                icon_path = config.get_logo_path('light')
            
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # 如果图标文件不存在，使用默认图标
                self.setWindowIcon(FluentIcon.MUSIC.icon())
        except (OSError, AttributeError):
            # 发生错误时使用默认图标
            self.setWindowIcon(FluentIcon.MUSIC.icon())
    
    def toggle_theme(self, checked: bool) -> None:
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
    
    def apply_theme(self, dark_mode: bool) -> None:
        """
        应用主题(外部调用接口)
        
        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        self.toggle_theme(dark_mode)
        if hasattr(self, 'combo_lessons'):
            self.update_chart()
    
    def set_windows_title_bar_color(self, dark_mode: bool) -> None:
        """
        设置Windows标题栏颜色(仅Windows 11有效)
        
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
    
    def apply_matplotlib_theme(self, dark_mode: bool) -> None:
        """
        应用matplotlib主题
        
        配置matplotlib的全局样式参数，包括颜色、字体、抗锯齿等
        
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
                'font.family': 'Segoe UI',
                'font.size': 10.5,
                'axes.labelsize': 10.5,
                'axes.titlesize': 10.5,
                'xtick.labelsize': 9.5,
                'ytick.labelsize': 9.5,
                'legend.fontsize': 9.5,
                
                # 抗锯齿设置
                'lines.antialiased': True,
                'patch.antialiased': True,
                'text.antialiased': True
            })
            
            # 提示框配置(深色主题)
            self.annot_config = {
                'font_family': 'Segoe UI',
                'font_size': 9.5,
                'font_color': '#FFFFFF',
                'bg_color': '#2D2D2D',
                'bg_alpha': 0.95,
                'edge_color': '#555555',
                'edge_width': 1
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
                'font.family': 'Segoe UI',
                'font.size': 10.5,
                'axes.labelsize': 10.5,
                'axes.titlesize': 10.5,
                'xtick.labelsize': 9.5,
                'ytick.labelsize': 9.5,
                'legend.fontsize': 9.5,
                
                # 抗锯齿设置
                'lines.antialiased': True,
                'patch.antialiased': True,
                'text.antialiased': True
            })
            
            # 提示框配置(浅色主题)
            self.annot_config = {
                'font_family': 'Segoe UI',
                'font_size': 9.5,
                'font_color': '#000000',
                'bg_color': '#FFFFFF',
                'bg_alpha': 0.95,
                'edge_color': '#CCCCCC',
                'edge_width': 1
            }
        
        self.is_dark_theme = dark_mode


# ==================== 测试代码 ====================
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from Statistics import stats_manager
    import sys
    
    app = QApplication(sys.argv)
    
    stats_window = StatisticsWindow(
        stats_manager, 
        is_dark_theme=False, 
        is_transparent=False
    )
    stats_window.show()
    
    sys.exit(app.exec())