"""
文本处理服务模块
Text Processing Service Module
"""

import logging
import time
import re
from typing import Tuple, Optional, List

from ..config.constants import SENTENCE_END_CHARS, PUNCTUATION_CHARS
from ..models.translation_models import TranslationTask

logger = logging.getLogger(__name__)


class TextProcessingService:
    """文本处理服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_complete_sentence(self, text: str) -> Tuple[Optional[str], str]:
        """
        提取以标点符号结尾的完整句子，支持标点符号和数字模式边界
        
        Args:
            text: 输入的文本内容
            
        Returns:
            (sentence, remaining) - 完整句子和剩余文本，sentence为None表示没有找到完整句子
        """
        if not text:
            return None, ""
        
        end_pos = -1
        
        # 查找最后一个标点符号位置
        for char in SENTENCE_END_CHARS:
            pos = text.rfind(char)
            if pos > end_pos:
                end_pos = pos
        
        # 检查数字模式（年份等）
        number_patterns = [
            r'\d{4}',  # 4位数字年份
            r'\d{1,2}/\d{1,2}/\d{4}',  # 日期格式
            r'\d{1,2}:\d{2}',  # 时间格式
        ]
        
        number_positions = []
        for pattern in number_patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                last_match = matches[-1]
                number_positions.append(last_match.end())
        
        # 如果有数字模式，取最后一个数字模式的位置
        if number_positions:
            max_number_pos = max(number_positions)
            if max_number_pos > end_pos:
                end_pos = max_number_pos - 1
        
        if end_pos != -1:
            sentence = text[:end_pos + 1]
            remaining = text[end_pos + 1:]
            return sentence, remaining
        
        return None, text
    
    def is_punctuation_only(self, text: str) -> bool:
        """
        检查文本是否只包含标点符号
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否只包含标点符号
        """
        if not text or not text.strip():
            return True
        return all(char in PUNCTUATION_CHARS for char in text.strip())
    
    def process_text_with_dual_channels(self, worker_instance, text_print: str, 
                                       last_processed_index: int, pending_text: str,
                                       translation_tasks, realtime_queue, task_counter: int,
                                       args, incremental_queue, incremental_tasks) -> Tuple[bool, int, str, int]:
        """
        双通道文本处理：完整句子用离线通道，碎片文本用在线通道
        
        Returns:
            (has_complete_sentence, new_last_processed_index, new_pending_text, new_task_counter)
        """
        worker_instance.last_text_receive_time = time.time()
        
        if not text_print or len(text_print) <= last_processed_index:
            return False, last_processed_index, pending_text, task_counter
        
        unprocessed_text = text_print[last_processed_index:]
        self.logger.info(f"未处理文本: {unprocessed_text}")
        
        # 检查是否有完整句子
        sentence, remaining = self.extract_complete_sentence(unprocessed_text)
        
        if sentence:
            self.logger.info(f"检测到完整句子: {sentence}")
            
            # 过滤只包含标点符号的句子
            if self.is_punctuation_only(sentence):
                self.logger.info(f"跳过翻译只包含标点符号的句子: {sentence}")
                new_last_processed_index = last_processed_index + len(sentence)
                new_pending_text = remaining
                return True, new_last_processed_index, new_pending_text, task_counter
            
            # 发送到离线通道进行高质量翻译
            worker_instance.offline_version += 1
            realtime_task = TranslationTask(
                sentence, task_counter, is_incremental=False, 
                version=worker_instance.offline_version
            )
            translation_tasks.append(realtime_task)
            realtime_queue.put(realtime_task)
            task_counter += 1
            self.logger.info(f"完整句子已发送到离线通道翻译（版本: {worker_instance.offline_version}）")
            
            # 更新处理位置
            new_last_processed_index = last_processed_index + len(sentence)
            new_pending_text = remaining
            
            # 清空增量任务
            incremental_tasks.clear()
            self.logger.info("已清空在线通道任务，完整句子优先")
            
            return True, new_last_processed_index, new_pending_text, task_counter
        
        # 在线翻译由其他函数专门处理
        new_pending_text = unprocessed_text
        self.logger.debug("双通道模式：在线翻译由专门函数处理，这里只处理完整句子")
        
        return False, last_processed_index, new_pending_text, task_counter
    
    def handle_timeout_with_dual_channels(self, worker_instance, is_running: bool, 
                                         last_text_receive_time: float, pending_text: str,
                                         translation_tasks, realtime_queue, task_counter: int,
                                         last_processed_index: int, status_update_signal,
                                         args, incremental_queue, incremental_tasks):
        """
        双通道超时处理：未完成文本强制发送到离线通道完成翻译
        """
        if not is_running:
            return
        
        current_time = time.time()
        if (current_time - last_text_receive_time >= args.timeout_seconds and
                pending_text and pending_text.strip()):
            
            self.logger.info(f"超时处理：{args.timeout_seconds}秒无新输入，强制翻译未完成文本: {pending_text}")
            
            # 过滤只包含标点符号的超时文本
            if self.is_punctuation_only(pending_text):
                self.logger.info(f"跳过翻译只包含标点符号的超时文本: {pending_text}")
                worker_instance.last_processed_index = last_processed_index + len(pending_text)
                worker_instance.pending_text = ""
                worker_instance.task_counter = task_counter
                incremental_tasks.clear()
                self.logger.info("已清空在线通道任务，跳过标点符号翻译")
                status_update_signal.emit(f"超时处理：{args.timeout_seconds}秒无新输入，跳过标点符号翻译")
                return
            
            # 超时文本发送到离线通道
            worker_instance.offline_version += 1
            timeout_task = TranslationTask(
                pending_text, task_counter, is_incremental=False, 
                version=worker_instance.offline_version
            )
            translation_tasks.append(timeout_task)
            realtime_queue.put(timeout_task)
            task_counter += 1
            self.logger.info(f"超时文本已发送到离线通道进行完整翻译（版本: {worker_instance.offline_version}）")
            
            # 更新状态
            worker_instance.last_processed_index = last_processed_index + len(pending_text)
            worker_instance.pending_text = ""
            worker_instance.task_counter = task_counter
            
            # 清空在线通道任务
            incremental_tasks.clear()
            self.logger.info("已清空在线通道任务，超时文本优先处理")
            
            status_update_signal.emit(f"超时处理：{args.timeout_seconds}秒无新输入，已翻译未完成文本")


# 保持兼容性的函数包装
def extract_complete_sentence(text: str) -> Tuple[Optional[str], str]:
    """兼容性函数包装"""
    service = TextProcessingService()
    return service.extract_complete_sentence(text)


def process_text_with_dual_channels(worker_instance, text_print: str, last_processed_index: int,
                                   pending_text: str, translation_tasks, realtime_queue,
                                   task_counter: int, args, incremental_queue, 
                                   incremental_tasks) -> Tuple[bool, int, str, int]:
    """兼容性函数包装"""
    service = TextProcessingService()
    return service.process_text_with_dual_channels(
        worker_instance, text_print, last_processed_index, pending_text,
        translation_tasks, realtime_queue, task_counter, args,
        incremental_queue, incremental_tasks
    )


def handle_timeout_with_dual_channels(worker_instance, is_running: bool, last_text_receive_time: float,
                                     pending_text: str, translation_tasks, realtime_queue,
                                     task_counter: int, last_processed_index: int,
                                     status_update_signal, args, incremental_queue, incremental_tasks):
    """兼容性函数包装"""
    service = TextProcessingService()
    return service.handle_timeout_with_dual_channels(
        worker_instance, is_running, last_text_receive_time, pending_text,
        translation_tasks, realtime_queue, task_counter, last_processed_index,
        status_update_signal, args, incremental_queue, incremental_tasks
    )