"""
主窗口UI模块
Main Window UI Module
"""

import sys
import logging
import os
import json
import datetime
from typing import Optional, List

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QComboBox, QSplitter,
                            QApplication, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from ..services.audio_service import AudioService
from ..models.audio_models import AudioDevice
from ..config.constants import (
    WINDOW_TITLE, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    TECH_CYAN, TECH_MAGENTA, CHINESE_FONT_FAMILY, ENGLISH_FONT_FAMILY
)
from .subtitle_window import SubtitleOverlayWindow

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口类 - 重构后的主窗口，遵循驼峰命名规范"""
    
    def __init__(self, args, workerClass):
        super().__init__()
        self.args = args
        self.workerClass = workerClass
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化服务 - 使用驼峰命名
        self.audioService = AudioService()
        
        # 初始化变量 - 使用驼峰命名
        self.worker = None
        self.chineseText = ""
        self.englishText = ""
        self.audioDevices: List[AudioDevice] = []
        self.subtitleWindow: Optional[SubtitleOverlayWindow] = None
        self.showSubtitleWindow = True
        self.isClearing = False
        self.clearingTimer = QTimer()
        self.clearingTimer.setSingleShot(True)
        self.clearingTimer.timeout.connect(self._resetClearingState)
        
        # 设置窗口
        self._setupWindow()
        self._createUi()
        self._setupConnections()
        
        # 初始化音频设备
        self.refreshAudioDevices()
        
        # 自动创建字幕窗口
        if self.showSubtitleWindow:
            self._createSubtitleWindow()
    
    def _setupWindow(self):
        """设置窗口属性"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # 设置科技感窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #0a0a2a,
                                          stop: 0.5 #1a1a3a,
                                          stop: 1 #0a0a2a);
                border: 2px solid #00ffff;
                border-radius: 12px;
            }
        """)
        
        # 窗口居中显示
        self._centerWindow()
    
    def _centerWindow(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        if screen:
            screenGeometry = screen.availableGeometry()
            windowGeometry = self.frameGeometry()
            centerX = screenGeometry.width() // 2 - windowGeometry.width() // 2
            centerY = screenGeometry.height() // 2 - windowGeometry.height() // 2 - 70
            self.move(centerX, centerY)
    
    def _createUi(self):
        """创建用户界面"""
        centralWidget = QWidget()
        centralWidget.setStyleSheet("QWidget { background: transparent; }")
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建组件
        self._createTitleBar(layout)
        self._createSubtitleDisplay(layout)
        self._createControlArea(layout)
    
    def _createTitleBar(self, layout):
        """创建标题栏"""
        titleLabel = QLabel("🚀 智能语音识别翻译系统")
        titleLabel.setFont(QFont(CHINESE_FONT_FAMILY, 18, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLabel.setStyleSheet(f"""
            QLabel {{
                color: {TECH_CYAN};
                background-color: rgba(0, 255, 255, 0.1);
                padding: 12px;
                border-radius: 8px;
                border: 1px solid rgba(0, 255, 255, 0.3);
            }}
        """)
        layout.addWidget(titleLabel)
    
    def _createSubtitleDisplay(self, layout):
        """创建字幕显示区域"""
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(0, 255, 255, 0.3);
                height: 3px;
            }
        """)

        # 中文和英文显示区域
        chineseWidget = self._createChineseDisplayWidget()
        englishWidget = self._createEnglishDisplayWidget()
        
        splitter.addWidget(chineseWidget)
        splitter.addWidget(englishWidget)
        splitter.setSizes([300, 200])
        layout.addWidget(splitter)
    
    def _createChineseDisplayWidget(self) -> QWidget:
        """创建中文显示组件"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1a1a3a, stop: 1 #0a0a2a);
                border-radius: 10px;
                border: 2px solid {TECH_CYAN};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题和文本显示
        chineseLabel = QLabel("🔤 语音识别")
        chineseLabel.setFont(QFont(CHINESE_FONT_FAMILY, 14, QFont.Bold))
        chineseLabel.setAlignment(Qt.AlignCenter)
        chineseLabel.setStyleSheet(f"""
            QLabel {{
                color: {TECH_CYAN};
                background-color: rgba(0, 255, 255, 0.15);
                padding: 8px; border-radius: 6px;
                border: 1px solid rgba(0, 255, 255, 0.3);
            }}
        """)
        
        self.chineseDisplay = QTextEdit()
        self.chineseDisplay.setReadOnly(True)
        self.chineseDisplay.setAlignment(Qt.AlignCenter)
        self.chineseDisplay.setFont(QFont(CHINESE_FONT_FAMILY, 20, QFont.Bold))
        self.chineseDisplay.setTextColor(QColor(255, 255, 255))
        self.chineseDisplay.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid rgba(0, 255, 255, 0.2);
                border-radius: 8px; color: white; padding: 20px;
                selection-background-color: rgba(0, 255, 255, 0.3);
            }
        """)
        self.chineseDisplay.setMinimumHeight(220)
        
        layout.addWidget(chineseLabel)
        layout.addWidget(self.chineseDisplay)
        return widget
    
    def _createEnglishDisplayWidget(self) -> QWidget:
        """创建英文显示组件"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1a1a3a, stop: 1 #0a0a2a);
                border-radius: 10px;
                border: 2px solid {TECH_MAGENTA};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        englishLabel = QLabel("🌐 文本翻译")
        englishLabel.setFont(QFont(CHINESE_FONT_FAMILY, 14, QFont.Bold))
        englishLabel.setAlignment(Qt.AlignCenter)
        englishLabel.setStyleSheet(f"""
            QLabel {{
                color: {TECH_MAGENTA};
                background-color: rgba(255, 0, 255, 0.15);
                padding: 8px; border-radius: 6px;
                border: 1px solid rgba(255, 0, 255, 0.3);
            }}
        """)
        
        self.englishDisplay = QTextEdit()
        self.englishDisplay.setReadOnly(True)
        self.englishDisplay.setAlignment(Qt.AlignCenter)
        self.englishDisplay.setFont(QFont(ENGLISH_FONT_FAMILY, 18, QFont.Bold))
        self.englishDisplay.setTextColor(QColor(220, 220, 255))
        self.englishDisplay.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid rgba(255, 0, 255, 0.2);
                border-radius: 8px; color: #DCDCF0; padding: 20px;
                selection-background-color: rgba(255, 0, 255, 0.3);
            }
        """)
        self.englishDisplay.setMinimumHeight(180)
        
        layout.addWidget(englishLabel)
        layout.addWidget(self.englishDisplay)
        return widget
    
    def _createControlArea(self, layout):
        """创建控制区域"""
        controlWidget = QWidget()
        controlWidget.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.4);
                border-radius: 10px;
                border: 1px solid rgba(0, 255, 255, 0.2);
                padding: 10px;
            }
        """)
        
        controlLayout = QHBoxLayout(controlWidget)
        controlLayout.setSpacing(10)
        
        # 设备选择和控制按钮
        self._createDeviceSelection(controlLayout)
        self._createControlButtons(controlLayout)
        
        layout.addWidget(controlWidget)
    
    def _createDeviceSelection(self, layout):
        """创建设备选择区域"""
        deviceLabel = QLabel("输入设备:")
        deviceLabel.setStyleSheet(f"""
            QLabel {{
                color: {TECH_CYAN};
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
            }}
        """)
        
        self.deviceCombo = QComboBox()
        self.deviceCombo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(0, 255, 255, 0.1);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px;
                color: {TECH_CYAN};
                min-width: 250px;
                font-weight: bold;
            }}
        """)
        
        self.refreshDevicesButton = QPushButton("刷新设备")
        self.refreshDevicesButton.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 200, 0.7);
                color: #ffffff;
                border: 2px solid rgba(0, 150, 255, 0.5);
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(deviceLabel)
        layout.addWidget(self.deviceCombo)
        layout.addWidget(self.refreshDevicesButton)
    
    def _createControlButtons(self, layout):
        """创建控制按钮"""
        # 按钮样式定义
        buttonStyles = {
            'start': """QPushButton {
                background-color: rgba(0, 150, 0, 0.7);
                color: #ffffff; border: 2px solid rgba(0, 200, 0, 0.5);
                border-radius: 6px; padding: 10px 15px;
                font-weight: bold; font-size: 12px;
            }""",
            'stop': """QPushButton {
                background-color: rgba(180, 0, 0, 0.7);
                color: #ffffff; border: 2px solid rgba(220, 0, 0, 0.5);
                border-radius: 6px; padding: 10px 15px;
                font-weight: bold; font-size: 12px;
            }""",
            'clear': """QPushButton {
                background-color: rgba(200, 120, 0, 0.7);
                color: #ffffff; border: 2px solid rgba(230, 150, 0, 0.5);
                border-radius: 6px; padding: 10px 15px;
                font-weight: bold; font-size: 12px;
            }""",
            'toggle': """QPushButton {
                background-color: rgba(100, 50, 180, 0.7);
                color: #ffffff; border: 2px solid rgba(140, 80, 220, 0.5);
                border-radius: 6px; padding: 10px 15px;
                font-weight: bold; font-size: 12px;
            }""",
            'export': """QPushButton {
                background-color: rgba(0, 100, 0, 0.7);
                color: #00ff00; border: 2px solid rgba(0, 255, 0, 0.5);
                border-radius: 8px; padding: 8px 16px;
                font-weight: bold; font-size: 12px; min-width: 80px;
            }"""
        }
        
        # 创建按钮
        self.startButton = QPushButton("开始识别")
        self.startButton.setStyleSheet(buttonStyles['start'])
        
        self.stopButton = QPushButton("停止识别")
        self.stopButton.setStyleSheet(buttonStyles['stop'])
        self.stopButton.setEnabled(False)
        
        self.clearButton = QPushButton("清空字幕")
        self.clearButton.setStyleSheet(buttonStyles['clear'])
        
        self.toggleSubtitleButton = QPushButton("隐藏透明字幕")
        self.toggleSubtitleButton.setStyleSheet(buttonStyles['toggle'])
        
        self.exportButton = QPushButton("导出字幕")
        self.exportButton.setStyleSheet(buttonStyles['export'])
        
        # 添加到布局
        layout.addWidget(self.startButton)
        layout.addWidget(self.stopButton)
        layout.addWidget(self.clearButton)
        layout.addWidget(self.toggleSubtitleButton)
        layout.addWidget(self.exportButton)
    
    def _setupConnections(self):
        """设置信号连接"""
        self.refreshDevicesButton.clicked.connect(self.refreshAudioDevices)
        self.startButton.clicked.connect(self.startRecognition)
        self.stopButton.clicked.connect(self.stopRecognition)
        self.clearButton.clicked.connect(self.clearSubtitles)
        self.toggleSubtitleButton.clicked.connect(self.toggleSubtitleWindow)
        self.exportButton.clicked.connect(self.exportSubtitles)
    
    def refreshAudioDevices(self):
        """刷新音频设备列表"""
        try:
            self.logger.info("刷新音频设备列表")
            self.deviceCombo.clear()
            
            devices = self.audioService.get_audio_devices()
            self.audioDevices = devices
            
            if not devices:
                self.deviceCombo.addItem("未找到可用的音频设备")
                self.deviceCombo.setEnabled(False)
                return
            
            self.deviceCombo.setEnabled(True)
            
            for device in devices:
                displayText = f"{device.name} [{device.device_type}] - {device.sample_rate:.0f}Hz"
                self.deviceCombo.addItem(displayText)
            
            # 选择默认设备
            defaultDevice = self.audioService.get_default_audio_device(self.args.audio_source)
            if defaultDevice:
                for i, device in enumerate(devices):
                    if device.index == defaultDevice.index:
                        self.deviceCombo.setCurrentIndex(i)
                        break
            
            self.logger.info(f"找到 {len(devices)} 个可用音频设备")
            
        except Exception as e:
            self.logger.error(f"刷新音频设备失败: {e}")
            QMessageBox.warning(self, "错误", f"刷新音频设备失败: {e}")
    
    # 其他方法占位符
    def startRecognition(self): pass
    def stopRecognition(self): pass
    def clearSubtitles(self): pass
    def toggleSubtitleWindow(self): pass
    def exportSubtitles(self): pass
    def updateChineseText(self, text): pass
    def updateEnglishText(self, text, isIncremental=False): pass
    def _createSubtitleWindow(self): pass
    def _resetClearingState(self): pass