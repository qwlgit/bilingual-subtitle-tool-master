"""
主窗口UI模块
包含SubtitleDisplay主窗口类
"""

import sys
import logging
import os
import json
import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QComboBox, QSplitter, QStatusBar,
                            QApplication, QMessageBox, QFileDialog, QDialog)  # 添加 QDialog 导入
from PyQt5.QtCore import Qt, QTimer, QEvent  # 添加 QEvent 导入
from PyQt5.QtGui import QFont, QColor

# 导入透明字幕窗口模块
from transparent_window import TransparentSubtitleWindow

# 在文件顶部添加导入
from audio_utils import get_audio_devices, get_default_audio_device
    

logger = logging.getLogger(__name__)


# 主窗口类
class SubtitleDisplay(QMainWindow):
    def __init__(self, args, worker_class):
        super().__init__()
        self.args = args
        self.worker_class = worker_class
        self.setWindowTitle("🔊 智能语音识别翻译系统")
        self.setGeometry(100, 100, 1200, 700)
        
        # 初始化变量
        self.worker = None
        self.chinese_text = ""
        self.english_text = ""
        self.audio_devices = []
        self.subtitle_window = None  # 透明字幕窗口
        self.show_subtitle_window = True  # 默认打开透明字幕窗口
        self.is_clearing = False  # 清空状态标志
        self.clearing_timer = QTimer()  # 清空状态定时器
        self.clearing_timer.setSingleShot(True)
        self.clearing_timer.timeout.connect(self._reset_clearing_state)

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
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_x = screen_geometry.width() // 2 - window_geometry.width() // 2
            center_y = screen_geometry.height() // 2 - window_geometry.height() // 2 - 70
            self.move(center_x, center_y)

        # 创建UI
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题栏
        title_label = QLabel("🚀 智能语音识别翻译系统")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                background-color: rgba(0, 255, 255, 0.1);
                padding: 12px;
                border-radius: 8px;
                border: 1px solid rgba(0, 255, 255, 0.3);
            }
        """)
        layout.addWidget(title_label)

        # 字幕显示区域
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(0, 255, 255, 0.3);
                height: 3px;
            }
        """)

        # 中文显示 - 科技感设计
        chinese_widget = QWidget()
        chinese_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1a1a3a,
                                          stop: 1 #0a0a2a);
                border-radius: 10px;
                border: 2px solid #00ffff;
            }
        """)
        chinese_layout = QVBoxLayout(chinese_widget)
        chinese_layout.setContentsMargins(10, 10, 10, 10)
        
        chinese_label = QLabel("🔤 语音识别")
        chinese_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        chinese_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chinese_label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                background-color: rgba(0, 255, 255, 0.15);
                padding: 8px;
                border-radius: 6px;
                border: 1px solid rgba(0, 255, 255, 0.3);
            }
        """)

        self.chinese_display = QTextEdit()
        self.chinese_display.setReadOnly(True)
        self.chinese_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chinese_display.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        self.chinese_display.setTextColor(QColor(255, 255, 255))
        self.chinese_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid rgba(0, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                padding: 20px;
                selection-background-color: rgba(0, 255, 255, 0.3);
            }
        """)
        self.chinese_display.setMinimumHeight(220)

        chinese_layout.addWidget(chinese_label)
        chinese_layout.addWidget(self.chinese_display)

        # 英文显示 - 科技感设计
        english_widget = QWidget()
        english_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1a1a3a,
                                          stop: 1 #0a0a2a);
                border-radius: 10px;
                border: 2px solid #ff00ff;
            }
        """)
        english_layout = QVBoxLayout(english_widget)
        english_layout.setContentsMargins(10, 10, 10, 10)
        
        english_label = QLabel("🌐 文本翻译")
        english_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        english_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        english_label.setStyleSheet("""
            QLabel {
                color: #ff00ff;
                background-color: rgba(255, 0, 255, 0.15);
                padding: 8px;
                border-radius: 6px;
                border: 1px solid rgba(255, 0, 255, 0.3);
            }
        """)

        self.english_display = QTextEdit()
        self.english_display.setReadOnly(True)
        self.english_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.english_display.setFont(QFont("Arial", 18, QFont.Bold))
        self.english_display.setTextColor(QColor(220, 220, 255))
        self.english_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid rgba(255, 0, 255, 0.2);
                border-radius: 8px;
                color: #DCDCF0;
                padding: 20px;
                selection-background-color: rgba(255, 0, 255, 0.3);
            }
        """)
        self.english_display.setMinimumHeight(180)

        english_layout.addWidget(english_label)
        english_layout.addWidget(self.english_display)

        splitter.addWidget(chinese_widget)
        splitter.addWidget(english_widget)
        splitter.setSizes([300, 200])

        # 控制按钮和音频源选择
        control_widget = QWidget()
        control_widget.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.4);
                border-radius: 10px;
                border: 1px solid rgba(0, 255, 255, 0.2);
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout(control_widget)
        control_layout.setSpacing(10)

        # 音频设备选择
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(0, 255, 255, 0.1);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px;
                color: #00ffff;
                min-width: 250px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a3a;
                color: #00ffff;
                selection-background-color: rgba(0, 255, 255, 0.3);
                border: 1px solid rgba(0, 255, 255, 0.2);
                outline: none;
                max-height: 300px;  /* 限制下拉菜单最大高度 */
                min-width: 550px;   /* 设置下拉菜单最小宽度，确保选项显示完整 */
            }
            QComboBox QAbstractItemView::item {
                height: 25px;  /* 设置每个选项的高度 */
                padding: 5px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(0, 255, 255, 0.3);
            }
            QScrollBar:vertical {
                background: rgba(0, 255, 255, 0.1);
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 255, 255, 0.5);
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 255, 255, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)
        self.refresh_devices_button = QPushButton("刷新设备")
        self.refresh_devices_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 200, 0.7);
                color: #ffffff;
                border: 2px solid rgba(0, 150, 255, 0.5);
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(0, 120, 220, 0.8);
                border-color: rgba(0, 200, 255, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(0, 80, 180, 0.9);
                border-color: rgba(0, 255, 255, 0.8);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
                color: rgba(255, 255, 255, 0.6);
                border-color: rgba(150, 150, 150, 0.3);
            }
        """)
        self.refresh_devices_button.clicked.connect(self.refresh_audio_devices)

        self.start_button = QPushButton("开始识别")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 150, 0, 0.7);
                color: #ffffff;
                border: 2px solid rgba(0, 200, 0, 0.5);
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(0, 180, 0, 0.8);
                border-color: rgba(0, 255, 100, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(0, 120, 0, 0.9);
                border-color: rgba(0, 255, 150, 0.8);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
                color: rgba(255, 255, 255, 0.6);
                border-color: rgba(150, 150, 150, 0.3);
            }
        """)
        self.start_button.clicked.connect(self.start_recognition)

        self.stop_button = QPushButton("停止识别")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(180, 0, 0, 0.7);
                color: #ffffff;
                border: 2px solid rgba(220, 0, 0, 0.5);
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(200, 0, 0, 0.8);
                border-color: rgba(255, 50, 50, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(150, 0, 0, 0.9);
                border-color: rgba(255, 100, 100, 0.8);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
                color: rgba(255, 255, 255, 0.6);
                border-color: rgba(150, 150, 150, 0.3);
            }
        """)
        self.stop_button.clicked.connect(self.stop_recognition)
        self.stop_button.setEnabled(False)

        self.clear_button = QPushButton("清空字幕")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(200, 120, 0, 0.7);
                color: #ffffff;
                border: 2px solid rgba(230, 150, 0, 0.5);
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(220, 140, 0, 0.8);
                border-color: rgba(255, 180, 0, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(180, 100, 0, 0.9);
                border-color: rgba(255, 200, 0, 0.8);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
                color: rgba(255, 255, 255, 0.6);
                border-color: rgba(150, 150, 150, 0.3);
            }
        """)
        self.clear_button.clicked.connect(self.clear_subtitles)

        # 添加透明字幕窗口控制按钮
        self.toggle_subtitle_button = QPushButton("隐藏透明字幕")  # 默认显示，所以按钮文字为隐藏
        self.toggle_subtitle_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 50, 180, 0.7);
                color: #ffffff;
                border: 2px solid rgba(140, 80, 220, 0.5);
                border-radius: 6px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(120, 60, 200, 0.8);
                border-color: rgba(180, 100, 255, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(80, 40, 160, 0.9);
                border-color: rgba(200, 120, 255, 0.8);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
                color: rgba(255, 255, 255, 0.6);
                border-color: rgba(150, 150, 150, 0.3);
            }
        """)
        self.toggle_subtitle_button.clicked.connect(self.toggle_subtitle_window)

        input_device_label = QLabel("输入设备:")
        input_device_label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
            }
        """)
        control_layout.addWidget(input_device_label)
        control_layout.addWidget(self.device_combo)
        control_layout.addWidget(self.refresh_devices_button)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.toggle_subtitle_button)

        # 添加导出按钮
        self.export_button = QPushButton("导出字幕")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 0, 0.7);
                color: #00ff00;
                border: 2px solid rgba(0, 255, 0, 0.5);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 0.9);
                border: 2px solid rgba(0, 255, 0, 0.8);
            }
            QPushButton:pressed {
                background-color: rgba(0, 200, 0, 1.0);
                border: 2px solid rgba(0, 255, 0, 1.0);
            }
            QPushButton:disabled {
                background-color: rgba(50, 50, 50, 0.5);
                color: #888888;
                border: 2px solid rgba(100, 100, 100, 0.3);
            }
        """)
        self.export_button.clicked.connect(self.export_subtitles)
        control_layout.addWidget(self.export_button)

        control_layout.addStretch()

        # 组装布局
        layout.addWidget(splitter)
        layout.addWidget(control_widget)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: rgba(0, 0, 0, 0.4);
                color: #00ffff;
                border-top: 2px solid rgba(0, 255, 255, 0.2);
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("系统就绪 - 等待指令")

        # 获取音频设备列表
        self.refresh_audio_devices()
        
        # 默认创建并显示透明字幕窗口
        self.toggle_subtitle_window()

    def refresh_audio_devices(self):
        """刷新音频设备列表，只显示真正可用的设备"""
        try:
            # 获取真正可用的音频设备
            self.audio_devices = get_audio_devices()

            self.device_combo.clear()
            
            # 只添加可用的设备
            available_count = 0
            for index, name, device_type, is_usable in self.audio_devices:
                if is_usable:
                    # 在设备名称中显示设备类型
                    display_name = f"{index}: {name} [{device_type}]"
                    self.device_combo.addItem(display_name, index)
                    available_count += 1

            # 选择最合适的默认设备
            if available_count > 0:
                # 根据当前音频源类型选择默认设备
                preferred_type = "system_audio" if self.args.audio_source == "system_audio" else "microphone"
                default_device = get_default_audio_device(preferred_type)
                
                if default_device:
                    device_index, device_name, device_type, is_usable = default_device
                    # 查找并选择默认设备
                    for i in range(self.device_combo.count()):
                        if self.device_combo.itemData(i) == device_index:
                            self.device_combo.setCurrentIndex(i)
                            logger.info(f"已选择默认设备: {device_name} [{device_type}]")
                            break
                
                status_bar = self.statusBar()
                if status_bar:
                    status_bar.showMessage(f"找到 {available_count} 个可用音频设备")
            else:
                status_bar = self.statusBar()
                if status_bar:
                    status_bar.showMessage("未找到可用的音频输入设备")
                logger.warning("未找到任何可用的音频设备")

        except Exception as e:
            logger.error(f"刷新音频设备列表时出错: {e}")
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(f"设备扫描失败: {e}")

    def start_recognition(self):
        logger.info("开始语音识别")
        self.status_bar.showMessage("正在启动语音识别引擎...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # 移除了音频源选择，所以不需要禁用
        self.device_combo.setEnabled(False)
        self.refresh_devices_button.setEnabled(False)

        # 获取选中的设备索引
        device_index = self.device_combo.currentData()

        # 启动工作线程
        self.worker = self.worker_class(device_index)
        self.worker.update_chinese.connect(self.update_chinese_text)
        self.worker.update_english.connect(self.update_english_text)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished.connect(self.on_worker_finished)

        self.worker.start()

    def stop_recognition(self):
        logger.info("停止语音识别")
        self.status_bar.showMessage("停止语音识别引擎...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        if self.worker:
            try:
                # 检查工作线程是否还在运行
                if hasattr(self.worker, 'is_running') and self.worker.is_running:
                    self.worker.stop()
                else:
                    logger.warning("工作线程已停止或未运行，跳过停止操作")
                    self.on_worker_finished()
            except Exception as e:
                logger.error(f"停止识别时发生错误: {e}")
                logger.error(f"错误类型: {type(e).__name__}")
                import traceback
                logger.error(f"堆栈跟踪: {traceback.format_exc()}")
                # 确保UI状态恢复正常
                self.on_worker_finished()
        
        # 不再自动清空字幕，保留用户内容
        # 只清空流式输出状态，确保下次开始时状态正常
        try:
            # 清空流式输出状态
            if hasattr(self, 'current_streaming_words'):
                self.current_streaming_words = []
                self.current_streaming_index = 0
            if hasattr(self, 'streaming_timer') and self.streaming_timer.isActive():
                self.streaming_timer.stop()
                
        except Exception as e:
            logger.error(f"清空流式状态时发生错误: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
            self.status_bar.showMessage(f"清空状态失败: {e}")
        
        # 更新状态栏消息，提示用户字幕内容已保留
        self.status_bar.showMessage("语音识别已停止 - 字幕内容已保留")

    def update_chinese_text(self, text):
        # 如果正在清空状态，忽略工作线程的更新
        if self.is_clearing:
            logger.info("清空状态中，忽略中文更新: %s", text)
            return
            
        logger.info("主字幕窗口更新中文显示: %s", text)
        self.chinese_text = text
        self.chinese_display.setText(text)
        
        # 滚动条自动滚动到底部
        scroll_bar = self.chinese_display.verticalScrollBar()
        if scroll_bar:
            scroll_bar.setValue(scroll_bar.maximum())

        # 同时更新透明字幕窗口
        if hasattr(self, 'subtitle_window') and self.subtitle_window:
            self.subtitle_window.update_chinese_text(text)

    def update_english_text(self, text, is_incremental=False):
        """更新英文显示，支持在线/离线通道模式（仿照中文更新策略）"""
        logger.info("窗口更新英文显示: %s (在线模式: %s)", text, is_incremental)
        
        # 如果正在清空状态，忽略工作线程的更新
        if self.is_clearing:
            logger.info("清空状态中，忽略英文更新: %s", text)
            return
        
        if is_incremental:
            # 在线模式：直接替换显示内容（类似2pass-online）
            self.english_text = text
            logger.info("在线模式更新英文显示: %s", text)
        else:
            # 离线模式：直接替换显示内容（类似2pass-offline）
            self.english_text = text
            logger.info("离线模式更新英文显示: %s", text)
        
        # 更新显示
        self.english_display.setText(self.english_text)
        
        # 滚动条自动滚动到底部
        scroll_bar = self.english_display.verticalScrollBar()
        if scroll_bar:
            scroll_bar.setValue(scroll_bar.maximum())
        
        # 同时更新透明字幕窗口
        if hasattr(self, 'subtitle_window') and self.subtitle_window:
            self.subtitle_window.update_english_text(self.english_text, is_incremental)
    


    def update_status(self, message):
        logger.info("状态更新: %s", message)
        self.status_bar.showMessage(message)
    
    def on_worker_finished(self):
        """当工作线程完成时，恢复UI状态"""
        logger.info("工作线程已完成，恢复UI状态")
        
        # 恢复按钮状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.refresh_devices_button.setEnabled(True)
        
        # 更新状态栏消息
        self.status_bar.showMessage("语音识别已停止 - 系统就绪")
        
        # 清空工作线程引用
        self.worker = None
    
    def clear_subtitles(self):
        """清空所有字幕内容，包括主窗口和副窗口"""
        logger.info("清空所有字幕内容")
        
        # 设置清空状态，防止工作线程更新覆盖
        self.is_clearing = True
        
        # 清空主窗口显示
        self.chinese_text = ""
        self.english_text = ""
        self.chinese_display.setText("")
        self.english_display.setText("")
        
        # 清空透明字幕窗口
        if hasattr(self, 'subtitle_window') and self.subtitle_window:
            self.subtitle_window.clear_text()
        
        # 清空工作线程中的英文在线/离线通道
        if self.worker and hasattr(self.worker, 'text_print_en_online'):
            self.worker.text_print_en_online = ""
            self.worker.text_print_en_offline = ""
            self.worker.text_print_en = ""
            logger.info("已清空工作线程中的英文在线/离线通道")
        
        # 如果正在识别中，停止并重新开始识别会话
        if self.worker and hasattr(self.worker, 'is_running') and self.worker.is_running:
            logger.info("识别状态下清空，执行停止并重新开始操作")
            self._restart_recognition_session()
        else:
            # 延迟1秒后重置清空状态
            self.clearing_timer.start(1000)
        
        self.status_bar.showMessage("字幕内容已清空")
    
    def _restart_recognition_session(self):
        """停止并重新开始识别会话，确保服务器端也清空历史"""
        try:
            # 保存当前设备选择
            current_device_index = self.device_combo.currentIndex()
            
            # 停止当前识别
            self.stop_recognition()
            
            # 延迟500毫秒后重新开始识别
            QTimer.singleShot(500, lambda: self._resume_recognition(current_device_index))
            
        except Exception as e:
            logger.error("重新开始识别会话时发生错误: %s", str(e))
            # 确保清空状态被重置
            self._reset_clearing_state()
    
    def _resume_recognition(self, device_index):
        """恢复识别会话"""
        try:
            # 设置设备选择
            if device_index >= 0 and device_index < self.device_combo.count():
                self.device_combo.setCurrentIndex(device_index)
            
            # 重新开始识别
            self.start_recognition()
            
            # 延迟1秒后重置清空状态
            self.clearing_timer.start(1000)
            
        except Exception as e:
            logger.error("恢复识别会话时发生错误: %s", str(e))
            self._reset_clearing_state()
    
    def _reset_clearing_state(self):
        """重置清空状态"""
        self.is_clearing = False
        logger.info("清空状态已重置")
    

    def changeEvent(self, a0):
        """处理窗口状态变化事件 - 确保最小化时不会关闭透明字幕窗口"""
        if a0 and a0.type() == QEvent.Type.WindowStateChange:
            # 检查窗口是否被最小化
            if bool(self.windowState() & Qt.WindowState.WindowMinimized):
                logger.info("主窗口被最小化，保持透明字幕窗口显示")
                # 这里不执行任何操作，透明字幕窗口会保持显示状态
            # 检查窗口是否从最小化状态恢复
            else:
                # 对于WindowStateChange事件，我们可以通过检查当前状态来判断是否从最小化恢复
                # 如果当前不是最小化状态，说明可能从最小化状态恢复了
                if not bool(self.windowState() & Qt.WindowState.WindowMinimized):
                    logger.info("主窗口状态变化，可能从最小化状态恢复")
        
        # 修复：使用安全的父类调用
        try:
            super().changeEvent(a0)
        except Exception as e:
            logger.error(f"父类 changeEvent 调用失败: {e}")
        
    def closeEvent(self, a0):
        """当主窗口关闭时，确保透明字幕窗口也被关闭"""
        if hasattr(self, 'subtitle_window') and self.subtitle_window:
            self.subtitle_window.close()
        if a0:
            a0.accept()

    def toggle_subtitle_window(self):
        """切换透明字幕窗口的显示/隐藏"""
        if not hasattr(self, 'subtitle_window') or not self.subtitle_window:
            # 创建透明字幕窗口 - 传入回调函数用于联动
            self.subtitle_window = TransparentSubtitleWindow(on_close_callback=self.on_subtitle_window_closed)
            self.subtitle_window.show()
            self.toggle_subtitle_button.setText("隐藏透明字幕")
            if not hasattr(self, 'show_subtitle_window'):
                self.show_subtitle_window = True
        else:
            # 检查窗口是否实际可见，而不是仅仅检查状态变量
            if self.subtitle_window.isVisible():
                self.subtitle_window.hide()
                self.toggle_subtitle_button.setText("显示透明字幕")
                self.show_subtitle_window = False
            else:
                self.subtitle_window.show()
                self.toggle_subtitle_button.setText("隐藏透明字幕")
                self.show_subtitle_window = True
    
    def on_subtitle_window_closed(self):
        """当透明字幕窗口被关闭时（通过右键菜单），更新主窗口按钮状态"""
        # 更新按钮文字为"显示透明字幕"
        self.toggle_subtitle_button.setText("显示透明字幕")
        self.show_subtitle_window = False
        # 清空副窗口引用，确保下次点击按钮会重新创建
        self.subtitle_window = None


    def export_subtitles(self):
        """导出中英文字幕到文件，并保存导出记录"""
        # 检查是否有内容可导出
        if not self.chinese_text.strip() and not self.english_text.strip():
            QMessageBox.warning(self, "导出失败", "当前没有字幕内容可导出！")
            return
        
        try:
            # 获取保存文件路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存字幕文件", "", "文本文件 (*.txt)"
            )
            
            if not file_path:
                return  # 用户取消了保存
            
            # 确保文件扩展名
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            # 格式化导出内容
            export_content = f"中文识别内容:\n{self.chinese_text}\n\n" \
                           f"英文翻译内容:\n{self.english_text}\n\n" \
                           f"导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(export_content)
            
            # 保存导出记录
            self._save_export_record(file_path, export_content)
            
            # 显示成功消息
            QMessageBox.information(self, "导出成功", 
                                  f"字幕已成功导出到:\n{file_path}\n\n"
                                  f"导出记录已保存到导出历史中。")
            
            logger.info(f"字幕导出成功: {file_path}")
            
        except Exception as e:
            error_msg = f"导出字幕时发生错误: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "导出错误", error_msg)
    
    def _save_export_record(self, file_path, content):
        """保存导出记录到历史文件"""
        try:
            # 创建导出记录目录
            export_dir = os.path.join(os.path.dirname(__file__), "export_history")
            os.makedirs(export_dir, exist_ok=True)
            
            # 导出记录文件路径
            record_file = os.path.join(export_dir, "export_history.json")
            
            # 读取现有记录
            records = []
            if os.path.exists(record_file):
                with open(record_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            
            # 添加新记录
            new_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "file_path": file_path,
                "chinese_length": len(self.chinese_text),
                "english_length": len(self.english_text),
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
            records.append(new_record)
            
            # 只保留最近50条记录
            if len(records) > 50:
                records = records[-50:]
            
            # 保存记录
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            logger.info(f"导出记录已保存: {record_file}")
            
        except Exception as e:
            logger.error(f"保存导出记录时出错: {e}")
            # 不中断主流程，记录错误即可

