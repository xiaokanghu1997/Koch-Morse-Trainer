"""
Koch 统计数据管理模块
记录和管理练习统计数据

Author: xiaokanghu1997
Date: 2025-11-13
Version: 1.1.0
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

from Config import config


class StatisticsManager:
    """
    统计数据管理类
    
    负责记录、存储和分析用户的练习数据:
    - 练习时长和次数统计
    - 准确率追踪
    - 历史记录管理
    - 按时间段聚合数据
    """
    
    # ==================== 类型注解 - 实例变量 ====================
    stats_file: Path                    # 统计数据文件路径
    data: Dict[str, Any]                # 统计数据字典
    
    def __init__(self):
        """
        初始化统计管理器
        
        自动加载已有的统计数据，如果文件不存在则创建默认数据结构
        """
        self.stats_file = config.base_dir / "Statistics.json"
        self.data = self.load_statistics()

        self._lesson_cache = {}  # 课程数据缓存，按编号索引
        self._overall_cache = None  # 总体统计缓存
    
    # ==================== 数据加载与保存 ====================
    
    def load_statistics(self) -> Dict[str, Any]:
        """
        从JSON文件加载统计数据
        
        Returns:
            统计数据字典，如果文件不存在或加载失败则返回默认结构
        """
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load statistics - {e}")
        
        # 返回默认数据结构
        return {
            "total_practice_time": 0,           # 总练习时长(秒)
            "total_practice_count": 0,          # 总练习次数
            "average_accuracy": 0.0,            # 平均准确率(%)
            "practiced_lesson_numbers": [0],    # 已练习课程编号列表(0 代表所有课程)
            "practiced_lesson_names": ["All learned lessons"],  # 课程名称列表
            "lessons": {}                       # 各课程统计，按编号索引
        }
    
    def save_statistics(self) -> None:
        """
        保存统计数据到JSON文件
        
        使用缩进格式化输出，便于人工阅读
        """
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save statistics - {e}")
    
    # ==================== 辅助方法 ====================
    
    @staticmethod
    def extract_lesson_number(lesson_name: str) -> int:
        """
        从课程名称中提取编号
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
            
        Returns:
            课程编号，如 1；提取失败返回 0
        """
        try:
            # 提取开头的数字部分
            number_str = lesson_name.split('-')[0].strip()
            return int(number_str)
        except (ValueError, IndexError):
            return 0
    
    def update_overall_stats(self) -> None:
        """
        更新总体统计数据
        
        重新计算:
        - 已练习课程列表(按编号排序)
        - 所有课程的平均准确率
        """
        # 获取所有课程编号及其名称
        lesson_info = []
        for lesson_key, lesson_data in self.data["lessons"].items():
            lesson_info.append((
                int(lesson_key),
                lesson_data.get("lesson_name", f"Lesson {lesson_key}")
            ))
        
        # 按编号排序
        lesson_info.sort(key=lambda x: x[0])
        
        # 更新课程编号和名称列表(0 开头，代表所有已学课程)
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
        
        # 清除缓存
        self._lesson_cache.clear()
        self._overall_cache = None
    
    # ==================== 练习记录管理 ====================
    
    def add_practice_record(
        self, 
        lesson_name: str, 
        accuracy: float, 
        practice_time: float,
    ) -> None:
        """
        添加一次练习记录
        
        自动更新总体统计、课程统计和历史记录
        
        Args:
            lesson_name: 课程名称，如 "01 - K, M"
            accuracy: 准确率(0-100)
            practice_time: 练习时长(秒)
        """
        # 提取课程编号
        lesson_number = self.extract_lesson_number(lesson_name)
        lesson_key = str(lesson_number)
        
        # 更新总计数据
        self.data["total_practice_time"] += practice_time
        self.data["total_practice_count"] += 1
        
        # 初始化课程数据(如果不存在)
        if lesson_key not in self.data["lessons"]:
            self.data["lessons"][lesson_key] = {
                "lesson_name": lesson_name,
                "practice_count": 0,
                "practice_time": 0.0,
                "average_accuracy": 0.0,
                "accuracy_history": []
            }
        
        lesson_data = self.data["lessons"][lesson_key]
        
        # 添加历史记录
        record = {
            "timestamp": datetime.now().isoformat(),
            "accuracy": round(accuracy, 2),
            "practice_time": round(practice_time, 2)
        }
        
        lesson_data["accuracy_history"].append(record)
        
        # 更新课程统计
        lesson_data["practice_count"] += 1
        lesson_data["practice_time"] += practice_time
        
        # 重新计算平均准确率(基于历史记录)
        total_accuracy = sum(
            record["accuracy"] for record in lesson_data["accuracy_history"]
        )
        lesson_data["average_accuracy"] = round(
            total_accuracy / len(lesson_data["accuracy_history"]), 2
        )
        
        # 更新总体统计
        self.update_overall_stats()
        
        # 保存数据
        self.save_statistics()

        # 清除缓存
        self._lesson_cache.clear()
        self._overall_cache = None
    
    # ==================== 数据查询方法 ====================
    
    def get_lesson_stats(self, lesson_identifier: Any) -> Optional[Dict[str, Any]]:
        """
        获取指定课程的统计数据
        
        Args:
            lesson_identifier: 课程编号(int)或课程名称(str)
                - 0 或 "0": 返回所有课程的汇总统计
                - 其他整数: 直接作为课程编号查找
                - 字符串: 从中提取课程编号
            
        Returns:
            课程统计数据字典，如果不存在返回None
        """
        # 如果是0，返回所有课程的汇总统计
        if lesson_identifier == 0 or lesson_identifier == "0":
            return self.get_overall_stats()
        
        # 如果是整数或数字字符串，直接作为编号查找
        if isinstance(lesson_identifier, int):
            lesson_key = str(lesson_identifier)
        elif str(lesson_identifier).isdigit():
            lesson_key = str(lesson_identifier)
        else:
            # 如果是课程名称，提取编号
            lesson_number = self.extract_lesson_number(str(lesson_identifier))
            lesson_key = str(lesson_number)
        
        # 检查缓存
        if lesson_key in self._lesson_cache:
            return self._lesson_cache[lesson_key]
        
        # 从数据中获取并缓存
        lesson_data = self.data["lessons"].get(lesson_key)
        if lesson_data is not None:
            self._lesson_cache[lesson_key] = lesson_data
        
        return lesson_data
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """
        获取总体统计数据
        
        Returns:
            包含总体统计信息的字典:
            {
                "total_practice_time": float,       # 总练习时长(秒)
                "total_practice_count": int,        # 总练习次数
                "average_accuracy": float,          # 平均准确率(%)
                "practiced_lesson_numbers": List[int],  # 已练习课程编号列表
                "practiced_lesson_names": List[str]     # 课程名称列表
            }
        """
        # 检查缓存
        if self._overall_cache is not None:
            return self._overall_cache
        
        # 构建结果并缓存
        result = {
            "total_practice_time": self.data["total_practice_time"],
            "total_practice_count": self.data["total_practice_count"],
            "average_accuracy": self.data["average_accuracy"],
            "practiced_lesson_numbers": self.data["practiced_lesson_numbers"],
            "practiced_lesson_names": self.data["practiced_lesson_names"]
        }

        self._overall_cache = result
        return result
    
    def get_recent_history(
        self, 
        lesson_identifier: Any, 
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取最近的练习历史记录
        
        Args:
            lesson_identifier: 课程编号或课程名称
            count: 返回记录数量
            
        Returns:
            最近的练习记录列表，每条记录包含timestamp、accuracy、practice_time
        """
        lesson_data = self.get_lesson_stats(lesson_identifier)
        if not lesson_data or "accuracy_history" not in lesson_data:
            return []
        
        history = lesson_data.get("accuracy_history", [])
        return history[-count:]
    
    # ==================== 数据聚合方法 ====================
    
    def aggregate_by_time_period(
        self, 
        lesson_identifier: Any, 
        mode: str = "Day"
    ) -> Tuple[List[str], List[float], List[int]]:
        """
        按时间段聚合练习数据
        
        将历史记录按指定时间粒度分组，计算每个时间段的平均准确率和练习次数
        
        Args:
            lesson_identifier: 课程编号或课程名称
            mode: 聚合模式 - "Hour"(小时), "Day"(天), "Month"(月), "Year"(年)
            
        Returns:
            三元组 (时间标签列表, 平均准确率列表, 练习次数列表)
            示例: (["01-15", "01-16"], [85.5, 90.2], [3, 5])
        """
        lesson_data = self.get_lesson_stats(lesson_identifier)
        if not lesson_data or "accuracy_history" not in lesson_data:
            return [], [], []
        
        history = lesson_data.get("accuracy_history", [])
        if not history:
            return [], [], []
        
        # 按时间段分组
        grouped_data = defaultdict(lambda: {"accuracies": [], "count": 0, "time": 0})
        
        for record in history:
            try:
                dt = datetime.fromisoformat(record["timestamp"])
                
                # 根据模式生成时间键和显示格式
                if mode == "Hour":
                    time_key = dt.strftime("%Y-%m-%d %H:00")
                    display_format = "%m-%d\n%H:00"
                elif mode == "Day":
                    time_key = dt.strftime("%Y-%m-%d")
                    display_format = "%m-%d"
                elif mode == "Month":
                    time_key = dt.strftime("%Y-%m")
                    display_format = "%Y-%m"
                elif mode == "Year":
                    time_key = dt.strftime("%Y")
                    display_format = "%Y"
                else:
                    time_key = dt.strftime("%Y-%m-%d")
                    display_format = "%m-%d"
                
                # 添加到分组
                grouped_data[time_key]["accuracies"].append(record["accuracy"])
                grouped_data[time_key]["count"] += 1
                grouped_data[time_key]["time"] += record.get("practice_time", 0)

                # 保存显示格式
                grouped_data[time_key]["display"] = datetime.strptime(
                    time_key, 
                    "%Y-%m-%d %H:%M" if mode == "Hour" else 
                    "%Y-%m-%d" if mode == "Day" else 
                    "%Y-%m" if mode == "Month" else "%Y"
                ).strftime(display_format)
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Failed to parse timestamp - {e}")
                continue
        
        # 排序并计算平均值
        sorted_groups = sorted(grouped_data.items())
        
        time_labels = []
        avg_accuracies = []
        counts = []
        practice_times = []
        
        for time_key, data in sorted_groups:
            time_labels.append(data["display"])
            avg_accuracy = sum(data["accuracies"]) / len(data["accuracies"])
            avg_accuracies.append(round(avg_accuracy, 2))
            counts.append(data["count"])
            practice_times.append(data["time"])

        return time_labels, avg_accuracies, counts, practice_times

    # ==================== 工具方法 ====================
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """
        格式化时间显示
        
        将秒数转换为人类可读的格式
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串:
            - 小于60秒: "45s"
            - 小于1小时: "23m 45s"
            - 1小时以上: "2h 15m"
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


# ==================== 全局统计管理器实例 ====================
stats_manager = StatisticsManager()