"""
音频工具模块
包含音频设备相关的工具方法
"""

import logging
import pyaudio
import numpy as np  # 新增：用于音频数据处理
import resampy  # 新增：用于音频重采样
import time

# 检查是否支持WASAPI
try:
    import pyaudiowpatch as pyaudiowpatch
    HAS_WASAPI = True
except ImportError:
    HAS_WASAPI = False

logger = logging.getLogger(__name__)


def resample_audio(audio_data, orig_sr, target_sr, orig_channels=2):
    """
    将音频数据从原始采样率转换为目标采样率

    参数:
        audio_data: 原始音频字节数据
        orig_sr: 原始采样率
        target_sr: 目标采样率
        orig_channels: 原始音频通道数

    返回:
        重采样后的音频字节数据
    """
    if orig_sr == target_sr:
        return audio_data  # 采样率相同，无需转换

    try:
        # 将字节数据转换为numpy数组 (16位整数)
        audio_np = np.frombuffer(audio_data, dtype=np.int16)

        # 多通道转单通道（如果需要）
        if orig_channels > 1:
            # 取平均值合并所有通道
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
        logger.error(f"音频重采样错误: {str(e)}")
        return audio_data  # 出错时返回原始数据


def test_audio_device(device_index, device_info):
    """
    测试音频设备是否真正可用
    
    Args:
        device_index: 设备索引
        device_info: 设备信息
        
    Returns:
        bool: 设备是否可用
    """
    p = None
    try:
        p = pyaudio.PyAudio()
        
        # 检查设备基本信息
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
                channels=min(max_input, 2),  # 最多使用2个通道
                rate=int(sample_rate),
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            return True
        except Exception as stream_error:
            logger.debug(f"设备 {device_index} 测试失败: {stream_error}")
            return False
        finally:
            if stream:
                try:
                    stream.close()
                except:
                    pass
            
    except Exception as e:
        logger.warning(f"测试设备 {device_index} 时出错: {e}")
        return False
    finally:
        if p:
            try:
                p.terminate()
            except:
                pass


def get_wasapi_loopback_devices():
    """
    获取WASAPI环回设备（如果可用）
    
    Returns:
        list: WASAPI环回设备列表
    """
    wasapi_devices = []
    
    if not HAS_WASAPI:
        return wasapi_devices
        
    try:
        with pyaudiowpatch.PyAudio() as p:
            # 正确的API应该是通过PyAudio实例的方法来访问WASAPI功能
            # pyaudiowpatch扩展了PyAudio类，添加了WASAPI支持
            wasapi_info = p.get_wasapi_loopback_devices()  # type: ignore[attr-defined]
            if wasapi_info:
                for i, device_info in enumerate(wasapi_info):
                    wasapi_devices.append({
                        'index': i,
                        'name': f"WASAPI Loopback: {device_info['name']}",
                        'is_loopback': True,
                        'max_input': 0,  # 环回设备通常没有输入通道
                        'max_output': device_info['maxOutputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
    except Exception as e:
        logger.warning(f"获取WASAPI环回设备时出错: {e}")
        
    return wasapi_devices


def get_audio_devices():
    """
    获取真正可用的音频输入设备（包括WASAPI环回设备）
    
    Returns:
        list: 音频设备列表，每个元素为(索引, 设备名称, 设备类型, 是否可用)元组
    """
    valid_devices = []
    
    try:
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        logger.info(f"开始扫描音频设备，共检测到 {device_count} 个设备")

        # 获取WASAPI环回设备
        wasapi_devices = get_wasapi_loopback_devices()
        
        # 扫描所有设备并测试可用性
        for i in range(device_count):
            try:
                device_info = p.get_device_info_by_index(i)
                device_name = str(device_info.get("name", ""))
                max_input = int(device_info.get("maxInputChannels", 0))
                max_output = int(device_info.get("maxOutputChannels", 0))
                sample_rate = float(device_info.get("defaultSampleRate", 0))
                
                # 测试设备是否可用
                is_usable = test_audio_device(i, device_info)
                
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
                    valid_devices.append((i, device_name, device_category, is_usable))
                    logger.info(f"可用设备 {i}: {device_name} [{device_category}] - 采样率: {sample_rate}Hz")
                else:
                    logger.debug(f"跳过不可用设备 {i}: {device_name}")

            except Exception as e:
                logger.warning(f"无法获取设备 {i} 的信息: {e}")
                continue

        # 添加WASAPI环回设备
        for wasapi_device in wasapi_devices:
            # 修复：使用负数索引以避免与普通设备冲突，便于识别
            wasapi_index = -(wasapi_device['index'] + 1)  # 负数索引，从-1开始
            valid_devices.append((
                wasapi_index,
                wasapi_device['name'],
                "系统音频",
                True
            ))

        # 记录统计信息
        logger.info(f"设备扫描完成:")
        logger.info(f"  - 总检测设备数: {device_count}")
        logger.info(f"  - 可用设备数: {len(valid_devices)}")
        logger.info(f"  - WASAPI环回设备: {len(wasapi_devices)}")

        # 按设备类型排序：系统音频 > 麦克风 > 音频输入
        valid_devices.sort(key=lambda x: (
            0 if x[2] == "系统音频" else 
            1 if x[2] == "麦克风" else 2,
            x[0]
        ))

        return valid_devices
        
    except Exception as e:
        logger.error(f"获取音频设备列表时出错: {e}")
        return []
    finally:
        try:
            p.terminate()
        except:
            pass


def get_default_audio_device(preferred_type="system_audio"):
    """
    获取推荐的默认音频设备
    
    Args:
        preferred_type: 首选设备类型 ("system_audio" 或 "microphone")
    
    Returns:
        tuple: (设备索引, 设备名称, 设备类型) 或 None
    """
    try:
        devices = get_audio_devices()
        if not devices:
            return None
            
        # 按优先级选择设备
        priority_order = ["系统音频", "麦克风", "音频输入"]
        
        if preferred_type == "system_audio":
            # 系统音频优先
            for device_type in priority_order:
                for device in devices:
                    if device[2] == device_type:
                        logger.info(f"推荐默认设备: 索引 {device[0]} - {device[1]} [{device[2]}]")
                        return device
        else:
            # 麦克风优先
            mic_priority = ["麦克风", "音频输入", "系统音频"]
            for device_type in mic_priority:
                for device in devices:
                    if device[2] == device_type:
                        logger.info(f"推荐默认设备: 索引 {device[0]} - {device[1]} [{device[2]}]")
                        return device
        
        # 如果没有找到匹配类型，返回第一个设备
        if devices:
            logger.info(f"使用第一个可用设备: 索引 {devices[0][0]} - {devices[0][1]} [{devices[0][2]}]")
            return devices[0]
        else:
            return None
            
    except Exception as e:
        logger.error(f"获取默认音频设备时出错: {e}")
        return None
