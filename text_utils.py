"""
文本处理工具模块
包含文本处理相关的工具方法
"""

import logging
import time

# 导入翻译任务类
from translation_manager import TranslationTask

logger = logging.getLogger(__name__)


def extract_complete_sentence(text):
    """
    提取以标点符号结尾的完整句子，支持标点符号和数字模式边界
    
    Args:
        text (str): 输入的文本内容
        
    Returns:
        tuple: (sentence, remaining) - 完整句子和剩余文本
               sentence为None表示没有找到完整句子
    """
    if not text:
        return None, ""
        
    sentence_end_chars = ['，', '。', '！', '？', '.', '!', '?', ';', '；']
    end_pos = -1

    # 查找最后一个标点符号位置
    for char in sentence_end_chars:
        pos = text.rfind(char)  # 使用rfind查找最后一个出现的位置
        if pos > end_pos:
            end_pos = pos

    # 检查数字模式（年份等）
    import re
    number_patterns = [
        r'\d{4}',  # 4位数字年份
        r'\d{1,2}/\d{1,2}/\d{4}',  # 日期格式
        r'\d{1,2}:\d{2}',  # 时间格式
    ]
    
    number_positions = []
    for pattern in number_patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            # 取最后一个匹配的位置
            last_match = matches[-1]
            number_positions.append(last_match.end())
    
    # 如果有数字模式，取最后一个数字模式的位置
    if number_positions:
        max_number_pos = max(number_positions)
        if max_number_pos > end_pos:
            end_pos = max_number_pos - 1  # 调整到数字结束位置

    if end_pos != -1:
        sentence = text[:end_pos + 1]  # 包含标点或数字
        remaining = text[end_pos + 1:]
        return sentence, remaining

    return None, text  # 无完整句子


def process_text_with_dual_channels(self, text_print, last_processed_index, pending_text, 
                                   translation_tasks, realtime_queue, task_counter, args,
                                   incremental_queue, incremental_tasks):
    """
    双通道文本处理：完整句子用离线通道，碎片文本用在线通道
    
    通道职责：
    - 离线通道(realtime_queue): 处理完整句子的高质量翻译（延迟稍高）
    - 在线通道(incremental_queue): 处理碎片文本的实时翻译（实时性优先）
    
    Args:
        self: 对象实例
        text_print: 待处理的文本
        last_processed_index: 上次处理位置
        pending_text: 待处理文本
        translation_tasks: 完整句子翻译任务列表
        realtime_queue: 完整句子翻译队列（离线通道）
        task_counter: 任务计数器
        args: 参数对象
        incremental_queue: 碎片文本翻译队列（在线通道）
        incremental_tasks: 增量翻译任务列表
        
    Returns:
        tuple: (has_complete_sentence, new_last_processed_index, new_pending_text, new_task_counter)
    """
    self.last_text_receive_time = time.time()

    if not text_print or len(text_print) <= last_processed_index:
        return False, last_processed_index, pending_text, task_counter

    unprocessed_text = text_print[last_processed_index:]
    logger.info("未处理文本: %s", unprocessed_text)

    # 步骤1：检查是否有完整句子
    sentence, remaining = extract_complete_sentence(unprocessed_text)

    if sentence:
        logger.info("检测到完整句子: %s", sentence)
        
        # 新增：过滤只包含标点符号的句子
        punctuation_chars = '，。！？,.!?'
        if sentence.strip() and all(char in punctuation_chars for char in sentence.strip()):
            logger.info(f"跳过翻译只包含标点符号的句子: {sentence}")
            # 更新处理位置但不发送翻译请求
            new_last_processed_index = last_processed_index + len(sentence)
            new_pending_text = remaining
            return True, new_last_processed_index, new_pending_text, task_counter
        
        # 发送到离线通道（realtime_queue）进行高质量翻译
        self.offline_version += 1  # 增加离线版本号
        realtime_task = TranslationTask(sentence, task_counter, is_incremental=False, version=self.offline_version)
        translation_tasks.append(realtime_task)
        realtime_queue.put(realtime_task)
        task_counter += 1
        logger.info("完整句子已发送到离线通道翻译（版本: %d）", self.offline_version)

        # 更新处理位置
        new_last_processed_index = last_processed_index + len(sentence)
        new_pending_text = remaining
        
        # 清空增量任务，因为完整句子会覆盖碎片翻译
        incremental_tasks.clear()
        logger.info("已清空在线通道任务，完整句子优先")
        
        return True, new_last_processed_index, new_pending_text, task_counter

    # 步骤2：在线翻译由_process_online_text_translation专门处理，这里不再处理
    # 避免重复发送导致版本号快速递增
    new_pending_text = unprocessed_text
    logger.debug("双通道模式：在线翻译由专门函数处理，这里只处理完整句子")
    
    return False, last_processed_index, new_pending_text, task_counter


def handle_timeout_with_dual_channels(self, is_running, last_text_receive_time, pending_text, 
                                     translation_tasks, realtime_queue, task_counter, 
                                     last_processed_index, status_update_signal, args,
                                     incremental_queue, incremental_tasks):
    """
    双通道超时处理：未完成文本强制发送到离线通道完成翻译
    
    超时策略：
    - 超时文本优先发送到离线通道（高质量翻译）
    - 清空在线通道相关任务，避免冲突
    """
    if not is_running:
        return

    current_time = time.time()
    if (current_time - last_text_receive_time >= args.timeout_seconds and
            pending_text and pending_text.strip()):
        logger.info(f"超时处理：{args.timeout_seconds}秒无新输入，强制翻译未完成文本: {pending_text}")

        # 新增：过滤只包含标点符号的超时文本
        punctuation_chars = '，。！？,.!?'
        if all(char in punctuation_chars for char in pending_text.strip()):
            logger.info(f"跳过翻译只包含标点符号的超时文本: {pending_text}")
            # 更新状态但不发送翻译请求
            self.last_processed_index = last_processed_index + len(pending_text)
            self.pending_text = ""  # 清空已处理的文本
            self.task_counter = task_counter
            
            # 清空在线通道任务
            incremental_tasks.clear()
            logger.info("已清空在线通道任务，跳过标点符号翻译")
            
            status_update_signal.emit(f"超时处理：{args.timeout_seconds}秒无新输入，跳过标点符号翻译")
            return
        
        # 超时文本发送到离线通道，确保高质量翻译
        self.offline_version += 1  # 增加离线版本号
        timeout_task = TranslationTask(pending_text, task_counter, is_incremental=False, version=self.offline_version)
        translation_tasks.append(timeout_task)
        realtime_queue.put(timeout_task)
        task_counter += 1
        logger.info("超时文本已发送到离线通道进行完整翻译（版本: %d）", self.offline_version)

        # 更新状态
        self.last_processed_index = last_processed_index + len(pending_text)
        self.pending_text = ""  # 清空已处理的文本
        self.task_counter = task_counter
        
        # 清空在线通道任务，避免与超时任务冲突
        incremental_tasks.clear()
        logger.info("已清空在线通道任务，超时文本优先处理")
        
        status_update_signal.emit(f"超时处理：{args.timeout_seconds}秒无新输入，已翻译未完成文本")