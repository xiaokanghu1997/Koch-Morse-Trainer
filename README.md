# Koch - 莫尔斯电码训练器

基于Koch方法的莫尔斯电码学习工具

## 版本信息
- **当前版本**: 1.1.0
- **作者**: xiaokanghu1997
- **更新日期**: 2025-11-10

## 功能特性

- ✅ 支持40个课程的渐进式学习
- ✅ 单字符音频练习（41个字符）
- ✅ 实时准确率检查
- ✅ 学习进度自动保存
- ✅ 深色/浅色主题切换
- ✅ 练习文本高亮显示

## 安装依赖

```bash
pip install PySide6 PySide6-fluent-widgets scipy numpy
```

## 使用方法

1. 运行 `Koch_Setup_v1.1.0.exe ` 安装软件
2. 运行 `Create Koch Morse Training Materials.exe` 生成训练材料
3. 运行 `Koch.exe` 启动训练器
4. 从第1课开始，逐步提升

## 项目结构

```
Koch/
├── Koch.exe                                  # 主程序
├── Config.py                                 # 配置管理
├── Create Koch Morse Training Materials.exe  # 资源生成工具
├── Statistics.json                           # 练习结果统计信息（不包含在Git中）
├── Resource/                                 # 训练资源目录（不包含在Git中）
│   ├── Character/                            # 单字符音频
│   └── Lesson-XX/                            # 课程音频和文本
└── Logo/                                     # 应用图标
```

## 版本历史

### v1.1.0 (2025-11-10)
- ✨ 新增统计功能
  - 记录每次练习的准确率
  - 统计总练习时间
  - 显示课程练习数据
  - 总体统计数据展示
- 🎨 优化界面布局
- 📊 新增统计窗口

### v1.0.0 (2025-11-10)
- 初始版本
- 实现Koch方法核心功能
- 支持40课程渐进学习

## 许可证

MIT License

## 联系方式

- GitHub: [@xiaokanghu1997](https://github.com/xiaokanghu1997)
```