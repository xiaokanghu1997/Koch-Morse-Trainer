"""
Koch 配置管理模块
处理路径、设置等配置项

Author: xiaokanghu1997
Date: 2025-11-10
Version: 1.1.0
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """配置管理类"""
    
    # ==================== 常量定义 ====================
    APP_NAME: str = "Koch"
    APP_VERSION: str = "1.1.0"
    AUTHOR: str = "xiaokanghu1997"
    
    def __init__(self):
        """初始化配置管理器"""
        self._base_dir = None
        self._resource_dir = None
        self._config_file = None
        self._user_settings = {}
        self._logo_dir = None  # 新增：Logo 目录
        
        self._init_paths()
        self._load_user_settings()
    
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
            else:
                # 回退到基础目录
                self._logo_dir = self._base_dir / "Logo"
        else:
            # 开发环境：使用脚本所在目录
            self._base_dir = Path(__file__).parent
            self._logo_dir = self._base_dir / "Logo"
        
        # 确保目录存在
        self._base_dir.mkdir(parents=True, exist_ok=True)
        
        # 资源目录
        self._resource_dir = self._base_dir / "Resource"
        self._resource_dir.mkdir(exist_ok=True)
        
        # 配置文件
        self._config_file = self._base_dir / "Config.json"
    
    def _load_user_settings(self) -> None:
        """加载用户配置文件"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._user_settings = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config file - {e}")
                self._user_settings = {}
    
    # ==================== 公共方法 ====================
    
    def save_user_settings(self) -> None:
        """保存用户配置到JSON文件"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save config file - {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._user_settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """设置配置项并自动保存"""
        self._user_settings[key] = value
        self.save_user_settings()
    
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
        logo_path = self._logo_dir / f"logo_{theme}.png"
        
        # 检查文件是否存在
        if not logo_path.exists():
            print(f"Warning: Logo file not found - {logo_path}")
        
        return logo_path
    
    def statistics_file(self) -> Path:
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