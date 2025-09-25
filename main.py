# -*- encoding: utf-8 -*-
import os
import time
import websockets
import ssl
import asyncio
import json
from collections import deque
from websockets.exceptions import ConnectionClosed
from multiprocessing import Queue  # 确保导入Queue

# PyQt5相关导入
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, pyqtSignal, QThread

# 导入UI模块
from window import SubtitleDisplay

# 导入文本处理工具模块
from text_utils import handle_timeout_with_dual_channels, process_text_with_dual_channels

# 导入音频工具模块
from audio_utils import resample_audio

# 导入配置模块
from config import parse_arguments, setup_logging, validate_arguments

# 导入翻译管理模块
from translation_manager import TranslationTask, RealTimeTranslationThread


# 参数解析和设置
args = parse_arguments()
args = validate_arguments(args)
logger = setup_logging(args)

# 全局变量
websocket = None

# 尝试导入pyaudiowpatch，回退到pyaudio
try:
    import pyaudiowpatch as pyaudio

    logger.info("使用pyaudiowpatch库（支持WASAPI环回录制）")
    HAS_WASAPI = True
except ImportError:
    try:
        import pyaudio

        logger.info("使用标准pyaudio库（WASAPI环回录制不可用）")
        HAS_WASAPI = False
    except ImportError:
        logger.error("未找到pyaudio或pyaudiowpatch库")
        HAS_WASAPI = False





# 异步工作线程
class AsyncWorker(QThread):
    update_chinese = pyqtSignal(str)
    update_english = pyqtSignal(str, bool)
    status_update = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, device_index=None, parent=None):
        super().__init__(parent)
        self.id = 0
        self.is_running = False
        # 修复1：恢复为multiprocessing.Queue（支持empty()方法）
        self.realtime_queue = Queue()
        self.realtime_thread = None
        self.text_print_en = ""  # 英文翻译累积
        self.text_print_cn = ""  # 中文翻译累积
        # 新增：英文翻译的在线/离线通道管理
        self.text_print_en_online = ""    # 英文在线通道（增量翻译）
        self.text_print_en_offline = ""   # 英文离线通道（完整翻译）
        
        # 按照记忆规范"双通道翻译显示策略"初始化变量
        self.offline_version = 0    # 离线翻译版本号
        self.online_version = 0     # 在线翻译版本号发送
        self.translation_tasks = deque()
        self.task_counter = 0
        self.last_processed_index = 0  # 上次处理位置
        self.pending_text = ""  # 待处理文本
        self.last_text_receive_time = 0  # 最后接收文本时间
        self.device_index = device_index  # 手动选择的设备索引

        # 增量翻译相关变量
        self.incremental_queue = Queue()  # 增量翻译队列
        self.incremental_thread = None   # 增量翻译线程
        self.incremental_tasks = deque() # 增量翻译任务列表
        self.current_incremental_text = ""  # 当前增量翻译文本
        
        # 顺序翻译控制
        self.is_incremental_translating = False  # 是否正在进行增量翻译
        self.pending_online_text = ""  # 等待翻译的在线文本

        self.timeout_timer = QTimer()
        # 修改信号连接，使用重构后的双通道超时处理函数
        self.timeout_timer.timeout.connect(
            lambda: handle_timeout_with_dual_channels(self, self.is_running, self.last_text_receive_time, 
                                                    self.pending_text, self.translation_tasks, 
                                                    self.realtime_queue, self.task_counter,
                                                    self.last_processed_index, self.status_update, args,
                                                    self.incremental_queue, self.incremental_tasks)
        )
        self.timeout_timer.start(500)
        self._audio_stream = None
        self._pyaudio_instance = None
        self.audio_start_time = None  # 音频开始时间

        # 音频参数
        self.input_sample_rate = 44100  # 输入采样率（系统音频）
        self.target_sample_rate = args.audio_fs  # 目标采样率（服务器要求）
        self.audio_channels = 2  # 音频通道数



    def set_id(self, worker_id):
        self.id = worker_id

    def run(self):
        self.is_running = True
        logger.info("启动工作线程")

        # 启动实时翻译线程
        self.realtime_thread = RealTimeTranslationThread(self.realtime_queue, args.translate_api)
        # 修复信号连接，直接连接信号到处理方法
        self.realtime_thread.translation_done.connect(self.handle_translation_result)
        self.realtime_thread.start()

        # 启动增量翻译线程
        self.incremental_thread = RealTimeTranslationThread(self.incremental_queue, args.translate_api)
        self.incremental_thread.translation_done.connect(self.handle_incremental_translation_result)
        self.incremental_thread.start()

        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.ws_client(self.id, 0, 1))
        except Exception as e:
            logger.error("工作线程运行错误: %s", str(e))
        finally:
            loop.close()
            self.cleanup_resources()
            self.finished.emit()

    def _process_online_text_translation(self, online_text):
        """
        对当前在线显示的中文进行增量翻译（实时响应）
        按照记忆规范"碎片化翻译触发策略"：1字符触发，首字即显
        
        Args:
            online_text: 当前在线显示的中文内容 (text_print_2pass_online)
        """
        if not online_text or not online_text.strip():
            return
        
        # 新增：过滤只包含标点符号的文本
        # 定义常见的中文和英文标点符号
        punctuation_chars = '，。！？,.!?'
        # 检查文本是否只包含标点符号
        if all(char in punctuation_chars for char in online_text.strip()):
            logger.info(f"跳过翻译只包含标点符号的文本: {online_text}")
            return
        
        # 立即发送实时翻译，实现首字即显
        self._send_incremental_translation_realtime(online_text)
        logger.info("实时翻译（首字即显）: %s", online_text)

    def _send_incremental_translation_realtime(self, text):
        """
        发送实时增量翻译请求（不等待顺序，直接发送）
        优化：降低重复检查，提升实时性
        """
        # 简化版本号管理
        self.online_version += 1
        incremental_task = TranslationTask(
            text, self.task_counter, is_incremental=True, version=self.online_version
        )
        self.incremental_tasks.append(incremental_task)
        
        # 立即发送，不再进行复杂的顺序检查
        self.incremental_queue.put(incremental_task)
        self.task_counter += 1
        logger.info("实时发送增量翻译: %s（版本: %d）", text, self.online_version)


    def handle_translation_result(self, task):
        """
        处理翻译结果，按照记忆规范"双通道翻译显示策略"实现
        在线通道：碎片化文本的实时翻译，追加到前一次离线翻译结果后实时显示
        离线通道：完整句子的高质量翻译，追加至历史离线内容并更新显示，同时清空在线通道内容
        """
        logger.info("处理翻译结果: %s (增量: %s, 版本: %s)", task.translated_text, task.is_incremental, task.version)
        
        if not task.translated_text:
            return
            
        if task.is_incremental:
            # 在线通道：碎片化文本的实时翻译
            # 直接替换在线翻译内容（不追加）
            self.text_print_en_online = task.translated_text
            logger.info("更新在线通道翻译: %s", self.text_print_en_online)
            
            # 按照双通道显示策略：追加到前一次离线翻译结果后实时显示
            if self.text_print_en_offline:
                # 有离线内容，追加在线翻译
                self.text_print_en = self.text_print_en_offline + " " + self.text_print_en_online
            else:
                # 没有离线内容，直接显示在线翻译
                self.text_print_en = self.text_print_en_online
            
            # 立即发送在线模式更新，实现实时显示
            self.update_english.emit(self.text_print_en, True)
            logger.info("实时显示英文内容: %s", self.text_print_en)
            
        else:
            # 离线通道：完整句子的高质量翻译
            # 按照记忆规范"字幕更新合并规则"：追加至历史离线内容
            if self.text_print_en_offline and not self.text_print_en_offline.endswith(' '):
                self.text_print_en_offline += ' '
            self.text_print_en_offline += task.translated_text
            logger.info("追加至离线通道: %s", self.text_print_en_offline)
            
            # 合并离线+在线内容并更新显示
            if self.text_print_en_online:
                self.text_print_en = self.text_print_en_offline + " " + self.text_print_en_online
            else:
                self.text_print_en = self.text_print_en_offline
            
            # 发送离线模式更新
            self.update_english.emit(self.text_print_en, False)
            logger.info("离线更新后的英文内容: %s", self.text_print_en)
            
            # 按照记忆规范"字幕更新合并规则"：更新完成后必须先清理在线内容
            self.text_print_en_online = ""
            logger.info("离线更新完成，清空在线内容")

    def handle_incremental_translation_result(self, task):
        """处理增量翻译结果（委托给handle_translation_result处理）"""
        # 直接委托给主处理方法，保持一致性
        self.handle_translation_result(task)

    def cleanup_resources(self):
        """清理音频资源"""
        try:
            if self._audio_stream:
                try:
                    # 检查音频流状态，避免在无效状态下操作
                    if self._audio_stream.is_active():
                        self._audio_stream.stop_stream()
                    self._audio_stream.close()
                    logger.info("音频流已关闭")
                except Exception as stream_error:
                    logger.error("关闭音频流时发生错误: %s", str(stream_error))
                    # 即使关闭失败，也继续清理其他资源
                finally:
                    self._audio_stream = None

            if self._pyaudio_instance:
                try:
                    self._pyaudio_instance.terminate()
                    logger.info("PyAudio实例已终止")
                except Exception as pyaudio_error:
                    logger.error("终止PyAudio实例时发生错误: %s", str(pyaudio_error))
                finally:
                    self._pyaudio_instance = None
        except Exception as e:
            logger.error("资源清理过程中发生未预期错误: %s", str(e))
            logger.error("错误类型: %s", type(e).__name__)
            import traceback
            logger.error("堆栈跟踪: %s", traceback.format_exc())

    def stop(self):
        logger.info("停止工作线程 #%d", self.id)
        self.is_running = False

        try:
            if self.timeout_timer.isActive():
                self.timeout_timer.stop()

            # 改进：先停止翻译线程，然后再清理资源
            if self.realtime_thread:
                logger.info("停止实时翻译线程")
                self.realtime_thread.stop()
                # 等待线程完全停止
                if self.realtime_thread.isRunning():
                    self.realtime_thread.wait(2000)  # 最多等待2秒
                    if self.realtime_thread.isRunning():
                        logger.warning("实时翻译线程未能在规定时间内停止")
                        self.realtime_thread.terminate()  # 强制终止
                self.realtime_thread = None

            if self.incremental_thread:
                logger.info("停止增量翻译线程")
                self.incremental_thread.stop()
                # 等待线程完全停止
                if self.incremental_thread.isRunning():
                    self.incremental_thread.wait(2000)  # 最多等待2秒
                    if self.incremental_thread.isRunning():
                        logger.warning("增量翻译线程未能在规定时间内停止")
                        self.incremental_thread.terminate()  # 强制终止
                self.incremental_thread = None

            # 清理音频资源
            self.cleanup_resources()
            
            # 清理队列（在翻译线程停止后）
            try:
                if hasattr(self, 'realtime_queue') and self.realtime_queue:
                    # 清空队列中的剩余任务
                    while not self.realtime_queue.empty():
                        try:
                            self.realtime_queue.get_nowait()
                        except:
                            break
                    logger.info("实时翻译队列已清空")
                    
                if hasattr(self, 'incremental_queue') and self.incremental_queue:
                    # 清空增量翻译队列
                    while not self.incremental_queue.empty():
                        try:
                            self.incremental_queue.get_nowait()
                        except:
                            break
                    logger.info("增量翻译队列已清空")
            except Exception as queue_error:
                logger.warning("清理队列时出错: %s", str(queue_error))
                
        except Exception as e:
            logger.error("停止工作线程时发生错误: %s", str(e))
            logger.error("错误类型: %s", type(e).__name__)
            import traceback
            logger.error("堆栈跟踪: %s", traceback.format_exc())



    async def record_audio(self, websocket):
        """录制音频（使用手动选择的设备或自动检测）"""
        try:
            FORMAT = pyaudio.paInt16
            CHANNELS = self.audio_channels  # 使用类中定义的通道数
            RATE = self.input_sample_rate  # 使用类中定义的输入采样率
            chunk_size = 20 * args.chunk_size[1] / args.chunk_interval
            CHUNK = int(RATE / 1000 * chunk_size)

            p = pyaudio.PyAudio()
            self._pyaudio_instance = p

            # 使用手动选择的设备或自动检测
            input_device_index = self.device_index
            device_name = "默认设备"

            # 如果没有手动选择设备，则根据音频源类型选择
            if input_device_index is None:
                if args.audio_source == "system_audio":
                    # 直接使用默认输入设备
                    default_device = p.get_default_input_device_info()
                    input_device_index = int(default_device['index'])
                    device_name = default_device['name']
                    logger.info(f"使用默认输入设备: {device_name} (索引: {input_device_index})")
                else:
                    # 使用默认麦克风设备
                    default_device = p.get_default_input_device_info()
                    input_device_index = int(default_device['index'])
                    device_name = default_device['name']
                    logger.info(f"使用默认麦克风设备: {device_name} (索引: {input_device_index})")

            # 打开音频流
            try:
                # 对于系统音频录制，使用特殊参数
                stream_params = {
                    'format': FORMAT,
                    'channels': CHANNELS,
                    'rate': RATE,
                    'input': True,
                    'frames_per_buffer': CHUNK,
                    'input_device_index': input_device_index
                }

                # 如果是系统音频且支持WASAPI，添加环回参数
                if (args.audio_source == "system_audio" and HAS_WASAPI and
                        "loopback" in p.get_device_info_by_index(input_device_index)["name"].lower()):
                    stream_params['as_loopback'] = True

                stream = p.open(**stream_params)
                self._audio_stream = stream

                # 获取实际使用的设备信息
                actual_device_info = p.get_device_info_by_index(input_device_index)
                actual_device_name = actual_device_info['name']

                logger.info(f"音频流打开成功，设备: {actual_device_name} (索引: {input_device_index})")
                logger.info(f"音频参数 - 采样率: {RATE}Hz, 通道数: {CHANNELS}, 格式: 16位整数")
                self.status_update.emit(f"使用音频设备: {actual_device_name} ({RATE}Hz -> {self.target_sample_rate}Hz)")
            except Exception as e:
                logger.error(f"无法打开音频流: {e}")
                self.status_update.emit(f"无法打开音频流: {e}")
                return

            # 记录音频开始时间
            self.audio_start_time = time.time()
            logger.info(f"音频录制开始，设置音频开始时间，音频源: {args.audio_source}")

            # 处理热词
            fst_dict = {}
            hotword_msg = ""
            if args.hotword.strip() != "":
                if os.path.exists(args.hotword):
                    with open(args.hotword, encoding="utf-8") as f_scp:
                        hot_lines = f_scp.readlines()
                        for line in hot_lines:
                            words = line.strip().split(" ")
                            if len(words) < 2:
                                self.status_update.emit("热词格式错误，请检查")
                                continue
                            try:
                                fst_dict[" ".join(words[:-1])] = int(words[-1])
                            except ValueError:
                                self.status_update.emit("热词格式错误，请检查")
                        hotword_msg = json.dumps(fst_dict)
                else:
                    hotword_msg = args.hotword

            use_itn = args.use_itn == 1

            # 发送初始配置消息
            message = json.dumps({
                "mode": args.mode,
                "chunk_size": args.chunk_size,
                "chunk_interval": args.chunk_interval,
                "encoder_chunk_look_back": args.encoder_chunk_look_back,
                "decoder_chunk_look_back": args.decoder_chunk_look_back,
                "wav_name": args.audio_source,
                "is_speaking": True,
                "hotwords": hotword_msg,
                "itn": use_itn,
                "sample_rate": self.target_sample_rate,  # 通知服务器使用的采样率
            })

            # 发送消息（用异常捕获替代状态判断）
            try:
                await websocket.send(message)
            except ConnectionClosed:
                logger.warning("WebSocket连接已关闭，无法发送初始消息")
                return
            except Exception as e:
                logger.error("发送初始消息失败: %s", str(e))
                return

            # 循环发送音频数据
            while self.is_running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)

                    # 新增：重采样音频数据
                    if self.input_sample_rate != self.target_sample_rate:
                        resampled_data = resample_audio(
                            data,
                            self.input_sample_rate,
                            self.target_sample_rate,
                            self.audio_channels
                        )
                    else:
                        resampled_data = data

                    # 发送重采样后的音频数据
                    await websocket.send(resampled_data)
                    await asyncio.sleep(0.005)
                except ConnectionClosed:
                    logger.warning("WebSocket连接已关闭，停止发送音频")
                    break
                except asyncio.CancelledError:
                    logger.info("录音任务被取消")
                    break
                except Exception as e:
                    logger.error("录音错误: %s", str(e))
                    break

        except Exception as e:
            logger.error(f"{args.audio_source}录制错误: %s", str(e))
            self.status_update.emit(f"{args.audio_source}录制错误: {e}")


    async def message(self, id, websocket):
        text_print = ""
        text_print_2pass_online = ""
        text_print_2pass_offline = ""

        ibest_writer = None
        if args.output_dir is not None:
            ibest_writer = open(
                os.path.join(args.output_dir, f"text.{id}"), "a", encoding="utf-8"
            )

        try:
            while self.is_running:
                try:
                    # 接收消息（用异常捕获替代状态判断）
                    meg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    meg = json.loads(meg)
                    wav_name = meg.get("wav_name", "demo")
                    text = meg["text"]
                    timestamp = ""

                    # 记录WebSocket返回的全部内容到日志
                    logger.info("WebSocket返回完整消息meg: %s", json.dumps(meg, ensure_ascii=False))
                    # 记录文本
                    logger.info("WebSocket返回语音识别文本text: %s", text)

                    if ibest_writer:
                        if timestamp:
                            text_write_line = f"{wav_name}\t{text}\t{timestamp}\n"
                        else:
                            text_write_line = f"{wav_name}\t{text}\n"
                        ibest_writer.write(text_write_line)

                    if "mode" not in meg:
                        continue

                    # 更新显示中文文本
                    if meg["mode"] == "online":
                        text_print += text

                    elif meg["mode"] == "2pass-online":
                        text_print_2pass_online += text
                        logger.info("在线通道中的内容text_print_2pass_online: %s", text_print_2pass_online)

                        text_print = text_print_2pass_offline + text_print_2pass_online
                        logger.info("2pass-online中在线通道和离线通道合并后要更新到窗口的内容text_print: %s", text_print)
                        
                        # 更新显示并处理文本
                        self.update_chinese.emit(text_print)
                        logger.info("发送中文显示内容到窗口: %s", text_print)
                        
                        # 根据记忆规范：直接使用实际显示的在线文本进行翻译
                        # 符合"在线翻译数据源选择"和"碎片化翻译触发策略"（1字符触发）
                        self._process_online_text_translation(text_print_2pass_online)

                    elif meg["mode"] == "2pass-offline":
                        text_print_2pass_offline += text
                        logger.info("离线通道中的内容text_print_2pass_offline: %s", text_print_2pass_offline)
                        
                        text_print = text_print_2pass_offline
                        logger.info("2pass-offline中在线通道和离线通道合并后要更新到窗口的内容text_print: %s", text_print)
                        # 在离线内容稳定后清空在线内容和增量任务历史
                        text_print_2pass_online = ""
                        self.incremental_tasks.clear()  # 清空增量任务历史，为新一轮做准备
                        
                        # 按照记忆规范"双通道翻译版本控制"：2pass-offline阶段重置在线翻译版本号
                        self.is_incremental_translating = False
                        self.pending_online_text = ""
                        self.text_print_en_online = ""  # 清空在线英文翻译
                        self.online_version = 0  # 重置在线翻译版本号，避免跨轮次状态污染
                        logger.info("状态重置：清空在线英文翻译和相关状态变量，重置版本号")
                        
                        # 更新显示并处理文本
                        self.update_chinese.emit(text_print)
                        logger.info("发送中文显示内容到窗口: %s", text_print)
                        
                        # 对完整的离线文本进行完整句子提取和翻译
                        updated, new_last_processed_index, new_pending_text, new_task_counter = process_text_with_dual_channels(
                            self, text_print, self.last_processed_index, self.pending_text,
                            self.translation_tasks, self.realtime_queue, self.task_counter, args,
                            self.incremental_queue, self.incremental_tasks
                        )
                        if updated:
                            self.last_processed_index = new_last_processed_index
                            self.pending_text = new_pending_text
                            self.task_counter = new_task_counter


                except ConnectionClosed:
                    logger.warning("WebSocket连接已关闭")
                    break
                except asyncio.TimeoutError:
                    continue  # 超时正常，继续等待
                except asyncio.CancelledError:
                    logger.info("消息处理任务被取消")
                    break
                except Exception as e:
                    logger.error("消息处理错误: %s", str(e))
                    self.status_update.emit(f"消息处理错误: {e}")
                    break

        except Exception as e:
            logger.error("消息处理循环错误: %s", str(e))
            self.status_update.emit(f"消息处理错误: {e}")
        finally:
            if ibest_writer:
                ibest_writer.close()
                logger.info("文本文件已关闭")

    async def ws_client(self, id, chunk_begin, chunk_size):
        for i in range(chunk_begin, chunk_begin + chunk_size):
            if not self.is_running:
                break

            # 配置SSL
            if args.ssl == 1:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # 修复SSL警告
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                uri = f"wss://{args.host}:{args.port}"
            else:
                ssl_context = None
                uri = f"ws://{args.host}:{args.port}"

            logger.info("连接到: %s", uri)
            self.status_update.emit(f"连接到 {uri}")

            try:
                async with websockets.connect(
                        uri, ping_interval=None, ssl=ssl_context
                ) as ws:
                    websocket = ws
                    logger.info("连接成功")
                    self.status_update.emit("连接成功")

                    # 创建任务
                    record_task = asyncio.create_task(self.record_audio(ws))
                    message_task = asyncio.create_task(self.message(f"{id}_{i}", ws))

                    # 等待任一任务完成
                    done, pending = await asyncio.wait(
                        [record_task, message_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # 取消未完成任务
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)

            except Exception as e:
                logger.error("连接错误: %s", str(e))
                self.status_update.emit(f"连接错误: {e}")
                if self.is_running:
                    await asyncio.sleep(5)  # 重试前等待
            finally:
                logger.info("WebSocket连接已关闭")
                websocket = None


if __name__ == "__main__":
    logger.info("启动应用程序")
    app = QApplication(sys.argv)
    window = SubtitleDisplay(args, AsyncWorker)
    window.show()
    sys.exit(app.exec_())