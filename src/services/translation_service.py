"""
翻译服务模块
Translation Service Module
"""

import logging
import requests
import time
from typing import Dict, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from ..models.translation_models import TranslationTask, TranslationRequest, TranslationResponse
from ..config.constants import (
    MAX_TRANSLATION_CACHE_SIZE, TRANSLATION_REQUEST_TIMEOUT,
    DEFAULT_TRANSLATE_API
)

logger = logging.getLogger(__name__)


class TranslationService:
    """翻译服务类"""
    
    def __init__(self, api_endpoint: str = DEFAULT_TRANSLATE_API):
        self.api_endpoint = api_endpoint
        self.translation_cache: Dict[str, str] = {}
        self.request_count = 0
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def translate_text(self, text: str, source_lang: str = "zh", 
                      target_lang: str = "en") -> Optional[str]:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            翻译结果或None
        """
        if not text or not text.strip():
            return None
        
        # 检查缓存
        cache_key = text.strip()
        if cache_key in self.translation_cache:
            self.logger.debug(f"使用缓存翻译: {text}")
            return self.translation_cache[cache_key]
        
        try:
            self.request_count += 1
            request_id = self.request_count
            start_time = time.time()
            
            self.logger.info(f"发送翻译请求 #{request_id}: {text}")
            
            payload = {"text": text}
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=TRANSLATION_REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"翻译API响应时间 #{request_id}: {elapsed_time:.3f}秒")
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("translated_text", "")
                
                if translated_text:
                    # 清理异常字符
                    translated_text = translated_text.replace("âª", "").strip()
                    if not translated_text:
                        translated_text = text
                    
                    # 更新缓存
                    self._update_cache(cache_key, translated_text)
                    
                    self.logger.info(f"翻译完成 #{request_id}: {text} -> {translated_text}")
                    return translated_text
                else:
                    self.logger.warning(f"翻译API返回空结果 #{request_id}")
                    return None
            else:
                self.logger.error(f"翻译API错误 #{request_id}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error(f"翻译请求超时 #{self.request_count}")
            return None
        except Exception as e:
            self.logger.error(f"翻译请求错误 #{self.request_count}: {str(e)}")
            return None
    
    def _update_cache(self, key: str, value: str):
        """更新翻译缓存"""
        self.translation_cache[key] = value
        
        # 限制缓存大小
        if len(self.translation_cache) > MAX_TRANSLATION_CACHE_SIZE:
            # 删除最旧的条目
            oldest_key = next(iter(self.translation_cache))
            del self.translation_cache[oldest_key]
    
    def clear_cache(self):
        """清空翻译缓存"""
        self.translation_cache.clear()
        self.logger.info("翻译缓存已清空")


class RealTimeTranslationThread(QThread):
    """实时翻译线程"""
    
    translation_done = pyqtSignal(TranslationTask)
    
    def __init__(self, queue, translate_api: str, parent=None):
        super().__init__(parent)
        self.queue = queue
        self.translation_service = TranslationService(translate_api)
        self.is_running = True
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self):
        """线程主循环"""
        while self.is_running:
            task_processed = False
            try:
                # 检查队列是否还在有效状态
                try:
                    if not self.queue.empty():
                        task = self.queue.get_nowait()
                        task_start_time = time.time()
                        queue_wait_time = task_start_time - task.create_time
                        
                        self.logger.info(f"开始处理翻译任务: {task.text} (队列等待: {queue_wait_time:.3f}秒)")
                        
                        if task.text and task.text.strip():
                            task_processed = True
                            
                            # 调用翻译服务
                            translated_text = self.translation_service.translate_text(task.text)
                            
                            if translated_text:
                                task.translated_text = translated_text
                                total_time = time.time() - task.create_time
                                self.logger.info(f"翻译完成: {task.text} -> {translated_text} (总计: {total_time:.3f}秒)")
                            else:
                                task.translated_text = task.text  # 翻译失败时使用原文
                                self.logger.warning(f"翻译失败，使用原文: {task.text}")
                            
                            self.translation_done.emit(task)
                            
                except (OSError, ValueError) as queue_error:
                    # 队列已关闭或无效，停止线程
                    if "handle is closed" in str(queue_error) or "closed" in str(queue_error).lower():
                        self.logger.info("翻译队列已关闭，停止翻译线程")
                        self.is_running = False
                        break
                    else:
                        self.logger.error(f"队列操作错误: {str(queue_error)}")
                        self.msleep(10)
                        continue
                except Exception as queue_error:
                    # 处理get_nowait可能抛出的异常
                    if "Empty" in str(queue_error) or "empty" in str(queue_error).lower():
                        # 队列为空，正常情况
                        pass
                    else:
                        self.logger.error(f"获取队列任务错误: {str(queue_error)}")
                    
                    # 如果没有处理任务，才等待
                    if not task_processed:
                        self.msleep(1)
                        
            except Exception as e:
                self.logger.error(f"实时翻译线程错误: {str(e)}")
                # 如果是队列相关错误，停止线程
                if "handle is closed" in str(e) or "closed" in str(e).lower():
                    self.logger.info("翻译线程因队列关闭而停止")
                    self.is_running = False
                    break
    
    def stop(self):
        """停止翻译线程"""
        self.logger.info("停止翻译线程")
        self.is_running = False
        self.quit()
        self.wait()