"""
音频服务测试模块
Audio Service Test Module
"""

import unittest
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.audio_service import AudioService
from src.models.audio_models import AudioDevice, AudioConfig


class TestAudioService(unittest.TestCase):
    """音频服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.audioService = AudioService()
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    def testResampleAudio(self):
        """测试音频重采样功能"""
        # 创建测试音频数据（16位，2通道，44100Hz）
        import numpy as np
        sampleRate = 44100
        targetRate = 16000
        channels = 2
        duration = 1.0  # 1秒
        
        # 生成正弦波测试数据
        t = np.linspace(0, duration, int(sampleRate * duration), False)
        frequency = 440  # A4音符
        audioData = np.sin(2 * np.pi * frequency * t)
        
        # 转换为16位整数并复制到双通道
        audioData = (audioData * 32767).astype(np.int16)
        stereoData = np.column_stack((audioData, audioData)).flatten()
        audioBytes = stereoData.tobytes()
        
        # 测试重采样
        resampledBytes = self.audioService.resample_audio(
            audioBytes, sampleRate, targetRate, channels
        )
        
        # 验证结果
        self.assertIsInstance(resampledBytes, bytes)
        self.assertGreater(len(resampledBytes), 0)
        
        # 重采样后的数据应该更短
        originalLength = len(audioBytes)
        resampledLength = len(resampledBytes)
        expectedRatio = targetRate / sampleRate
        actualRatio = resampledLength / originalLength
        
        # 允许10%的误差
        self.assertAlmostEqual(actualRatio, expectedRatio, delta=0.1)
    
    def testGetAudioDevices(self):
        """测试获取音频设备列表"""
        devices = self.audioService.get_audio_devices()
        
        # 验证返回的是设备列表
        self.assertIsInstance(devices, list)
        
        # 如果有设备，验证设备对象类型
        if devices:
            device = devices[0]
            self.assertIsInstance(device, AudioDevice)
            self.assertIsInstance(device.index, int)
            self.assertIsInstance(device.name, str)
            self.assertIsInstance(device.device_type, str)
            self.assertIsInstance(device.is_available, bool)
    
    def testGetDefaultAudioDevice(self):
        """测试获取默认音频设备"""
        # 测试系统音频优先
        systemDevice = self.audioService.get_default_audio_device("system_audio")
        if systemDevice:
            self.assertIsInstance(systemDevice, AudioDevice)
            self.assertTrue(systemDevice.is_available)
        
        # 测试麦克风优先
        micDevice = self.audioService.get_default_audio_device("microphone")
        if micDevice:
            self.assertIsInstance(micDevice, AudioDevice)
            self.assertTrue(micDevice.is_available)
    
    def testTestAudioDevice(self):
        """测试音频设备测试功能"""
        # 创建模拟设备信息
        deviceInfo = {
            "name": "Test Device",
            "maxInputChannels": 2,
            "defaultSampleRate": 44100
        }
        
        # 注意：这个测试可能在没有音频设备的环境中失败
        # 实际测试时需要根据环境调整
        try:
            result = self.audioService.test_audio_device(0, deviceInfo)
            self.assertIsInstance(result, bool)
        except Exception:
            # 在CI环境中可能没有音频设备，跳过此测试
            self.skipTest("音频设备测试需要实际的音频硬件")
    
    def testGetWasapiLoopbackDevices(self):
        """测试WASAPI环回设备获取"""
        devices = self.audioService.get_wasapi_loopback_devices()
        
        # 验证返回的是列表
        self.assertIsInstance(devices, list)
        
        # 如果有设备，验证设备信息结构
        if devices:
            device = devices[0]
            self.assertIn('index', device)
            self.assertIn('name', device)
            self.assertIn('is_loopback', device)
            self.assertTrue(device['is_loopback'])


class TestAudioModels(unittest.TestCase):
    """音频模型测试类"""
    
    def testAudioDevice(self):
        """测试音频设备模型"""
        device = AudioDevice(
            index=0,
            name="Test Device",
            device_type="麦克风",
            is_available=True,
            max_input_channels=2,
            max_output_channels=0,
            sample_rate=44100.0,
            is_loopback=False,
            is_wasapi=False
        )
        
        self.assertEqual(device.index, 0)
        self.assertEqual(device.name, "Test Device")
        self.assertEqual(device.device_type, "麦克风")
        self.assertTrue(device.is_available)
        self.assertEqual(device.max_input_channels, 2)
        self.assertEqual(device.sample_rate, 44100.0)
        self.assertFalse(device.is_loopback)
    
    def testAudioConfig(self):
        """测试音频配置模型"""
        config = AudioConfig(
            device_index=0,
            sample_rate=16000,
            channels=2,
            format=16,
            chunk_size=1024
        )
        
        self.assertEqual(config.device_index, 0)
        self.assertEqual(config.sample_rate, 16000)
        self.assertEqual(config.channels, 2)
        self.assertEqual(config.format, 16)
        self.assertEqual(config.chunk_size, 1024)


if __name__ == '__main__':
    unittest.main()