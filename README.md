# Koch - 摩尔斯电码训练器

基于Koch方法的摩尔斯电码学习工具

## 版本信息
- **当前版本**: 1.2.0
- **作者**: Xiaokang HU
- **更新日期**: 2025-11-28

## 功能特性

### 核心功能
- ✅ 支持40个课程的渐进式学习
- ✅ 单字符音频练习（41个字符）
- ✅ 实时准确率检查
- ✅ 学习进度自动保存
- ✅ 练习文本高亮显示（正确/错误/缺失/多余）
- ✅ 深色/浅色主题切换
- ✅ 窗口透明度调节

### 统计功能
- 📊 练习时长、次数和准确率统计
- 📅 日历热力图显示每日练习活动
- 📈 交互式图表展示（基于Echarts）
- 🕐 多种时间聚合模式（小时/天/月/年）
- 🎯 课程级和全局统计数据
- 💾 自动保存统计数据到 JSON 文件

## 使用方法

1. 运行 `Koch_Setup_v1.2.0.exe ` 安装软件
2. 运行 `Create Koch Morse Training Materials.exe` 生成训练材料
3. 运行 `Koch.exe` 启动训练器
4. 从第1课开始，逐步提升

## 项目结构

```
Koch/
├── Koch.exe                                  # 主程序
├── Koch.py                                   # 主程序源代码
├── Config.py                                 # 配置管理模块
├── Statistics.py                             # 统计数据管理模块
├── Statistics_Window.py                      # 统计窗口显示模块
├── Create Koch Morse Training Materials.exe  # 资源生成工具
├── Create_Koch_Morse_Training_Materials.py   # 资源生成工具源代码
├── Statistics.json                           # 练习结果统计信息（不包含在Git中）
├── Config.json                               # 用户配置文件（不包含在Git中）
├── Resource/                                 # 训练资源目录（不包含在Git中）
│   ├── Character/                            # 单字符音频（41个文件）
│   └── Lesson-XX/                            # 课程音频和文本（40个课程）
├── Logo/                                     # 应用图标
│   ├── logo_light.png                        # 浅色主题图标
│   └── logo_dark.png                         # 深色主题图标
├── Echarts/                                  # 图表HTML模板
│   ├── calendar.html                         # 日历热力图模板
│   ├── table.html                            # 统计图表模板
│   └── echarts.min.js                        # Echarts配置文件
└── Installer/                                # 安装程序构建文件
    ├── Build_Installer.bat                   # 构建脚本
    ├── setup.iss                             # Inno Setup 配置
    ├── logo.ico                              # 安装程序图标
    └── logo.bmp                              # 安装向导图片
```

## 快捷键

- **Ctrl+Enter**: 检查结果 / 下一个练习
- **Ctrl+R**: 重播文本音频
- **Space**: 播放/暂停文本音频

## 版本历史

### v1.2.0 (2025-11-28)
- ✨ 新增功能
  - 📅 日历热力图，直观显示每日练习活动
  - 📊 交互式统计图表（基于Echarts）
  - 🕐 多种时间聚合模式（小时/天/月/年）
  - ⏱️ 练习时长精确追踪
  - 🎨 主题切换时标题栏颜色同步（Windows 11）
  - 🖼️ 支持浅色/深色主题专用 Logo
- 🐛 修复
  - 改进统计窗口交互性能


### v1.1.0 (2025-11-17)
- ✨ 新增统计功能
  - 记录每次练习的准确率
  - 统计练习时长、次数和准确率
  - 课程练习数据展示
  - 总体统计数据展示
- 🎨 优化界面布局
- 📊 新增统计窗口

### v1.0.0 (2025-11-10)
- 🎉 初始版本
- 实现Koch方法核心功能
- 支持40课程渐进学习
- 单字符音频练习
- 实时准确率检查

## 技术栈

- **语言**: Python 3.10
- **GUI框架**: PySide6 (Qt for Python)
- **UI组件库**: qfluentwidgets
- **音频处理**: scipy, numpy
- **数据可视化**: Echarts 6.0
- **打包工具**: PyInstaller, Inno Setup

## 许可证

MIT License

## 联系方式

- GitHub: [@xiaokanghu1997](https://github.com/xiaokanghu1997)
