"""
音频服务模块
Audio Service Module
"""

import logging
import pyaudio
import numpy as np
import resampy
import time
from typing import List, Optional, Tuple, Dict, Any, Union

# 检查是否支持WASAPI
try:
    import pyaudiowpatch as pyaudiowpatch
    HAS_WASAPI = True
except ImportError:
    HAS_WASAPI = False

from ..models.audio_models import AudioDevice, AudioConfig, AudioStream, AudioData
from ..config.constants import (
    AUDIO_FORMAT, DEFAULT_CHANNELS, DEFAULT_SAMPLE_RATE,
    DEFAULT_AUDIO_FS
)

logger = logging.getLogger(__name__)


class AudioService:
    """音频服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._pyaudio_instance = None
        self._current_stream = None
    
    def resample_audio(self, audio_data: bytes, orig_sr: int, target_sr: int, 
                      orig_channels: int = 2) -> bytes:
        """
        将音频数据从原始采样率转换为目标采样率
        
        Args:
            audio_data: 原始音频字节数据
            orig_sr: 原始采样率
            target_sr: 目标采样率
            orig_channels: 原始音频通道数
            
        Returns:
            重采样后的音频字节数据
        """
        if orig_sr == target_sr:
            return audio_data
        
        try:
            # 将字节数据转换为numpy数组 (16位整数)
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            # 多通道转单通道（如果需要）
            if orig_channels > 1:
                audio_np = audio_np.reshape(-1, orig_channels).mean(axis=1).astype(np.int16)
            
            # 重采样
            resampled_np = resampy.resample(
                audio_np.astype(np.float32),
                orig_sr,
                target_sr
            )
            
            # 转换回16位整数并返回字节数据
            return resampled_np.astype(np.int16).tobytes()
            
        except Exception as e:
            self.logger.error(f"音频重采样错误: {str(e)}")
            return audio_data
    
    def test_audio_device(self, device_index: int, device_info: Dict[str, Any]) -> bool:
        """
        测试音频设备是否真正可用
        
        Args:
            device_index: 设备索引
            device_info: 设备信息
            
        Returns:
            设备是否可用
        """
        try:
            p = pyaudio.PyAudio()
            
            device_name = str(device_info.get("name", ""))
            max_input = int(device_info.get("maxInputChannels", 0))
            sample_rate = float(device_info.get("defaultSampleRate", 0))
            
            # 过滤掉明显无效的设备
            if (max_input <= 0 or 
                sample_rate <= 0 or 
                "virtual" in device_name.lower() or
                "disabled" in device_name.lower() or
                "禁用" in device_name.lower() or
                ("mme" in device_name.lower() and "primary" not in device_name.lower())):
                return False
            
            # 尝试打开设备进行简单测试
            stream = None
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=min(max_input, 2),
                    rate=int(sample_rate),
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
                return True
            except Exception as stream_error:
                self.logger.debug(f"设备 {device_index} 测试失败: {stream_error}")
                return False
            finally:
                if stream:
                    try:
                        stream.close()
                    except:
                        pass
                        
        except Exception as e:
            self.logger.warning(f"测试设备 {device_index} 时出错: {e}")
            return False
        finally:
            try:
                p.terminate()
            except:
                pass
    
    def get_wasapi_loopback_devices(self) -> List[dict]:
        """
        获取WASAPI环回设备（如果可用）
        
        Returns:
            WASAPI环回设备列表
        """
        wasapi_devices = []
        
        if not HAS_WASAPI:
            return wasapi_devices
            
        try:
            with pyaudiowpatch.PyAudio() as p:
                wasapi_info = p.get_wasapi_loopback_devices()
                if wasapi_info:
                    for i, device_info in enumerate(wasapi_info):
                        wasapi_devices.append({
                            'index': i,
                            'name': f"WASAPI Loopback: {device_info['name']}",
                            'is_loopback': True,
                            'max_input': 0,
                            'max_output': device_info['maxOutputChannels'],
                            'sample_rate': device_info['defaultSampleRate']
                        })
        except Exception as e:
            self.logger.warning(f"获取WASAPI环回设备时出错: {e}")
            
        return wasapi_devices
    
    def get_audio_devices(self) -> List[AudioDevice]:
        """
        获取真正可用的音频输入设备（包括WASAPI环回设备）
        
        Returns:
            音频设备列表
        """
        valid_devices = []
        p = None
        
        try:
            p = pyaudio.PyAudio()
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            self.logger.info(f"开始扫描音频设备，共检测到 {device_count} 个设备")

            # 获取WASAPI环回设备
            wasapi_devices = self.get_wasapi_loopback_devices()
            
            # 扫描所有设备并测试可用性
            for i in range(device_count):
                try:
                    device_info = p.get_device_info_by_index(i)
                    device_name = str(device_info.get("name", ""))
                    max_input = int(device_info.get("maxInputChannels", 0))
                    max_output = int(device_info.get("maxOutputChannels", 0))
                    sample_rate = float(device_info.get("defaultSampleRate", 0))
                    
                    # 测试设备是否可用  
                    is_usable = self.test_audio_device(i, dict(device_info))
                    
                    # 确定设备类型
                    device_category = "未知"
                    is_loopback = False
                    
                    # 检查是否为环回设备
                    loopback_keywords = ["loopback", "stereo mix", "what you hear", "立体声混音", "系统音频"]
                    is_loopback = any(keyword in device_name.lower() for keyword in loopback_keywords)
                    
                    if is_loopback:
                        device_category = "系统音频"
                    elif max_input > 0:
                        # 检查是否为麦克风
                        mic_keywords = ["microphone", "mic", "麦克风", "audio input"]
                        if any(keyword in device_name.lower() for keyword in mic_keywords):
                            device_category = "麦克风"
                        else:
                            device_category = "音频输入"
                    
                    # 只添加可用的设备
                    if is_usable:
                        device = AudioDevice(
                            index=i,
                            name=device_name,
                            device_type=device_category,
                            is_available=True,
                            max_input_channels=max_input,
                            max_output_channels=max_output,
                            sample_rate=sample_rate,
                            is_loopback=is_loopback
                        )
                        valid_devices.append(device)
                        self.logger.info(f"可用设备 {i}: {device_name} [{device_category}] - 采样率: {sample_rate}Hz")
                    else:
                        self.logger.debug(f"跳过不可用设备 {i}: {device_name}")

                except Exception as e:
                    self.logger.warning(f"无法获取设备 {i} 的信息: {e}")
                    continue

            # 添加WASAPI环回设备
            for wasapi_device in wasapi_devices:
                wasapi_index = -(wasapi_device['index'] + 1)
                device = AudioDevice(
                    index=wasapi_index,
                    name=wasapi_device['name'],
                    device_type="系统音频",
                    is_available=True,
                    max_input_channels=0,
                    max_output_channels=wasapi_device['max_output'],
                    sample_rate=wasapi_device['sample_rate'],
                    is_loopback=True,
                    is_wasapi=True
                )
                valid_devices.append(device)

            # 记录统计信息
            self.logger.info(f"设备扫描完成:")
            self.logger.info(f"  - 总检测设备数: {device_count}")
            self.logger.info(f"  - 可用设备数: {len(valid_devices)}")
            self.logger.info(f"  - WASAPI环回设备: {len(wasapi_devices)}")

            # 按设备类型排序：系统音频 > 麦克风 > 音频输入
            valid_devices.sort(key=lambda x: (
                0 if x.device_type == "系统音频" else 
                1 if x.device_type == "麦克风" else 2,
                x.index
            ))

    def cleanup_resources(self):
        """
        清理音频资源
        """
        try:
            if self._current_stream:
                try:
                    if hasattr(self._current_stream, 'is_active') and callable(getattr(self._current_stream, 'is_active', None)):
                        if self._current_stream.is_active():
                            self._current_stream.stop_stream()
                    if hasattr(self._current_stream, 'close') and callable(getattr(self._current_stream, 'close', None)):
                        self._current_stream.close()
                    self.logger.info("音频流已关闭")
                except Exception as stream_error:
                    self.logger.error(f"关闭音频流时发生错误: {stream_error}")
                finally:
                    self._current_stream = None
            
            if self._pyaudio_instance:
                try:
                    if hasattr(self._pyaudio_instance, 'terminate') and callable(getattr(self._pyaudio_instance, 'terminate', None)):
                        self._pyaudio_instance.terminate()
                    self.logger.info("PyAudio实例已终止")
                except Exception as pyaudio_error:
                    self.logger.error(f"终止PyAudio实例时发生错误: {pyaudio_error}")
                finally:
                    self._pyaudio_instance = None
                    
        except Exception as e:
            self.logger.error(f"清理音频资源时发生错误: {e}")
    
    def get_default_audio_device(self, preferred_type: str = "system_audio") -> Optional[AudioDevice]:
        """
        获取推荐的默认音频设备
        
        Args:
            preferred_type: 首选设备类型 ("system_audio" 或 "microphone")
        
        Returns:
            推荐的音频设备或None
        """
        try:
            devices = self.get_audio_devices()
            if not devices:
                return None
                
            # 按优先级选择设备
            priority_order = ["系统音频", "麦克风", "音频输入"]
            
            if preferred_type == "system_audio":
                # 系统音频优先
                for device_type in priority_order:
                    for device in devices:
                        if device.device_type == device_type:
                            self.logger.info(f"推荐默认设备: 索引 {device.index} - {device.name} [{device.device_type}]")
                            return device
            else:
                # 麦克风优先
                mic_priority = ["麦克风", "音频输入", "系统音频"]
                for device_type in mic_priority:
                    for device in devices:
                        if device.device_type == device_type:
                            self.logger.info(f"推荐默认设备: 索引 {device.index} - {device.name} [{device.device_type}]")
                            return device
            
            # 如果没有找到匹配类型，返回第一个设备
            if devices:
                device = devices[0]
                self.logger.info(f"使用第一个可用设备: 索引 {device.index} - {device.name} [{device.device_type}]")
                return device
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"获取默认音频设备时出错: {e}")
            return None