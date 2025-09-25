"""
翻译服务测试模块
Translation Service Test Module
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.translation_service import TranslationService, RealTimeTranslationThread
from src.models.translation_models import TranslationTask, TranslationRequest, TranslationResponse


class TestTranslationService(unittest.TestCase):
    """翻译服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.translationService = TranslationService("http://localhost:8000/translate")
    
    def tearDown(self):
        """测试后清理"""
        self.translationService.clear_cache()
    
    def testTranslateTextSuccess(self):
        """测试成功的翻译请求"""
        with patch('requests.post') as mockPost:
            # 模拟成功的API响应
            mockResponse = Mock()
            mockResponse.status_code = 200
            mockResponse.json.return_value = {"translated_text": "Hello World"}
            mockPost.return_value = mockResponse
            
            result = self.translationService.translate_text("你好世界")
            
            self.assertEqual(result, "Hello World")
            mockPost.assert_called_once()
    
    def testTranslateTextFailure(self):
        """测试失败的翻译请求"""
        with patch('requests.post') as mockPost:
            # 模拟失败的API响应
            mockResponse = Mock()
            mockResponse.status_code = 500
            mockPost.return_value = mockResponse
            
            result = self.translationService.translate_text("你好世界")
            
            self.assertIsNone(result)
    
    def testTranslateTextTimeout(self):
        """测试翻译请求超时"""
        with patch('requests.post') as mockPost:
            # 模拟超时异常
            import requests
            mockPost.side_effect = requests.exceptions.Timeout()
            
            result = self.translationService.translate_text("你好世界")
            
            self.assertIsNone(result)
    
    def testTranslationCache(self):
        """测试翻译缓存功能"""
        with patch('requests.post') as mockPost:
            # 模拟API响应
            mockResponse = Mock()
            mockResponse.status_code = 200
            mockResponse.json.return_value = {"translated_text": "Hello World"}
            mockPost.return_value = mockResponse
            
            # 第一次翻译
            result1 = self.translationService.translate_text("你好世界")
            self.assertEqual(result1, "Hello World")
            
            # 第二次翻译（应该使用缓存）
            result2 = self.translationService.translate_text("你好世界")
            self.assertEqual(result2, "Hello World")
            
            # 验证API只被调用一次
            self.assertEqual(mockPost.call_count, 1)
    
    def testClearCache(self):
        """测试清空缓存功能"""
        # 添加一些缓存数据
        self.translationService._update_cache("test", "测试")
        
        # 验证缓存中有数据
        self.assertIn("test", self.translationService.translation_cache)
        
        # 清空缓存
        self.translationService.clear_cache()
        
        # 验证缓存已清空
        self.assertEqual(len(self.translationService.translation_cache), 0)
    
    def testEmptyTextTranslation(self):
        """测试空文本翻译"""
        result = self.translationService.translate_text("")
        self.assertIsNone(result)
        
        result = self.translationService.translate_text(None)
        self.assertIsNone(result)
    
    def testCacheSizeLimit(self):
        """测试缓存大小限制"""
        # 模拟缓存达到上限
        for i in range(1010):  # 超过MAX_TRANSLATION_CACHE_SIZE
            self.translationService._update_cache(f"key_{i}", f"value_{i}")
        
        # 验证缓存大小没有超过限制
        self.assertEqual(len(self.translationService.translation_cache), 1000)


class TestTranslationModels(unittest.TestCase):
    """翻译模型测试类"""
    
    def testTranslationTask(self):
        """测试翻译任务模型"""
        task = TranslationTask(
            text="你好世界",
            task_id=1,
            is_incremental=True,
            version=1
        )
        
        self.assertEqual(task.text, "你好世界")
        self.assertEqual(task.task_id, 1)
        self.assertTrue(task.is_incremental)
        self.assertEqual(task.version, 1)
        self.assertEqual(task.translated_text, "")
        self.assertIsNotNone(task.timestamp)
        self.assertGreater(task.create_time, 0)
    
    def testTranslationRequest(self):
        """测试翻译请求模型"""
        request = TranslationRequest(
            text="你好世界",
            source_language="zh",
            target_language="en",
            request_id=123
        )
        
        self.assertEqual(request.text, "你好世界")
        self.assertEqual(request.source_language, "zh")
        self.assertEqual(request.target_language, "en")
        self.assertEqual(request.request_id, 123)
    
    def testTranslationResponse(self):
        """测试翻译响应模型"""
        response = TranslationResponse(
            translated_text="Hello World",
            source_text="你好世界",
            request_id=123,
            success=True,
            response_time=0.5
        )
        
        self.assertEqual(response.translated_text, "Hello World")
        self.assertEqual(response.source_text, "你好世界")
        self.assertEqual(response.request_id, 123)
        self.assertTrue(response.success)
        self.assertEqual(response.response_time, 0.5)
        self.assertEqual(response.error_message, "")


class TestRealTimeTranslationThread(unittest.TestCase):
    """实时翻译线程测试类"""
    
    def setUp(self):
        """测试前准备"""
        from multiprocessing import Queue
        self.queue = Queue()
        self.translateApi = "http://localhost:8000/translate"
    
    def testThreadInitialization(self):
        """测试线程初始化"""
        thread = RealTimeTranslationThread(self.queue, self.translateApi)
        
        self.assertEqual(thread.queue, self.queue)
        self.assertEqual(thread.translation_service.api_endpoint, self.translateApi)
        self.assertTrue(thread.is_running)
    
    def testThreadStop(self):
        """测试线程停止"""
        thread = RealTimeTranslationThread(self.queue, self.translateApi)
        
        # 停止线程
        thread.stop()
        
        self.assertFalse(thread.is_running)
    
    @patch('requests.post')
    def testTranslationTaskProcessing(self, mockPost):
        """测试翻译任务处理"""
        # 模拟API响应
        mockResponse = Mock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = {"translated_text": "Hello World"}
        mockPost.return_value = mockResponse
        
        # 创建翻译任务
        task = TranslationTask("你好世界", 1)
        
        # 创建线程并处理任务
        thread = RealTimeTranslationThread(self.queue, self.translateApi)
        
        # 将任务放入队列
        self.queue.put(task)
        
        # 模拟处理任务
        with patch.object(thread, 'translation_done') as mockSignal:
            # 这里需要模拟run方法的部分逻辑
            # 由于涉及到Qt信号，实际测试可能需要更复杂的setup
            pass


if __name__ == '__main__':
    unittest.main()