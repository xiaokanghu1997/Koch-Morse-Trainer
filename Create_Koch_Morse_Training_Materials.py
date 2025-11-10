"""
Koch方法摩尔斯电码训练材料创建工具
用于学习和练习莫尔斯电码字符识别

Author: xiaokanghu1997
Date: 2025-11-06
Version: 1.0.0
"""

import random
import numpy as np
from pathlib import Path
from Config import config
from scipy.io import wavfile
from PySide6.QtCore import QSettings

class MorseCodeGenerator:
    def __init__(self, char_wpm=20, effective_wpm=10, tone_freq=600, sample_rate=44100):
        """
        初始化摩尔斯电码生成器（按照LCWO标准）
        
        参数:
        - char_wpm: 字符速率 (words per minute)
        - effective_wpm: 有效速率 (words per minute)
        - tone_freq: 音调频率 (Hz)
        - sample_rate: 采样率 (Hz)
        """
        self.char_wpm = char_wpm
        self.effective_wpm = effective_wpm
        self.tone_freq = tone_freq
        self.sample_rate = sample_rate
        
        # 完整的摩尔斯电码映射表（Koch方法字符集）
        self.morse_code = {
            'K': '-.-',   'M': '--',    'U': '..-',   'R': '.-.',
            'E': '.',     'S': '...',   'N': '-.',    'A': '.-',
            'P': '.--.',  'T': '-',     'L': '.-..',  'W': '.--',
            'I': '..',    '.': '.-.-.-','J': '.---',  'Z': '--..',
            '=': '-...-', 'F': '..-.',  'O': '---',   'Y': '-.--',
            ',': '--..--','V': '...-',  'G': '--.',   '5': '.....',
            '/': '-..-.',  'Q': '--.-', '9': '----.',  '2': '..---',
            'H': '....',  '3': '...--', '8': '---..',  'B': '-...',
            '?': '..--..','4': '....-', '7': '--...',  'C': '-.-.',
            '1': '.----', 'D': '-..',   '6': '-....',  '0': '-----',
            'X': '-..-',  ' ': ' '
        }
        
        # 计算基本时间单位（dit）- 基于字符速率
        self.dit_time = 1.2 / char_wpm
        self.dah_time = 3 * self.dit_time
        
        # 字符内部元素间隔（点划之间）- 总是1个dit
        self.element_space_time = self.dit_time
        
        # 计算Farnsworth间隔
        if effective_wpm < char_wpm:
            standard_char_space = 3 * self.dit_time
            standard_word_space = 7 * self.dit_time
            
            char_time_per_word = 60.0 / char_wpm
            target_time_per_word = 60.0 / effective_wpm
            extra_time = target_time_per_word - char_time_per_word
            
            total_space_units = 19
            extra_per_unit = extra_time / total_space_units
            
            self.char_space_time = standard_char_space + 3 * extra_per_unit
            self.word_space_time = standard_word_space + 7 * extra_per_unit
        else:
            self.char_space_time = 3 * self.dit_time
            self.word_space_time = 7 * self.dit_time
        
    def generate_tone(self, duration):
        """生成指定时长的音调"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        fade_samples = int(self.sample_rate * 0.005)  # 5ms淡入淡出
        tone = np.sin(2 * np.pi * self.tone_freq * t)
        
        if len(tone) > 2 * fade_samples:
            tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
            tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return tone
    
    def generate_silence(self, duration):
        """生成指定时长的静音"""
        return np.zeros(int(self.sample_rate * duration))
    
    def char_to_morse_audio(self, char):
        """将单个字符转换为摩尔斯电码音频"""
        if char not in self.morse_code:
            return np.array([])
        
        morse = self.morse_code[char]
        audio = np.array([])
        
        for i, symbol in enumerate(morse):
            if symbol == '.':
                audio = np.append(audio, self.generate_tone(self.dit_time))
            elif symbol == '-':
                audio = np.append(audio, self.generate_tone(self.dah_time))
            
            if i < len(morse) - 1:
                audio = np.append(audio, self.generate_silence(self.element_space_time))
        
        return audio
    
    def text_to_morse_audio(self, text):
        """将文本转换为摩尔斯电码音频"""
        audio = self.generate_silence(0.8)  # 初始化空音频
        
        for i, char in enumerate(text):
            if char == ' ':
                # 直接添加完整的单词间隔
                audio = np.append(audio, self.generate_silence(self.word_space_time))
            else:
                audio = np.append(audio, self.char_to_morse_audio(char))
                
                if i < len(text) - 1 and text[i + 1] != ' ':
                    audio = np.append(audio, self.generate_silence(self.char_space_time))
        audio = np.append(audio, self.generate_silence(1.2))  # 结尾添加空白
        return audio
    
    def generate_single_character_pattern(self, char, count=15):
        """
        生成单个字符的重复音频
        
        参数:
        - char: 要练习的字符
        - count: 字符重复次数
        """
        # 生成15个字符        
        text = char * count
        audio = self.text_to_morse_audio(text)
        
        return audio, text
    
    def generate_pattern(self, char_set, num_chars=50, weights=None):
        """
        生成指定字符集的随机组合
        
        参数:
        - char_set: 可用字符集合（字符串）
        - num_chars: 总字符数（不含空格）
        - weights: 字符权重列表（可选，用于控制频率）
        """
        text = ""
        chars_list = list(char_set)
        
        # 生成50个字符，每5个一组
        for i in range(10):  # 10组
            if weights:
                # 使用加权随机选择
                group = ''.join(random.choices(chars_list, weights=weights, k=5))
            else:
                # 使用均匀分布
                group = ''.join(random.choice(chars_list) for _ in range(5))
            
            text += group
            if i < 9:
                text += ' '
        
        audio = self.text_to_morse_audio(text)
        return audio, text
    
    def save_audio(self, audio, filename):
        """保存音频到WAV文件"""
        if len(audio) == 0:
            print(f"⚠ 警告: 音频为空，跳过保存 {filename}")
            return
        audio_normalized = np.int16(audio / np.max(np.abs(audio)) * 32767)
        wavfile.write(filename, self.sample_rate, audio_normalized)
    
    @staticmethod
    def save_text(text, filename):
        """保存文本到TXT文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)


class KochMethodTrainer:
    """Koch方法训练器（支持字符频率控制）"""
    
    KOCH_SEQUENCE = "KMURESNAPTLWI.JZ=FOY,VG5/Q92H38B?47C1D60X"
    
    def __init__(self, char_wpm=20, effective_wpm=10, tone_freq=600, frequency_mode='uniform'):
        self.char_wpm = char_wpm
        self.effective_wpm = effective_wpm
        self.tone_freq = tone_freq
        self.frequency_mode = frequency_mode
        self.generator = MorseCodeGenerator(char_wpm, effective_wpm, tone_freq)
    
    def get_character_weights(self, char_set, mode='uniform'):
        """
        获取字符权重
        
        参数:
        - char_set: 字符集
        - mode: 频率模式
        """
        n = len(char_set)
        
        if mode == 'uniform':
            return None  # None表示均匀分布
        
        elif mode == 'new_char_focus':
            # 新字符权重2倍，其他字符权重1倍
            weights = [1.0] * (n - 1) + [2.0]
            return weights
        
        elif mode == 'gradual':
            # 渐进式：新字符1.5倍
            weights = [1.0] * (n - 1) + [1.5]
            return weights
        
        elif mode == 'difficulty':
            # 根据摩尔斯码长度设置权重
            morse_code = self.generator.morse_code
            weights = []
            for char in char_set:
                morse = morse_code.get(char, '.')
                weight = 1.0 + len(morse) * 0.15
                weights.append(weight)
            return weights
        
        return None
    
    def create_character_lessons(self, output_dir='Resource'):
        """
        创建单个字符练习音频
        
        在Resource/Character目录下生成koch-000到koch-040共41个音频文件
        每个音频包含15个该字符的重复，字符间用空格分隔
        只生成音频文件，不生成文本文件
        """
        # 创建Character目录
        char_dir = config.character_dir
        char_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f" 生成单字符练习音频")
        print(f"{'='*70}\n")
        print(f"配置参数:")
        print(f"  字符速率: {self.char_wpm} WPM")
        print(f"  有效速率: {self.effective_wpm} WPM")
        print(f"  音调频率: {self.tone_freq} Hz")
        print(f"  每个音频重复次数: 15")
        print(f"\n{'='*70}\n")
        
        # 生成41个字符的音频（koch-000到koch-040）
        for idx, char in enumerate(self.KOCH_SEQUENCE):
            # 生成音频
            audio, text = self.generator.generate_single_character_pattern(char, count=15)
            
            # 文件名（只生成音频）
            base_name = f"koch-{idx:03d}"
            audio_file = char_dir / f"{base_name}.wav"
            
            # 保存音频文件
            self.generator.save_audio(audio, str(audio_file))
            
            # 获取摩尔斯码
            morse = self.generator.morse_code.get(char, '?')
            
            print(f"✓ {base_name}.wav: '{char}' ({morse}) - 15次重复")
        
        print(f"\n{'='*70}")
        print(f"✓ 单字符练习音频生成完成！")
        print(f"✓ 总计: 41 个字符音频文件")
        print(f"✓ 输出目录: {char_dir.absolute()}")
        print(f"{'='*70}\n")
    
    def create_lessons(self, output_dir='Resource', files_per_lesson=10):
        """创建Koch方法的所有课程"""
        base_path = Path(output_dir)
        base_path.mkdir(exist_ok=True)
        
        mode_description = {
            'uniform': '均匀分布',
            'new_char_focus': '新字符重点（2倍频率）',
            'gradual': '渐进式（新字符1.5倍）',
            'difficulty': '难度加权'
        }
        
        print(f"\n{'='*70}")
        print(f" Koch方法摩尔斯电码训练材料创建工具")
        print(f"{'='*70}\n")
        print(f"配置参数:")
        print(f"  字符速率: {self.char_wpm} WPM")
        print(f"  有效速率: {self.effective_wpm} WPM")
        print(f"  音调频率: {self.tone_freq} Hz")
        print(f"  频率模式: {mode_description.get(self.frequency_mode, self.frequency_mode)}")
        print(f"  每课程文件数: {files_per_lesson}")
        print(f"  每文件字符数: 50 (10组 × 5字符/组)")
        print(f"\n{'='*70}\n")
        
        for lesson_num in range(1, 41):
            char_set = self.KOCH_SEQUENCE[:lesson_num + 1]
            lesson_dir = config.get_lesson_dir(lesson_num)
            lesson_dir.mkdir(exist_ok=True)
            
            # 获取字符权重
            weights = self.get_character_weights(char_set, self.frequency_mode)
            
            print(f"生成 Lesson-{lesson_num:02d}  字符集: {char_set}")
            if weights and lesson_num <= 5:  # 只显示前5节课的权重
                weight_str = ', '.join([f"{c}:{w:.1f}" for c, w in zip(char_set, weights)])
                print(f"  权重: {weight_str}")
            
            for file_num in range(1, files_per_lesson + 1):
                audio, text = self.generator.generate_pattern(char_set, num_chars=50, weights=weights)
                
                base_name = f"koch-{file_num:03d}"
                audio_file = lesson_dir / f"{base_name}.wav"
                text_file = lesson_dir / f"{base_name}.txt"
                
                self.generator.save_audio(audio, str(audio_file))
                self.generator.save_text(text, str(text_file))
            
            print(f"  ✓ 已生成 {files_per_lesson} 个练习文件")
        
        print(f"\n{'='*70}")
        print(f"✓ 所有课程生成完成！")
        print(f"✓ 输出目录: {base_path.absolute()}")
        print(f"{'='*70}\n")
    
    def create_all(self, output_dir='Resource', files_per_lesson=10):
        """
        创建所有内容：单字符练习 + 课程练习
        """
        # 1. 先生成单字符练习音频
        self.create_character_lessons(output_dir)
        
        # 2. 再生成课程练习
        self.create_lessons(output_dir, files_per_lesson)
        
        # 3. 生成总结信息
        self.print_summary(output_dir, files_per_lesson)

        # 4. 清空学习进度记录
        self.clear_progress_settings()
    
    def clear_progress_settings(self):
        """
        清空学习进度的注册表记录
        避免新生成的材料与旧进度不匹配
        """
        try:
            settings = QSettings("Koch", "LessonProgress")
            # 读取当前进度（如果需要备份）
            current_lesson = settings.value("current_lesson", None)
            # 获取所有的文本索引
            all_keys = settings.allKeys()
            index_keys = [key for key in all_keys if key.endswith("_index")]
            if not index_keys and not current_lesson:
                print(f"\n{'='*70}")
                print(f"✅ 未检测到学习进度记录，无需清空")
                print(f"{'='*70}\n")
                return
            
            # 显示当前状态
            print(f"\n{'='*70}")
            print(f"📝 重置学习进度")
            print(f"{'='*70}\n")
            
            if current_lesson:
                print(f"✅ 保留当前课程: {current_lesson}")
            else:
                print(f"⚠️ 未检测到当前课程记录")
            
            # 删除所有文本索引记录
            cleared_count = 0
            for key in index_keys:
                settings.remove(key)
                cleared_count += 1
            
            settings.sync()
            
            print(f"✅ 已清空 {cleared_count} 个课程的练习进度")
            print(f"✅ 每个课程将从第 1 个练习开始")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"\n⚠ 警告：重置进度失败 - {e}")
    
    def print_summary(self, output_dir, files_per_lesson):
        """打印生成总结"""
        print(f"\n{'='*70}")
        print(f" 📊 生成总结")
        print(f"{'='*70}\n")
        
        char_dir = Path(output_dir) / 'Character'
        
        print(f"目录结构:")
        print(f"  {output_dir}/")
        print(f"  ├── Character/")
        print(f"  │   ├── koch-000.wav (K 字符 × 15)")
        print(f"  │   ├── koch-001.wav (M 字符 × 15)")
        print(f"  │   ├── koch-002.wav (U 字符 × 15)")
        print(f"  │   ├── ...")
        print(f"  │   └── koch-040.wav (X 字符 × 15)")
        print(f"  │   共 41 个音频文件")
        print(f"  │")
        print(f"  ├── Lesson-01/ (字符: KM)")
        print(f"  │   ├── koch-001.wav")
        print(f"  │   ├── koch-001.txt")
        print(f"  │   ├── koch-002.wav")
        print(f"  │   ├── koch-002.txt")
        print(f"  │   ├── ...")
        print(f"  │   ├── koch-{files_per_lesson:03d}.wav")
        print(f"  │   └── koch-{files_per_lesson:03d}.txt")
        print(f"  │   共 {files_per_lesson} 个练习 × 2 文件 = {files_per_lesson * 2} 个文件")
        print(f"  │")
        print(f"  ├── Lesson-02/ (字符: KMU)")
        print(f"  ├── Lesson-03/ (字符: KMUR)")
        print(f"  ├── ...")
        print(f"  └── Lesson-40/ (全部41个字符)")
        print(f"\n")
        print(f"统计信息:")
        print(f"  • 单字符练习: 41 个音频文件 (Character目录)")
        print(f"  • 课程练习: 40 课 × {files_per_lesson} 练习 × 2 文件 = {40 * files_per_lesson * 2} 个文件")
        print(f"  • 总文件数: {41 + 40 * files_per_lesson * 2} 个文件")
        print(f"\n")
        print(f"学习建议:")
        print(f"  1) 先听 Character/ 目录下的单字符音频，熟悉每个字符的声音")
        print(f"     例如: koch-000.wav (K), koch-001.wav (M) 等")
        print(f"  2) 从 Lesson-01 开始，逐课练习混合字符")
        print(f"  3) 每课达到90%准确率后再进入下一课")
        print(f"  4) 定期回顾之前学过的字符")
        print(f"\n")
        print(f"Koch方法字符顺序:")
        print(f"  {self.KOCH_SEQUENCE}")
        print(f"\n{'='*70}\n")


def main():
    """主函数"""
    
    try:
        print(f"\n{'='*70}")
        print(f" 🎯 Koch方法摩尔斯电码训练材料创建工具")
        print(f"{'='*70}\n")

        c_wpm = input("请输入字符速率 (WPM, 默认20): ").strip() or "20"
        e_wpm = input("\n请输入有效速率 (WPM, 默认10): ").strip() or "10"
        tone_freq = input("\n请输入音调频率 (Hz, 默认600): ").strip() or "600"
        
        print("\n请选择字符频率模式:")
        print("1. 均匀分布 (所有字符概率相同) [推荐新手]")
        print("2. 新字符重点 (新字符出现2倍频率)")
        print("3. 渐进式 (新字符出现1.5倍频率) [推荐]")
        print("4. 难度加权 (摩尔斯码越长权重越高)")
        
        choice = input("\n请输入选项 (1-4, 默认为3): ").strip() or "3"
        
        mode_map = {
            '1': 'uniform',
            '2': 'new_char_focus',
            '3': 'gradual',
            '4': 'difficulty'
        }
        
        frequency_mode = mode_map.get(choice, 'gradual')
        
        trainer = KochMethodTrainer(
            char_wpm=int(c_wpm),
            effective_wpm=int(e_wpm),
            tone_freq=int(tone_freq),
            frequency_mode=frequency_mode
        )

        lesson_count = input("\n请输入每课练习文件数 (默认10): ").strip() or "10"
        
        trainer.create_all(output_dir='Resource', files_per_lesson=int(lesson_count))
        
        print("\n" + "="*70)
        print("✅ 所有文件生成完成！")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断操作")
    except Exception as e:
        print(f"\n\n❌ 程序执行出错：{e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按 Enter 键退出...")

if __name__ == "__main__":
    main()