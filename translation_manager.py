"""翻译任务管理模块"""
import logging
import requests
import time  # 新增：用于计时
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger("Client")


class TranslationTask:
    def __init__(self, text, task_id, is_incremental=False, version=None):
        self.text = text  # 需要翻译的原始文本
        self.task_id = task_id  # 任务唯一标识符
        self.translated_text = ""  # 存储翻译结果
        self.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 时间戳
        self.create_time = time.time()  # 添加：任务创建的精确时间戳
        self.is_incremental = is_incremental  # 是否为增量翻译任务
        self.version = version  # 版本号，用于解决异步时序问题


class RealTimeTranslationThread(QThread):
    translation_done = pyqtSignal(TranslationTask)

    def __init__(self, queue, translate_api, parent=None):
        super().__init__(parent)
        self.queue = queue
        self.translate_api = translate_api
        self.is_running = True
        self.translation_cache = {}  # 翻译缓存
        self.request_count = 0  # 请求计数器

    def run(self):
        while self.is_running:
            try:
                # 检查队列是否还在有效状态
                try:
                    # 优化：减少队列检查延迟，使用非阻塞方式
                    task_processed = False  # 标记是否处理了任务
                    if not self.queue.empty():
                        task = self.queue.get_nowait()  # 使用非阻塞获取
                        task_start_time = time.time()  # 记录任务开始处理时间
                        queue_wait_time = task_start_time - task.create_time  # 计算队列等待时间
                        logger.info("开始处理翻译任务 #%d: %s (队列等待: %.3f秒)", self.request_count + 1, task.text, queue_wait_time)
                        
                        if task.text and task.text.strip():
                            task_processed = True  # 标记已处理任务
                            # 检查缓存
                            cache_key = task.text.strip()
                            if cache_key in self.translation_cache:
                                task.translated_text = self.translation_cache[cache_key]
                                self.translation_done.emit(task)
                                logger.info("使用缓存翻译: %s -> %s", task.text, task.translated_text)
                                continue

                            # 调用翻译API，优化超时和编码处理
                            try:
                                self.request_count += 1
                                request_id = self.request_count
                                start_time = time.time()  # 记录开始时间
                                logger.info("发送翻译请求 #%d: %s", request_id, task.text)

                                payload = {"text": task.text}
                                # 优化：进一步降低超时时间，提升实时性
                                response = requests.post(
                                    self.translate_api, 
                                    json=payload, 
                                    timeout=1.2,  # 从1.5秒降低到1.2秒，进一步提升响应速度
                                    headers={'Content-Type': 'application/json; charset=utf-8'}
                                )

                                elapsed_time = time.time() - start_time
                                logger.info("翻译API响应时间 #%d: %.3f秒", request_id, elapsed_time)

                                if response.status_code == 200:
                                    result = response.json()
                                    translated_text = result.get("translated_text", "")
                                    if translated_text:
                                        # 清理异常字符
                                        translated_text = translated_text.replace("âª", "").strip()
                                        if not translated_text:  # 如果清理后为空，使用原文
                                            translated_text = task.text
                                            
                                        task.translated_text = translated_text
                                        # 更新缓存（限制大小）
                                        self.translation_cache[cache_key] = translated_text
                                        if len(self.translation_cache) > 1000:
                                            oldest_key = next(iter(self.translation_cache))
                                            del self.translation_cache[oldest_key]
                                        
                                        # 添加任务创建time传递给翻译结果处理
                                        if hasattr(task, 'create_time'):
                                            setattr(task, 'create_time', task.create_time)
                                        
                                        self.translation_done.emit(task)
                                        total_time = time.time() - task.create_time  # 计算总耗时
                                        logger.info("翻译完成 #%d: %s -> %s (API: %.3f秒, 总计: %.3f秒)", request_id, task.text, task.translated_text, elapsed_time, total_time)
                                    else:
                                        logger.warning("翻译API返回空结果 #%d", request_id)
                                else:
                                    logger.error("翻译API错误 #%d: HTTP %s", request_id, response.status_code)
                            except Exception as e:
                                # 确保 request_id 已定义，避免 UnboundLocalError
                                req_id = getattr(locals(), 'request_id', self.request_count)
                                logger.error("翻译请求错误 #%d: %s", req_id, str(e))
                except (OSError, ValueError) as queue_error:
                    # 队列已关闭或无效，停止线程
                    if "handle is closed" in str(queue_error) or "closed" in str(queue_error).lower():
                        logger.info("翻译队列已关闭，停止翻译线程")
                        self.is_running = False
                        break
                    else:
                        logger.error("队列操作错误: %s", str(queue_error))
                        # 短暂停顿后重试
                        self.msleep(10)  # 从50ms减少到10ms，提升响应速度
                        continue
                except Exception as queue_error:
                    # 处理get_nowait可能抛出的异常
                    if "Empty" in str(queue_error) or "empty" in str(queue_error):
                        # 队列为空，正常情况
                        pass
                    else:
                        logger.error("获取队列任务错误: %s", str(queue_error))

                    # 如果没有处理任务，才等待；如果处理了任务，立即检查下一个
                    if not task_processed:
                        self.msleep(1)  # 只有在没有任务时才等待
            except Exception as e:
                logger.error("实时翻译线程错误: %s", str(e))
                # 如果是队列相关错误，停止线程
                if "handle is closed" in str(e) or "closed" in str(e).lower():
                    logger.info("翻译线程因队列关闭而停止")
                    self.is_running = False
                    break

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()
