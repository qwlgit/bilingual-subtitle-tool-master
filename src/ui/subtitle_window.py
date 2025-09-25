"""
副字幕窗口模块
Subtitle Overlay Window Module
"""

import logging
from collections import deque
from typing import Optional, Callable

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenu
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QFont

from ..config.constants import (
    SUBTITLE_WINDOW_TITLE, DEFAULT_SUBTITLE_WIDTH_RATIO, SUBTITLE_BOTTOM_DISTANCE,
    DEFAULT_FONT_SIZE, CHINESE_FONT_FAMILY, ENGLISH_FONT_FAMILY,
    SHORT_SENTENCE_DISPLAY_TIME, MEDIUM_SENTENCE_DISPLAY_TIME, LONG_SENTENCE_DISPLAY_TIME
)
from ..services.text_service import TextProcessingService

logger = logging.getLogger(__name__)


class SubtitleOverlayWindow(QMainWindow):
    """透明悬浮字幕窗口类"""
    
    def __init__(self, onCloseCallback: Optional[Callable] = None):
        super().__init__()
        self.onCloseCallback = onCloseCallback
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化服务
        self.textService = TextProcessingService()
        
        # 设置窗口
        self.setWindowTitle(SUBTITLE_WINDOW_TITLE)
        self._setupWindow()
        
        # 初始化变量
        self.opacity = 0.95
        self.fontSize = DEFAULT_FONT_SIZE
        self.isDragging = False
        self.dragPosition = QPoint()
        
        # 文本缓存
        self.chineseTextBuffer = ""
        self.englishTextBuffer = ""
        self.pairedSentenceQueue = deque()
        self.isShowingSentence = False
        
        # 创建UI
        self._createUi()
        
        # 显示定时器
        self.displayTimer = QTimer()
        self.displayTimer.timeout.connect(self.updateDisplay)
        self.displayTimer.start(2000)
    
    def _setupWindow(self):
        """设置窗口属性"""
        # 设置窗口标志
        windowFlags = Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        self.setWindowFlags(windowFlags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口大小
        screen = self.screen()
        if screen:
            screenGeometry = screen.availableGeometry()
            self.defaultWidth = int(screenGeometry.width() * DEFAULT_SUBTITLE_WIDTH_RATIO)
            self.defaultHeight = 120
            self.resize(self.defaultWidth, self.defaultHeight)
            
            # 居中显示在底部
            centerX = screenGeometry.width() // 2 - self.defaultWidth // 2
            bottomY = screenGeometry.height() - SUBTITLE_BOTTOM_DISTANCE
            self.move(centerX, bottomY)
        else:
            self.defaultWidth = 1024
            self.defaultHeight = 120
            self.resize(self.defaultWidth, self.defaultHeight)
    
    def _createUi(self):
        """创建用户界面"""
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout(self.centralWidget)
        
        # 创建标签
        self.chineseLabel = QLabel("")
        self.englishLabel = QLabel("")
        
        # 设置样式
        self.chineseLabel.setStyleSheet("""
            color: #00ffff;
            background-color: rgba(10, 10, 40, 0.85);
            padding: 15px 25px;
            border-radius: 12px;
            border: 2px solid rgba(0, 255, 255, 0.4);
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.7);
        """)
        
        self.englishLabel.setStyleSheet("""
            color: #ff00ff;
            background-color: rgba(40, 10, 40, 0.85);
            padding: 12px 25px;
            border-radius: 12px;
            border: 2px solid rgba(255, 0, 255, 0.4);
            text-shadow: 0 0 10px rgba(255, 0, 255, 0.7);
        """)
        
        # 设置字体和对齐
        self.setFontSize(self.fontSize)
        self.chineseLabel.setAlignment(Qt.AlignCenter)
        self.englishLabel.setAlignment(Qt.AlignCenter)
        self.chineseLabel.setWordWrap(False)
        self.englishLabel.setWordWrap(False)
        
        # 添加到布局
        self.mainLayout.addWidget(self.chineseLabel)
        self.mainLayout.addWidget(self.englishLabel)
        self.mainLayout.setSpacing(8)
        self.mainLayout.setContentsMargins(15, 10, 15, 10)
        
        # 设置透明度
        self.setWindowOpacity(self.opacity)
    
    def updateDisplay(self):
        """更新显示内容"""
        if self.pairedSentenceQueue and not self.isShowingSentence:
            chineseSentence, englishSentence = self.pairedSentenceQueue.popleft()
            
            self.chineseLabel.setText(chineseSentence)
            self.englishLabel.setText(englishSentence)
            
            self.isShowingSentence = True
            
            # 计算显示时间
            maxLength = max(len(chineseSentence), len(englishSentence))
            displayTime = self.calculateDisplayTime(maxLength)
            QTimer.singleShot(displayTime, self.clearCurrentSentence)
    
    def calculateDisplayTime(self, length: int) -> int:
        """计算显示时间"""
        if length <= 5:
            return SHORT_SENTENCE_DISPLAY_TIME
        elif length <= 15:
            return MEDIUM_SENTENCE_DISPLAY_TIME
        else:
            return LONG_SENTENCE_DISPLAY_TIME
    
    def clearCurrentSentence(self):
        """清除当前句子"""
        self.isShowingSentence = False
        self.chineseLabel.setText("")
        self.englishLabel.setText("")
    
    def updateChineseText(self, text: str):
        """更新中文文本"""
        self.chineseTextBuffer = text
        # 这里可以添加文本处理逻辑
    
    def updateEnglishText(self, text: str, isIncremental: bool = False):
        """更新英文文本"""
        if isIncremental:
            self.englishLabel.setText(text)
        else:
            self.englishTextBuffer = text
            # 这里可以添加文本处理逻辑
    
    def clearText(self):
        """清空文本"""
        self.chineseLabel.setText("")
        self.englishLabel.setText("")
        self.chineseTextBuffer = ""
        self.englishTextBuffer = ""
        self.pairedSentenceQueue.clear()
        self.isShowingSentence = False
    
    def setFontSize(self, size: int):
        """设置字体大小"""
        self.fontSize = size
        
        chineseFont = QFont(CHINESE_FONT_FAMILY)
        chineseFont.setPointSize(size)
        chineseFont.setBold(True)
        self.chineseLabel.setFont(chineseFont)
        
        englishFont = QFont(ENGLISH_FONT_FAMILY)
        englishFont.setPointSize(size)
        englishFont.setBold(True)
        self.englishLabel.setFont(englishFont)
    
    def setOpacity(self, opacity: float):
        """设置透明度"""
        self.opacity = opacity
        self.setWindowOpacity(opacity)
    
    # 事件处理
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event and event.button() == Qt.MouseButton.LeftButton:
            self.isDragging = True
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event and self.isDragging and bool(event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPos() - self.dragPosition)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event:
            self.isDragging = False
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        if not event:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(20, 20, 50, 0.95);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 8px;
                color: #00ffff;
            }
            QMenu::item:selected {
                background-color: rgba(0, 255, 255, 0.2);
            }
        """)
        
        # 透明度菜单
        opacityMenu = menu.addMenu("🎨 透明度调节")
        for opacity in [0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]:
            action = opacityMenu.addAction(f"{opacity*100:.0f}% 透明度")
            action.triggered.connect(lambda checked, o=opacity: self.setOpacity(o))
        
        # 字体大小菜单
        fontMenu = menu.addMenu("🔤 字体大小")
        for size in [18, 20, 24, 28, 32, 36, 40]:
            action = fontMenu.addAction(f"{size}px")
            action.triggered.connect(lambda checked, s=size: self.setFontSize(s))
        
        menu.addSeparator()
        
        # 关闭菜单
        closeAction = menu.addAction("❌ 关闭副字幕")
        closeAction.triggered.connect(self.handleClose)
        
        menu.exec_(event.globalPos())
    
    def handleClose(self):
        """处理关闭操作"""
        if self.onCloseCallback:
            self.onCloseCallback()
        self.close()


# 兼容性别名
TransparentSubtitleWindow = SubtitleOverlayWindow