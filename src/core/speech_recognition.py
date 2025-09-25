"""
语音识别核心模块
Speech Recognition Core Module
"""

import os
import time
import websockets
import ssl
import asyncio
import json
import logging
from collections import deque
from websockets.exceptions import ConnectionClosed
from multiprocessing import Queue
from typing import Optional

from PyQt5.QtCore import QTimer, pyqtSignal, QThread

# 导入服务模块
from ..services.audio_service import AudioService
from ..services.translation_service import RealTimeTranslationThread
from ..services.text_service import (
    handle_timeout_with_dual_channels, 
    process_text_with_dual_channels,
    TextProcessingService
)

# 导入模型
from ..models.translation_models import TranslationTask
from ..models.audio_models import AudioConfig

# 尝试导入音频库
try:
    import pyaudiowpatch as pyaudio
    HAS_WASAPI = True
except ImportError:
    try:
        import pyaudio
        HAS_WASAPI = False
    except ImportError:
        pyaudio = None
        HAS_WASAPI = False

logger = logging.getLogger(__name__)


class SpeechRecognitionWorker(QThread):
    """语音识别工作线程 - 重构后的核心类，遵循驼峰命名规范"""
    
    # 信号定义
    updateChinese = pyqtSignal(str)
    updateEnglish = pyqtSignal(str, bool)
    statusUpdate = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, deviceIndex: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 基本属性
        self.id = 0
        self.isRunning = False
        self.deviceIndex = deviceIndex
        
        # 初始化服务
        self.audioService = AudioService()
        self.textService = TextProcessingService()
        
        # 双通道翻译队列 - 遵循项目记忆中的双通道翻译架构
        self.realtimeQueue = Queue()  # 离线通道：完整句子的高质量翻译
        self.incrementalQueue = Queue()  # 在线通道：增量文本的实时翻译
        
        # 翻译线程
        self.realtimeThread = None
        self.incrementalThread = None
        
        # 文本状态管理 - 使用驼峰命名
        self.textPrintEn = ""  # 英文翻译累积
        self.textPrintCn = ""  # 中文翻译累积
        self.textPrintEnOnline = ""   # 英文在线通道（增量翻译）
        self.textPrintEnOffline = ""  # 英文离线通道（完整翻译）
        
        # 双通道翻译版本控制
        self.offlineVersion = 0    # 离线翻译版本号
        self.onlineVersion = 0     # 在线翻译版本号
        self.translationTasks = deque()
        self.taskCounter = 0
        self.lastProcessedIndex = 0
        self.pendingText = ""
        self.lastTextReceiveTime = 0
        
        # 增量翻译控制
        self.incrementalTasks = deque()
        self.currentIncrementalText = ""
        self.isIncrementalTranslating = False
        self.pendingOnlineText = ""
        
        # 音频相关
        self._audioStream = None
        self._pyaudioInstance = None
        self.audioStartTime = None
        self.inputSampleRate = 44100
        self.targetSampleRate = 16000  # 默认值，会从args更新
        self.audioChannels = 2
        
        # 超时定时器
        self.timeoutTimer = QTimer()
        self.timeoutTimer.timeout.connect(self._handleTimeout)
        self.timeoutTimer.start(500)
    
    def setId(self, workerId: int):
        """设置工作线程ID"""
        self.id = workerId
    
    def setArgs(self, args):
        """设置参数配置"""
        self.args = args
        self.targetSampleRate = args.audio_fs
    
    def run(self):
        """线程主运行方法"""
        self.isRunning = True
        self.logger.info("启动语音识别工作线程 #%d", self.id)
        
        try:
            # 启动翻译线程
            self._startTranslationThreads()
            
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self.wsClient(self.id, 0, 1))
            except Exception as e:
                self.logger.error("WebSocket客户端运行错误: %s", str(e))
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error("工作线程运行错误: %s", str(e))
        finally:
            self.cleanup()
            self.finished.emit()
    
    def _startTranslationThreads(self):
        """启动翻译线程"""
        if not hasattr(self, 'args'):
            self.logger.error("未设置参数配置，无法启动翻译线程")
            return
            
        # 启动实时翻译线程（离线通道）
        self.realtimeThread = RealTimeTranslationThread(
            self.realtimeQueue, 
            self.args.translate_api
        )
        self.realtimeThread.translation_done.connect(self.handleTranslationResult)
        self.realtimeThread.start()
        
        # 启动增量翻译线程（在线通道）
        self.incrementalThread = RealTimeTranslationThread(
            self.incrementalQueue, 
            self.args.translate_api
        )
        self.incrementalThread.translation_done.connect(self.handleIncrementalTranslationResult)
        self.incrementalThread.start()
    
    def _handleTimeout(self):
        """处理超时"""
        if not hasattr(self, 'args'):
            return
            
        handle_timeout_with_dual_channels(
            self, self.isRunning, self.lastTextReceiveTime,
            self.pendingText, self.translationTasks, 
            self.realtimeQueue, self.taskCounter,
            self.lastProcessedIndex, self.statusUpdate, self.args,
            self.incrementalQueue, self.incrementalTasks
        )
    
    def processOnlineTextTranslation(self, onlineText: str):
        """
        对当前在线显示的中文进行增量翻译（实时响应）
        按照项目记忆中的双通道翻译架构实现
        """
        if not onlineText or not onlineText.strip():
            return
            
        # 立即发送实时翻译，实现首字即显
        self._sendIncrementalTranslationRealtime(onlineText)
        self.logger.info("实时翻译（首字即显）: %s", onlineText)
    
    def _sendIncrementalTranslationRealtime(self, text: str):
        """发送实时增量翻译请求"""
        self.onlineVersion += 1
        incrementalTask = TranslationTask(
            text, self.taskCounter, 
            is_incremental=True, 
            version=self.onlineVersion
        )
        self.incrementalTasks.append(incrementalTask)
        self.incrementalQueue.put(incrementalTask)
        self.taskCounter += 1
        self.logger.info("实时发送增量翻译: %s（版本: %d）", text, self.onlineVersion)
    
    def handleTranslationResult(self, task: TranslationTask):
        """
        处理翻译结果，按照双通道翻译显示策略实现
        在线通道：碎片化文本的实时翻译，追加到前一次离线翻译结果后实时显示
        离线通道：完整句子的高质量翻译，追加至历史离线内容并更新显示，同时清空在线通道内容
        """
        self.logger.info("处理翻译结果: %s (增量: %s, 版本: %s)", 
                        task.translated_text, task.is_incremental, task.version)
        
        if not task.translated_text:
            return
            
        if task.is_incremental:
            # 在线通道：碎片化文本的实时翻译
            self.textPrintEnOnline = task.translated_text
            self.logger.info("更新在线通道翻译: %s", self.textPrintEnOnline)
            
            # 追加到前一次离线翻译结果后实时显示
            if self.textPrintEnOffline:
                self.textPrintEn = self.textPrintEnOffline + " " + self.textPrintEnOnline
            else:
                self.textPrintEn = self.textPrintEnOnline
            
            # 立即发送在线模式更新，实现实时显示
            self.updateEnglish.emit(self.textPrintEn, True)
            self.logger.info("实时显示英文内容: %s", self.textPrintEn)
            
        else:
            # 离线通道：完整句子的高质量翻译
            if self.textPrintEnOffline and not self.textPrintEnOffline.endswith(' '):
                self.textPrintEnOffline += ' '
            self.textPrintEnOffline += task.translated_text
            self.logger.info("追加至离线通道: %s", self.textPrintEnOffline)
            
            # 合并离线+在线内容并更新显示
            if self.textPrintEnOnline:
                self.textPrintEn = self.textPrintEnOffline + " " + self.textPrintEnOnline
            else:
                self.textPrintEn = self.textPrintEnOffline
            
            # 发送离线模式更新
            self.updateEnglish.emit(self.textPrintEn, False)
            self.logger.info("离线更新后的英文内容: %s", self.textPrintEn)
            
            # 更新完成后清理在线内容
            self.textPrintEnOnline = ""
            self.logger.info("离线更新完成，清空在线内容")
    
    def handleIncrementalTranslationResult(self, task: TranslationTask):
        """处理增量翻译结果"""
        self.handleTranslationResult(task)
    
    async def recordAudio(self, websocket):
        """录制音频"""
        if not pyaudio:
            self.logger.error("PyAudio库未安装，无法录制音频")
            return
            
        try:
            FORMAT = pyaudio.paInt16
            CHANNELS = self.audioChannels
            RATE = self.inputSampleRate
            chunkSize = 20 * self.args.chunk_size[1] / self.args.chunk_interval
            CHUNK = int(RATE / 1000 * chunkSize)
            
            p = pyaudio.PyAudio()
            self._pyaudioInstance = p
            
            # 设备选择逻辑
            inputDeviceIndex = self.deviceIndex
            deviceName = "默认设备"
            
            if inputDeviceIndex is not None:
                try:
                    deviceInfo = p.get_device_info_by_index(inputDeviceIndex)
                    deviceName = deviceInfo['name']
                    self.logger.info(f"使用手动选择的设备: {deviceName} (索引: {inputDeviceIndex})")
                except Exception as e:
                    self.logger.error(f"无法使用手动选择的设备 {inputDeviceIndex}: {e}")
                    inputDeviceIndex = None
                    self.statusUpdate.emit(f"无法使用选择的设备，使用默认设备: {e}")
            
            if inputDeviceIndex is None:
                defaultDevice = p.get_default_input_device_info()
                inputDeviceIndex = int(defaultDevice['index'])
                deviceName = defaultDevice['name']
                self.logger.info(f"使用默认设备: {deviceName}")
            
            # 打开音频流
            streamParams = {
                'format': FORMAT,
                'channels': CHANNELS,
                'rate': RATE,
                'input': True,
                'frames_per_buffer': CHUNK,
                'input_device_index': inputDeviceIndex
            }
            
            stream = p.open(**streamParams)
            self._audioStream = stream
            
            self.logger.info(f"音频流开启成功，设备: {deviceName}")
            self.statusUpdate.emit(f"使用音频设备: {deviceName}")
            
            # 发送初始配置
            await self._sendInitialConfig(websocket)
            
            # 录音循环
            while self.isRunning:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    
                    # 重采样音频
                    if self.inputSampleRate != self.targetSampleRate:
                        resampledData = self.audioService.resample_audio(
                            data, self.inputSampleRate, 
                            self.targetSampleRate, self.audioChannels
                        )
                    else:
                        resampledData = data
                    
                    await websocket.send(resampledData)
                    await asyncio.sleep(0.005)
                    
                except ConnectionClosed:
                    self.logger.warning("WebSocket连接已关闭，停止发送音频")
                    break
                except Exception as e:
                    self.logger.error("录音错误: %s", str(e))
                    break
                    
        except Exception as e:
            self.logger.error(f"音频录制错误: {str(e)}")
            self.statusUpdate.emit(f"音频录制错误: {e}")
    
    async def _sendInitialConfig(self, websocket):
        """发送初始配置消息"""
        hotwordMsg = ""
        if hasattr(self.args, 'hotword') and self.args.hotword.strip():
            if os.path.exists(self.args.hotword):
                # 处理热词文件
                pass
            else:
                hotwordMsg = self.args.hotword
        
        message = json.dumps({
            "mode": self.args.mode,
            "chunk_size": self.args.chunk_size,
            "chunk_interval": self.args.chunk_interval,
            "encoder_chunk_look_back": self.args.encoder_chunk_look_back,
            "decoder_chunk_look_back": self.args.decoder_chunk_look_back,
            "wav_name": self.args.audio_source,
            "is_speaking": True,
            "hotwords": hotwordMsg,
            "itn": self.args.use_itn == 1,
            "sample_rate": self.targetSampleRate,
        })
        
        await websocket.send(message)
    
    async def handleMessages(self, websocket):
        """处理WebSocket消息"""
        textPrint = ""
        textPrint2passOnline = ""
        textPrint2passOffline = ""
        
        while self.isRunning:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                data = json.loads(message)
                
                text = data["text"]
                self.logger.info("WebSocket返回语音识别文本: %s", text)
                
                if "mode" not in data:
                    continue
                
                # 处理不同模式的消息
                if data["mode"] == "online":
                    textPrint += text
                    
                elif data["mode"] == "2pass-online":
                    textPrint2passOnline += text
                    textPrint = textPrint2passOffline + textPrint2passOnline
                    
                    self.updateChinese.emit(textPrint)
                    self.processOnlineTextTranslation(textPrint2passOnline)
                    
                elif data["mode"] == "2pass-offline":
                    textPrint2passOffline += text
                    textPrint = textPrint2passOffline
                    textPrint2passOnline = ""
                    
                    # 重置在线翻译状态
                    self.isIncrementalTranslating = False
                    self.pendingOnlineText = ""
                    self.textPrintEnOnline = ""
                    self.onlineVersion = 0
                    
                    self.updateChinese.emit(textPrint)
                    
                    # 处理完整文本翻译
                    updated, newLastProcessedIndex, newPendingText, newTaskCounter = process_text_with_dual_channels(
                        self, textPrint, self.lastProcessedIndex, self.pendingText,
                        self.translationTasks, self.realtimeQueue, self.taskCounter, 
                        self.args, self.incrementalQueue, self.incrementalTasks
                    )
                    if updated:
                        self.lastProcessedIndex = newLastProcessedIndex
                        self.pendingText = newPendingText
                        self.taskCounter = newTaskCounter
                        
            except ConnectionClosed:
                self.logger.warning("WebSocket连接已关闭")
                break
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error("消息处理错误: %s", str(e))
                break
    
    async def wsClient(self, clientId: int, chunkBegin: int, chunkSize: int):
        """WebSocket客户端"""
        for i in range(chunkBegin, chunkBegin + chunkSize):
            if not self.isRunning:
                break
                
            # 配置SSL
            if hasattr(self.args, 'ssl') and self.args.ssl == 1:
                sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                sslContext.check_hostname = False
                sslContext.verify_mode = ssl.CERT_NONE
                uri = f"wss://{self.args.host}:{self.args.port}"
            else:
                sslContext = None
                uri = f"ws://{self.args.host}:{self.args.port}"
            
            self.logger.info("连接到: %s", uri)
            self.statusUpdate.emit(f"连接到 {uri}")
            
            try:
                async with websockets.connect(uri, ping_interval=None, ssl=sslContext) as ws:
                    self.logger.info("连接成功")
                    self.statusUpdate.emit("连接成功")
                    
                    # 创建任务
                    recordTask = asyncio.create_task(self.recordAudio(ws))
                    messageTask = asyncio.create_task(self.handleMessages(ws))
                    
                    # 等待任一任务完成
                    done, pending = await asyncio.wait(
                        [recordTask, messageTask],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # 取消未完成任务
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                    
            except Exception as e:
                self.logger.error("连接错误: %s", str(e))
                self.statusUpdate.emit(f"连接错误: {e}")
                if self.isRunning:
                    await asyncio.sleep(5)
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if self.timeoutTimer.isActive():
                self.timeoutTimer.stop()
            
            # 停止翻译线程
            if self.realtimeThread and self.realtimeThread.isRunning():
                self.realtimeThread.stop()
            if self.incrementalThread and self.incrementalThread.isRunning():
                self.incrementalThread.stop()
            
            # 清理音频资源
            self.audioService.cleanup_resources() if hasattr(self.audioService, 'cleanup_resources') else None
            
            # 清理队列
            self._clearQueues()
            
        except Exception as e:
            self.logger.error("资源清理错误: %s", str(e))
    
    def _clearQueues(self):
        """清理队列"""
        try:
            while not self.realtimeQueue.empty():
                self.realtimeQueue.get_nowait()
        except:
            pass
            
        try:
            while not self.incrementalQueue.empty():
                self.incrementalQueue.get_nowait()
        except:
            pass
    
    def stop(self):
        """停止工作线程"""
        self.logger.info("停止语音识别工作线程 #%d", self.id)
        self.isRunning = False


# 兼容性别名
AsyncWorker = SpeechRecognitionWorker