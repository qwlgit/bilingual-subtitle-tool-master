# 智能语音识别翻译系统架构文档

## 📁 项目结构

```
bilingual-subtitle-tool/
├── src/                           # 源码目录
│   ├── __init__.py
│   ├── main.py                    # 新的入口文件（简化版）
│   │
│   ├── core/                      # 核心业务逻辑层
│   │   ├── __init__.py
│   │   ├── speech_recognition.py  # 语音识别核心逻辑
│   │   ├── websocket_client.py    # WebSocket客户端
│   │   └── subtitle_processor.py  # 字幕处理核心逻辑
│   │
│   ├── services/                  # 服务层
│   │   ├── __init__.py
│   │   ├── audio_service.py       # 音频服务
│   │   ├── translation_service.py # 翻译服务
│   │   └── text_service.py        # 文本处理服务
│   │
│   ├── ui/                        # 用户界面层
│   │   ├── __init__.py
│   │   ├── main_window.py         # 主窗口
│   │   ├── subtitle_window.py     # 悬浮字幕窗口
│   │   └── ui_components.py       # UI组件工具
│   │
│   ├── models/                    # 数据模型层
│   │   ├── __init__.py
│   │   ├── translation_models.py  # 翻译相关数据模型
│   │   ├── audio_models.py        # 音频相关数据模型
│   │   └── subtitle_models.py     # 字幕相关数据模型
│   │
│   ├── config/                    # 配置层
│   │   ├── __init__.py
│   │   ├── app_config.py          # 应用配置
│   │   └── constants.py           # 常量定义
│   │
│   └── utils/                     # 工具层
│       ├── __init__.py
│       ├── logger.py              # 日志工具
│       ├── file_utils.py          # 文件操作工具
│       └── common_utils.py        # 通用工具函数
│
├── tests/                         # 测试目录
├── docs/                          # 文档目录
├── requirements.txt               # 依赖文件
└── README.md                      # 项目说明
```

## 🏗️ 架构设计

### 分层架构

1. **表示层 (UI Layer)** - `src/ui/`
   - 负责用户界面展示和交互
   - 主窗口、字幕窗口、UI组件

2. **业务逻辑层 (Core Layer)** - `src/core/`
   - 核心业务逻辑处理
   - 语音识别、WebSocket通信、字幕处理

3. **服务层 (Service Layer)** - `src/services/`
   - 封装具体的业务服务
   - 音频服务、翻译服务、文本处理服务

4. **数据模型层 (Model Layer)** - `src/models/`
   - 定义数据结构和模型
   - 翻译模型、音频模型、字幕模型

5. **配置层 (Config Layer)** - `src/config/`
   - 应用配置和常量定义
   - 参数解析、日志配置、系统常量

6. **工具层 (Utils Layer)** - `src/utils/`
   - 通用工具函数
   - 日志工具、文件操作、通用函数

### 模块职责

#### Core 模块
- **speech_recognition.py**: 语音识别主逻辑（原main.py中的AsyncWorker类）
- **websocket_client.py**: WebSocket客户端连接和通信
- **subtitle_processor.py**: 字幕处理和同步逻辑

#### Services 模块
- **audio_service.py**: 音频设备管理、音频流处理、音频重采样
- **translation_service.py**: 翻译API调用、缓存管理、翻译线程
- **text_service.py**: 文本解析、句子提取、双通道处理

#### UI 模块
- **main_window.py**: 主窗口界面（原window.py）
- **subtitle_window.py**: 透明悬浮字幕窗口（原transparent_window.py）
- **ui_components.py**: 可复用的UI组件

#### Models 模块
- **translation_models.py**: 翻译任务、请求、响应等数据模型
- **audio_models.py**: 音频设备、配置、流等数据模型
- **subtitle_models.py**: 字幕文本、配对、显示状态等数据模型

## 🔄 数据流

```
音频输入 → Audio Service → WebSocket Client → 
Speech Recognition → Text Service → Translation Service → 
Subtitle Processor → UI Display
```

## 🎯 重构优势

1. **清晰的职责分离**: 每个模块都有明确的职责边界
2. **更好的可维护性**: 代码组织更清晰，易于维护和扩展
3. **提高可测试性**: 模块化设计便于单元测试
4. **降低耦合度**: 通过服务层和模型层减少模块间耦合
5. **提升代码复用**: 服务和工具可在不同模块间复用
6. **便于协作开发**: 不同开发者可专注于不同模块