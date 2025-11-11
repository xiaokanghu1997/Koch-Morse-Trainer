"""
Koch 统计窗口
显示学习统计数据和图表

Author: xiaokanghu1997
Date: 2025-11-10
Version: 1.1.0
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    BodyLabel, ComboBox
)
from Statistics import StatisticsManager
from Config import config
import pyqtgraph as pg
from datetime import datetime


class StatisticsWindow(QWidget):
    """统计数据展示窗口"""
    
    def __init__(self, stats_manager: StatisticsManager):
        super().__init__()
        self.stats_manager = stats_manager
        
        # 窗口设置
        self.setWindowTitle("Statistics")
        self.setFixedSize(777, 500)
        icon_path = config.get_logo_path('light')
        self.setWindowIcon(QIcon(str(icon_path)))
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 初始化UI
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # ========== 第一行：标签和下拉框 ==========
        self.first_row_layout = QHBoxLayout()
        
        self.label_select = BodyLabel("Select lesson:")
        self.first_row_layout.addWidget(self.label_select)
        
        self.combo_lessons = ComboBox()
        self.combo_lessons.setFixedSize(200, 30)
        self.combo_lessons.setMaxVisibleItems(10)
        
        # 添加选项
        self.combo_lessons.addItem("Current all lessons")
        lessons_data = self.stats_manager.data.get("lessons", {})
        for i in range(1, 41):
            lesson_key = None
            # 查找对应的课程键
            for key in lessons_data.keys():
                if key.startswith(f"{i:02d} - "):
                    lesson_key = key
                    break
            if lesson_key and lessons_data.get(lesson_key, {}).get("practice_count", 0) > 0:
                self.combo_lessons.addItem(lesson_key)
        
        self.combo_lessons.currentTextChanged.connect(self.update_chart)
        self.first_row_layout.addWidget(self.combo_lessons)
        self.first_row_layout.addStretch(1)
        
        self.main_layout.addLayout(self.first_row_layout)
        
        # ========== 第二行：图表 ==========
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        self.main_layout.addWidget(self.plot_widget)
        
        # 初始化显示
        self.update_chart("Current all lessons")
    
    def update_chart(self, selection: str):
        """
        根据选择更新图表
        
        Args:
            selection: 选择的课程名称
        """
        self.plot_widget.clear()
        
        if selection == "Current all lessons":
            self.draw_all_lessons_chart()
        else:
            # 提取课程编号
            lesson_num = int(selection.split()[0])
            self.draw_single_lesson_chart(lesson_num)
    
    def draw_all_lessons_chart(self):
        """绘制所有课程的双Y轴统计图（仅绘制有练习记录的课程）"""
        # 配置图表
        self.plot_widget.setLabel('left', 'Accuracy (%)', color='#0078D4')
        self.plot_widget.setLabel('bottom', 'Lesson Number', color='black')
        self.plot_widget.showAxis('right')
        self.plot_widget.getAxis('right').setLabel('Practice Count', color='#10893E')
        
        # 获取统计数据
        lessons_data = self.stats_manager.data.get("lessons", {})
        
        # 如果没有任何练习记录，显示提示
        if not lessons_data:
            text_item = pg.TextItem(
                "No practice data available yet.\nStart practicing to see statistics!",
                color='#888888',
                anchor=(0.5, 0.5)
            )
            text_item.setPos(20, 50)
            self.plot_widget.addItem(text_item)
            self.plot_widget.setYRange(0, 100, padding=0)
            self.plot_widget.setXRange(1, 40, padding=0)
            self.plot_widget.disableAutoRange()
            return
        
        # 准备数据（只包含有记录的课程）
        x_data = []
        accuracy_data = []
        practice_count_data = []
        
        for i in range(1, 41):
            lesson_key = None
            # 查找对应的课程键
            for key in lessons_data.keys():
                if key.startswith(f"{i:02d} - "):
                    lesson_key = key
                    break
            
            # 只添加有练习记录的课程
            if lesson_key and lesson_key in lessons_data:
                lesson_stats = lessons_data[lesson_key]
                # 确保至少有一次练习记录
                if lesson_stats.get("practice_count", 0) > 0:
                    x_data.append(i)
                    accuracy_data.append(lesson_stats.get("average_accuracy", 0))
                    practice_count_data.append(lesson_stats.get("practice_count", 0))
        
        # 如果没有有效数据，显示提示
        if not x_data:
            text_item = pg.TextItem(
                "No valid practice data available.\nComplete at least one practice to see statistics!",
                color='#888888',
                anchor=(0.5, 0.5)
            )
            text_item.setPos(20, 50)
            self.plot_widget.addItem(text_item)
            self.plot_widget.setYRange(0, 100, padding=0)
            self.plot_widget.setXRange(1, 40, padding=0)
            self.plot_widget.disableAutoRange()
            return
        
        # 绘制折线图（准确率）- 左Y轴
        pen_accuracy = pg.mkPen(color='#0078D4', width=2)
        accuracy_line = pg.PlotCurveItem(
            x_data, 
            accuracy_data, 
            pen=pen_accuracy,
            name='Accuracy'
        )
        self.plot_widget.addItem(accuracy_line)
        
        # 添加折线图的散点
        accuracy_scatter = pg.ScatterPlotItem(
            x_data, 
            accuracy_data, 
            size=8, 
            brush='#0078D4'
        )
        self.plot_widget.addItem(accuracy_scatter)
        
        # 创建第二个Y轴（右侧）- 用于练习次数
        self.view_box2 = pg.ViewBox()
        self.plot_widget.scene().addItem(self.view_box2)
        self.plot_widget.getAxis('right').linkToView(self.view_box2)
        self.view_box2.setXLink(self.plot_widget)
        
        # 绘制柱状图（练习次数）- 右Y轴
        bargraph = pg.BarGraphItem(
            x=x_data, 
            height=practice_count_data, 
            width=0.6, 
            brush='#10893E',
            name='Practice Count'
        )
        self.view_box2.addItem(bargraph)
        
        # 计算平均准确率
        avg_accuracy = sum(accuracy_data) / len(accuracy_data) if accuracy_data else 0
        
        # 添加平均准确率线（虚线）
        avg_line = pg.InfiniteLine(
            pos=avg_accuracy, 
            angle=0, 
            pen=pg.mkPen(color='#FF8C00', width=2, style=Qt.PenStyle.DashLine),
            label=f'Avg: {avg_accuracy:.1f}%',
            labelOpts={'position': 0.95, 'color': '#FF8C00', 'fill': '#FFFFFF', 'movable': False}
        )
        self.plot_widget.addItem(avg_line)
        
        # 添加90%准确率线（虚线）
        target_line = pg.InfiniteLine(
            pos=90, 
            angle=0, 
            pen=pg.mkPen(color='#E74856', width=2, style=Qt.PenStyle.DashLine),
            label='Target: 90%',
            labelOpts={'position': 0.05, 'color': '#E74856', 'fill': '#FFFFFF', 'movable': False}
        )
        self.plot_widget.addItem(target_line)
        
        # 更新视图函数
        def updateViews():
            self.view_box2.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
            self.view_box2.linkedViewChanged(self.plot_widget.getViewBox(), self.view_box2.XAxis)
        
        updateViews()
        self.plot_widget.getViewBox().sigResized.connect(updateViews)
        
        # 设置X轴刻度显示1-40的所有课程编号
        x_ticks = [(i, str(i)) for i in range(1, 41)]
        x_axis = self.plot_widget.getAxis('bottom')
        x_axis.setTicks([x_ticks])
        
        # 固定显示范围
        self.plot_widget.setXRange(0, 41, padding=0)
        self.plot_widget.setYRange(0, 100, padding=0)
        
        # 禁用自动范围调整（关键步骤）
        self.plot_widget.disableAutoRange()
        
        # 添加图例
        legend = self.plot_widget.addLegend(offset=(10, 10))
        legend.setParentItem(self.plot_widget.getPlotItem())
    
    def draw_single_lesson_chart(self, lesson_num: int):
        """
        绘制单个课程的练习历史折线图
        
        Args:
            lesson_num: 课程编号（1-40）
        """
        # 配置图表
        self.plot_widget.setLabel('left', 'Accuracy (%)', color='#0078D4')
        self.plot_widget.setLabel('bottom', 'Practice Time', color='black')
        self.plot_widget.getAxis('right').setStyle(showValues=False)
        
        # 获取课程统计数据
        lessons_data = self.stats_manager.data.get("lessons", {})
        lesson_key = None
        
        # 查找对应的课程键
        for key in lessons_data.keys():
            if key.startswith(f"{lesson_num:02d} - "):
                lesson_key = key
                break
        
        if not lesson_key or lesson_key not in lessons_data:
            # 没有数据时显示提示
            text_item = pg.TextItem(
                "No practice data available for this lesson.\nStart practicing to see your progress!",
                color='#888888',
                anchor=(0.5, 0.5)
            )
            text_item.setPos(5, 50)
            self.plot_widget.addItem(text_item)
            self.plot_widget.setYRange(0, 100, padding=0)
            self.plot_widget.setXRange(0, 10, padding=0)
            return
        
        lesson_stats = lessons_data[lesson_key]
        history = lesson_stats.get("accuracy_history", [])
        
        if not history:
            # 没有历史记录时显示提示
            text_item = pg.TextItem(
                "No practice history available for this lesson.\nComplete at least one practice!",
                color='#888888',
                anchor=(0.5, 0.5)
            )
            text_item.setPos(5, 50)
            self.plot_widget.addItem(text_item)
            self.plot_widget.setYRange(0, 100, padding=0)
            self.plot_widget.setXRange(0, 10, padding=0)
            return
        
        # 准备数据
        x_data = list(range(1, len(history) + 1))
        accuracy_data = [record.get("accuracy", 0) for record in history]
        time_labels = []
        
        for record in history:
            timestamp = record.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_labels.append(dt.strftime("%m-%d %H:%M"))
                except ValueError:
                    time_labels.append("")
            else:
                time_labels.append("")
        
        # 绘制折线图
        pen = pg.mkPen(color='#0078D4', width=2)
        line = pg.PlotCurveItem(
            x_data, 
            accuracy_data, 
            pen=pen,
            name='Accuracy'
        )
        self.plot_widget.addItem(line)
        
        # 添加散点
        scatter = pg.ScatterPlotItem(
            x_data, 
            accuracy_data, 
            size=8, 
            brush='#0078D4'
        )
        self.plot_widget.addItem(scatter)
        
        # 添加90%准确率线（虚线）
        target_line = pg.InfiniteLine(
            pos=90, 
            angle=0, 
            pen=pg.mkPen(color='#E74856', width=2, style=Qt.PenStyle.DashLine),
            label='Target: 90%',
            labelOpts={'position': 0.95, 'color': '#E74856', 'fill': '#FFFFFF', 'movable': False}
        )
        self.plot_widget.addItem(target_line)
        
        # 设置X轴刻度标签
        if len(time_labels) <= 10:
            # 数据点少于10个时，显示所有时间标签
            x_ticks = [(i+1, label) for i, label in enumerate(time_labels)]
        else:
            # 数据点多于10个时，只显示部分时间标签
            step = max(1, len(time_labels) // 10)
            x_ticks = [(i+1, time_labels[i]) for i in range(0, len(time_labels), step)]
        
        x_axis = self.plot_widget.getAxis('bottom')
        x_axis.setTicks([x_ticks])
        
        # 设置Y轴范围
        self.plot_widget.setYRange(0, 100, padding=0.1)
        
        # 设置X轴范围
        self.plot_widget.setXRange(0.5, len(x_data) + 0.5, padding=0.05)
        
        # 添加图例
        legend = self.plot_widget.addLegend(offset=(10, 10))
        legend.setParentItem(self.plot_widget.getPlotItem())