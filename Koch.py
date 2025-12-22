"""
Koch - 摩尔斯电码训练器
用于学习和练习摩尔斯电码字符识别

Author: Xiaokang HU
Date: 2025-12-22
Version: 1.2.6
"""

import sys
import wave
import logging
import numpy as np
import pyqtgraph as pg

from ctypes import windll, byref, sizeof, c_int
from typing import Optional, Dict, List
from datetime import datetime

from PySide6.QtCore import Qt, QUrl, QSettings, QTimer, QSize, QSignalBlocker
from PySide6.QtGui import QShortcut, QKeySequence, QIcon, QFont, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox

from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, ComboBox, Slider, ToolButton, PushButton,
    TextEdit, setTheme, setThemeColor, Theme, SwitchButton, FluentIcon
)

from Config import config
from Statistics import stats_manager


class KochWindow(QWidget):
    """Koch主窗口类"""
    
    # ==================== 常量定义 ====================
    APPLICATION_VERSION = "v1.2.6"              # 应用程序版本

    # 窗口尺寸
    WINDOW_WIDTH = 780                          # 窗口宽度
    WINDOW_HEIGHT = 280                         # 窗口高度
    WINDOW_HEIGHT_WAVE = 380                    # 窗口高度（启用波形时）

    # 控件尺寸
    COMBO_BOX_WIDTH = 100                       # 下拉框宽度
    COMBO_BOX_HEIGHT = 30                       # 下拉框高度
    PROGRESS_BAR_WIDTH = 270                    # 进度条宽度
    PROGRESS_BAR_HEIGHT = 21                    # 进度条高度
    PROGRESS_BAR_MIN = 0                        # 进度条最小值
    PROGRESS_BAR_MAX = 1000                     # 进度条最大值
    PROGRESS_BAR_DEFAULT = 0                    # 进度条默认值
    LABEL_WIDTH = 40                            # 标签宽度
    BUTTON_NORMAL_WIDTH = 100                   # 普通按钮宽度
    BUTTON_NORMAL_HEIGHT = 30                   # 普通按钮高度
    ICON_SIZE = QSize(12, 12)                   # 按钮图标大小

    # 设置面板尺寸
    SETTINGS_VIEW_WIDTH = 262                   # 设置面板宽度
    SETTINGS_VIEW_HEIGHT = 154                  # 设置面板高度

    # 透明度配置
    TRANSPARENCY_MIN = 10                       # 最小透明度
    TRANSPARENCY_MAX = 100                      # 最大透明度
    TRANSPARENCY_DEFAULT = 100                  # 默认透明度

    # 音量配置
    VOLUME_MIN = 0                              # 最小音量
    VOLUME_MAX = 100                            # 最大音量
    VOLUME_DEFAULT = 50                         # 默认音量

    # 倒计时配置
    COUNTDOWN_SECONDS = 3                       # 倒计时秒数
    
    # 颜色配置（BGR格式）
    DARK_THEME_COLOR = "#92E0D3"              # 深色主题主色调
    DARK_BACKGROUND_COLOR = "#202020"         # 深色模式背景颜色
    DARK_TITLE_BAR_COLOR = 0x00202020           # 深色模式标题栏颜色 RGB(32, 32, 32)
    LIGHT_THEME_COLOR = "#4A9B8E"             # 浅色主题主色调
    LIGHT_BACKGROUND_COLOR = "#F3F3F3"        # 浅色模式背景颜色
    LIGHT_TITLE_BAR_COLOR = 0x00F3F3F3          # 浅色模式标题栏颜色 RGB(243, 243, 243)
    
    # 准确率评价阈值
    EXCELLENT_THRESHOLD = 95.0                  # 优秀
    GREAT_THRESHOLD = 90.0                      # 很好
    GOOD_THRESHOLD = 80.0                       # 良好
    FAIR_THRESHOLD = 70.0                       # 及格

    # 波形图配置
    MORSE_BLOCK_SIZE = 100                      # 每个摩尔斯码块长度
    WAVEFORM_UPDATE_INTERVAL = 10               # 每次更新波形长度 (ms)
    WAVEFORM_WINDOW_SIZE = 1000                 # 波形显示窗口大小
    WAVEFORM_CHUNK_SIZE = 5                     # 每次波形更新块大小
    
    # ==================== 类型注解 - UI控件 ====================
    # 布局对象
    layout_main: QVBoxLayout                    # 主垂直布局
    hbox1: QHBoxLayout                          # 第一行水平布局
    hbox11: QHBoxLayout                         # 第一行左侧布局
    hbox12: QHBoxLayout                         # 第一行右侧布局
    hbox2: QHBoxLayout                          # 第二行水平布局
    hbox21: QHBoxLayout                         # 第二行左侧布局
    hbox3: QHBoxLayout                          # 第三行水平布局
    hbox31: QHBoxLayout                         # 第三行左侧布局
    hbox32: QHBoxLayout                         # 第三行右侧布局
    hbox4: QHBoxLayout                          # 第四行水平布局
    hbox41: QHBoxLayout                         # 第四行左侧布局
    hbox42: QHBoxLayout                         # 第四行右侧布局
    hbox5: QHBoxLayout                          # 第五行水平布局
    hbox6: QHBoxLayout                          # 第六行水平布局
    hbox7: QHBoxLayout                          # 第七行水平布局
    hbox71: QHBoxLayout                         # 第七行左侧布局
    hbox72: QHBoxLayout                         # 第七行中间布局
    hbox73: QHBoxLayout                         # 第七行右侧布局
    
    # 标签控件
    label_lesson_num: StrongBodyLabel           # 当前课程编号
    label_char_sound: StrongBodyLabel           # 当前字符显示
    label_char_total_time: BodyLabel            # 字符音频总时长
    label_char_current_time: BodyLabel          # 字符音频当前时间
    label_text_total_time: BodyLabel            # 文本音频总时长
    label_text_current_time: BodyLabel          # 文本音频当前时间
    
    # 交互控件
    combo_lessons: ComboBox                     # 课程选择下拉框
    progress_char: Slider                       # 字符音频进度条
    progress_text: Slider                       # 文本音频进度条
    text_input: TextEdit                        # 练习文本输入框
    
    # 按钮控件
    btn_char_play_pause: PushButton             # 字符音频播放/暂停按钮
    btn_char_restart: PushButton                # 字符音频重播按钮
    btn_text_play_pause: PushButton             # 文本音频播放/暂停按钮
    btn_text_restart: PushButton                # 文本音频重播按钮
    btn_settings: ToolButton                    # 设置按钮
    btn_check: PushButton                       # 检查结果按钮
    btn_statistics: PushButton                  # 统计窗口显示按钮
    
    # ==================== 类型注解 - 媒体播放器 ====================
    media_devices: QMediaDevices                # 音频设备管理器
    char_player: QMediaPlayer                   # 字符音频播放器
    char_audio_file: str                        # 字符音频文件路径
    char_audio_output: QAudioOutput             # 字符音频输出
    char_audio_duration: int                    # 字符音频总时长（毫秒）
    char_morse_array: Optional[List[int]]       # 字符摩尔斯码音频数据数组
    text_player: QMediaPlayer                   # 文本音频播放器
    text_audio_file: str                        # 文本音频文件路径
    text_audio_output: QAudioOutput             # 文本音频输出
    text_audio_duration: int                    # 文本音频总时长（毫秒）
    text_morse_array: Optional[List[int]]       # 文本摩尔斯码音频数据数组
    countdown_timer: QTimer                     # 倒计时定时器

    # ==================== 类型注解 - 设置面板 ====================
    settings_view: Optional[QWidget]            # 设置面板视图
    slider_volume: Optional[Slider]             # 音量滑块
    label_volume: Optional[BodyLabel]           # 音量标签
    slider_transparency: Optional[Slider]       # 透明度滑块
    label_transparency: Optional[BodyLabel]     # 透明度标签
    switch_theme: Optional[SwitchButton]        # 主题开关
    switch_waveform: Optional[SwitchButton]     # 波形显示开关

    # ==================== 类型注解 - 波形图 ====================
    plot_widget: Optional[pg.PlotWidget]        # 波形图控件
    waveform_curve: Optional[pg.PlotCurveItem]  # 波形曲线
    waveform_timer: Optional[QTimer]            # 波形更新定时器
    waveform_ptr: int                           # 当前绘制位置指针
    morse_array: Optional[List[int]]            # 当前音频摩尔斯码数据数组

    # ==================== 类型注解 - 日志记录器 ====================
    logger: logging.Logger                      # 日志记录器
    
    # ==================== 类型注解 - 数据与状态 ====================
    settings: QSettings                         # 设置存储对象
    total_characters: str                       # 所有字符序列
    lesson_data: Dict[str, List[str]]           # 课程数据字典
    current_lesson_name: Optional[str]          # 当前课程名称
    current_text_index: int                     # 当前练习文本索引
    is_result_checked: bool                     # 是否已检查结果
    is_char_playing: bool                       # 字符音频是否正在播放
    is_char_restart: bool                       # 字符音频重播状态
    is_char_seeking: bool                       # 字符音频进度条拖动状态
    is_char_playback_finished: bool             # 字符音频播放是否结束
    is_char_updating: bool                      # 字符音频进度条更新状态
    is_text_playing: bool                       # 文本音频是否正在播放
    is_text_restart: bool                       # 文本音频重播状态
    is_text_seeking: bool                       # 文本音频进度条拖动状态
    is_text_manually_seeked: bool               # 文本音频进度条手动拖动状态
    is_text_playback_finished: bool             # 文本音频播放是否结束
    is_text_updating: bool                      # 文本音频进度条更新状态
    countdown_value: int                        # 倒计时当前值
    is_countdown_active: bool                   # 倒计时是否激活
    is_settings_tip_open: bool                  # 设置面板是否打开
    is_dark_theme: bool                         # 当前是否为深色主题
    is_waveform_enabled: bool                   # 是否启用波形显示
    
    def __init__(self):
        """初始化Koch窗口"""
        super().__init__()

        # ==================== 日志记录配置 ====================
        self.logger = logging.getLogger("Koch")
        self.logger.info("Initializing Koch Application")

        # ==================== 检查资源完整性 ====================
        resource_status = config.check_resources()
        if not resource_status["complete"]:
            self._show_resource_warning(resource_status)
            self.logger.warning(f"Incomplete resources detected: {resource_status}")
        
        # ==================== 初始化状态变量 ====================
        self.is_char_playing = False  # 字符音频是否正在播放
        self.is_char_restart = False  # 字符音频重播状态
        self.is_char_seeking = False  # 字符音频进度条拖动状态
        self.is_char_playback_finished = False  # 字符音频播放是否结束
        self.is_char_updating = False   # 字符音频进度条更新状态（防止递归）

        self.is_text_playing = False  # 文本音频是否正在播放
        self.is_text_restart = False  # 文本音频重播状态
        self.is_text_seeking = False  # 文本音频进度条拖动状态
        self.is_text_manually_seeked = False  # 文本音频进度条手动拖动状态
        self.is_text_playback_finished = False  # 文本音频播放是否结束
        self.is_text_updating = False   # 文本音频进度条更新状态（防止递归）
        
        self.current_lesson_name = None  # 当前课程名称
        self.current_text_index = 0  # 当前练习文本索引（0-19）

        self.countdown_value = self.COUNTDOWN_SECONDS  # 倒计时当前值
        self.is_countdown_active = False  # 倒计时是否激活

        self.is_settings_tip_open = False  # 设置面板是否打开
        self.is_waveform_enabled = False  # 是否启用波形显示
        self.is_result_checked = False  # 结果是否已检查
        
        # ==================== 初始化设置存储 ====================
        self.settings = QSettings("Koch", "LessonProgress")
        
        # ==================== 窗口基础设置 ====================
        self.is_dark_theme = self.settings.value("dark_theme", False, type=bool)
        self.setWindowTitle(f"Koch - Morse Code Trainer {self.APPLICATION_VERSION}")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setWindowOpacity(self.TRANSPARENCY_DEFAULT / 100.0)  # 设置默认透明度
        # 应用主题
        if self.is_dark_theme:
            setTheme(Theme.DARK)
            setThemeColor(QColor(self.DARK_THEME_COLOR))
            self.setStyleSheet(f"QWidget {{ background-color: {self.DARK_BACKGROUND_COLOR}; }}")
            self.set_windows_title_bar_color(True)
            self.update_window_icon(True)
        else:
            setTheme(Theme.LIGHT)
            setThemeColor(QColor(self.LIGHT_THEME_COLOR))
            self.setStyleSheet(f"QWidget {{ background-color: {self.LIGHT_BACKGROUND_COLOR}; }}")
            self.set_windows_title_bar_color(False)
            self.update_window_icon(False)

        # ==================== 初始化练习计时器数据 ====================
        self.practice_start_time = None  # 练习开始时间
        self.practice_end_time = None  # 练习结束时间

        # ==================== 初始化波形图相关变量 ====================
        self.plot_widget = None  # 波形图控件
        self.waveform_curve = None  # 波形曲线
        self.waveform_ptr = 0  # 当前绘制位置指针
        self.morse_array = None  # 当前音频摩尔斯码数据数组
        self.waveform_timer = QTimer()  # 波形更新定时器
        self.waveform_timer.timeout.connect(self.update_waveform)
        # 预创建波形图控件
        self._create_waveform_widget()
        
        # ==================== 初始化课程数据 ====================
        self.init_lesson_data()
        
        # ==================== 初始化媒体播放器 ====================
        self.init_media_players()
        # 加载保存的音量，若无则使用默认值
        current_volume = self.settings.value("volume", self.VOLUME_DEFAULT / 100.0, type=float)
        self.char_audio_output.setVolume(current_volume)
        self.text_audio_output.setVolume(current_volume)
        # 获取媒体设备管理器
        self.media_devices = QMediaDevices(self)
        self.media_devices.audioOutputsChanged.connect(self.on_audio_device_changed)

        self.char_audio_file = None  # 字符音频文件路径
        self.char_audio_duration = 0  # 字符音频总时长（毫秒）
        self.char_morse_array = None  # 字符摩尔斯码音频数据数组
        self.text_audio_file = None  # 文本音频文件路径
        self.text_audio_duration = 0  # 文本音频总时长（毫秒）
        self.text_morse_array = None  # 文本摩尔斯码音频数据数组
        
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
        if not status["character_audio"]:
            msg += "- Missing character audio files.\n"
        if status["lessons"]:
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
        self._setup_row5()  # 波形图显示（可选）
        self._setup_row6()  # 文本输入框
        self._setup_row7()  # 设置和结果显示
        
        # 将所有行添加到主布局
        self.layout_main.addLayout(self.hbox1)
        self.layout_main.addLayout(self.hbox2)
        self.layout_main.addLayout(self.hbox3)
        self.layout_main.addLayout(self.hbox4)
        self.layout_main.addLayout(self.hbox5)
        self.layout_main.addLayout(self.hbox6)
        self.layout_main.addLayout(self.hbox7)
    
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
        self.combo_lessons.setFixedSize(self.COMBO_BOX_WIDTH, self.COMBO_BOX_HEIGHT)
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
        self.progress_char = Slider(Qt.Horizontal)
        self.progress_char.setFixedSize(self.PROGRESS_BAR_WIDTH, self.PROGRESS_BAR_HEIGHT)
        self.progress_char.setMinimum(self.PROGRESS_BAR_MIN)
        self.progress_char.setMaximum(self.PROGRESS_BAR_MAX)
        self.progress_char.setValue(self.PROGRESS_BAR_DEFAULT)
        self.progress_char.sliderPressed.connect(self.on_char_slider_pressed)
        self.progress_char.sliderReleased.connect(self.on_char_slider_released)
        self.progress_char.valueChanged.connect(self.on_char_slider_value_changed)
        self.hbox32.addWidget(self.progress_char)
        self.hbox32.addSpacing(-8)  # 微调间距
        
        # 时间显示
        self.label_char_current_time = BodyLabel("00:00")
        self.label_char_current_time.setFixedWidth(self.LABEL_WIDTH)
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
        self.btn_char_play_pause.setFixedSize(self.BUTTON_NORMAL_WIDTH, self.BUTTON_NORMAL_HEIGHT)
        self.btn_char_play_pause.clicked.connect(self.char_play_pause)
        self.hbox32.addWidget(self.btn_char_play_pause)
        
        # 重播按钮
        self.btn_char_restart = PushButton("Restart")
        self.btn_char_restart.setIcon(FluentIcon.SYNC)
        self.btn_char_restart.setIconSize(self.ICON_SIZE)
        self.btn_char_restart.setFixedSize(self.BUTTON_NORMAL_WIDTH, self.BUTTON_NORMAL_HEIGHT)
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
        self.progress_text = Slider(Qt.Horizontal)
        self.progress_text.setFixedSize(self.PROGRESS_BAR_WIDTH, self.PROGRESS_BAR_HEIGHT)
        self.progress_text.setMinimum(self.PROGRESS_BAR_MIN)
        self.progress_text.setMaximum(self.PROGRESS_BAR_MAX)
        self.progress_text.setValue(self.PROGRESS_BAR_DEFAULT)
        self.progress_text.sliderPressed.connect(self.on_text_slider_pressed)
        self.progress_text.sliderReleased.connect(self.on_text_slider_released)
        self.progress_text.valueChanged.connect(self.on_text_slider_value_changed)
        self.hbox42.addWidget(self.progress_text)
        self.hbox42.addSpacing(-8)  # 微调间距
        
        # 时间显示
        self.label_text_current_time = BodyLabel("00:00")
        self.label_text_current_time.setFixedWidth(self.LABEL_WIDTH)
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
        self.btn_text_play_pause.setFixedSize(self.BUTTON_NORMAL_WIDTH, self.BUTTON_NORMAL_HEIGHT)
        self.btn_text_play_pause.clicked.connect(self.text_play_pause)
        self.hbox42.addWidget(self.btn_text_play_pause)
        
        # 重播按钮
        self.btn_text_restart = PushButton("Restart")
        self.btn_text_restart.setIcon(FluentIcon.SYNC)
        self.btn_text_restart.setIconSize(self.ICON_SIZE)
        self.btn_text_restart.setFixedSize(self.BUTTON_NORMAL_WIDTH, self.BUTTON_NORMAL_HEIGHT)
        self.btn_text_restart.setEnabled(False)
        self.btn_text_restart.clicked.connect(self.text_restart)
        self.hbox42.addWidget(self.btn_text_restart)
        
        self.hbox42.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合左右两侧
        self.hbox4.addLayout(self.hbox41)
        self.hbox4.addStretch(1)
        self.hbox4.addLayout(self.hbox42)
    
    def _setup_row5(self):
        """第五行：波形图显示（可选）"""
        self.hbox5 = QHBoxLayout()
        self.hbox5.addWidget(self.plot_widget)
    
    def _setup_row6(self):
        """第六行：练习文本输入框"""
        self.hbox6 = QHBoxLayout()
        self.text_input = TextEdit()
        self.text_input.setPlaceholderText("Enter your practice text here...")
        self.text_input.setFixedHeight(89)

        # 设置字体为等宽字体，提升摩尔斯码输入体验
        mono_font = QFont("Consolas", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_input.setFont(mono_font)
        
        # 连接文本变化信号，实时转换为大写
        self.text_input.textChanged.connect(self._convert_input_to_uppercase)
        
        self.hbox6.addWidget(self.text_input)
    
    def _setup_row7(self):
        """第七行：设置开关和结果显示"""
        self.hbox7 = QHBoxLayout()
        
        # 左侧：设置按钮
        self.hbox71 = QHBoxLayout()

        # 设置按钮
        self.btn_settings = ToolButton()
        self.btn_settings.setIcon(FluentIcon.SETTING)
        self.btn_settings.setIconSize(self.ICON_SIZE)
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.clicked.connect(self.show_settings_view)
        self.hbox71.addWidget(self.btn_settings)
        
        self.hbox71.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 中间：结果显示（动态生成）
        self.hbox72 = QHBoxLayout()
        self.hbox72.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 右侧：检查按钮和统计按钮
        self.hbox73 = QHBoxLayout()

        # 检查按钮
        self.btn_check = PushButton("Check Result")
        self.btn_check.setIcon(FluentIcon.ACCEPT)
        self.btn_check.setIconSize(self.ICON_SIZE)
        self.btn_check.setFixedSize(140, 30)
        self.btn_check.clicked.connect(self.check_result)
        self.hbox73.addWidget(self.btn_check)

        # 统计按钮
        self.btn_statistics = PushButton("Statistics")
        self.btn_statistics.setIcon(FluentIcon.CALORIES)
        self.btn_statistics.setIconSize(self.ICON_SIZE)
        self.btn_statistics.setFixedSize(110, 30)
        self.btn_statistics.clicked.connect(self.show_statistics_window)
        self.hbox73.addWidget(self.btn_statistics)

        self.hbox73.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 组合所有部分
        self.hbox7.addLayout(self.hbox71)
        self.hbox7.addLayout(self.hbox72)
        self.hbox7.addStretch(1)
        self.hbox7.addLayout(self.hbox73)
    
    def _create_waveform_widget(self):
        """预创建波形图控件（初始隐藏状态）"""
        self.plot_widget = pg.PlotWidget(parent=self)
        self.plot_widget.setFixedHeight(94)  # 设置波形图高度
        self.plot_widget.plotItem.layout.setContentsMargins(5, 5, 5, 5)  # 设置边距

        self.plot_widget.setYRange(-0.2, 1.2)  # 设置Y轴范围

        self.plot_widget.showAxis("top", True)  # 显示顶部X轴
        self.plot_widget.showAxis("right", True)  # 显示右侧Y轴

        for axis in ["left", "bottom", "top", "right"]:
            self.plot_widget.getAxis(axis).setStyle(showValues=False)  # 隐藏刻度值

        self.plot_widget.enableAutoRange(axis="x", enable=False)  # 禁用X轴自动缩放
        self.plot_widget.enableAutoRange(axis="y", enable=False)  # 禁用Y轴自动缩放
        self.plot_widget.setMenuEnabled(False)  # 禁用右键菜单
        self.plot_widget.setMouseEnabled(x=True, y=False)  # X轴可交互，Y轴不可
        self.plot_widget.getViewBox().setMouseMode(pg.ViewBox.PanMode)  # 设置为平移模式
        self.plot_widget.hideButtons()  # 隐藏缩放按钮

        self.waveform_curve = self.plot_widget.plot([], [], antialias=True, stepMode=True)  # 初始化波形曲线
        self.waveform_curve.setZValue(100)  # 设置Z值，确保在顶部显示

        self.update_waveform_theme()  # 根据主题设置波形颜色
        self.plot_widget.hide()  # 初始隐藏波形图
    
    # ==================== 快捷键设置 ====================
    
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
            return 0
    
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
            # 使用信号阻塞器，避免递归触发
            with QSignalBlocker(self.text_input):
                # 设置大写文本
                self.text_input.setPlainText(upper_text)
            
                # 恢复光标位置
                cursor.setPosition(current_position)
                self.text_input.setTextCursor(cursor)
    
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
    
    def process_audio_to_morse(self, audio_path: str) -> List[int]:
        """
        处理音频文件，提取摩尔斯码音频数据数组
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            摩尔斯码音频数据数组
        """
        try:
            audio = wave.open(audio_path, 'rb')
            n_channels, _, sample_rate, n_frames = audio.getparams()[:4]
            str_wave_data = audio.readframes(n_frames)
            audio.close()

            wave_data = np.frombuffer(str_wave_data, dtype=np.short)
            if n_channels == 2:
                wave_data = wave_data.reshape(-1, 2).mean(axis=1)  # 转为单声道
            
            wave_avg = int(np.mean(np.abs(wave_data / 10))) * 10 # 计算平均振幅
            audio_duration = int((n_frames / sample_rate) * 1000)  # 毫秒

            morse_arr = []
            for i in range(0, len(wave_data), self.MORSE_BLOCK_SIZE):
                block = wave_data[i:i + self.MORSE_BLOCK_SIZE]
                if len(block) == 0:
                    continue
                value = 1 if np.mean(np.abs(block)) > wave_avg else 0
                morse_arr.append(value)
            
            return morse_arr, audio_duration
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            return [], 0
    
    def load_waveform(self, morse_array: Optional[List[int]], flag: bool, start_position: int = 0):
        """
        加载音频文件并处理波形数据
        
        Args:
            morse_array: 预处理的摩尔斯码音频数据数组
            flag: 标志位，指示是字符音频还是文本音频（True表示字符音频，False表示文本音频）
            start_position: 起始播放位置（毫秒），用于同步波形显示
        """        
        if morse_array is None:
            return
        
        self.morse_array = morse_array

        # 根据播放位置计算波形指针位置
        if self.morse_array and start_position > 0:
            if flag:
                audio_duration = self.char_audio_duration
            else:
                audio_duration = self.text_audio_duration
            if audio_duration > 0:
                # 计算对应的波形指针位置
                progress_ratio = start_position / audio_duration
                self.waveform_ptr = int(progress_ratio * len(self.morse_array))
        elif start_position == 0:
            # 如果波形指针已经到达末尾，不要重置
            is_char_waveform = (morse_array == self.char_morse_array)
            is_text_waveform = (morse_array == self.text_morse_array)
            if is_char_waveform and self.is_char_playback_finished and self.waveform_ptr >= len(self.morse_array):
                return
            elif is_text_waveform and self.is_text_playback_finished and self.waveform_ptr >= len(self.morse_array):
                return
            else:
                self.waveform_ptr = 0  # 从头开始

        # 重置波形曲线
        if self.waveform_curve is not None:
            if self.waveform_ptr > 0:  # 如果有数据，绘制初始波形
                y_data = self.morse_array[:self.waveform_ptr]
                x_data = list(range(len(y_data) + 1))
                self.waveform_curve.setData(x_data, y_data)

                center = self.waveform_ptr
                x_min = center - self.WAVEFORM_WINDOW_SIZE  # 左侧显示整个窗口
                x_max = center  # 右侧显示到当前点
                # x_min = center - int(self.WAVEFORM_WINDOW_SIZE * 0.75)  # 左侧显示75%的窗口
                # x_max = center + int(self.WAVEFORM_WINDOW_SIZE * 0.25)  # 右侧显示25%的窗口
                # x_min = center - self.WAVEFORM_WINDOW_SIZE // 2  # 左侧显示50%的窗口
                # x_max = center + self.WAVEFORM_WINDOW_SIZE // 2  # 右侧显示50%的窗口
                self.plot_widget.setXRange(x_min, x_max, padding=0)
            else:  # 从头开始，清空波形
                self.waveform_curve.setData([], [])
                self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)
    
    def update_waveform(self):
        """更新波形图显示"""
        if self.morse_array is None or self.waveform_curve is None:
            return
        # 根据当前播放器位置计算波形指针位置
        if self.is_char_playing:
            current_position = self.char_player.position()
            total_duration = self.char_audio_duration
        elif self.is_text_playing:
            current_position = self.text_player.position()
            total_duration = self.text_audio_duration
        else:
            return
        # 根据播放进度计算应该显示到哪个波形点
        if total_duration > 0:
            progress_ratio = current_position / total_duration
            target_ptr = int(progress_ratio * len(self.morse_array))
            target_ptr = min(target_ptr, len(self.morse_array))
        else:
            return
        # 检查是否到达末尾
        if target_ptr >= len(self.morse_array):
            # 播放结束，停止更新
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            return
        # 如果当前位置远落后于目标位置，快速推进
        if target_ptr > self.waveform_ptr:
            distance = target_ptr - self.waveform_ptr
            if distance > 50:
                step = max(distance // 10, self.WAVEFORM_CHUNK_SIZE)
            else:
                step = self.WAVEFORM_CHUNK_SIZE
            self.waveform_ptr = min(self.waveform_ptr + step, target_ptr)
        elif target_ptr < self.waveform_ptr:
            # 播放被拖动到前面，回退波形指针
            self.waveform_ptr = target_ptr
        # 绘制当前波形
        if self.waveform_ptr > 0:
            y_data = self.morse_array[:self.waveform_ptr]
            x_data = list(range(len(y_data) + 1))
            self.waveform_curve.setData(x_data, y_data)
            # 调整X轴范围以保持波形居中
            center = self.waveform_ptr
            x_min = center - self.WAVEFORM_WINDOW_SIZE  # 左侧显示整个窗口
            x_max = center  # 右侧显示到当前点
            # x_min = center - int(self.WAVEFORM_WINDOW_SIZE * 0.75)  # 左侧显示75%的窗口
            # x_max = center + int(self.WAVEFORM_WINDOW_SIZE * 0.25)  # 右侧显示25%的窗口
            # x_min = center - self.WAVEFORM_WINDOW_SIZE // 2  # 左侧显示50%的窗口
            # x_max = center + self.WAVEFORM_WINDOW_SIZE // 2  # 右侧显示50%的窗口
            self.plot_widget.setXRange(x_min, x_max, padding=0)
    
    # ==================== 课程信息更新 ====================
    
    def update_information(self, lesson_name: str):
        """
        更新课程信息显示
        当用户切换课程时调用
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
        """
        self.logger.info(f"Switching to lesson: {lesson_name}")
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
    
    # ==================== 音频设备管理 ====================

    def on_audio_device_changed(self):
        """
        音频设备发生变化时
        重新加载字符和文本音频播放器的音频输出设备
        """
        # 保存当前播放状态
        char_was_playing = self.is_char_playing
        text_was_playing = self.is_text_playing
        char_position = self.char_player.position()
        text_position = self.text_player.position()
        char_source = self.char_player.source()
        text_source = self.text_player.source()

        # 保存当前音量
        current_volume = self.char_audio_output.volume()

        # 停止播放
        if char_was_playing:
            self.char_player.pause()
        if text_was_playing:
            self.text_player.pause()

        # 重新设置音频输出设备
        self.char_audio_output = QAudioOutput()
        self.char_player.setAudioOutput(self.char_audio_output)
        self.text_audio_output = QAudioOutput()
        self.text_player.setAudioOutput(self.text_audio_output)

        # 恢复音量
        self.char_audio_output.setVolume(current_volume)
        self.text_audio_output.setVolume(current_volume)

        # 恢复播放位置
        if char_source.isValid():
            self.char_player.setSource(char_source)
            if char_position > 0:
                self.char_player.setPosition(char_position)
            if char_was_playing:
                self.char_player.play()
                if self.is_waveform_enabled and self.plot_widget is not None:
                    self.load_waveform(self.char_morse_array, True, char_position)
                    if self.waveform_timer is not None:
                        self.waveform_timer.start(self.WAVEFORM_UPDATE_INTERVAL)
        
        if text_source.isValid():
            self.text_player.setSource(text_source)
            if text_position > 0:
                self.text_player.setPosition(text_position)
            if text_was_playing:
                self.text_player.play()
                if self.is_waveform_enabled and self.plot_widget is not None:
                    self.load_waveform(self.text_morse_array, False, text_position)
                    if self.waveform_timer is not None:
                        self.waveform_timer.start(self.WAVEFORM_UPDATE_INTERVAL)
    
    # ==================== 字符音频控制 ====================
    
    def char_media_load(self):
        """
        加载字符音频文件
        根据当前显示的字符加载对应的音频
        """
        current_character = self.label_char_sound.text()
        char_index = self.total_characters.index(current_character)
        
        self.char_audio_file = config.get_character_audio(char_index)  # 使用 pathlib 构建音频文件路径
        self.logger.debug(f"Loading character audio: {current_character} from {self.char_audio_file}")
        self.char_morse_array, self.char_audio_duration = self.process_audio_to_morse(str(self.char_audio_file))
        self.char_player.setSource(QUrl.fromLocalFile(str(self.char_audio_file)))

        if self.is_waveform_enabled and self.plot_widget is not None:
            # 停止波形更新定时器
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            # 重置波形图指针
            if self.is_waveform_enabled:
                self.waveform_ptr = 0
                self.waveform_curve.setData([], [])
                self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)

        self.is_char_playback_finished = True
    
    def char_play_pause(self):
        """字符音频播放/暂停切换"""
        if not self.is_char_playing:  # 当前暂停，开始播放
            # 如果文本音频正在播放，先暂停文本音频
            if self.is_countdown_active:
                self.cancel_countdown()
            if self.is_text_playing:
                self.text_player.pause()
                if self.waveform_timer is not None:
                    self.waveform_timer.stop()
                if self.is_waveform_enabled:
                    self.waveform_ptr = 0
                    self.waveform_curve.setData([], [])
                    self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)
                self.set_play_button_state(self.btn_text_play_pause, False)
                self.is_text_playing = False
            if self.char_player.position() == 0 and self.is_char_playback_finished:
                self.is_char_playback_finished = False
            # 播放字符音频
            self.char_player.play()
            # 加载并开始更新字符音频波形
            if self.is_waveform_enabled and self.plot_widget is not None:
                self.load_waveform(self.char_morse_array, True, self.char_player.position())
                if self.waveform_timer is not None:
                    self.waveform_timer.start(self.WAVEFORM_UPDATE_INTERVAL)
            # 更新按钮状态
            self.set_play_button_state(self.btn_char_play_pause, True)
            self.is_char_restart = False
            self.btn_char_restart.setEnabled(True)
        else:  # 当前播放，暂停
            self.char_player.pause()
            # 停止更新字符音频波形
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            self.set_play_button_state(self.btn_char_play_pause, False)
        
        self.is_char_playing = not self.is_char_playing
    
    def char_restart(self):
        """
        字符音频重播
        """
        # 停止当前播放
        self.char_player.stop()
        # 停止波形更新定时器
        if self.waveform_timer is not None:
            self.waveform_timer.stop()
        # 重置波形图指针
        if self.is_waveform_enabled:
            self.waveform_ptr = 0
            self.waveform_curve.setData([], [])
            self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)
        # 重置播放按钮和状态
        self.set_play_button_state(self.btn_char_play_pause, False)
        self.is_char_playback_finished = True
        self.is_char_playing = False
        self.is_char_restart = False
    
    def update_char_progress(self, position: int):
        """
        更新字符音频播放进度
        
        Args:
            position: 当前播放位置（毫秒）
        """
        if not self.is_char_seeking:
            if self.char_player.duration() > 0:
                progress = int((position / self.char_player.duration()) * 1000)
                # 使用标志位防止递归
                self.is_char_updating = True
                self.progress_char.setValue(progress)
                self.is_char_updating = False
            self.label_char_current_time.setText(self.format_time(position))
    
    def update_char_duration(self, duration: int):
        """
        更新字符音频总时长
        
        Args:
            duration: 音频总时长（毫秒）
        """
        self.label_char_total_time.setText(self.format_time(duration))
    
    def update_char_playback_state(self, state: QMediaPlayer.PlaybackState):
        """
        更新字符音频播放状态
        当音频播放完毕时重置按钮状态
        
        Args:
            state: 播放器状态
        """
        if state == QMediaPlayer.PlaybackState.StoppedState:
            if self.is_char_playing:
                self.is_char_playback_finished = True
            # 停止波形更新定时器
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            # 加载完整波形
            if self.is_waveform_enabled and self.char_morse_array is not None:
                self.waveform_ptr = len(self.char_morse_array)
                y_data = self.char_morse_array
                x_data = list(range(len(y_data) + 1))
                self.waveform_curve.setData(x_data, y_data)
                self.plot_widget.setXRange(0, max(x_data), padding=0)
            # 重置播放按钮和进度条
            self.set_play_button_state(self.btn_char_play_pause, False)
            self.is_char_playing = False
            self.progress_char.setValue(0)
            self.btn_char_restart.setEnabled(False)
            self.is_char_restart = False
            self.is_char_seeking = False
            # 重置当前时间显示
            self.label_char_current_time.setText("00:00")
            self.label_char_total_time.setText(self.format_time(self.char_player.duration()))
    
    # ==================== 字符音频进度条控制 ====================

    def on_char_slider_pressed(self):
        """
        字符音频进度条开始拖动
        """
        self.is_char_seeking = True
    
    def on_char_slider_released(self):
        """
        字符音频进度条结束拖动
        更新播放位置
        """
        self.is_char_seeking = False
        if self.char_player.duration() > 0:
            position = int((self.progress_char.value() / 1000) * self.char_player.duration())
            self.char_player.setPosition(position)
            if self.is_waveform_enabled and self.plot_widget is not None:
                self.load_waveform(self.char_morse_array, True, position)
    
    def on_char_slider_value_changed(self, value: int):
        """
        字符音频进度条值变化时更新当前时间显示
        
        Args:
            value: 进度条当前值（0-1000）
        """
        if self.is_char_updating or self.char_player.duration() <= 0:
            return
        position = int((value / 1000) * self.char_player.duration())
        # 拖动时更新标签
        if self.is_char_seeking:
            self.label_char_current_time.setText(self.format_time(position))
        # 点击跳转时更新标签和播放位置
        elif not self.progress_char.isSliderDown():
            current_position = self.char_player.position()
            if abs(current_position - position) > 50:  # 避免微小变化频繁跳转
                self.is_char_updating = True
                try:
                    self.char_player.setPosition(position)
                    self.label_char_current_time.setText(self.format_time(position))
                    if self.is_waveform_enabled and self.plot_widget is not None:
                        self.load_waveform(self.char_morse_array, True, position)
                finally:
                    self.is_char_updating = False
    
    # ==================== 练习文本音频控制 ====================
    
    def text_media_load(self):
        """
        加载练习文本音频文件
        根据当前课程和文本索引加载对应的音频
        """
        lesson_num = self.label_lesson_num.text()
        self.text_audio_file = config.get_lesson_audio(int(lesson_num), self.current_text_index + 1)

        self.logger.debug(f"Loading practice text audio for lesson {lesson_num}, index {self.current_text_index + 1}")
        self.text_morse_array, self.text_audio_duration = self.process_audio_to_morse(str(self.text_audio_file))
        self.text_player.setSource(QUrl.fromLocalFile(str(self.text_audio_file)))

        if self.is_waveform_enabled and self.plot_widget is not None:
            # 停止波形更新定时器
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            # 重置波形图指针
            if self.is_waveform_enabled:
                self.waveform_ptr = 0
                self.waveform_curve.setData([], [])
                self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)

        # 使用信号阻塞器，避免触发信号
        with QSignalBlocker(self.text_input):
            self.text_input.clear()  # 清空输入框
            self.text_input.setPlainText("")  # 重置为纯文本
            self.text_input.setReadOnly(False)  # 允许输入

        self.clear_layout(self.hbox72)  # 清除结果显示
        self._reset_check_button()  # 重置检查按钮状态

        self.practice_start_time = None  # 重置练习开始时间
        self.practice_end_time = None  # 重置练习结束时间

        self.is_text_manually_seeked = False  # 重置手动拖动标志
        self.is_text_playback_finished = True  # 重置播放完成标志
    
    def text_play_pause(self):
        """
        练习文本音频播放/暂停切换
        如果从头开始播放，会先进行倒计时
        """
        if self.is_countdown_active:  # 倒计时中，点击取消
            self.cancel_countdown()
        elif not self.is_text_playing:  # 当前暂停，开始播放
            # 如果字符音频正在播放，先暂停字符音频
            if self.is_char_playing:
                self.char_player.pause()
                if self.waveform_timer is not None:
                    self.waveform_timer.stop()
                if self.is_waveform_enabled:
                    self.waveform_ptr = 0
                    self.waveform_curve.setData([], [])
                    self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)
                self.set_play_button_state(self.btn_char_play_pause, False)
                self.is_char_playing = False
            # 如果从头开始播放且之前播放已结束，启动倒计时
            if self.text_player.position() == 0 and self.is_text_playback_finished:
                self.is_text_playback_finished = False
                self.start_countdown()
            else:  # 继续播放
                if self.practice_start_time is None:
                    self.practice_start_time = datetime.now()
                # 播放文本音频
                self.text_player.play()
                # 开始波形
                if self.is_waveform_enabled and self.plot_widget is not None:
                    self.load_waveform(self.text_morse_array, False, self.text_player.position())
                    if self.waveform_timer is not None:
                        self.waveform_timer.start(self.WAVEFORM_UPDATE_INTERVAL)
                # 更新按钮状态
                self.set_play_button_state(self.btn_text_play_pause, True)
                self.is_text_playing = True
                self.btn_text_restart.setEnabled(True)
        else:  # 当前播放，暂停
            self.text_player.pause()
            # 停止波形更新定时器
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            # 更新按钮状态
            self.set_play_button_state(self.btn_text_play_pause, False)
            self.is_text_playing = False
    
    def start_countdown(self):
        """开始3秒倒计时"""
        self.countdown_value = self.COUNTDOWN_SECONDS
        self.is_countdown_active = True
        # 停止波形更新定时器
        if self.waveform_timer is not None:
            self.waveform_timer.stop()
        # 重置波形图指针
        if self.is_waveform_enabled:
            self.waveform_ptr = 0
            self.waveform_curve.setData([], [])
            self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)
        # 设置按钮为取消状态
        self.btn_text_play_pause.setText("Cancel")
        self.btn_text_play_pause.setIcon(FluentIcon.CANCEL)
        self.btn_text_play_pause.setIconSize(self.ICON_SIZE)
        # 禁用重播按钮
        self.btn_text_restart.setEnabled(False)
        # 初始化倒计时标签
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
            # 记录练习开始时间
            if self.practice_start_time is None:
                self.practice_start_time = datetime.now()  
            # 播放文本音频
            self.text_player.play()
            # 开始波形
            if self.is_waveform_enabled and self.plot_widget is not None:
                self.load_waveform(self.text_morse_array, False, self.text_player.position())
                if self.waveform_timer is not None:
                    self.waveform_timer.start(self.WAVEFORM_UPDATE_INTERVAL)
            # 更新按钮状态
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
        self.is_text_playback_finished = True
    
    def text_restart(self):
        """
        练习文本音频重播
        停止当前播放，重置到开头，启动倒计时
        """
        # 停止当前播放
        self.text_player.stop()
        # 停止波形更新定时器
        if self.waveform_timer is not None:
            self.waveform_timer.stop()
        # 重置波形图指针
        if self.is_waveform_enabled:
            self.waveform_ptr = 0
            self.waveform_curve.setData([], [])
            self.plot_widget.setXRange(-self.WAVEFORM_WINDOW_SIZE // 2, self.WAVEFORM_WINDOW_SIZE // 2, padding=0)
        # 重置标志位
        self.is_text_manually_seeked = False
        self.is_text_playback_finished = True
        # 重置播放状态
        self.set_play_button_state(self.btn_text_play_pause, False)
        self.is_text_playing = False
        self.is_text_restart = False
    
    def update_text_progress(self, position: int):
        """
        更新练习文本音频播放进度
        
        Args:
            position: 当前播放位置（毫秒）
        """
        if not self.is_text_seeking:
            if self.text_player.duration() > 0:
                progress = int((position / self.text_player.duration()) * 1000)
                # 使用标志位防止递归
                self.is_text_updating = True
                self.progress_text.setValue(progress)
                self.is_text_updating = False
            self.label_text_current_time.setText(self.format_time(position))
    
    def update_text_duration(self, duration: int):
        """
        更新练习文本音频总时长
        
        Args:
            duration: 音频总时长（毫秒）
        """
        self.label_text_total_time.setText(self.format_time(duration))
    
    def update_text_playback_state(self, state: QMediaPlayer.PlaybackState):
        """
        更新练习文本音频播放状态
        当音频播放完毕时重置按钮状态
        
        Args:
            state: 播放器状态
        """
        if state == QMediaPlayer.PlaybackState.StoppedState:
            # 停止波形更新定时器
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            # 加载完整波形
            if self.is_waveform_enabled and self.text_morse_array is not None:
                self.waveform_ptr = len(self.text_morse_array)
                y_data = self.text_morse_array
                x_data = list(range(len(y_data) + 1))
                self.waveform_curve.setData(x_data, y_data)
                self.plot_widget.setXRange(0, max(x_data), padding=0)
            # 如果当前正在播放，说明是自然播放完成
            if self.is_text_playing:
                self.is_text_playback_finished = True
                self.is_text_manually_seeked = False  # 重置手动拖动标志
            # 更新UI和标志位
            self.set_play_button_state(self.btn_text_play_pause, False)
            self.is_text_playing = False
            self.progress_text.setValue(0)
            self.btn_text_restart.setEnabled(False)
            self.is_text_restart = False
            self.is_text_seeking = False
            # 重置当前时间显示
            self.label_text_current_time.setText("00:00")
            self.label_text_total_time.setText(self.format_time(self.text_player.duration()))
    
    # ==================== 练习文本音频进度条控制 ====================

    def on_text_slider_pressed(self):
        """
        练习文本音频进度条开始拖动
        """
        self.is_text_seeking = True
        self.is_text_manually_seeked = True  # 标记为手动拖动
        # 如果正在倒计时，取消倒计时
        if self.is_countdown_active:
            self.cancel_countdown()
    
    def on_text_slider_released(self):
        """
        练习文本音频进度条结束拖动
        更新播放位置
        """
        self.is_text_seeking = False
        if self.text_player.duration() > 0:
            position = int((self.progress_text.value() / 1000) * self.text_player.duration())
            self.text_player.setPosition(position)
            if self.is_waveform_enabled and self.plot_widget is not None:
                self.load_waveform(self.text_morse_array, False, position)
    
    def on_text_slider_value_changed(self, value: int):
        """
        练习文本音频进度条值变化时更新当前时间显示
        
        Args:
            value: 进度条当前值（0-1000）
        """
        if self.is_text_updating or self.text_player.duration() <= 0:
            return
        position = int((value / 1000) * self.text_player.duration())
        # 拖动时更新标签
        if self.is_text_seeking:
            if self.progress_text.isSliderDown() and self.is_countdown_active:
                # 如果在倒计时中拖动进度条，取消倒计时
                self.cancel_countdown()
            self.label_text_current_time.setText(self.format_time(position))
        # 点击跳转时更新标签和播放位置
        elif not self.progress_text.isSliderDown():
            current_position = self.text_player.position()
            if abs(current_position - position) > 50:  # 避免微小变化频繁跳转
                self.is_text_updating = True
                try:
                    self.is_text_manually_seeked = True  # 标记为手动拖动
                    if self.is_countdown_active:
                        self.cancel_countdown()
                    self.text_player.setPosition(position)
                    self.label_text_current_time.setText(self.format_time(position))
                    if self.is_waveform_enabled and self.plot_widget is not None:
                        self.load_waveform(self.text_morse_array, False, position)
                finally:
                    self.is_text_updating = False
    
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
            
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # 从第一行开始读取
                    result_characters = "".join(lines).replace("\n", " ").upper().strip()
            except FileNotFoundError:
                self.logger.error(f"Answer file not found: {result_file}", exc_info=True)
                raise
            except Exception as e:
                self.logger.error(f"Error reading {result_file}: {e}", exc_info=True)
                self.clear_layout(self.hbox72)
                self.hbox72.addWidget(BodyLabel(f"Error: {str(e)}"))
                return
            
            # 定义等宽字体样式的HTML模板
            html_styles = {
                "correct": "color: #00AA00;",  # 绿色
                "incorrect": "color: #CC0000; background-color: #FFE6E6;",  # 红色 + 浅红色背景
                "missing": "color: #FF8C00; background-color: #FFF4E6;",  # 橙色 + 浅橙色背景
                "extra": "color: #0066CC; background-color: #E6F2FF;",  # 蓝色 + 浅蓝色背景
                "separator": "color: #888888;",  # 灰色分隔线
                "answer": "color: #888888;",  # 灰色答案
            }
            font_family = "font-family: Consolas, monospace;"

            # 逐字符对比并生成HTML高亮文本
            correct_count = 0
            total_count = max(len(practice_text), len(result_characters))  # 总字符数取较大值（防止多输入影响计算结果）
            html_text = ""

            for i in range(len(result_characters)):
                if i < len(practice_text):
                    if practice_text[i] == result_characters[i]:  # 正确字符：绿色
                        html_text += f'<span style="{font_family} {html_styles["correct"]}">{practice_text[i]}</span>'
                        correct_count += 1
                    else:  # 错误字符：红色 + 浅红色背景
                        html_text += f'<span style="{font_family} {html_styles["incorrect"]}">{practice_text[i]}</span>'
                else:  # 缺失字符：橙色 + 浅橙色背景
                    html_text += f'<span style="{font_family} {html_styles["missing"]}">{result_characters[i]}</span>'
            
            # 处理多余的字符
            if len(practice_text) > len(result_characters):
                for i in range(len(result_characters), len(practice_text)):  # 多余字符：蓝色 + 浅蓝色背景
                    html_text += f'<span style="{font_family} {html_styles["extra"]}">{practice_text[i]}</span>'
            
            # 使用信号阻塞器，避免触发信号
            separator_text = "-" * 59
            with QSignalBlocker(self.text_input):
                # 显示标准答案
                separator = f'<br><span style="{font_family} {html_styles["separator"]}">{separator_text}</span>'
                answer_text = f'<br><span style="{font_family} {html_styles["answer"]}">{result_characters}</span>'

                full_html = html_text + separator + answer_text

                # 显示高亮结果（不清空内容）
                self.text_input.setHtml(full_html)

                # 设置text_input为只读，防止用户修改结果
                self.text_input.setReadOnly(True)

            # 计算并显示准确率
            accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
            
            self.clear_layout(self.hbox72)
            comment = self._get_accuracy_comment(accuracy)
            self.hbox72.addWidget(BodyLabel(f"Accuracy: {accuracy:.2f}%{comment}"))

            # 保存统计数据
            if self.practice_start_time:
                self.practice_end_time = datetime.now()
                practice_time = (self.practice_end_time - self.practice_start_time).total_seconds()
            else:
                # 如果没有记录开始时间，使用音频时长作为练习时间
                practice_time = self.text_player.duration() / 1000.0  # 转化为秒
            stats_manager.add_practice_record(
                lesson_name=self.current_lesson_name,
                accuracy=accuracy,
                practice_time=practice_time,
            )
            
        except FileNotFoundError:
            # 文件不存在时的错误处理
            self.logger.error(f"Answer file not found for lesson {self.label_lesson_num.text()}, index {self.current_text_index + 1}", exc_info=True)
            self.clear_layout(self.hbox72)
            self.hbox72.addWidget(BodyLabel("Error: Answer file not found!"))
        except Exception as e:
            # 其他异常的错误处理
            self.logger.error(f"Error checking result: {str(e)}", exc_info=True)
            self.clear_layout(self.hbox72)
            self.hbox72.addWidget(BodyLabel(f"Error: {str(e)}"))
    
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
        self.logger.debug(f"Saved progress: {lesson_name}, index {text_index}")
    
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
    
    # ==================== 设置面板 ====================
    
    def show_settings_view(self):
        """显示设置侧边栏"""
        # 检查设置面板是否已经打开
        if self.is_settings_tip_open:
            return
        if hasattr(self, "settings_view") and self.settings_view is not None:
            self.settings_view.close()
            self.settings_view.deleteLater()
            self.settings_view = None
        
        # 标记设置面板为打开状态
        self.is_settings_tip_open = True

        # 创建设置面板内容
        self.settings_view = QWidget(None)
        self.settings_view.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Popup
        )

        # 创建一个容器来承载所有控件
        settings_layout = QVBoxLayout(self.settings_view)
        settings_layout.setContentsMargins(15, 10, 15, 10)
        settings_layout.addWidget(StrongBodyLabel("Settings"))

        # 音量滑块
        hbox_volume = QHBoxLayout()
        hbox_volume1 = QHBoxLayout()
        hbox_volume2 = QHBoxLayout()

        label_volume = BodyLabel("Volume:")
        label_volume.setFixedWidth(85)
        hbox_volume1.addWidget(label_volume)
        hbox_volume1.setAlignment(Qt.AlignmentFlag.AlignLeft)

        current_volume = round(float(self.char_audio_output.volume()), 2)

        self.slider_volume = Slider(Qt.Orientation.Horizontal)
        self.slider_volume.setFixedSize(100, 21)
        self.slider_volume.setMinimum(self.VOLUME_MIN)
        self.slider_volume.setMaximum(self.VOLUME_MAX)
        self.slider_volume.setValue(int(current_volume * 100))
        self.slider_volume.valueChanged.connect(self.on_volume_changed)
        hbox_volume2.addWidget(self.slider_volume)

        self.label_volume = BodyLabel(f"{int(current_volume * 100)}%")
        self.label_volume.setFixedWidth(35)
        hbox_volume2.addWidget(self.label_volume)
        hbox_volume2.setAlignment(Qt.AlignmentFlag.AlignRight)

        hbox_volume.addLayout(hbox_volume1)
        hbox_volume.addLayout(hbox_volume2)
        settings_layout.addLayout(hbox_volume)
        
        # 透明度滑块
        hbox_transparency = QHBoxLayout()
        hbox_transparency1 = QHBoxLayout()
        hbox_transparency2 = QHBoxLayout()

        label_transparency = BodyLabel("Transparency:")
        label_transparency.setFixedWidth(85)
        hbox_transparency1.addWidget(label_transparency)
        hbox_transparency1.setAlignment(Qt.AlignmentFlag.AlignLeft)

        current_opacity = round(float(self.windowOpacity()), 2)

        self.slider_transparency = Slider(Qt.Orientation.Horizontal)
        self.slider_transparency.setFixedSize(100, 21)
        self.slider_transparency.setMinimum(self.TRANSPARENCY_MIN)
        self.slider_transparency.setMaximum(self.TRANSPARENCY_MAX)
        self.slider_transparency.setValue(int(current_opacity * 100))
        self.slider_transparency.valueChanged.connect(self.on_transparency_changed)
        hbox_transparency2.addWidget(self.slider_transparency)

        self.label_transparency = BodyLabel(f"{int(current_opacity * 100)}%")
        self.label_transparency.setFixedWidth(35)
        hbox_transparency2.addWidget(self.label_transparency)
        hbox_transparency2.setAlignment(Qt.AlignmentFlag.AlignRight)

        hbox_transparency.addLayout(hbox_transparency1)
        hbox_transparency.addLayout(hbox_transparency2)
        settings_layout.addLayout(hbox_transparency)
        
        # 主题开关
        hbox_theme = QHBoxLayout()
        hbox_theme1 = QHBoxLayout()
        hbox_theme2 = QHBoxLayout()

        hbox_theme1.addWidget(BodyLabel("Application Dark Mode:"))
        hbox_theme1.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.switch_theme = SwitchButton()
        self.switch_theme.setCheckedIndicatorColor(
            QColor(150, 150, 150), 
            QColor(90, 90, 90)
        )
        self.switch_theme.setChecked(self.is_dark_theme)
        self.switch_theme.checkedChanged.connect(self.toggle_theme)
        hbox_theme2.addWidget(self.switch_theme)
        hbox_theme2.setAlignment(Qt.AlignmentFlag.AlignRight)

        hbox_theme.addLayout(hbox_theme1)
        hbox_theme.addLayout(hbox_theme2)
        settings_layout.addLayout(hbox_theme)

        # 波形图开关
        hbox_waveform = QHBoxLayout()
        hbox_waveform1 = QHBoxLayout()
        hbox_waveform2 = QHBoxLayout()

        hbox_waveform1.addWidget(BodyLabel("Morse Code Waveform:"))
        hbox_waveform1.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.switch_waveform = SwitchButton()
        self.switch_waveform.setCheckedIndicatorColor(
            QColor(150, 150, 150), 
            QColor(90, 90, 90)
        )
        self.switch_waveform.setChecked(self.is_waveform_enabled)
        self.switch_waveform.checkedChanged.connect(self.toggle_waveform)
        hbox_waveform2.addWidget(self.switch_waveform)
        hbox_waveform2.setAlignment(Qt.AlignmentFlag.AlignRight)

        hbox_waveform.addLayout(hbox_waveform1)
        hbox_waveform.addLayout(hbox_waveform2)
        settings_layout.addLayout(hbox_waveform)

        settings_layout.addSpacing(5)

        self.settings_view.setFixedSize(self.SETTINGS_VIEW_WIDTH, self.SETTINGS_VIEW_HEIGHT)

        btn_global_pos = self.btn_settings.mapToGlobal(self.btn_settings.rect().topLeft())
        panel_x = btn_global_pos.x() - 2
        panel_y = btn_global_pos.y() - self.settings_view.height() - 3
        self.settings_view.move(panel_x, panel_y)

        self.settings_view.setStyleSheet(self.styleSheet())
        self.settings_view.setWindowOpacity(self.windowOpacity())

        try:
            hwnd = int(self.settings_view.winId())
            
            dwmwa_window_corner_preference = 33
            corner_preference = c_int(2)
            
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                dwmwa_window_corner_preference,
                byref(corner_preference),
                sizeof(corner_preference)
            )
        except AttributeError:
            pass

        self.settings_view.show()

        def on_close_event(event):
            self.is_settings_tip_open = False
            event.accept()
        self.settings_view.closeEvent = on_close_event
    
    def resizeEvent(self, event):
        """
        重写窗口调整大小事件，确保设置面板位置正确

        Args:
            event: 调整大小事件对象
        """
        if hasattr(self, "settings_view") and self.settings_view is not None:
            btn_global_pos = self.btn_settings.mapToGlobal(self.btn_settings.rect().topLeft())
            panel_x = btn_global_pos.x() - 2
            panel_y = btn_global_pos.y() - self.settings_view.height() - 3
            self.settings_view.move(panel_x, panel_y)
        super().resizeEvent(event)

    def on_volume_changed(self, value: int):
        """
        切换音量大小
        
        Args:
            value: 滑块值（0-100），对应音量0%-100%
        """
        volume = value / 100.0
        # 设置音频输出音量
        self.char_audio_output.setVolume(volume)
        self.text_audio_output.setVolume(volume)
        # 更新标签显示
        if hasattr(self, "label_volume"):
            self.label_volume.setText(f"{value}%")
        # 保存音量设置
        self.settings.setValue("volume", volume)
        self.settings.sync()
    
    def on_transparency_changed(self, value: int):
        """
        切换窗口透明度
        
        Args:
            value: 滑块值（10-100），对应透明度10%-100%
        """
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        # 同步更新设置面板透明度
        if hasattr(self, "settings_view") and self.settings_view is not None:
            self.settings_view.setWindowOpacity(opacity)
        # 更新标签显示
        if hasattr(self, "label_transparency"):
            self.label_transparency.setText(f"{value}%")
    
    def toggle_theme(self, checked: bool):
        """
        切换浅色/深色主题
        
        Args:
            checked: True为深色主题，False为浅色主题
        """
        if checked:  # 深色主题
            setTheme(Theme.DARK)
            setThemeColor(QColor(self.DARK_THEME_COLOR))
            self.setStyleSheet(f"QWidget {{ background-color: {self.DARK_BACKGROUND_COLOR}; }}")
            self.set_windows_title_bar_color(True)
            self.update_window_icon(True)
            self.is_dark_theme = True
        else:  # 浅色主题
            setTheme(Theme.LIGHT)
            setThemeColor(QColor(self.LIGHT_THEME_COLOR))
            self.setStyleSheet(f"QWidget {{ background-color: {self.LIGHT_BACKGROUND_COLOR}; }}")
            self.set_windows_title_bar_color(False)
            self.update_window_icon(False)
            self.is_dark_theme = False
        if self.settings_view is not None:
            self.settings_view.setStyleSheet(self.styleSheet())
        if self.is_waveform_enabled and self.plot_widget is not None:
            self.update_waveform_theme()
        
        # 保存主题设置
        self.settings.setValue("dark_theme", self.is_dark_theme)
        self.settings.sync()
    
    def update_window_icon(self, dark_mode: bool):
        """
        根据主题更新窗口图标

        Args:
            dark_mode: True为深色主题，False为浅色主题
        """
        try:
            if dark_mode:
                icon_path = config.get_logo_path("dark")  # 深色模式图标路径
            else:
                icon_path = config.get_logo_path("light")  # 浅色模式图标路径

            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # 如果图标文件不存在，使用默认图标
                self.setWindowIcon(FluentIcon.MUSIC.icon())
        except (OSError, AttributeError):
            # 发生错误时使用默认图标
            self.setWindowIcon(FluentIcon.MUSIC.icon())
    
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
    
    def update_waveform_theme(self):
        """根据主题更新波形图颜色"""
        if self.plot_widget is None:
            return
        if self.is_dark_theme:
            bg_color = self.DARK_BACKGROUND_COLOR
            grid_alpha = 0.1
            axis_color = (120, 120, 120)
            waveform_color = (146, 224, 211)
        else:
            bg_color = self.LIGHT_BACKGROUND_COLOR
            grid_alpha = 0.2
            axis_color = (200, 200, 200)
            waveform_color = (74, 155, 142)

        self.plot_widget.setBackground(bg_color)  # 设置背景颜色
        self.plot_widget.showGrid(x=True, y=True, alpha=grid_alpha)  # 设置网格颜色
        if self.waveform_curve is not None:
            self.waveform_curve.setPen(pg.mkPen(color=waveform_color, width=4))  # 设置波形颜色
        for axis in ["left", "bottom", "top", "right"]:
            self.plot_widget.getAxis(axis).setPen(pg.mkPen(color=axis_color, width=1.5))  # 设置坐标轴颜色
    
    def toggle_waveform(self, checked: bool):
        """
        切换波形图显示状态
        
        Args:
            checked: True为显示波形图，False为隐藏波形图
        """
        self.is_waveform_enabled = checked
        if checked:
            self.update_waveform_theme()
            self.plot_widget.show()
            self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT_WAVE)
        else:
            self.plot_widget.hide()
            self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
            if self.waveform_timer is not None:
                self.waveform_timer.stop()
            self.morse_array = None
            self.waveform_ptr = 0
    
    # ==================== 统计窗口显示 ====================

    def show_statistics_window(self):
        """显示统计信息窗口"""
        # 延迟导入，避免循环依赖
        from Statistics_Window import StatisticsWindow
        
        # 传入当前主题状态（True=深色，False=浅色）
        current_theme = self.is_dark_theme
        current_transparent = round(float(self.windowOpacity()), 2)

        # 创建统计窗口实例
        statistics_window = StatisticsWindow(
            stats_manager,
            current_theme,
            current_transparent,
            parent=self
        )

        # 设置模态窗口，阻塞主窗口交互
        statistics_window.setWindowModality(Qt.WindowModality.ApplicationModal)

        # 计算居中位置
        parent_geometry = self.geometry()
        child_width = statistics_window.width()
        child_height = statistics_window.height()
    
        x = parent_geometry.x() + (parent_geometry.width() - child_width) // 2
        y = parent_geometry.y() - (parent_geometry.height() - child_height) // 2
    
        statistics_window.move(x, y)
    
        # 模态显示
        statistics_window.show()
    
    # ==================== 窗口事件处理 ====================
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        在关闭前保存当前进度
        
        Args:
            event: 关闭事件对象
        """
        self.save_lesson_progress(self.current_lesson_name, self.current_text_index)
        self.logger.info("Koch Application closed")
        super().closeEvent(event)


# ==================== 程序入口 ====================

if __name__ == "__main__":
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 获取日志记录器
    logger = logging.getLogger("Koch")
    logger.info("=" * 50)
    logger.info("Koch Application started")
    logger.info(f"Version: {config.APP_VERSION}")
    logger.info("=" * 50)
    
    # 创建并显示主窗口
    window = KochWindow()
    window.show()
    
    # 进入应用程序主循环
    exit_code = app.exec()
    logger.info(f"Koch Application exited with code {exit_code}")
    sys.exit(exit_code)