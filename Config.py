"""
Koch 配置管理模块
处理路径、设置等配置项

Author: Xiaokang HU
Date: 2025-12-22
Version: 1.2.6
"""

import sys
import logging

from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理类"""
    
    # ==================== 常量定义 ====================
    APP_NAME: str = "Koch"
    APP_VERSION: str = "1.2.6"
    AUTHOR: str = "Xiaokang HU"
    
    def __init__(self):
        """初始化配置管理器"""
        self._base_dir = None
        self._resource_dir = None
        self._logo_dir = None  # Logo 目录
        self._echarts_dir = None  # Echarts 目录
        
        self._init_paths()
        self._init_logging()
    
    # ==================== 私有方法 ====================
    
    def _init_paths(self) -> None:
        """
        初始化路径配置
        
        根据运行环境(打包exe或开发环境)设置基础目录
        打包后使用固定路径: D:/Program Files (x86)/Koch/
        开发环境使用脚本所在目录
        """
        if getattr(sys, 'frozen', False):
            # 打包后的exe运行环境
            self._base_dir = Path("D:/Program Files (x86)/Koch")
            
            # PyInstaller 解压的临时目录
            if hasattr(sys, '_MEIPASS'):
                # Logo 从打包的资源中获取
                self._logo_dir = Path(sys._MEIPASS) / "Logo"
                # Echarts 从打包的资源中获取
                self._echarts_dir = Path(sys._MEIPASS) / "Echarts"
            else:
                # 回退到基础目录
                self._logo_dir = self._base_dir / "Logo"
                self._echarts_dir = self._base_dir / "Echarts"
        else:
            # 开发环境：使用脚本所在目录
            self._base_dir = Path(__file__).parent
            self._logo_dir = self._base_dir / "Logo"
            self._echarts_dir = self._base_dir / "Echarts"
        
        # 确保目录存在
        self._base_dir.mkdir(parents=True, exist_ok=True)
        
        # 资源目录
        self._resource_dir = self._base_dir / "Resource"
        self._resource_dir.mkdir(exist_ok=True)
    
    def _init_logging(self, level: int = logging.INFO) -> logging.Logger:
        """初始化日志记录器"""
        logger = logging.getLogger("Koch")
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        logger.setLevel(level)
        # 日志文件处理器（自动轮转，最大10MB，保留3个备份）
        file_handler = RotatingFileHandler(
            filename=self.log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(level)

        # 控制台处理器（只显示警告及以上级别）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger
    
    # ==================== 路径属性 ====================
    
    @property
    def base_dir(self) -> Path:
        """获取基础目录"""
        return self._base_dir
    
    @property
    def resource_dir(self) -> Path:
        """获取资源目录"""
        return self._resource_dir
    
    @property
    def character_dir(self) -> Path:
        """获取字符音频目录"""
        path = self._resource_dir / "Character"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def logo_dir(self) -> Path:
        """
        获取Logo目录
        
        Returns:
            Logo目录的Path对象（打包后从临时目录读取，开发环境从源目录读取）
        """
        return self._logo_dir
    
    @property
    def echarts_dir(self) -> Path:
        """
        获取Echarts目录
        
        Returns:
            Echarts目录的Path对象（打包后从临时目录读取，开发环境从源目录读取）
        """
        return self._echarts_dir
    
    @property
    def log_file(self) -> Path:
        """
        获取日志文件路径

        Returns:
            日志文件的Path对象
        """
        return self._base_dir / "Koch.log"
    
    def get_lesson_dir(self, lesson_num: int) -> Path:
        """获取指定课程的目录"""
        path = self._resource_dir / f"Lesson-{lesson_num:02d}"
        path.mkdir(exist_ok=True)
        return path
    
    def get_character_audio(self, char_index: int) -> Path:
        """获取字符音频文件路径"""
        return self.character_dir / f"koch-{char_index:03d}.wav"
    
    def get_lesson_audio(self, lesson_num: int, file_index: int) -> Path:
        """获取课程音频文件路径"""
        return self.get_lesson_dir(lesson_num) / f"koch-{file_index:03d}.wav"
    
    def get_lesson_text(self, lesson_num: int, file_index: int) -> Path:
        """获取课程文本文件路径"""
        return self.get_lesson_dir(lesson_num) / f"koch-{file_index:03d}.txt"
    
    def get_logo_path(self, theme: str = 'light') -> Path:
        """
        获取Logo文件路径
        
        Args:
            theme: 主题名称，可选 'light' 或 'dark'
            
        Returns:
            Logo文件的Path对象
            - 打包后：从 PyInstaller 临时目录读取
            - 开发环境：从项目 Logo 目录读取
        """
        logger = logging.getLogger("Koch")
        logo_path = self._logo_dir / f"logo_{theme}.png"
        
        # 检查文件是否存在
        if not logo_path.exists():
            logger.warning(f"Logo file not found: {logo_path}")
        
        return logo_path
    
    def get_echarts_html(self, template_name: str) -> Path:
        """
        获取Echarts HTML模板文件路径

        Args:
            template_name: HTML模板文件名, 可选 "calendar.html" 或 "table.html"
        
        Returns:
            HTML模板文件的Path对象
            - 打包后：从 PyInstaller 临时目录读取
            - 开发环境：从项目 Echarts 目录读取
        """
        logger = logging.getLogger("Koch")
        html_path = self._echarts_dir / f"{template_name}.html"
        if not html_path.exists():
            logger.warning(f"Echarts HTML file not found: {html_path}")
            
        return html_path
    
    def get_statistics_file(self) -> Path:
        """获取统计数据文件路径"""
        return self.base_dir / "Statistics.json"
    
    # ==================== 资源完整性检查 ====================
    
    def check_resources(self) -> Dict[str, Any]:
        """
        检查资源完整性
        
        Returns:
            包含检查结果的字典
        """
        result = {
            'character_audio': True,
            'lessons': [],
            'complete': True
        }
        
        # 检查字符音频（41个）
        for i in range(41):
            if not self.get_character_audio(i).exists():
                result['character_audio'] = False
                result['complete'] = False
                break
        
        # 检查40个课程
        for lesson in range(1, 41):
            lesson_complete = True
            for file_num in range(1, 2):
                audio = self.get_lesson_audio(lesson, file_num)
                text = self.get_lesson_text(lesson, file_num)
                if not audio.exists() or not text.exists():
                    lesson_complete = False
                    break
            
            if not lesson_complete:
                result['lessons'].append(lesson)
                result['complete'] = False
        
        return result


# ==================== 全局配置实例 ====================
config = Config()