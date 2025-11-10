"""
Koch 配置管理模块
处理路径、设置等配置项
"""

import sys
from pathlib import Path
import json

class Config:
    """配置管理类"""
    
    # 应用信息
    APP_NAME = "Koch"
    APP_VERSION = "1.0.0"
    AUTHOR = "xiaokanghu1997"
    
    def __init__(self):
        """初始化配置"""
        self._base_dir = None
        self._resource_dir = None
        self._config_file = None
        self._user_settings = {}
        
        self._init_paths()
        self._load_user_settings()
    
    def _init_paths(self):
        """初始化路径配置"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe运行环境
            # 资源存放在 D:/Program Files (x86)/Koch/
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
    
    def _load_user_settings(self):
        """加载用户配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._user_settings = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config file - {e}")
                self._user_settings = {}
    
    def save_user_settings(self):
        """保存用户配置"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save config file - {e}")
    
    def get_setting(self, key, default=None):
        """获取配置项"""
        return self._user_settings.get(key, default)
    
    def set_setting(self, key, value):
        """设置配置项"""
        self._user_settings[key] = value
        self.save_user_settings()
    
    # ========== 路径相关属性 ==========
    
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
        """获取Logo目录"""
        path = self._base_dir / "Logo"
        path.mkdir(exist_ok=True)
        return path
    
    def get_lesson_dir(self, lesson_num: int) -> Path:
        """获取课程目录"""
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
    
    def get_logo_path(self, theme='light') -> Path:
        """获取Logo路径"""
        return self.logo_dir / f"logo_{theme}.png"
    
    # ========== 资源检查 ==========
    
    def check_resources(self) -> dict:
        """
        检查资源完整性
        返回: {
            'character_audio': bool,  # 41个字符音频
            'lessons': list,          # 缺失的课程编号
            'complete': bool          # 是否完整
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


# 全局配置实例
config = Config()