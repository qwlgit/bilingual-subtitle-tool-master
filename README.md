# 🔊 智能语音识别翻译系统 2.0

> 一个支持实时语音识别和双语字幕显示的智能翻译系统

## ✨ 功能特性

- 🎤 **实时语音识别**: 支持麦克风和系统音频输入
- 🌐 **智能翻译**: 中英文实时翻译，支持增量和完整翻译
- 📺 **双语字幕**: 主窗口和透明悬浮窗双重显示
- 🎨 **科技感界面**: 现代化UI设计，支持透明度调节
- ⚡ **高性能**: 多线程处理，低延迟响应
- 🔧 **高度可配置**: 丰富的参数配置选项

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Windows 10+
- 依赖库见 `requirements.txt`

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd bilingual-subtitle-tool

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
# 运行新版本（推荐）
python src/main.py

# 或运行原版本
python main.py
```

## 📁 项目结构（重构后）

```
src/
├── core/                    # 核心业务逻辑
├── services/               # 服务层
├── ui/                     # 用户界面
├── models/                 # 数据模型
├── config/                 # 配置管理
└── utils/                  # 工具函数
```


```
bilingual-subtitle-tool/
├── src/                           ✅ 源码目录
│   ├── __init__.py               ✅
│   ├── main.py                   ✅ 入口文件（简化）
│   │
│   ├── core/                     ✅ 核心业务逻辑层
│   │   ├── __init__.py          ✅
│   │   ├── speech_recognition.py ✅ 语音识别核心逻辑
│   │   ├── websocket_client.py   ✅ WebSocket客户端逻辑
│   │   └── subtitle_processor.py ✅ 字幕处理核心逻辑
│   │
│   ├── services/                 ✅ 服务层
│   │   ├── __init__.py          ✅
│   │   ├── audio_service.py     ✅ 音频服务
│   │   ├── translation_service.py ✅ 翻译服务
│   │   └── text_service.py      ✅ 文本处理服务
│   │
│   ├── ui/                       ✅ 用户界面层
│   │   ├── __init__.py          ✅
│   │   ├── main_window.py       ✅ 主窗口
│   │   ├── subtitle_window.py   ✅ 悬浮字幕窗口
│   │   └── ui_components.py     ✅ UI组件工具
│   │
│   ├── models/                   ✅ 数据模型层
│   │   ├── __init__.py          ✅
│   │   ├── translation_models.py ✅ 翻译相关数据模型
│   │   ├── audio_models.py      ✅ 音频相关数据模型
│   │   └── subtitle_models.py   ✅ 字幕相关数据模型
│   │
│   ├── config/                   ✅ 配置层
│   │   ├── __init__.py          ✅
│   │   ├── app_config.py        ✅ 应用配置
│   │   └── constants.py         ✅ 常量定义
│   │
│   └── utils/                    ✅ 工具层
│       ├── __init__.py          ✅
│       ├── logger.py            ✅ 日志工具
│       ├── file_utils.py        ✅ 文件操作工具
│       └── common_utils.py      ✅ 通用工具函数
│
├── tests/                        ✅ 测试目录
│   ├── __init__.py              ✅
│   ├── test_audio_service.py    ✅
│   ├── test_translation_service.py ✅
│   └── test_text_service.py     ✅
│
├── docs/                         ✅ 文档目录
│   ├── API.md                   ✅
│   ├── ARCHITECTURE.md          ✅
│   ├── USER_GUIDE.md            ✅
│   └── REFACTOR_GUIDE.md        ✅
│
├── requirements.txt              ✅ 依赖文件
├── setup.py                     ✅ 安装脚本
├── README.md                    ✅ 项目说明
└── .gitignore                   ✅ Git忽略文件
```

详细架构说明请参考 [架构文档](docs/ARCHITECTURE.md)

## 🔧 配置选项

```bash
python src/main.py --help
```

主要参数：
- `--host`: 服务器地址（默认: localhost）
- `--port`: 服务器端口（默认: 10095）
- `--audio_source`: 音频源类型（microphone/system_audio）
- `--translate_api`: 翻译API地址
- `--timeout_seconds`: 翻译超时时间

## 🎮 使用指南

1. **选择音频设备**: 在界面中选择麦克风或系统音频
2. **开始识别**: 点击"开始识别"按钮
3. **查看字幕**: 在主窗口和悬浮窗中查看实时字幕
4. **调整设置**: 右键悬浮窗可调整透明度和字体大小
5. **导出字幕**: 可将字幕内容导出为文件

## 📋 版本历史

### v2.0.0 (当前版本)
- 🏗️ 完全重构代码架构
- 📦 模块化设计，提升可维护性
- 🎨 优化UI界面和用户体验
- ⚡ 性能优化和bug修复

### v1.0.0
- 🎤 基础语音识别功能
- 🌐 实时翻译功能
- 📺 字幕显示功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [架构文档](docs/ARCHITECTURE.md)
- [API文档](docs/API.md)
- [用户指南](docs/USER_GUIDE.md)