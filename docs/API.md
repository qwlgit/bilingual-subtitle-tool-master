# 📖 API 文档

## 🔧 服务层 API

### AudioService 音频服务

#### 类初始化
```python
from src.services.audio_service import AudioService

audioService = AudioService()
```

#### 主要方法

##### `resample_audio(audio_data, orig_sr, target_sr, orig_channels=2)`
重采样音频数据

**参数:**
- `audio_data` (bytes): 原始音频字节数据
- `orig_sr` (int): 原始采样率
- `target_sr` (int): 目标采样率  
- `orig_channels` (int): 原始音频通道数

**返回:** bytes - 重采样后的音频字节数据

##### `get_audio_devices()`
获取可用的音频设备列表

**返回:** List[AudioDevice] - 音频设备列表

##### `get_default_audio_device(preferred_type="system_audio")`
获取推荐的默认音频设备

**参数:**
- `preferred_type` (str): 首选设备类型 ("system_audio" 或 "microphone")

**返回:** Optional[AudioDevice] - 推荐的音频设备

---

### TranslationService 翻译服务

#### 类初始化
```python
from src.services.translation_service import TranslationService

translationService = TranslationService("http://localhost:8000/translate")
```

#### 主要方法

##### `translate_text(text, source_lang="zh", target_lang="en")`
翻译文本

**参数:**
- `text` (str): 要翻译的文本
- `source_lang` (str): 源语言代码
- `target_lang` (str): 目标语言代码

**返回:** Optional[str] - 翻译结果

##### `clear_cache()`
清空翻译缓存

**返回:** None

---

### TextProcessingService 文本处理服务

#### 类初始化
```python
from src.services.text_service import TextProcessingService

textService = TextProcessingService()
```

#### 主要方法

##### `extract_complete_sentence(text)`
提取完整句子

**参数:**
- `text` (str): 输入文本

**返回:** Tuple[Optional[str], str] - (完整句子, 剩余文本)

##### `is_punctuation_only(text)`
检查文本是否只包含标点符号

**参数:**
- `text` (str): 要检查的文本

**返回:** bool - 是否只包含标点符号

---

## 🧠 核心层 API

### SpeechRecognitionWorker 语音识别工作线程

#### 类初始化
```python
from src.core.speech_recognition import SpeechRecognitionWorker

worker = SpeechRecognitionWorker(deviceIndex=0)
```

#### 信号

##### `updateChinese(str)`
更新中文文本信号

##### `updateEnglish(str, bool)`
更新英文文本信号
- 参数1: 英文文本
- 参数2: 是否为增量翻译

##### `statusUpdate(str)`
状态更新信号

##### `finished()`
完成信号

#### 主要方法

##### `setArgs(args)`
设置参数配置

**参数:**
- `args`: 配置参数对象

##### `start()`
启动工作线程

##### `stop()`
停止工作线程

---

### SubtitleProcessor 字幕处理器

#### 类初始化
```python
from src.core.subtitle_processor import SubtitleProcessor

processor = SubtitleProcessor()
```

#### 主要方法

##### `processChineseText(text, timestamp=None)`
处理中文文本

**参数:**
- `text` (str): 中文文本
- `timestamp` (Optional[str]): 时间戳

**返回:** List[SubtitleText] - 字幕文本列表

##### `processEnglishText(text, isIncremental=False, timestamp=None)`
处理英文文本

**参数:**
- `text` (str): 英文文本
- `isIncremental` (bool): 是否为增量翻译
- `timestamp` (Optional[str]): 时间戳

**返回:** List[SubtitleText] - 字幕文本列表

##### `createSubtitlePair(chineseText, englishText, timestamp=None)`
创建中英文字幕对

**参数:**
- `chineseText` (str): 中文文本
- `englishText` (str): 英文文本
- `timestamp` (Optional[str]): 时间戳

**返回:** SubtitlePair - 字幕对对象

##### `exportSubtitles(format="txt")`
导出字幕

**参数:**
- `format` (str): 导出格式 (txt, srt, vtt)

**返回:** str - 导出的字幕内容

---

## 🎨 UI层 API

### MainWindow 主窗口

#### 类初始化
```python
from src.ui.main_window import MainWindow

mainWindow = MainWindow(args, workerClass)
```

#### 主要方法

##### `refreshAudioDevices()`
刷新音频设备列表

##### `startRecognition()`
开始语音识别

##### `stopRecognition()`
停止语音识别

##### `clearSubtitles()`
清空字幕

##### `exportSubtitles()`
导出字幕

---

### SubtitleOverlayWindow 悬浮字幕窗口

#### 类初始化
```python
from src.ui.subtitle_window import SubtitleOverlayWindow

subtitleWindow = SubtitleOverlayWindow(onCloseCallback)
```

#### 主要方法

##### `updateChineseText(text)`
更新中文文本

**参数:**
- `text` (str): 中文文本

##### `updateEnglishText(text, isIncremental=False)`
更新英文文本

**参数:**
- `text` (str): 英文文本
- `isIncremental` (bool): 是否为增量翻译

##### `setFontSize(size)`
设置字体大小

**参数:**
- `size` (int): 字体大小

##### `setOpacity(opacity)`
设置透明度

**参数:**
- `opacity` (float): 透明度值 (0.0-1.0)

---

## 📊 数据模型 API

### AudioDevice 音频设备模型

```python
from src.models.audio_models import AudioDevice

device = AudioDevice(
    index=0,
    name="设备名称",
    device_type="设备类型",
    is_available=True,
    max_input_channels=2,
    sample_rate=44100.0
)
```

### TranslationTask 翻译任务模型

```python
from src.models.translation_models import TranslationTask

task = TranslationTask(
    text="要翻译的文本",
    task_id=1,
    is_incremental=False,
    version=1
)
```

### SubtitleText 字幕文本模型

```python
from src.models.subtitle_models import SubtitleText

subtitle = SubtitleText(
    text="字幕文本",
    language="zh",
    is_complete=True,
    timestamp="12:34:56.789"
)
```

---

## 🛠️ 工具类 API

### FileManager 文件管理器

```python
from src.utils.file_utils import FileManager

fileManager = FileManager("/path/to/project")
```

### LoggerConfig 日志配置

```python
from src.utils.logger import LoggerConfig

logger = LoggerConfig.setupLogger("MyApp", "INFO", "app.log")
```

---

## 🔧 配置 API

### 应用配置

```python
from src.config.app_config import parse_arguments, setup_logging

args = parse_arguments()
logger = setup_logging(args)
```

### 常量使用

```python
from src.config.constants import TECH_CYAN, DEFAULT_FONT_SIZE

print(f"主题颜色: {TECH_CYAN}")
print(f"默认字体大小: {DEFAULT_FONT_SIZE}")
```

---

## 📝 使用示例

### 基本使用流程

```python
from src.config.app_config import parse_arguments
from src.services.audio_service import AudioService
from src.core.speech_recognition import SpeechRecognitionWorker

# 1. 解析配置
args = parse_arguments()

# 2. 初始化音频服务
audioService = AudioService()
devices = audioService.get_audio_devices()

# 3. 创建语音识别工作线程
worker = SpeechRecognitionWorker(devices[0].index)
worker.setArgs(args)

# 4. 连接信号
worker.updateChinese.connect(lambda text: print(f"中文: {text}"))
worker.updateEnglish.connect(lambda text, inc: print(f"英文: {text}"))

# 5. 启动工作线程
worker.start()
```

### 字幕处理示例

```python
from src.core.subtitle_processor import SubtitleProcessor

processor = SubtitleProcessor()

# 处理中文文本
chineseSubtitles = processor.processChineseText("你好世界。")

# 处理英文文本
englishSubtitles = processor.processEnglishText("Hello World.")

# 尝试配对
pair = processor.tryPairSubtitles()

# 导出字幕
txtContent = processor.exportSubtitles("txt")
```