"""
字幕相关数据模型
Subtitle Data Models
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Union
from collections import deque


@dataclass
class SubtitleText:
    """字幕文本数据模型"""
    text: str
    language: str  # "zh" or "en"
    is_complete: bool = False
    timestamp: Optional[str] = None
    display_duration: int = 2000  # 显示时长（毫秒）


@dataclass
class SubtitlePair:
    """中英文字幕对数据模型"""
    chinese: SubtitleText
    english: SubtitleText
    pair_id: int
    create_time: float
    is_synchronized: bool = True


@dataclass
class SubtitleDisplayState:
    """字幕显示状态数据模型"""
    current_chinese: str = ""
    current_english: str = ""
    is_showing_sentence: bool = False
    is_showing_long_sentence: bool = False
    chinese_processed_length: int = 0
    english_processed_length: int = 0


@dataclass
class SubtitleBuffer:
    """字幕缓冲区数据模型"""
    chinese_buffer: str = ""
    english_buffer: str = ""
    chinese_sentence_buffer: str = ""
    english_sentence_buffer: str = ""
    paired_queue: Optional[deque] = None
    
    def __post_init__(self):
        if self.paired_queue is None:
            self.paired_queue = deque()


@dataclass
class SubtitleWindowConfig:
    """字幕窗口配置数据模型"""
    width: int = 1024
    height: int = 120
    opacity: float = 0.95
    font_size: int = 24
    bottom_distance: int = 180
    is_transparent: bool = True
    stay_on_top: bool = True
    is_draggable: bool = True