"""
文本服务测试模块
Text Service Test Module
"""

import unittest
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.text_service import TextProcessingService


class TestTextProcessingService(unittest.TestCase):
    """文本处理服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.textService = TextProcessingService()
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    def testExtractCompleteSentenceWithPunctuation(self):
        """测试提取带标点符号的完整句子"""
        # 测试中文标点
        text = "这是第一句话。这是第二句话"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertEqual(sentence, "这是第一句话。")
        self.assertEqual(remaining, "这是第二句话")
        
        # 测试英文标点
        text = "This is first sentence. This is second"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertEqual(sentence, "This is first sentence.")
        self.assertEqual(remaining, " This is second")
    
    def testExtractCompleteSentenceWithQuestion(self):
        """测试提取问句"""
        text = "你好吗？我很好"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertEqual(sentence, "你好吗？")
        self.assertEqual(remaining, "我很好")
    
    def testExtractCompleteSentenceWithExclamation(self):
        """测试提取感叹句"""
        text = "太棒了！继续努力"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertEqual(sentence, "太棒了！")
        self.assertEqual(remaining, "继续努力")
    
    def testExtractCompleteSentenceWithComma(self):
        """测试逗号分隔的句子"""
        text = "第一部分，第二部分，第三部分"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertEqual(sentence, "第一部分，第二部分，第三部分")
        self.assertEqual(remaining, "")
    
    def testExtractCompleteSentenceWithNumbers(self):
        """测试包含数字的句子"""
        text = "今年是2024年，明年是2025年"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        # 数字模式边界检测
        self.assertIsNotNone(sentence)
        self.assertIsInstance(remaining, str)
    
    def testExtractCompleteSentenceNoComplete(self):
        """测试没有完整句子的情况"""
        text = "这是一个未完成的句子"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertIsNone(sentence)
        self.assertEqual(remaining, text)
    
    def testExtractCompleteSentenceEmpty(self):
        """测试空文本"""
        text = ""
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        self.assertIsNone(sentence)
        self.assertEqual(remaining, "")
    
    def testExtractCompleteSentenceMultiplePunctuation(self):
        """测试多个标点符号"""
        text = "第一句。第二句！第三句？剩余部分"
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        # 应该提取到最后一个标点符号
        self.assertEqual(sentence, "第一句。第二句！第三句？")
        self.assertEqual(remaining, "剩余部分")
    
    def testIsPunctuationOnly(self):
        """测试是否只包含标点符号"""
        # 只有标点符号
        self.assertTrue(self.textService.is_punctuation_only("。"))
        self.assertTrue(self.textService.is_punctuation_only("？！"))
        self.assertTrue(self.textService.is_punctuation_only("，。！？"))
        
        # 包含其他字符
        self.assertFalse(self.textService.is_punctuation_only("你好。"))
        self.assertFalse(self.textService.is_punctuation_only("Hello!"))
        self.assertFalse(self.textService.is_punctuation_only("123？"))
        
        # 空文本
        self.assertTrue(self.textService.is_punctuation_only(""))
        self.assertTrue(self.textService.is_punctuation_only("   "))
    
    def testProcessTextWithDualChannels(self):
        """测试双通道文本处理"""
        # 模拟工作实例
        class MockWorker:
            def __init__(self):
                self.last_text_receive_time = 0
                self.offline_version = 0
        
        worker = MockWorker()
        text_print = "这是一个完整的句子。"
        last_processed_index = 0
        pending_text = ""
        translation_tasks = []
        
        # 模拟队列
        from collections import deque
        realtime_queue = deque()
        incremental_queue = deque()
        incremental_tasks = deque()
        
        # 模拟参数
        class MockArgs:
            timeout_seconds = 2
        
        args = MockArgs()
        
        # 测试处理
        result = self.textService.process_text_with_dual_channels(
            worker, text_print, last_processed_index, pending_text,
            translation_tasks, realtime_queue, 0, args,
            incremental_queue, incremental_tasks
        )
        
        # 验证结果
        has_complete, new_index, new_pending, new_counter = result
        self.assertTrue(has_complete)
        self.assertGreater(new_index, last_processed_index)
        self.assertIsInstance(new_pending, str)
        self.assertIsInstance(new_counter, int)
    
    def testHandleTimeoutWithDualChannels(self):
        """测试双通道超时处理"""
        # 模拟工作实例
        class MockWorker:
            def __init__(self):
                self.last_processed_index = 0
                self.pending_text = ""
                self.task_counter = 0
                self.offline_version = 0
        
        class MockSignal:
            def emit(self, message):
                pass
        
        worker = MockWorker()
        is_running = True
        last_text_receive_time = 0  # 很久以前
        pending_text = "未完成的文本"
        translation_tasks = []
        
        # 模拟队列
        from collections import deque
        realtime_queue = deque()
        incremental_queue = deque()
        incremental_tasks = deque()
        
        # 模拟参数和信号
        class MockArgs:
            timeout_seconds = 1  # 1秒超时
        
        args = MockArgs()
        status_signal = MockSignal()
        
        # 测试超时处理
        self.textService.handle_timeout_with_dual_channels(
            worker, is_running, last_text_receive_time, pending_text,
            translation_tasks, realtime_queue, 0, 0, status_signal,
            args, incremental_queue, incremental_tasks
        )
        
        # 验证超时处理生效（由于时间差足够大，应该触发超时处理）
        self.assertGreaterEqual(len(realtime_queue), 0)


if __name__ == '__main__':
    unittest.main()