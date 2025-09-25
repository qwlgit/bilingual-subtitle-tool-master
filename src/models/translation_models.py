"""
翻译相关数据模型
Translation Data Models
"""

import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class TranslationTask:
    """翻译任务数据模型"""
    text: str
    task_id: int
    is_incremental: bool = False
    version: Optional[int] = None
    translated_text: str = ""
    timestamp: str = ""
    create_time: float = 0.0
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if self.create_time == 0.0:
            self.create_time = time.time()


@dataclass
class TranslationRequest:
    """翻译请求数据模型"""
    text: str
    source_language: str = "zh"
    target_language: str = "en"
    request_id: Optional[int] = None


@dataclass
class TranslationResponse:
    """翻译响应数据模型"""
    translated_text: str
    source_text: str
    request_id: Optional[int] = None
    success: bool = True
    error_message: str = ""
    response_time: float = 0.0


@dataclass
class TranslationCache:
    """翻译缓存数据模型"""
    source_text: str
    translated_text: str
    timestamp: float
    hit_count: int = 1
    
    def is_expired(self, expiry_seconds: int = 3600) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.timestamp > expiry_seconds