"""
Koch 统计窗口
显示学习统计数据和图表

Author: Xiaokang HU
Date: 2025-11-28
Version: 1.2.0
"""

from ctypes import windll, byref, sizeof, c_int
from datetime import datetime
from typing import Optional

from PySide6 import QtGui
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDialog, QSizePolicy

from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, ComboBox, SegmentedToolWidget,
    setTheme, Theme, FluentIcon
)

from Config import config
from Statistics import StatisticsManager


class StatisticsWindow(QDialog):
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
    DARK_TITLE_BAR_COLOR = 0x00202020        # 深色模式标题栏颜色 RGB(32, 32, 32)
    LIGHT_TITLE_BAR_COLOR = 0x00F3F3F3       # 浅色模式标题栏颜色 RGB(243, 243, 243)

    WINDOW_WIDTH_CALENDAR = 840              # 日历热力图窗口宽度
    WINDOW_HEIGHT_CALENDAR = 250             # 日历热力图窗口高度
    WINDOW_WIDTH_TABLE = 840                 # 统计图表窗口宽度
    WINDOW_HEIGHT_TABLE = 360                # 统计图表窗口高度
    
    # ==================== 类型注解 - UI控件 ====================
    layout_main: QVBoxLayout                 # 主布局
    hbox1: QHBoxLayout                       # 第一行布局
    hbox11: QHBoxLayout                      # 日历与统计图表切换
    hbox12: QHBoxLayout                      # 统计信息与统计模式选择区
    hbox121: QHBoxLayout                     # 日历信息与课程选择区
    hbox122: QHBoxLayout                     # 统计模式选择区
    hbox13: QHBoxLayout                      # 统计信息显示区
    hbox2: QHBoxLayout                       # 第二行布局(图表)
    
    segmented_tool: SegmentedToolWidget      # 日历与统计图表切换控件
    combo_year: ComboBox                     # 年份选择下拉框
    combo_lessons: ComboBox                  # 课程选择下拉框
    combo_mode: Optional[ComboBox]           # 统计模式下拉框(动态创建)
    label_year_total_count: StrongBodyLabel  # 年度总练习次数标签
    label_year_total_time: StrongBodyLabel   # 年度总练习时长标签
    label_year_avg_accuracy: StrongBodyLabel # 年度平均准确率标签
    label_total_time: StrongBodyLabel        # 总练习时长标签
    label_total_count: StrongBodyLabel       # 总练习次数标签
    chart_view: QWebEngineView               # 图表显示控件
    
    # ==================== 类型注解 - 状态变量 ====================
    stats_manager: StatisticsManager         # 统计管理器实例
    is_dark_theme: bool                      # 是否为深色主题
    is_transparent: bool                     # 是否为透明窗口

    # ==================== 类型注解 - 图表信息 ====================
    current_html_theme: str                  # 当前HTML主题
    current_table_info: str                  # 当前表格信息
    current_calendar_info: str               # 当前日历信息

    def __init__(
        self, 
        statistics_manager,
        is_dark_theme: bool = False, 
        is_transparent: bool = False,
        parent: Optional[QWidget] = None
    ):
        """
        初始化统计窗口
        
        Args:
            statistics_manager: 统计数据管理器实例
            is_dark_theme: 是否应用深色主题
            is_transparent: 是否应用透明效果
        """
        super().__init__(parent)

        # 设置数据管理器
        self.stats_manager = statistics_manager
        
        # 设置窗口基础属性
        self.setWindowTitle("Statistics")
        self.setFixedSize(self.WINDOW_WIDTH_CALENDAR, self.WINDOW_HEIGHT_CALENDAR)

        # 初始化状态变量
        self.is_dark_theme = is_dark_theme
        self.is_transparent = is_transparent

        # 设置图表信息
        self.current_html_theme = None
        self.current_table_info = None
        self.current_calendar_info = None

        # 初始化数据结构
        self._html_templates = {}
        self._chart_initialized = False
        self._titlebar_applied = False

        # 加载HTML模板
        self._load_html_templates()

        # 应用主题与透明度设置
        self.toggle_theme(is_dark_theme)
        self.toggle_transparency(is_transparent)
        
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
        self.layout_main.addLayout(self.hbox2, stretch=1)
        self.layout_main.setAlignment(Qt.AlignmentFlag.AlignTop)
    
    def _setup_row1(self) -> None:
        """
        第一行: 统计信息和课程选择
        
        包含:
        - 左侧: 课程选择下拉框 + 统计模式选择(动态显示)
        - 右侧: 总练习时长和总练习次数
        """
        self.hbox1 = QHBoxLayout()

        # 左侧: 日历与统计图表切换
        self.hbox11 = QHBoxLayout()
        self.segmented_tool = SegmentedToolWidget()
        self.segmented_tool.addItem("Calendar", FluentIcon.CALENDAR)
        self.segmented_tool.addItem("Table", FluentIcon.MARKET)
        self.segmented_tool.setFixedSize(60, 30)
        self.segmented_tool.setCurrentItem("Calendar")
        self.segmented_tool.currentItemChanged.connect(self.update_chart)
        self.hbox11.addWidget(self.segmented_tool)
        
        # 中间: 课程与统计模式选择区
        self.hbox12 = QHBoxLayout()
        self.hbox121 = QHBoxLayout()
        total_years = self.stats_manager.get_all_practice_years()
        practice_data, practice_info = self.stats_manager.get_daily_practice_count_by_year(total_years[-1])
        self.label_year_total_count = StrongBodyLabel()
        self.label_year_total_count.setText(f"{practice_info.get('total_practice_count', 0)}")
        self.hbox121.addWidget(self.label_year_total_count)
        self.hbox121.addWidget(BodyLabel("practics,"))
        self.label_year_total_time = StrongBodyLabel()
        self.label_year_total_time.setText(
            self.stats_manager.format_time(practice_info.get('total_practice_time', 0))
        )
        self.hbox121.addWidget(self.label_year_total_time)
        self.hbox121.addWidget(BodyLabel("total time,"))
        self.label_year_avg_accuracy = StrongBodyLabel()
        self.label_year_avg_accuracy.setText(
            f"{practice_info.get('average_accuracy', 0):.2f}%"
        )
        self.hbox121.addWidget(self.label_year_avg_accuracy)
        self.hbox121.addWidget(BodyLabel("average accuracy in"))
        self.combo_year = ComboBox()
        self.combo_year.setFixedSize(80, 30)
        self.combo_year.addItems([str(year) for year in total_years])
        self.combo_year.setCurrentIndex(len(total_years) - 1)
        self.combo_year.currentIndexChanged.connect(self.update_calendar)
        self.hbox121.addWidget(self.combo_year)
        self.hbox12.addLayout(self.hbox121)
        self.hbox12.addSpacing(10)
        self.hbox122 = QHBoxLayout()
        self.hbox12.addLayout(self.hbox122)
        self.hbox12.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 右侧: 统计信息显示
        self.hbox13 = QHBoxLayout()
        self.hbox13.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合左中右布局
        self.hbox1.addLayout(self.hbox11)
        self.hbox1.addSpacing(10)
        self.hbox1.addLayout(self.hbox12)
        self.hbox1.addSpacing(10)
        self.hbox1.addLayout(self.hbox13)
        self.hbox1.setAlignment(Qt.AlignmentFlag.AlignLeft)
    
    def _setup_row2(self) -> None:
        """
        第二行: 统计图表区域
        
        使用echarts绘制图表:
        """
        self.hbox2 = QHBoxLayout()
        
        self.chart_view = QWebEngineView()
        self.chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        bg_color = QtGui.QColor(32, 32, 32) if self.is_dark_theme else QtGui.QColor(243, 243, 243)
        self.chart_view.page().setBackgroundColor(bg_color)

        start_page = f'<html><body style="background-color: {bg_color.name()}; margin: 0; padding: 0; width: 100%; height: 100%;"></body></html>'
        self.chart_view.setHtml(start_page)

        self.hbox2.addWidget(self.chart_view)  
    
    def _setup_calendar_ui(self) -> None:
        """
        设置日历热力图的UI控件
        """
        self.setFixedSize(self.WINDOW_WIDTH_CALENDAR, self.WINDOW_HEIGHT_CALENDAR)
        self.clear_all_widgets()

        total_years = self.stats_manager.get_all_practice_years()
        practice_data, practice_info = self.stats_manager.get_daily_practice_count_by_year(total_years[-1])
        
        self.label_year_total_count = StrongBodyLabel(f"{practice_info.get('total_practice_count', 0)}")
        self.hbox121.addWidget(self.label_year_total_count)
        self.hbox121.addWidget(BodyLabel("practics,"))
        
        self.label_year_total_time = StrongBodyLabel(
            self.stats_manager.format_time(practice_info.get('total_practice_time', 0))
        )
        self.hbox121.addWidget(self.label_year_total_time)
        self.hbox121.addWidget(BodyLabel("total time,"))
        
        self.label_year_avg_accuracy = StrongBodyLabel(
            f"{practice_info.get('average_accuracy', 0):.2f}%"
        )
        self.hbox121.addWidget(self.label_year_avg_accuracy)
        self.hbox121.addWidget(BodyLabel("average accuracy in"))

        self.combo_year = ComboBox()
        self.combo_year.setFixedSize(80, 30)
        self.combo_year.addItems([str(year) for year in total_years])
        self.combo_year.setCurrentIndex(len(total_years) - 1)
        self.combo_year.currentIndexChanged.connect(self.update_calendar)
        self.hbox121.addWidget(self.combo_year)
    
    def _setup_table_ui(self) -> None:
        """
        设置统计图表的UI控件
        """
        self.setFixedSize(self.WINDOW_WIDTH_TABLE, self.WINDOW_HEIGHT_TABLE)
        self.clear_all_widgets()

        self.hbox121.addWidget(BodyLabel("Select lesson:"))
        self.combo_lessons = ComboBox()
        self.combo_lessons.setFixedSize(100, 30)
        self.combo_lessons.setMaxVisibleItems(5)
        lesson_names = self.stats_manager.get_overall_stats().get("practiced_lesson_names")
        self.combo_lessons.addItems(lesson_names)
        self.combo_lessons.currentIndexChanged.connect(self.update_table)
        self.hbox121.addWidget(self.combo_lessons)

        self.hbox13.addWidget(BodyLabel("Total practice time:"))
        total_time = self.stats_manager.get_overall_stats().get("total_practice_time")
        self.label_total_time = StrongBodyLabel(self.stats_manager.format_time(total_time))
        self.hbox13.addWidget(self.label_total_time)
        self.hbox13.addSpacing(10)

        self.hbox13.addWidget(BodyLabel("Total practice count:"))
        total_count = self.stats_manager.get_overall_stats().get("total_practice_count")
        self.label_total_count = StrongBodyLabel(f"{total_count}")
        self.hbox13.addWidget(self.label_total_count)
    
    # ==================== 图表更新控制 ====================

    def update_chart(self) -> None:
        """
        根据segmented_tool情况绘制图表

        两种情况：
        1. 日历热力图: 显示当年每日的练习数量
        2. 统计图表: 显示课程的练习情况
        """
        if self.segmented_tool.currentRouteKey() == "Calendar":
            self._setup_calendar_ui()
            self._plot_calendar_statistics()
        else:
            self._setup_table_ui()
            self._plot_global_statistics()
    
    def update_calendar(self) -> None:
        """
        根据选择更新日历热力图
        
        显示所选年份的每日练习数量
        """
        self._plot_calendar_statistics()
    
    def update_table(self) -> None:
        """
        根据选择更新统计图表
        
        处理两种情况:
        1. 全局统计(索引0): 显示所有课程的统计对比
        2. 单课程统计: 显示该课程的练习历史
        """
        if self.combo_lessons.currentIndex() == 0:
            # 全局统计模式
            total_time = self.stats_manager.get_overall_stats().get("total_practice_time")
            total_count = self.stats_manager.get_overall_stats().get("total_practice_count")
            
            # 隐藏统计模式选择
            self.clear_layout(self.hbox122)
            self.combo_mode = None
        else:
            # 单课程统计模式
            lesson_id = self.combo_lessons.currentIndex()
            lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
            total_time = lesson_data.get("practice_time")
            total_count = lesson_data.get("practice_count")
            
            # 显示统计模式选择
            self.clear_layout(self.hbox122)
            self.combo_mode = None
            self.hbox122.addWidget(BodyLabel("Statistic by:"))
            
            # 创建统计模式下拉框
            self.combo_mode = ComboBox()
            self.combo_mode.setFixedSize(90, 30)
            self.combo_mode.setMaxVisibleItems(5)
            self.combo_mode.addItems(["Default", "Hour", "Day", "Month", "Year"])
            self.combo_mode.currentIndexChanged.connect(self.mode_changed)
            self.hbox122.addWidget(self.combo_mode)
        
        # 绘制图表
        self.plot(self.combo_lessons.currentIndex())
        
        # 更新统计信息
        self.label_total_time.setText(self.stats_manager.format_time(total_time))
        self.label_total_count.setText(f"{total_count}")
    
    def mode_changed(self) -> None:
        """
        统计模式改变时更新图表
        
        当用户切换时间聚合模式(小时/天/月/年)时触发
        """
        self.plot(self.combo_lessons.currentIndex())
    
    # ==================== 图表绘制方法 ====================
    
    def plot(self, index: int) -> None:
        """
        根据索引绘制相应的统计图表
        
        Args:
            index: 课程索引
                - 0: 绘制全局统计(所有课程对比)
                - 其他: 绘制单课程历史统计
        """
        if index == 0:
            # 绘制全局统计
            self._plot_global_statistics()
        else:
            # 绘制单课程统计
            self._plot_lesson_statistics(index)
    
    def _plot_calendar_statistics(self) -> None:
        """
        绘制日历热力图统计图表
        
        显示当年每日的练习数量
        """
        # 获取数据
        year = int(self.combo_year.currentText())
        practice_data, practice_info = self.stats_manager.get_daily_practice_count_by_year(year)

        self.label_year_total_count.setText(f"{practice_info.get('total_practice_count', 0)}")
        self.label_year_total_time.setText(
            self.stats_manager.format_time(practice_info.get('total_practice_time', 0))
        )
        self.label_year_avg_accuracy.setText(
            f"{practice_info.get('average_accuracy', 0):.2f}%"
        )

        html_content = self._generate_html('calendar', {
            "const dataYear = 2025;": f"const dataYear = {year};",
            "const calendarData = [];": f"const calendarData = {repr(practice_data)};"
        })

        base_url = QUrl.fromLocalFile(str(config.echarts_dir) + "/")
        self.chart_view.setHtml(html_content, base_url)

    def _plot_global_statistics(self) -> None:
        """
        绘制全局统计图表(所有课程对比)
        
        X轴: 课程编号(01-40)
        左Y轴: 平均准确率
        右Y轴: 练习次数
        """
        # 获取数据
        avg_accuracy = "{:.2f}".format(self.stats_manager.get_overall_stats().get("average_accuracy"))
        lessons_index = self.stats_manager.get_overall_stats().get("practiced_lesson_numbers")
        lessons_index = [int(num) for num in lessons_index[1:]]  # 跳过"所有已学课程"
        
        accuracies = []
        counts = []
        
        for num in lessons_index:
            lesson_data = self.stats_manager.get_lesson_stats(num)
            accuracies.append("{:.2f}".format(lesson_data.get("average_accuracy", 0)))
            counts.append(int(lesson_data.get("practice_count", 0)))
        
        xtickvalues = [str(i).zfill(2) for i in range(1, 41)]
        total_characters = "KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X"
        lesson_id = [f"01 - {', '.join(total_characters[:2])}"]
        for i in range(2, len(total_characters)):
            lesson_id.append(f"{i:02d} - {total_characters[i]}")
        
        data_replacement = {
            "const xlabel = '';": "const xlabel = 'Lesson ID';",
            "const xtickvalues = [];": f"const xtickvalues = {repr(xtickvalues)};",
            "const lessonID = [];": f"const lessonID = {repr(lesson_id)};",
            "const y0label = '';": "const y0label = 'Practice Accuracy';",
            "const y0labelunit = '';": "const y0labelunit = '(%)';",
            "const y0min = 0;": "const y0min = 0;",
            "const y0max = 0;": "const y0max = 100;",
            "const y0values = [];": f"const y0values = {repr(accuracies)};",
            "const y1label = '';": "const y1label = 'Practice Count';",
            "const y1labelunit = '';": "const y1labelunit = '';",
            "const y1min = 0;": "const y1min = 0;",
            "const y1max = 0;": "const y1max = 20;",
            "const y1values = [];": f"const y1values = {repr(counts)};",
            "const accuracy_avg = 0;": f"const accuracy_avg = {repr(avg_accuracy)};",
            "const threshold = 90;": "const threshold = 90;"
        }

        html_content = self._generate_html('table', data_replacement)
        base_url = QUrl.fromLocalFile(str(config.echarts_dir) + "/")
        self.chart_view.setHtml(html_content, base_url)

    def _plot_lesson_statistics(self, lesson_id: int) -> None:
        """
        绘制单课程统计图表(练习历史)
        
        Args:
            lesson_id: 课程编号
        """
        # 获取数据
        lesson_data = self.stats_manager.get_lesson_stats(lesson_id)
        avg_accuracy = "{:.2f}".format(lesson_data.get("average_accuracy"))
        
        # 获取聚合模式
        mode = self.combo_mode.currentText() if self.combo_mode else "Default"
        
        if mode == "Default":
            # 原始数据（逐次练习）
            history = lesson_data.get("accuracy_history", [])
            timestamps = [
                datetime.fromisoformat(record["timestamp"])
                for record in history
            ]
            formatted = [dt.strftime("%m-%d\n%H:%M") for dt in timestamps]
            accuracies = ["{:.2f}".format(record["accuracy"]) for record in history]
            counts = ["{:.2f}".format(record["practice_time"] / 60) for record in history]
            y1label = 'Practice Time'
            y1labelunit = '(min)'
            y1max = 10
        else:
            # 按时间聚合
            formatted, accuracies, counts, practice_times = self.stats_manager.aggregate_by_time_period(
                lesson_id, mode
            )
            accuracies = ["{:.2f}".format(accuracy) for accuracy in accuracies]
            y1label = 'Practice Count'
            y1labelunit = ''
            y1max = 20
        
        data_replacement = {
            "const xlabel = '';": "const xlabel = 'Time';",
            "const xtickvalues = [];": f"const xtickvalues = {repr(formatted)};",
            "const lessonID = [];": f"const lessonID = [];",
            "const y0label = '';": "const y0label = 'Practice Accuracy';",
            "const y0labelunit = '';": "const y0labelunit = '(%)';",
            "const y0min = 0;": "const y0min = 0;",
            "const y0max = 0;": "const y0max = 100;",
            "const y0values = [];": f"const y0values = {repr(accuracies)};",
            "const y1label = '';": f"const y1label = {repr(y1label)};",
            "const y1labelunit = '';": f"const y1labelunit = {repr(y1labelunit)};",
            "const y1min = 0;": "const y1min = 0;",
            "const y1max = 0;": f"const y1max = {y1max};",
            "const y1values = [];": f"const y1values = {repr(counts)};",
            "const accuracy_avg = 0;": f"const accuracy_avg = {repr(avg_accuracy)};",
            "const threshold = 90;": "const threshold = 90;"
        }

        html_content = self._generate_html('table', data_replacement)
        base_url = QUrl.fromLocalFile(str(config.echarts_dir) + "/")
        self.chart_view.setHtml(html_content, base_url)
        
    # ==================== 加载HTML ====================

    def _load_html_templates(self) -> None:
        """
        预加载HTML模板文件到内存
        """
        try:
            calendar_path = config.get_echarts_html('calendar')
            table_path = config.get_echarts_html('table')

            with open(calendar_path, 'r', encoding='utf-8') as file:
                self._html_templates['calendar'] = file.read()
            with open(table_path, 'r', encoding='utf-8') as file:
                self._html_templates['table'] = file.read()
        except FileNotFoundError:
            self._html_templates = {'calendar': '', 'table': ''}
    
    def _generate_html(self, template_type: str, data_dict: dict) -> str:
        """
        从模板生成HTML内容，不写入文件
        """
        html = self._html_templates.get(template_type, "")
        theme_str = "const isDark = true;" if self.is_dark_theme else "const isDark = false;"
        html = html.replace("const isDark = false;", theme_str)

        bg_color = "#202020" if self.is_dark_theme else "#F3F3F3"
        html = html.replace("background-color: #F3F3F3", f"background-color: {bg_color}")

        for key, value in data_dict.items():
            html = html.replace(key, value)
        return html

    # ==================== 辅助方法 ====================

    def clear_all_widgets(self) -> None:
        """
        清除所有动态创建的控件
        """
        self.clear_layout(self.hbox121)
        self.clear_layout(self.hbox122)
        self.clear_layout(self.hbox13)
        self.combo_year = None
        self.combo_lessons = None
        self.combo_mode = None
        self.label_total_time = None
        self.label_total_count = None
        self.label_year_total_count = None
        self.label_year_total_time = None
        self.label_year_avg_accuracy = None
    
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
    
    def toggle_theme(self, dark_mode: bool) -> None:
        """
        应用主题但不修改标题栏颜色(用于初始化时)
        
        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        if hasattr(self, 'chart_view'):
            bg_color = QtGui.QColor(32, 32, 32) if dark_mode else QtGui.QColor(243, 243, 243)
            self.chart_view.page().setBackgroundColor(bg_color)
        if dark_mode:  # 深色主题
            setTheme(Theme.DARK)
            self.setStyleSheet("QWidget { background-color: #202020; }")
            self.set_windows_title_bar_color(True)
            self.update_window_icon(True)
            self.apply_html_theme(True)
        else:  # 浅色主题
            setTheme(Theme.LIGHT)
            self.setStyleSheet("QWidget { background-color: #F3F3F3; }")
            self.set_windows_title_bar_color(False)
            self.update_window_icon(False)
            self.apply_html_theme(False)
    
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
    
    def apply_html_theme(self, dark_mode: bool) -> None:
        """
        应用HTML图表主题
        
        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        if hasattr(self, 'segmented_tool'):
            self.update_chart()

        self.is_dark_theme = dark_mode
    
    # ==================== 延迟渲染图表 ====================

    def showEvent(self, event) -> None:
        """
        窗口显示事件处理
        
        延迟渲染图表以提升初始加载性能
        """
        super().showEvent(event)
        if not self._titlebar_applied:
            self.set_windows_title_bar_color(self.is_dark_theme)
            self._titlebar_applied = True
        if not self._chart_initialized:
            self.update_chart()
            self._chart_initialized = True

    # ==================== 关闭窗口并重置HTML内容 ====================
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        在关闭前重置HTML内容
        
        Args:
            event: 关闭事件对象
        """
        if hasattr(self, 'chart_view'):
            self.chart_view.setHtml("")
        if hasattr(self, '_html_templates'):
            self._html_templates.clear()
        if hasattr(self, 'stats_manager'):
            if hasattr(self.stats_manager, '_lesson_cache'):
                self.stats_manager._lesson_cache.clear()
            if hasattr(self.stats_manager, '_overall_cache'):
                self.stats_manager._overall_cache = None
        super().closeEvent(event)

# ==================== 测试代码 ====================
# if __name__ == "__main__":
#     from PySide6.QtWidgets import QApplication
#     from Statistics import stats_manager
#     import sys
#     a = datetime.now()
#     app = QApplication(sys.argv)
#
#     stats_window = StatisticsWindow(stats_manager, is_dark_theme=False, is_transparent=False)
#     stats_window.show()
#     b = datetime.now()
#     print("Statistics window initialized in:", (b - a).total_seconds(), "seconds")
#
#     sys.exit(app.exec())