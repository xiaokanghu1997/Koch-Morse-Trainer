"""
Koch 统计数据管理模块
记录和管理练习统计数据

Author: xiaokanghu1997
Date: 2025-11-11
Version: 1.2.0
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from Config import config


class StatisticsManager:
    """统计数据管理类"""
    
    def __init__(self):
        """初始化统计管理器"""
        self.stats_file = config.base_dir / "statistics.json"
        self.data = self.load_statistics()
    
    def load_statistics(self) -> dict:
        """
        从JSON文件加载统计数据
        
        Returns:
            统计数据字典
        """
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load statistics - {e}")
        
        # 返回默认数据结构
        return {
            "total_practice_time": 0,  # 总练习时长（秒）
            "total_practice_count": 0,  # 总练习次数
            "average_accuracy": 0.0,  # 平均准确率
            "practiced_lesson_numbers": [0],  # 有练习记录的课程编号列表（0代表所有课程）
            "practiced_lesson_names": ["All learned lessons"],  # 课程名称列表
            "lessons": {}  # 各课程统计，按编号索引
        }
    
    def save_statistics(self):
        """保存统计数据到JSON文件"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save statistics - {e}")
    
    def extract_lesson_number(self, lesson_name: str) -> int:
        """
        从课程名称中提取编号
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
            
        Returns:
            课程编号，如 1
        """
        try:
            # 提取开头的数字部分
            number_str = lesson_name.split('-')[0].strip()
            return int(number_str)
        except:
            return 0
    
    def update_overall_stats(self):
        """更新总体统计数据"""
        # 获取所有课程编号及其名称
        lesson_info = []
        for lesson_number, lesson_data in self.data["lessons"].items():
            lesson_info.append((
                int(lesson_number),
                lesson_data.get("lesson_name", f"Lesson {lesson_number}")
            ))
        
        # 按编号排序
        lesson_info.sort(key=lambda x: x[0])
        
        # 更新课程编号和名称列表（0开头，代表所有已学课程）
        self.data["practiced_lesson_numbers"] = [0] + [num for num, _ in lesson_info]
        self.data["practiced_lesson_names"] = ["All learned lessons"] + [name for _, name in lesson_info]
        
        # 计算总平均准确率
        total_lessons = len(self.data["lessons"])
        if total_lessons > 0:
            total_avg = sum(
                lesson.get("average_accuracy", 0)
                for lesson in self.data["lessons"].values()
            ) / total_lessons
            self.data["average_accuracy"] = round(total_avg, 2)
        else:
            self.data["average_accuracy"] = 0.0
    
    def add_practice_record(
        self, 
        lesson_name: str, 
        accuracy: float, 
        practice_time: float,
        text_index: int
    ):
        """
        添加一次练习记录
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
            accuracy: 准确率（0-100）
            practice_time: 练习时长（秒）
            text_index: 练习文本索引
        """
        # 提取课程编号
        lesson_number = self.extract_lesson_number(lesson_name)
        lesson_key = str(lesson_number)
        
        # 更新总计数据
        self.data["total_practice_time"] += practice_time
        self.data["total_practice_count"] += 1
        
        # 初始化课程数据（如果不存在）
        if lesson_key not in self.data["lessons"]:
            self.data["lessons"][lesson_key] = {
                "lesson_name": lesson_name,  # 课程名称
                "practice_count": 0,  # 总练习次数
                "practice_time": 0.0,  # 总练习时间
                "average_accuracy": 0.0,  # 平均准确率
                "accuracy_history": []  # 历史记录
            }
        
        lesson_data = self.data["lessons"][lesson_key]
        
        # 添加历史记录
        record = {
            "timestamp": datetime.now().isoformat(),
            "accuracy": round(accuracy, 2),
            "practice_time": round(practice_time, 2),
            "text_index": text_index
        }
        lesson_data["accuracy_history"].append(record)
        
        # 更新课程统计
        lesson_data["practice_count"] += 1
        lesson_data["practice_time"] += practice_time
        
        # 重新计算平均准确率（基于历史记录）
        total_accuracy = sum(record["accuracy"] for record in lesson_data["accuracy_history"])
        lesson_data["average_accuracy"] = round(
            total_accuracy / len(lesson_data["accuracy_history"]), 2
        )
        
        # 更新总体统计
        self.update_overall_stats()
        
        # 保存数据
        self.save_statistics()
    
    def get_lesson_stats(self, lesson_identifier) -> Optional[dict]:
        """
        获取指定课程的统计数据
        
        Args:
            lesson_identifier: 课程编号（int）或课程名称（str）
            
        Returns:
            课程统计数据字典，如果不存在返回None
        """
        # 如果是0，返回所有课程的汇总统计
        if lesson_identifier == 0 or lesson_identifier == "0":
            return self.get_overall_stats()
        
        # 如果是整数或数字字符串，直接作为编号查找
        if isinstance(lesson_identifier, int):
            lesson_key = str(lesson_identifier)
        elif lesson_identifier.isdigit():
            lesson_key = lesson_identifier
        else:
            # 如果是课程名称，提取编号
            lesson_number = self.extract_lesson_number(lesson_identifier)
            lesson_key = str(lesson_number)
        
        return self.data["lessons"].get(lesson_key)
    
    def get_overall_stats(self) -> dict:
        """
        获取总体统计数据
        
        Returns:
            包含总体统计信息的字典
        """
        total_lessons = len(self.data["lessons"])
        completed_lessons = sum(
            1 for lesson in self.data["lessons"].values()
            if lesson.get("average_accuracy", 0) >= 90.0
        )
        
        return {
            "total_practice_time": self.data["total_practice_time"],
            "total_practice_count": self.data["total_practice_count"],
            "average_accuracy": self.data["average_accuracy"],
            "practiced_lesson_numbers": self.data["practiced_lesson_numbers"],
            "practiced_lesson_names": self.data["practiced_lesson_names"],
            "total_lessons_practiced": total_lessons,
            "completed_lessons": completed_lessons
        }
    
    def get_recent_history(self, lesson_identifier, count: int = 10) -> List[dict]:
        """
        获取最近的练习历史记录
        
        Args:
            lesson_identifier: 课程编号或课程名称
            count: 返回记录数量
            
        Returns:
            最近的练习记录列表
        """
        lesson_data = self.get_lesson_stats(lesson_identifier)
        if not lesson_data:
            return []
        
        history = lesson_data.get("accuracy_history", [])
        return history[-count:]
    
    def format_time(self, seconds: float) -> str:
        """
        格式化时间显示
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串，如 "1h 23m" 或 "45m 30s"
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        
        if minutes < 60:
            return f"{minutes}m {remaining_seconds}s"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        return f"{hours}h {remaining_minutes}m"


# 全局统计管理器实例
stats_manager = StatisticsManager()