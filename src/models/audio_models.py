"""
音频相关数据模型
Audio Data Models
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class AudioDevice:
    """音频设备数据模型"""
    index: int
    name: str
    device_type: str  # "麦克风", "系统音频", "音频输入"
    is_available: bool
    max_input_channels: int = 0
    max_output_channels: int = 0
    sample_rate: float = 0.0
    is_loopback: bool = False
    is_wasapi: bool = False


@dataclass
class AudioConfig:
    """音频配置数据模型"""
    device_index: Optional[int] = None
    sample_rate: int = 16000
    channels: int = 2
    format: int = 16  # 16位
    chunk_size: int = 1024
    input_sample_rate: int = 44100
    target_sample_rate: int = 16000


@dataclass
class AudioStream:
    """音频流数据模型"""
    config: AudioConfig
    device: AudioDevice
    is_active: bool = False
    is_recording: bool = False
    start_time: Optional[float] = None
    
    
@dataclass
class AudioData:
    """音频数据模型"""
    data: bytes
    sample_rate: int
    channels: int
    timestamp: float
    device_index: int
    
    @property
    def duration(self) -> float:
        """计算音频数据时长（秒）"""
        # 假设16位音频
        samples_count = len(self.data) // 2 // self.channels
        return samples_count / self.sample_rate