"""
Koch - 莫尔斯电码训练器
用于学习和练习莫尔斯电码字符识别

Author: xiaokanghu1997
Date: 2025-11-10
Version: 1.1.0
"""

import sys
from ctypes import windll, byref, sizeof, c_int
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from PySide6 import QtGui
from PySide6.QtCore import Qt, QUrl, QSettings, QTimer, QSize
from PySide6.QtGui import QShortcut, QKeySequence, QIcon, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox

from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, ComboBox, ProgressBar, 
    PushButton, TextEdit, setTheme, Theme, SwitchButton, FluentIcon
)

from Config import config
from Statistics import stats_manager


class KochWindow(QWidget):
    """Koch主窗口类"""
    
    # ==================== 常量定义 ====================
    COUNTDOWN_SECONDS = 3  # 倒计时秒数
    ICON_SIZE = QSize(12, 12)  # 按钮图标大小
    WINDOW_WIDTH = 777  # 窗口宽度
    WINDOW_HEIGHT = 300  # 窗口高度
    
    # 颜色配置（BGR格式）
    DARK_TITLE_BAR_COLOR = 0x00202020  # 深色模式标题栏颜色 RGB(32, 32, 32)
    LIGHT_TITLE_BAR_COLOR = 0x00F3F3F3  # 浅色模式标题栏颜色 RGB(243, 243, 243)
    
    # 准确率评价阈值
    EXCELLENT_THRESHOLD = 95.0  # 优秀
    GREAT_THRESHOLD = 90.0      # 很好
    GOOD_THRESHOLD = 80.0       # 良好
    FAIR_THRESHOLD = 70.0       # 及格
    
    # ==================== 类型注解 - UI控件 ====================
    # 布局对象
    layout_main: QVBoxLayout
    hbox1: QHBoxLayout
    hbox11: QHBoxLayout
    hbox12: QHBoxLayout
    hbox2: QHBoxLayout
    hbox21: QHBoxLayout
    hbox3: QHBoxLayout
    hbox31: QHBoxLayout
    hbox32: QHBoxLayout
    hbox4: QHBoxLayout
    hbox41: QHBoxLayout
    hbox42: QHBoxLayout
    hbox5: QHBoxLayout
    hbox6: QHBoxLayout
    hbox61: QHBoxLayout
    hbox62: QHBoxLayout
    hbox63: QHBoxLayout
    
    # 标签控件
    label_lesson_num: StrongBodyLabel  # 当前课程编号
    label_char_sound: StrongBodyLabel  # 当前字符显示
    label_char_total_time: BodyLabel  # 字符音频总时长
    label_char_current_time: BodyLabel  # 字符音频当前时间
    label_text_total_time: BodyLabel  # 文本音频总时长
    label_text_current_time: BodyLabel  # 文本音频当前时间
    
    # 交互控件
    combo_lessons: ComboBox  # 课程选择下拉框
    progress_char: ProgressBar  # 字符音频进度条
    progress_text: ProgressBar  # 文本音频进度条
    text_input: TextEdit  # 练习文本输入框
    
    # 按钮控件
    btn_char_play_pause: PushButton  # 字符音频播放/暂停按钮
    btn_char_restart: PushButton  # 字符音频重播按钮
    btn_text_play_pause: PushButton  # 文本音频播放/暂停按钮
    btn_text_restart: PushButton  # 文本音频重播按钮
    btn_check: PushButton  # 检查结果按钮
    
    # 开关控件
    switch_transparency: SwitchButton  # 透明度开关
    switch_theme: SwitchButton  # 主题开关
    
    # ==================== 类型注解 - 媒体播放器 ====================
    char_player: QMediaPlayer  # 字符音频播放器
    char_audio_output: QAudioOutput  # 字符音频输出
    text_player: QMediaPlayer  # 文本音频播放器
    text_audio_output: QAudioOutput  # 文本音频输出
    countdown_timer: QTimer  # 倒计时定时器
    
    # ==================== 类型注解 - 数据与状态 ====================
    settings: QSettings  # 设置存储对象
    total_characters: str  # 所有字符序列
    lesson_data: Dict[str, List[str]]  # 课程数据字典
    current_lesson_name: Optional[str]  # 当前课程名称
    current_text_index: int  # 当前练习文本索引
    is_result_checked: bool  # 是否已检查结果
    is_char_playing: bool  # 字符音频是否正在播放
    is_char_restart: bool  # 字符音频重播状态
    is_text_playing: bool  # 文本音频是否正在播放
    is_text_restart: bool  # 文本音频重播状态
    countdown_value: int  # 倒计时当前值
    is_countdown_active: bool  # 倒计时是否激活
    
    def __init__(self):
        """初始化Koch窗口"""
        super().__init__()

        # ==================== 检查资源完整性 ====================
        resource_status = config.check_resources()
        if not resource_status['complete']:
            self._show_resource_warning(resource_status)
        
        # ==================== 窗口基础设置 ====================
        self.setWindowTitle("Koch - Morse Code Trainer")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.set_windows_title_bar_color(False)  # 初始化为浅色标题栏
        self.update_window_icon(False)
        
        # ==================== 初始化设置存储 ====================
        self.settings = QSettings("Koch", "LessonProgress")
        
        # ==================== 初始化状态变量 ====================
        self.is_char_playing = False  # 字符音频是否正在播放
        self.is_char_restart = False  # 字符音频重播状态
        self.is_text_playing = False  # 文本音频是否正在播放
        self.is_text_restart = False  # 文本音频重播状态
        self.current_lesson_name = None  # 当前课程名称
        self.current_text_index = 0  # 当前练习文本索引（0-19）
        self.countdown_value = self.COUNTDOWN_SECONDS  # 倒计时当前值
        self.is_countdown_active = False  # 倒计时是否激活
        self.is_result_checked = False  # 结果是否已检查

        # ==================== 初始化练习计时器数据 ====================
        self.practice_start_time = None  # 练习开始时间
        self.practice_end_time = None  # 练习结束时间
        
        # ==================== 初始化课程数据 ====================
        self.init_lesson_data()
        
        # ==================== 初始化媒体播放器 ====================
        self.init_media_players()
        
        # ==================== 设置用户界面 ====================
        self.setup_ui()
        
        # ==================== 设置快捷键 ====================
        self.setup_shortcuts()
        
        # ==================== 加载上次保存的进度 ====================
        # 临时断开信号连接，避免加载进度时触发保存
        self.combo_lessons.currentTextChanged.disconnect(self.update_information)
        self.load_lesson_progress()
        # 重新连接信号
        self.combo_lessons.currentTextChanged.connect(self.update_information)
    
    # ==================== 初始化方法 ====================
    
    def init_lesson_data(self):
        """
        初始化课程数据
        根据Koch方法的字符序列生成40个课程
        每个课程包含当前及之前的所有字符
        """
        # Koch方法推荐的字符学习序列
        self.total_characters = "KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X"
        
        # 第1课：K和M
        self.lesson_data = {f"01 - {', '.join(self.total_characters[:2])}": list(
            self.total_characters[:2]
        )}

        # 第2 - 40课：逐步添加新字符
        for i in range(2, len(self.total_characters)):
            key = f"{i:02d} - {self.total_characters[i]}"
            self.lesson_data[key] = list(self.total_characters[:i + 1])
    
    def init_media_players(self):
        """
        初始化媒体播放器和相关组件
        包括字符音频播放器、文本音频播放器和倒计时定时器
        """
        # ========== 字符音频播放器 ==========
        self.char_player = QMediaPlayer()
        self.char_audio_output = QAudioOutput()
        self.char_player.setAudioOutput(self.char_audio_output)
        
        # 连接字符播放器信号
        self.char_player.positionChanged.connect(self.update_char_progress)
        self.char_player.durationChanged.connect(self.update_char_duration)
        self.char_player.playbackStateChanged.connect(self.update_char_playback_state)
        
        # ========== 文本音频播放器 ==========
        self.text_player = QMediaPlayer()
        self.text_audio_output = QAudioOutput()
        self.text_player.setAudioOutput(self.text_audio_output)
        
        # 连接文本播放器信号
        self.text_player.positionChanged.connect(self.update_text_progress)
        self.text_player.durationChanged.connect(self.update_text_duration)
        self.text_player.playbackStateChanged.connect(self.update_text_playback_state)
        
        # ========== 倒计时定时器 ==========
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
    
    # ==================== 资源检查方法 ====================

    def _show_resource_warning(self, status: dict):
        """显示资源缺失警告信息框"""
        msg = "Detected incomplete training resources!\n\n"
        if not status['character_audio']:
            msg += "- Missing character audio files.\n"
        if status['lessons']:
            msg += f"- Missing lessons: {', '.join(map(str, status['lessons']))}\n"
        msg += "\nPlease ensure all resources are available for proper functionality."

        QMessageBox.warning(self, "Resource Warning", msg)

    # ==================== 界面布局 ====================
    
    def setup_ui(self):
        """设置用户界面布局"""
        self.layout_main = QVBoxLayout(self)
        
        # 构建各行布局
        self._setup_row1()  # 课程信息和选择
        self._setup_row2()  # 当前课程字符显示
        self._setup_row3()  # 字符音频播放控制
        self._setup_row4()  # 文本音频播放控制
        self._setup_row5()  # 文本输入框
        self._setup_row6()  # 设置和结果显示
        
        # 将所有行添加到主布局
        self.layout_main.addLayout(self.hbox1)
        self.layout_main.addLayout(self.hbox2)
        self.layout_main.addLayout(self.hbox3)
        self.layout_main.addLayout(self.hbox4)
        self.layout_main.addLayout(self.hbox5)
        self.layout_main.addLayout(self.hbox6)
        
        # 初始化显示第一个课程的信息
        self.update_information(self.combo_lessons.currentText())
    
    def _setup_row1(self):
        """第一行：课程信息和选择下拉框"""
        self.hbox1 = QHBoxLayout()
        
        # 左侧：当前课程信息显示
        self.hbox11 = QHBoxLayout()
        self.hbox11.addWidget(BodyLabel("You are currently on lesson"))
        self.label_lesson_num = StrongBodyLabel("01")
        self.hbox11.addWidget(self.label_lesson_num)
        self.hbox11.addWidget(BodyLabel("of"))
        self.hbox11.addWidget(StrongBodyLabel("40"))
        self.hbox11.addWidget(BodyLabel("total lessons."))
        self.hbox11.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 右侧：课程选择下拉框
        self.hbox12 = QHBoxLayout()
        self.hbox12.addWidget(BodyLabel("Change to lesson:"))
        self.combo_lessons = ComboBox()
        self.combo_lessons.setFixedSize(100, 30)
        self.combo_lessons.setMaxVisibleItems(5)
        self.combo_lessons.addItems(list(self.lesson_data.keys()))
        self.combo_lessons.currentTextChanged.connect(self.update_information)
        self.hbox12.addWidget(self.combo_lessons)
        self.hbox12.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合左右两侧
        self.hbox1.addLayout(self.hbox11)
        self.hbox1.addStretch(1)  # 弹性空间
        self.hbox1.addLayout(self.hbox12)
    
    def _setup_row2(self):
        """第二行：当前课程包含的字符显示"""
        self.hbox2 = QHBoxLayout()
        self.hbox2.addWidget(BodyLabel("Current lesson characters:"))
        
        # 字符标签容器（动态生成）
        self.hbox21 = QHBoxLayout()
        self.hbox21.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.hbox2.addLayout(self.hbox21)
        self.hbox2.setAlignment(Qt.AlignmentFlag.AlignLeft)
    
    def _setup_row3(self):
        """第三行：字符音频播放控制"""
        self.hbox3 = QHBoxLayout()
        
        # 左侧：字符声音显示
        self.hbox31 = QHBoxLayout()
        self.hbox31.addWidget(StrongBodyLabel("The sound of character:"))
        self.label_char_sound = StrongBodyLabel("")
        self.hbox31.addWidget(self.label_char_sound)
        self.hbox31.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 右侧：播放控制
        self.hbox32 = QHBoxLayout()
        
        # 进度条
        self.progress_char = ProgressBar()
        self.progress_char.setFixedWidth(250)
        self.progress_char.setValue(0)
        self.hbox32.addWidget(self.progress_char)
        
        # 时间显示
        self.label_char_current_time = BodyLabel("00:00")
        self.label_char_current_time.setFixedWidth(40)
        self.label_char_current_time.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.hbox32.addWidget(self.label_char_current_time)
        self.hbox32.addWidget(BodyLabel("/"))
        self.label_char_total_time = BodyLabel("00:00")
        self.hbox32.addWidget(self.label_char_total_time)
        
        # 播放/暂停按钮
        self.btn_char_play_pause = PushButton("Play")
        self.btn_char_play_pause.setIcon(FluentIcon.PLAY)
        self.btn_char_play_pause.setIconSize(self.ICON_SIZE)
        self.btn_char_play_pause.setFixedSize(100, 30)
        self.btn_char_play_pause.clicked.connect(self.char_play_pause)
        self.hbox32.addWidget(self.btn_char_play_pause)
        
        # 重播按钮
        self.btn_char_restart = PushButton("Restart")
        self.btn_char_restart.setIcon(FluentIcon.SYNC)
        self.btn_char_restart.setIconSize(self.ICON_SIZE)
        self.btn_char_restart.setFixedSize(100, 30)
        self.btn_char_restart.setEnabled(False)
        self.btn_char_restart.clicked.connect(self.char_restart)
        self.hbox32.addWidget(self.btn_char_restart)
        
        self.hbox32.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合左右两侧
        self.hbox3.addLayout(self.hbox31)
        self.hbox3.addStretch(1)
        self.hbox3.addLayout(self.hbox32)
    
    def _setup_row4(self):
        """第四行：练习文本音频播放控制"""
        self.hbox4 = QHBoxLayout()
        
        # 左侧：标签
        self.hbox41 = QHBoxLayout()
        self.hbox41.addWidget(StrongBodyLabel("Practice text:"))
        self.hbox41.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 右侧：播放控制
        self.hbox42 = QHBoxLayout()
        
        # 进度条
        self.progress_text = ProgressBar()
        self.progress_text.setFixedWidth(250)
        self.progress_text.setValue(0)
        self.hbox42.addWidget(self.progress_text)
        
        # 时间显示
        self.label_text_current_time = BodyLabel("00:00")
        self.label_text_current_time.setFixedWidth(40)
        self.label_text_current_time.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.hbox42.addWidget(self.label_text_current_time)
        self.hbox42.addWidget(BodyLabel("/"))
        self.label_text_total_time = BodyLabel("00:00")
        self.hbox42.addWidget(self.label_text_total_time)
        
        # 播放/暂停按钮
        self.btn_text_play_pause = PushButton("Play")
        self.btn_text_play_pause.setIcon(FluentIcon.PLAY)
        self.btn_text_play_pause.setIconSize(self.ICON_SIZE)
        self.btn_text_play_pause.setFixedSize(100, 30)
        self.btn_text_play_pause.clicked.connect(self.text_play_pause)
        self.hbox42.addWidget(self.btn_text_play_pause)
        
        # 重播按钮
        self.btn_text_restart = PushButton("Restart")
        self.btn_text_restart.setIcon(FluentIcon.SYNC)
        self.btn_text_restart.setIconSize(self.ICON_SIZE)
        self.btn_text_restart.setFixedSize(100, 30)
        self.btn_text_restart.setEnabled(False)
        self.btn_text_restart.clicked.connect(self.text_restart)
        self.hbox42.addWidget(self.btn_text_restart)
        
        self.hbox42.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合左右两侧
        self.hbox4.addLayout(self.hbox41)
        self.hbox4.addStretch(1)
        self.hbox4.addLayout(self.hbox42)
    
    def _setup_row5(self):
        """第五行：练习文本输入框"""
        self.hbox5 = QHBoxLayout()
        self.text_input = TextEdit()
        self.text_input.setPlaceholderText("Enter your practice text here...")

        # 设置字体为等宽字体，提升莫尔斯码输入体验
        mono_font = QFont("Consolas", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_input.setFont(mono_font)
        
        # 连接文本变化信号，实时转换为大写
        self.text_input.textChanged.connect(self._convert_input_to_uppercase)
        
        self.hbox5.addWidget(self.text_input)
    
    def _setup_row6(self):
        """第六行：设置开关和结果显示"""
        self.hbox6 = QHBoxLayout()
        
        # 左侧：透明度和主题切换
        self.hbox61 = QHBoxLayout()
        
        # 透明度开关
        self.hbox61.addWidget(BodyLabel("Transparency:"))
        self.switch_transparency = SwitchButton()
        self.switch_transparency.setText("")
        self.switch_transparency.setCheckedIndicatorColor(
            QtGui.QColor(150, 150, 150), 
            QtGui.QColor(90, 90, 90)
        )
        self.switch_transparency.checkedChanged.connect(self.toggle_transparency)
        self.hbox61.addWidget(self.switch_transparency)
        
        # 主题开关
        self.hbox61.addWidget(BodyLabel("Dark Theme:"))
        self.switch_theme = SwitchButton()
        self.switch_theme.setText("")
        self.switch_theme.setCheckedIndicatorColor(
            QtGui.QColor(150, 150, 150), 
            QtGui.QColor(90, 90, 90)
        )
        self.switch_theme.checkedChanged.connect(self.toggle_theme)
        self.hbox61.addWidget(self.switch_theme)
        
        self.hbox61.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 中间：结果显示（动态生成）
        self.hbox62 = QHBoxLayout()
        self.hbox62.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 右侧：检查按钮和统计按钮
        self.hbox63 = QHBoxLayout()

        # 检查按钮
        self.btn_check = PushButton("Check Result")
        self.btn_check.setIcon(FluentIcon.ACCEPT)
        self.btn_check.setIconSize(self.ICON_SIZE)
        self.btn_check.setFixedSize(140, 30)
        self.btn_check.clicked.connect(self.check_result)
        self.hbox63.addWidget(self.btn_check)

        # 统计按钮
        self.btn_statistics = PushButton("Statistics")
        self.btn_statistics.setIcon(FluentIcon.CALORIES)
        self.btn_statistics.setIconSize(self.ICON_SIZE)
        self.btn_statistics.setFixedSize(110, 30)
        self.btn_statistics.clicked.connect(self.show_statistics_window)
        self.hbox63.addWidget(self.btn_statistics)

        self.hbox63.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合所有部分
        self.hbox6.addLayout(self.hbox61)
        self.hbox6.addLayout(self.hbox62)
        self.hbox6.addStretch(1)
        self.hbox6.addLayout(self.hbox63)
    
    def setup_shortcuts(self):
        """设置键盘快捷键"""
        # Ctrl+Enter 检查结果或下一个练习
        check_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        check_shortcut.activated.connect(self.check_result)
        
        # Ctrl+R 重播文本音频
        restart_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        restart_shortcut.activated.connect(self.text_restart)
        
        # Space 播放/暂停文本音频
        play_shortcut = QShortcut(QKeySequence("Space"), self)
        play_shortcut.activated.connect(self.text_play_pause)
    
    # ==================== 辅助工具方法 ====================

    @staticmethod
    def format_time(milliseconds: int) -> str:
        """
        将毫秒转换为 MM:SS 格式
        
        Args:
            milliseconds: 毫秒数
            
        Returns:
            格式化的时间字符串，如 "01:23"
        """
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def get_lesson_text_count(lesson_name: str) -> int:
        """
        获取指定课程的练习文本数量(课程文件夹下文件数量的一半)

        Args:
            lesson_name: 课程名称,如 "01 - K, M"
        
        Returns:
            练习文本数量
        """
        lesson_num = lesson_name.split(" ")[0]
        lesson_folder = config.get_lesson_dir(int(lesson_num))

        try:
            # 统计文件夹下的音频文件数量
            audio_files = list(lesson_folder.glob("koch-*.wav"))
            total_files = len(audio_files)
        
            # 返回文件数量的一半(向下取整)
            return total_files // 2
        except (OSError, FileNotFoundError):
            # 如果文件夹不存在或出错,返回默认值10
            return 10
    
    def set_play_button_state(self, button: PushButton, is_playing: bool):
        """
        统一设置播放按钮的状态（文本、图标）
        
        Args:
            button: 要设置的按钮对象
            is_playing: True为播放状态，False为暂停状态
        """
        button.setText("Pause" if is_playing else "Play")
        button.setIcon(FluentIcon.PAUSE if is_playing else FluentIcon.PLAY)
        button.setIconSize(self.ICON_SIZE)
    
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
    
    def _convert_input_to_uppercase(self):
        """
        将文本输入框中的内容实时转换为大写
        保持光标位置不变，避免干扰用户输入体验
        """
        # 获取当前光标位置
        cursor = self.text_input.textCursor()
        current_position = cursor.position()
        
        # 获取当前文本
        current_text = self.text_input.toPlainText()
        upper_text = current_text.upper()
        
        # 只有在文本实际改变时才更新（避免无限循环）
        if current_text != upper_text:
            # 临时断开信号连接，避免递归触发
            self.text_input.textChanged.disconnect(self._convert_input_to_uppercase)
            
            # 设置大写文本
            self.text_input.setPlainText(upper_text)
            
            # 恢复光标位置
            cursor.setPosition(current_position)
            self.text_input.setTextCursor(cursor)
            
            # 重新连接信号
            self.text_input.textChanged.connect(self._convert_input_to_uppercase)
    
    def _reset_check_button(self):
        """重置检查按钮到初始状态（内部方法）"""
        self.is_result_checked = False
        self.btn_check.setText("Check Result")
        self.btn_check.setIcon(FluentIcon.ACCEPT)
        self.btn_check.setIconSize(self.ICON_SIZE)
    
    def _get_accuracy_comment(self, accuracy: float) -> str:
        """
        根据准确率返回评价
        
        Args:
            accuracy: 准确率（0-100）
            
        Returns:
            评价字符串
        """
        if accuracy >= self.EXCELLENT_THRESHOLD:
            return " - Excellent!"
        elif accuracy >= self.GREAT_THRESHOLD:
            return " - Great!"
        elif accuracy >= self.GOOD_THRESHOLD:
            return " - Good!"
        elif accuracy >= self.FAIR_THRESHOLD:
            return " - Keep practicing!"
        else:
            return ""
    
    # ==================== 课程信息更新 ====================
    
    def update_information(self, lesson_name: str):
        """
        更新课程信息显示
        当用户切换课程时调用
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
        """
        # 如果是用户手动切换课程，保存课程名并重置文本索引
        if self.sender() == self.combo_lessons:
            self.save_lesson_name(lesson_name)
            self.current_text_index = self.settings.value(
                f"{lesson_name}_index", 0, type=int
            )
        
        # 更新当前课程信息
        self.current_lesson_name = lesson_name
        self.label_lesson_num.setText(lesson_name.split(" ")[0])
        
        # 清空并重新生成字符显示
        self.clear_layout(self.hbox21)
        
        # 为每个字符创建可点击的标签
        for char in self.lesson_data[lesson_name]:
            label_char = StrongBodyLabel(char)
            
            # 添加下划线样式
            font = label_char.font()
            font.setUnderline(True)
            label_char.setFont(font)
            
            # 设置鼠标悬停样式和点击事件
            label_char.setCursor(Qt.CursorShape.PointingHandCursor)
            label_char.mousePressEvent = lambda event, ch=char: self.update_label_char_sound(ch)
            self.hbox21.addWidget(label_char)
        
        # 更新字符声音显示
        # 第一次课只显示第一个字符，其他课显示最新学习的字符
        if lesson_name == "01 - K, M":
            self.label_char_sound.setText(self.lesson_data[lesson_name][0])
        else:
            self.label_char_sound.setText(self.lesson_data[lesson_name][-1])
        
        # 加载对应的音频资源
        self.char_media_load()
        self.text_media_load()
    
    def update_label_char_sound(self, character: str):
        """
        更新字符声音显示
        当用户点击字符标签时调用
        
        Args:
            character: 要显示和播放的字符
        """
        self.label_char_sound.setText(character)
        self.char_media_load()
    
    # ==================== 字符音频控制 ====================
    
    def char_media_load(self):
        """
        加载字符音频文件
        根据当前显示的字符加载对应的音频
        """
        current_character = self.label_char_sound.text()
        char_index = self.total_characters.index(current_character)
        
        # 使用 pathlib 构建音频文件路径
        audio_file = config.get_character_audio(char_index)
        self.char_player.setSource(QUrl.fromLocalFile(str(audio_file)))
    
    def char_play_pause(self):
        """字符音频播放/暂停切换"""
        if not self.is_char_playing:  # 当前暂停，开始播放
            self.char_player.play()
            self.set_play_button_state(self.btn_char_play_pause, True)
            self.is_char_restart = False
            self.btn_char_restart.setEnabled(True)
        else:  # 当前播放，暂停
            self.char_player.pause()
            self.set_play_button_state(self.btn_char_play_pause, False)
        
        self.is_char_playing = not self.is_char_playing
    
    def char_restart(self):
        """
        字符音频重播
        第一次点击停止播放，第二次点击从头播放
        """
        if not self.is_char_restart:  # 第一次点击：停止
            self.char_player.stop()
            self.is_char_restart = True
            self.set_play_button_state(self.btn_char_play_pause, False)
            self.is_char_playing = False
        else:  # 第二次点击：从头播放
            self.char_player.play()
            self.is_char_restart = False
            self.set_play_button_state(self.btn_char_play_pause, True)
            self.is_char_playing = True
        
        self.is_char_restart = not self.is_char_restart
    
    def update_char_progress(self, position: int):
        """
        更新字符音频播放进度
        
        Args:
            position: 当前播放位置（毫秒）
        """
        self.progress_char.setValue(position)
        self.label_char_current_time.setText(self.format_time(position))
    
    def update_char_duration(self, duration: int):
        """
        更新字符音频总时长
        
        Args:
            duration: 音频总时长（毫秒）
        """
        self.label_char_total_time.setText(self.format_time(duration))
        self.progress_char.setMaximum(duration)
    
    def update_char_playback_state(self, state: QMediaPlayer.PlaybackState):
        """
        更新字符音频播放状态
        当音频播放完毕时重置按钮状态
        
        Args:
            state: 播放器状态
        """
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.set_play_button_state(self.btn_char_play_pause, False)
            self.is_char_playing = False
            self.progress_char.setValue(0)
            self.btn_char_restart.setEnabled(False)
            self.is_char_restart = False
    
    # ==================== 练习文本音频控制 ====================
    
    def text_media_load(self):
        """
        加载练习文本音频文件
        根据当前课程和文本索引加载对应的音频
        """
        lesson_num = self.label_lesson_num.text()
        audio_file = config.get_lesson_audio(int(lesson_num), self.current_text_index + 1)

        self.text_player.setSource(QUrl.fromLocalFile(str(audio_file)))

        # 重新连接信号（如果之前断开过）
        try:
            self.text_input.textChanged.disconnect(self._convert_input_to_uppercase)
        except (TypeError, RuntimeError):
            # 如果信号未连接或已断开，忽略错误
            pass

        self.text_input.clear()  # 清空输入框
        self.text_input.setPlainText("")  # 重置为纯文本
        self.text_input.setReadOnly(False)  # 允许输入

        # 重新连接信号
        self.text_input.textChanged.connect(self._convert_input_to_uppercase)

        self.clear_layout(self.hbox62)  # 清除结果显示
        self._reset_check_button()  # 重置检查按钮状态

        self.practice_start_time = None  # 重置练习开始时间
        self.practice_end_time = None  # 重置练习结束时间
    
    def text_play_pause(self):
        """
        练习文本音频播放/暂停切换
        如果从头开始播放，会先进行倒计时
        """
        if self.is_countdown_active:  # 倒计时中，点击取消
            self.cancel_countdown()
        elif not self.is_text_playing:  # 当前暂停，开始播放
            if self.text_player.position() == 0:  # 从头开始，启动倒计时
                self.start_countdown()
            else:  # 继续播放
                self.text_player.play()
                self.set_play_button_state(self.btn_text_play_pause, True)
                self.is_text_playing = True
                self.btn_text_restart.setEnabled(True)
        else:  # 当前播放，暂停
            self.text_player.pause()
            self.set_play_button_state(self.btn_text_play_pause, False)
            self.is_text_playing = False
    
    def start_countdown(self):
        """开始3秒倒计时"""
        self.countdown_value = self.COUNTDOWN_SECONDS
        self.is_countdown_active = True
        
        # 设置按钮为取消状态
        self.btn_text_play_pause.setText("Cancel")
        self.btn_text_play_pause.setIcon(FluentIcon.CANCEL)
        self.btn_text_play_pause.setIconSize(self.ICON_SIZE)
        
        self.btn_text_restart.setEnabled(False)
        self.label_text_current_time.setText(f"-00:0{self.countdown_value}")
        self.countdown_timer.start(1000)  # 每秒触发一次
    
    def update_countdown(self):
        """
        更新倒计时显示
        倒计时结束后自动开始播放
        """
        self.countdown_value -= 1
        
        if self.countdown_value > 0:  # 还在倒计时
            self.label_text_current_time.setText(f"-00:0{self.countdown_value}")
        else:  # 倒计时结束，开始播放
            self.countdown_timer.stop()
            self.is_countdown_active = False

            if self.practice_start_time is None:
                self.practice_start_time = datetime.now()  # 记录练习开始时间

            self.text_player.play()
            self.set_play_button_state(self.btn_text_play_pause, True)
            self.is_text_playing = True
            self.btn_text_restart.setEnabled(True)
    
    def cancel_countdown(self):
        """取消倒计时"""
        self.countdown_timer.stop()
        self.is_countdown_active = False
        self.countdown_value = self.COUNTDOWN_SECONDS
        self.set_play_button_state(self.btn_text_play_pause, False)
        self.label_text_current_time.setText("00:00")
    
    def text_restart(self):
        """
        练习文本音频重播
        第一次点击停止播放，第二次点击从头播放
        """
        if not self.is_text_restart:  # 第一次点击：停止
            self.text_player.stop()
            self.is_text_restart = True
            self.set_play_button_state(self.btn_text_play_pause, False)
            self.is_text_playing = False
        else:  # 第二次点击：从头播放
            self.text_player.play()
            self.is_text_restart = False
            self.set_play_button_state(self.btn_text_play_pause, True)
            self.is_text_playing = True
        
        self.is_text_restart = not self.is_text_restart
    
    def update_text_progress(self, position: int):
        """
        更新练习文本音频播放进度
        
        Args:
            position: 当前播放位置（毫秒）
        """
        self.progress_text.setValue(position)
        self.label_text_current_time.setText(self.format_time(position))
    
    def update_text_duration(self, duration: int):
        """
        更新练习文本音频总时长
        
        Args:
            duration: 音频总时长（毫秒）
        """
        self.label_text_total_time.setText(self.format_time(duration))
        self.progress_text.setMaximum(duration)
    
    def update_text_playback_state(self, state: QMediaPlayer.PlaybackState):
        """
        更新练习文本音频播放状态
        当音频播放完毕时重置按钮状态
        
        Args:
            state: 播放器状态
        """
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.set_play_button_state(self.btn_text_play_pause, False)
            self.is_text_playing = False
            self.progress_text.setValue(0)
            self.btn_text_restart.setEnabled(False)
            self.is_text_restart = False
    
    # ==================== 结果检查与评分 ====================
    
    def check_result(self):
        """
        检查练习结果或进入下一个练习
        根据当前状态决定行为：
        - 未检查状态：检查结果并显示准确率
        - 已检查状态：进入下一个练习
        """
        if not self.is_result_checked:
            # ========== 第一次点击：检查结果 ==========
            self._show_check_result()
            
            # 更新按钮状态
            self.is_result_checked = True
            self.btn_check.setText("Next Practice")
            self.btn_check.setIcon(FluentIcon.CHEVRON_RIGHT)
            self.btn_check.setIconSize(self.ICON_SIZE)
        else:
            # ========== 第二次点击：下一个练习 ==========
            self.next_text()
    
    def _show_check_result(self):
        """
        显示检查结果（内部方法）
        比对用户输入与标准答案，计算准确率并高亮显示错误
        """
        try:
            # 获取用户输入的文本
            practice_text = self.text_input.toPlainText().upper()
            practice_text = practice_text.replace("\n", " ").strip()
            
            # 读取标准答案文件（使用 pathlib）
            lesson_num = self.label_lesson_num.text()
            result_file = config.get_lesson_text(int(lesson_num), self.current_text_index + 1)
            
            with open(result_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # 从第一行开始读取
                result_characters = "".join(lines).replace("\n", " ").upper().strip()
            
            # 定义等宽字体样式的HTML模板
            font_family = "font-family: Consolas, monospace;"

            # 逐字符对比并生成HTML高亮文本
            correct_count = 0
            total_count = max(len(practice_text), len(result_characters))  # 总字符数取较大值（防止多输入影响计算结果）
            html_text = ""

            for i in range(len(result_characters)):
                if i < len(practice_text):
                    if practice_text[i] == result_characters[i]:  # 正确字符：绿色
                        html_text += f'<span style="{font_family} color: #00AA00;">{practice_text[i]}</span>'
                        correct_count += 1
                    else:  # 错误字符：红色 + 浅红色背景
                        html_text += f'<span style="{font_family} color: #CC0000; background-color: #FFE6E6;">{practice_text[i]}</span>'
                else:  # 缺失字符：橙色 + 浅橙色背景
                    html_text += f'<span style="{font_family} color: #FF8C00; background-color: #FFF4E6;">{result_characters[i]}</span>'
            
            # 处理多余的字符
            if len(practice_text) > len(result_characters):
                for i in range(len(result_characters), len(practice_text)):  # 多余字符：蓝色 + 浅蓝色背景
                    html_text += f'<span style="{font_family} color: #0066CC; background-color: #E6F2FF;">{practice_text[i]}</span>'
            
            # 断开大写转换信号，避免干扰HTML设置
            self.text_input.textChanged.disconnect(self._convert_input_to_uppercase)

            # 显示标准答案
            separator = f'<br><span style="{font_family} color: #888888;">----------------------------</span>'
            answer_text = f'<br><span style="{font_family} color: #888888;">{result_characters}</span>'

            full_html = html_text + separator + answer_text

            # 显示高亮结果（不清空内容）
            self.text_input.setHtml(full_html)

            # 计算并显示准确率
            accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
            
            self.clear_layout(self.hbox62)
            comment = self._get_accuracy_comment(accuracy)
            self.hbox62.addWidget(BodyLabel(f"Accuracy: {accuracy:.2f}%{comment}"))

            # 设置text_input为只读，防止用户修改结果
            self.text_input.setReadOnly(True)

            # 保存统计数据
            if self.practice_start_time:
                self.practice_end_time = datetime.now()
                practice_time = (self.practice_end_time - self.practice_start_time).total_seconds()
                stats_manager.add_practice_record(
                    lesson_num=self.current_lesson_name,
                    accuracy=accuracy,
                    practice_time=practice_time,
                )
            
        except FileNotFoundError:
            # 文件不存在时的错误处理
            self.clear_layout(self.hbox62)
            self.hbox62.addWidget(BodyLabel("Error: Answer file not found!"))
        except Exception as e:
            # 其他异常的错误处理
            self.clear_layout(self.hbox62)
            self.hbox62.addWidget(BodyLabel(f"Error: {str(e)}"))
    
    def next_text(self):
        """
        进入下一个练习文本
        索引循环范围根据当前课程的文本数量决定
        """
        # 获取当前课程的文本数量
        max_texts = self.get_lesson_text_count(self.current_lesson_name)
        
        self.current_text_index += 1
        if self.current_text_index >= max_texts:
            self.current_text_index = 0
        
        self.save_lesson_progress(self.current_lesson_name, self.current_text_index)
        self.text_media_load()  # 这会自动清空输入框、重置按钮状态
    
    # ==================== 进度保存与加载 ====================
    
    def save_lesson_name(self, lesson_name: str):
        """
        保存当前课程名称
        
        Args:
            lesson_name: 要保存的课程名称
        """
        self.settings.setValue("current_lesson", lesson_name)
        self.settings.sync()
    
    def save_lesson_progress(self, lesson_name: str, text_index: int):
        """
        保存课程进度
        
        Args:
            lesson_name: 课程名称
            text_index: 练习文本索引（0-19）
        """
        self.settings.setValue(f"{lesson_name}_index", text_index)
        self.save_lesson_name(lesson_name)
    
    def load_lesson_progress(self):
        """
        加载上次保存的课程进度
        如果没有保存记录，则从第一课开始
        """
        saved_lesson = self.settings.value("current_lesson", None)
        
        if saved_lesson and saved_lesson in self.lesson_data:
            # 加载保存的课程
            combo_index = self.combo_lessons.findText(saved_lesson)
            if combo_index != -1:
                self.combo_lessons.setCurrentIndex(combo_index)
                saved_text_index = self.settings.value(
                    f"{saved_lesson}_index", 0, type=int
                )
                self.current_lesson_name = saved_lesson
                self.current_text_index = saved_text_index
                self.update_information(saved_lesson)
        else:
            # 从第一课开始
            self.combo_lessons.setCurrentIndex(0)
            self.current_lesson_name = self.combo_lessons.currentText()
            self.current_text_index = 0
            self.update_information(self.current_lesson_name)
    
    # ==================== 主题与透明度设置 ====================
    
    def toggle_transparency(self, checked: bool):
        """
        切换窗口透明度
        
        Args:
            checked: True为透明，False为不透明
        """
        self.setWindowOpacity(0.1 if checked else 1.0)
        self.switch_transparency.setText("")

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
        
        self.switch_theme.setText("")
    
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
    
    # ==================== 统计窗口显示 ====================

    def show_statistics_window(self):
        """显示统计信息窗口"""
        # 延迟导入，避免循环依赖
        from Statistics_Window import StatisticsWindow
        
        # 传入当前主题状态（True=深色，False=浅色）
        current_theme = self.switch_theme.isChecked()
        current_transparent = self.switch_transparency.isChecked()
    
        if not hasattr(self, 'statistics_window') or not self.statistics_window.isVisible():
            self.statistics_window = StatisticsWindow(stats_manager, current_theme, current_transparent)
            self.statistics_window.show()
        else:
            # 如果窗口已存在，更新主题并激活
            self.statistics_window.apply_theme(current_theme)
            self.statistics_window.activateWindow()
            self.statistics_window.raise_()
    
    # ==================== 窗口事件处理 ====================
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        在关闭前保存当前进度
        
        Args:
            event: 关闭事件对象
        """
        self.save_lesson_progress(self.current_lesson_name, self.current_text_index)
        super().closeEvent(event)


# ==================== 程序入口 ====================

if __name__ == "__main__":
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置默认浅色主题
    setTheme(Theme.LIGHT)
    
    # 创建并显示主窗口
    window = KochWindow()
    window.show()
    
    # 进入应用程序主循环
    sys.exit(app.exec())