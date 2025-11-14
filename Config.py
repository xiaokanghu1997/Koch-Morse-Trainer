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
    """
    配置管理类
    
    负责管理应用程序的路径配置、用户设置和资源完整性检查
    """
    
    # ==================== 常量定义 ====================
    APP_NAME: str = "Koch"
    APP_VERSION: str = "1.1.0"
    AUTHOR: str = "xiaokanghu1997"
    
    # ==================== 类型注解 - 实例变量 ====================
    _base_dir: Path                     # 基础目录
    _resource_dir: Path                 # 资源目录
    _config_file: Path                  # 配置文件路径
    _user_settings: Dict[str, Any]      # 用户设置字典
    
    def __init__(self):
        """
        初始化配置管理器
        
        自动检测运行环境(打包/开发)并初始化路径和设置
        """
        self._base_dir = None
        self._resource_dir = None
        self._config_file = None
        self._user_settings = {}
        
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
        else:
            # 开发环境：使用脚本所在目录
            self._base_dir = Path(__file__).parent
        
        # 确保目录存在
        self._base_dir.mkdir(parents=True, exist_ok=True)
        
        # 资源目录
        self._resource_dir = self._base_dir / "Resource"
        self._resource_dir.mkdir(exist_ok=True)
        
        # 配置文件
        self._config_file = self._base_dir / "Config.json"
    
    def _load_user_settings(self) -> None:
        """
        加载用户配置文件
        
        从JSON文件读取用户设置，如果文件不存在或加载失败则使用空字典
        """
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._user_settings = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config file - {e}")
                self._user_settings = {}
    
    # ==================== 公共方法 ====================
    
    def save_user_settings(self) -> None:
        """
        保存用户配置到JSON文件
        
        将当前的用户设置字典序列化为JSON并保存到文件
        """
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save config file - {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项键名
            default: 默认值，当配置项不存在时返回
            
        Returns:
            配置项的值，如果不存在则返回default
        """
        return self._user_settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        设置配置项并自动保存
        
        Args:
            key: 配置项键名
            value: 配置项的值
        """
        self._user_settings[key] = value
        self.save_user_settings()
    
    # ==================== 路径属性 ====================
    
    @property
    def base_dir(self) -> Path:
        """
        获取基础目录
        
        Returns:
            应用程序基础目录的Path对象
        """
        return self._base_dir
    
    @property
    def resource_dir(self) -> Path:
        """
        获取资源目录
        
        Returns:
            Resource目录的Path对象
        """
        return self._resource_dir
    
    @property
    def character_dir(self) -> Path:
        """
        获取字符音频目录
        
        自动创建目录(如果不存在)
        
        Returns:
            Resource/Character目录的Path对象
        """
        path = self._resource_dir / "Character"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def logo_dir(self) -> Path:
        """
        获取Logo目录
        
        自动创建目录(如果不存在)
        
        Returns:
            Logo目录的Path对象
        """
        path = self._base_dir / "Logo"
        path.mkdir(exist_ok=True)
        return path
    
    def get_lesson_dir(self, lesson_num: int) -> Path:
        """
        获取指定课程的目录
        
        自动创建目录(如果不存在)
        
        Args:
            lesson_num: 课程编号 (1-40)
            
        Returns:
            课程目录的Path对象 (格式: Resource/Lesson-XX)
        """
        path = self._resource_dir / f"Lesson-{lesson_num:02d}"
        path.mkdir(exist_ok=True)
        return path
    
    def get_character_audio(self, char_index: int) -> Path:
        """
        获取字符音频文件路径
        
        Args:
            char_index: 字符索引 (0-40，对应41个Koch字符)
            
        Returns:
            字符音频文件的Path对象 (格式: koch-XXX.wav)
        """
        return self.character_dir / f"koch-{char_index:03d}.wav"
    
    def get_lesson_audio(self, lesson_num: int, file_index: int) -> Path:
        """
        获取课程音频文件路径
        
        Args:
            lesson_num: 课程编号 (1-40)
            file_index: 文件索引 (1-10，对应每课的练习编号)
            
        Returns:
            课程音频文件的Path对象 (格式: Lesson-XX/koch-XXX.wav)
        """
        return self.get_lesson_dir(lesson_num) / f"koch-{file_index:03d}.wav"
    
    def get_lesson_text(self, lesson_num: int, file_index: int) -> Path:
        """
        获取课程文本文件路径
        
        Args:
            lesson_num: 课程编号 (1-40)
            file_index: 文件索引 (1-10，对应每课的练习编号)
            
        Returns:
            课程文本文件的Path对象 (格式: Lesson-XX/koch-XXX.txt)
        """
        return self.get_lesson_dir(lesson_num) / f"koch-{file_index:03d}.txt"
    
    def get_logo_path(self, theme: str = 'light') -> Path:
        """
        获取Logo文件路径
        
        Args:
            theme: 主题名称，可选 'light' 或 'dark'
            
        Returns:
            Logo文件的Path对象 (格式: Logo/logo_{theme}.png)
        """
        return self.logo_dir / f"logo_{theme}.png"
    
    def statistics_file(self) -> Path:
        """
        获取统计数据文件路径
        
        Returns:
            统计数据JSON文件的Path对象
        """
        return self.base_dir / "Statistics.json"
    
    # ==================== 资源完整性检查 ====================
    
    def check_resources(self) -> Dict[str, Any]:
        """
        检查资源完整性
        
        验证所有必需的训练资源文件是否存在:
        - 41个字符音频文件 (koch-000.wav 到 koch-040.wav)
        - 40个课程目录，每个包含至少1组音频和文本文件
        
        Returns:
            包含检查结果的字典:
            {
                'character_audio': bool,  # 字符音频是否完整
                'lessons': List[int],     # 缺失的课程编号列表
                'complete': bool          # 整体是否完整
            }
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
        
        # 检查40个课程（每个课程至少一个音频和文本）
        for lesson in range(1, 41):
            lesson_complete = True
            for file_num in range(1, 2):  # 只检查第一个文件
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