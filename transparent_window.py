"""
副字幕窗口模块
包含TransparentSubtitleWindow类，用于显示透明悬浮字幕
"""

import logging
from collections import deque
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QMenu
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QShowEvent, QMouseEvent, QContextMenuEvent, QFont

# 导入文本处理工具模块
from text_utils import extract_complete_sentence

logger = logging.getLogger(__name__)


class TransparentSubtitleWindow(QMainWindow):
    def __init__(self, on_close_callback=None):
        super().__init__()
        self.on_close_callback = on_close_callback  # 保存回调函数
        self.setWindowTitle("智能字幕显示")
        # 使用类型转换修复setWindowFlags的类型问题
        window_flags = Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint
        self.setWindowFlags(window_flags)  # type: ignore
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 设置窗口大小和位置（固定长度为屏幕宽度的80%，位于屏幕最下方）
        screen = self.screen()
        if screen is not None:
            screen_geometry = screen.availableGeometry()
            self.default_width = int(screen_geometry.width() * 0.8)  # 默认宽度
            self.default_height = 120
            
            # 固定底部距离（距离屏幕底部180像素）
            self.fixed_bottom_distance = 180
            
            self.resize(self.default_width, self.default_height)
            
            # 将窗口放置在屏幕最下方中间
            center_x = screen_geometry.width() // 2 - self.default_width // 2
            bottom_y = screen_geometry.height() - self.fixed_bottom_distance
            self.move(center_x, bottom_y)
            
            # 记录初始的底部位置
            self.initial_bottom_y = bottom_y
        else:
            # 如果无法获取屏幕信息，使用默认值
            self.default_width = 1024
            self.default_height = 120
            self.fixed_bottom_distance = 180
            self.resize(self.default_width, self.default_height)
            self.move(100, 100)
        
        # 创建中央部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建文本显示框
        self.chinese_label = QLabel("")
        self.english_label = QLabel("")
        
        # 设置字体和样式
        self.font_size = 24
        self.set_font_size(self.font_size)
        
        # 禁用自动换行，让文本在一行显示
        self.chinese_label.setWordWrap(False)
        self.english_label.setWordWrap(False)
        
        # 科技感半透明样式 - 深色背景带发光效果
        chinese_style = """
            color: #00ffff;
            background-color: rgba(10, 10, 40, 0.85);
            padding: 15px 25px;
            border-radius: 12px;
            border: 2px solid rgba(0, 255, 255, 0.4);
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.7);
        """
        
        english_style = """
            color: #ff00ff;
            background-color: rgba(40, 10, 40, 0.85);
            padding: 12px 25px;
            border-radius: 12px;
            border: 2px solid rgba(255, 0, 255, 0.4);
            text-shadow: 0 0 10px rgba(255, 0, 255, 0.7);
        """
        
        self.chinese_label.setStyleSheet(chinese_style)
        self.english_label.setStyleSheet(english_style)
        
        # 设置文本对齐
        self.chinese_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.english_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加到布局
        self.main_layout.addWidget(self.chinese_label)
        self.main_layout.addWidget(self.english_label)
        
        # 设置布局间距
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(15, 10, 15, 10)
        
        # 初始化透明度
        self.opacity = 0.95
        self.setWindowOpacity(self.opacity)
        
        # 初始化拖动相关变量
        self.dragging = False
        self.drag_position = QPoint()
        
        # 初始化文本缓存和句子队列
        self.chinese_text_buffer = ""  # 中文文本缓存
        self.english_text_buffer = ""  # 英文文本缓存
        self.chinese_sentence_queue = deque()  # 中文句子队列
        self.english_sentence_queue = deque()  # 英文句子队列
        self.current_chinese_sentence = ""  # 当前显示的中文句子
        self.current_english_sentence = ""  # 当前显示的英文句子
        self.chinese_processed_length = 0  # 中文已处理文本长度
        self.english_processed_length = 0  # 英文已处理文本长度
        # 新增：配对队列和相关变量
        self.paired_sentence_queue = deque()  # 存储(中文, 英文)句子对
        self.chinese_sentence_buffer = ""     # 中文句子缓存（用于配对）
        self.english_sentence_buffer = ""     # 英文句子缓存（用于配对）
        self.last_chinese_sentence = ""       # 上一个中文句子
        self.last_english_sentence = ""       # 上一个英文句子
                
        # 初始化显示定时器（每2秒检查一次是否需要更新句子）
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(2000)  # 每2秒检查一次
        
        # 记录当前是否正在显示长句子
        self.is_showing_long_sentence = False
        
        # 句子显示状态控制
        self.is_showing_sentence = False  # 是否正在显示句子



    def calculate_text_width(self, text, is_chinese=True):
        """计算文本所需的宽度"""
        if not text:
            return 0
            
        # 创建临时标签来计算文本宽度
        temp_label = QLabel(text)
        if is_chinese:
            font = QFont("Microsoft YaHei")
        else:
            font = QFont("Arial")
        font.setPointSize(self.font_size)
        font.setBold(True)
        temp_label.setFont(font)
        
        # 禁用自动换行以确保正确计算单行宽度
        temp_label.setWordWrap(False)
        
        # 计算理想宽度（文本实际需要的宽度）
        text_width = temp_label.sizeHint().width() + 50  # 加上边距
        
        # 限制最大宽度不超过屏幕宽度的95%
        screen = self.screen()
        if screen is not None:
            max_width = int(screen.availableGeometry().width() * 0.95)
        else:
            max_width = 1920  # 默认最大宽度
        return min(text_width, max_width)

    def adjust_window_width(self, new_sentence, is_chinese=True):
        """根据新句子内容调整窗口宽度"""
        # 计算新句子所需的宽度
        required_width = self.calculate_text_width(new_sentence, is_chinese)
        
        logger.info(f"句子: '{new_sentence}', 需要宽度: {required_width}px, 当前宽度: {self.width()}px, 默认宽度: {self.default_width}px")
        
        # 如果新句子宽度超过默认宽度，调整窗口大小
        if required_width > self.default_width:
            self.is_showing_long_sentence = True
            
            # 保存当前底部位置
            current_bottom = self.geometry().bottom()
            screen = self.screen()
            if screen is not None:
                screen_height = screen.availableGeometry().height()
                current_bottom_distance = screen_height - current_bottom
            else:
                current_bottom_distance = 180  # 默认值
            
            self.resize(required_width, self.default_height)  # 始终使用默认高度
            
            # 重新居中窗口，但保持底部位置不变
            self.center_on_screen_fixed_bottom()
            logger.info(f"窗口宽度调整为: {required_width}px, 底部距离保持: {self.fixed_bottom_distance}px")
        else:
            # 如果新句子不需要调整宽度，但当前窗口是扩展状态，则恢复默认宽度
            if self.width() > self.default_width:
                self.restore_default_width()
            self.is_showing_long_sentence = False
            logger.info(f"句子宽度正常，保持默认宽度: {self.default_width}px")

    def restore_default_width(self):
        """恢复窗口到默认宽度"""
        self.resize(self.default_width, self.default_height)  # 始终使用默认高度
        self.center_on_screen_fixed_bottom()  # 使用固定底部位置的居中方法
        self.is_showing_long_sentence = False
        logger.info("窗口宽度恢复到默认大小")

    def center_on_screen(self):
        screen = self.screen()
        if screen is None:
            return
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        
        # 计算屏幕中心位置（保持底部位置不变）
        center_x = screen_geometry.width() // 2 - window_geometry.width() // 2
        
        # 保持固定的底部距离
        bottom_y = screen_geometry.height() - self.fixed_bottom_distance
        
        # 将窗口放在屏幕下方中间（保持底部位置固定）
        self.move(center_x, bottom_y)

    def center_on_screen_fixed_bottom(self):
        """使用固定底部位置的居中方法"""
        screen = self.screen()
        if screen is None:
            return
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        
        # 计算屏幕中心位置
        center_x = screen_geometry.width() // 2 - window_geometry.width() // 2
        
        # 保持固定的底部距离
        bottom_y = screen_geometry.height() - self.fixed_bottom_distance
        
        # 将窗口放在屏幕下方中间（保持底部位置固定）
        self.move(center_x, bottom_y)
        logger.info(f"窗口重新居中，底部距离保持: {self.fixed_bottom_distance}px")

    def update_display(self):
        """定时更新显示（每2秒调用一次）"""
        # 检查配对句子队列 - 同时显示中英文
        if self.paired_sentence_queue and not self.is_showing_sentence:
            chinese_sentence, english_sentence = self.paired_sentence_queue.popleft()
            
            # 更新当前显示的句子
            self.current_chinese_sentence = chinese_sentence
            self.current_english_sentence = english_sentence
            
            # 同时显示中英文
            self.chinese_label.setText(chinese_sentence)
            self.english_label.setText(english_sentence)
            
            logger.info(f"同时显示中英文: 中文='{chinese_sentence}', 英文='{english_sentence}'")
            
            # 根据最长的句子调整窗口宽度
            chinese_width = self.calculate_text_width(chinese_sentence, True)
            english_width = self.calculate_text_width(english_sentence, False)
            max_width = max(chinese_width, english_width, self.default_width)
            
            if max_width > self.default_width:
                self.resize(max_width, self.default_height)
                self.center_on_screen_fixed_bottom()
                self.is_showing_long_sentence = True
            else:
                self.restore_default_width()
                self.is_showing_long_sentence = False
            
            # 设置显示状态和定时器
            self.is_showing_sentence = True
            # 根据文本长度计算显示时间（取中英文中最长的）
            chinese_length = len(chinese_sentence.strip())
            english_length = len(english_sentence.strip())
            max_length = max(chinese_length, english_length)
            display_time = self.calculate_display_time_by_length(max_length)
            QTimer.singleShot(display_time, self.clear_current_sentence)

    def calculate_display_time_by_length(self, length):
        """根据文本长度计算显示时间（毫秒）"""
        if length <= 5:
            return 2000  # 2秒
        elif length <= 15:
            return 3000  # 3秒
        else:
            return 5000  # 5秒

    def clear_current_sentence(self):
        """清除当前显示的句子，准备显示下一个"""
        self.is_showing_sentence = False
        # 清空当前显示的句子内容
        self.chinese_label.setText("")
        self.english_label.setText("")
        self.current_chinese_sentence = ""
        self.current_english_sentence = ""
        # 恢复默认窗口宽度
        self.restore_default_width()

    def update_chinese_text(self, text):
        """更新中文文本（主窗口调用）"""
        if text != self.chinese_text_buffer:
            self.chinese_text_buffer = text
            self.process_chinese_text()
            # 尝试配对中英文句子
            self.try_pair_sentences()

    def update_english_text(self, text, is_incremental=False):
        """更新英文文本（主窗口调用），支持增量翻译和完整翻译的区分处理"""
        logger.info(f"副窗口更新英文显示: {text} (增量: {is_incremental})")
        
        if is_incremental:
            # 增量翻译：直接更新显示，不进行句子提取和配对
            self.english_label.setText(text)
        else:
            # 完整翻译：更新文本缓冲区并处理完整句子
            if text != self.english_text_buffer:
                self.english_text_buffer = text
                self.process_english_text()
                # 尝试配对中英文句子
                self.try_pair_sentences()
                
                # 统一更新显示内容
                if self.english_sentence_buffer:
                    # 只显示当前缓存句子的内容（不包含已处理的文本）
                    display_text = self.english_sentence_buffer
                    # 更新字幕显示
                    self.english_label.setText(display_text)

    def process_chinese_text(self):
        """处理中文文本，提取完整句子到缓存"""
        if not self.chinese_text_buffer:
            return
        
        # 只处理新增的文本部分
        text_to_process = self.chinese_text_buffer[self.chinese_processed_length:]
        if not text_to_process:
            return
            
        # 从新增文本中提取完整句子
        remaining_text = text_to_process
        
        while remaining_text:
            sentence, remaining = extract_complete_sentence(remaining_text)
            if sentence:
                # 将完整句子添加到缓存（用于配对）
                self.chinese_sentence_buffer = sentence
                # 更新已处理长度（加上提取的句子长度）
                self.chinese_processed_length += len(sentence)
                remaining_text = remaining
                logger.info(f"提取到中文句子: {sentence}")
            else:
                # 如果没有完整句子，等待更多文本
                logger.info(f"未找到完整中文句子，等待更多文本: {remaining_text}")
                break

    def process_english_text(self):
        """处理英文文本，提取完整句子到缓存，支持累积显示机制"""
        if not self.english_text_buffer:
            return
        
        # 只处理新增的文本部分
        text_to_process = self.english_text_buffer[self.english_processed_length:]
        if not text_to_process:
            return
            
        # 从新增文本中提取完整句子
        remaining_text = text_to_process
        
        while remaining_text:
            sentence, remaining = extract_complete_sentence(remaining_text)
            if sentence:
                # 检查是否已经有缓存句子，如果有则替换（实现完整句子替换碎片化翻译）
                if self.english_sentence_buffer:
                    # 只有当新句子比缓存句子更长或更完整时才替换
                    if len(sentence) > len(self.english_sentence_buffer) or sentence.endswith(('.', '!', '?')):
                        logger.info(f"用完整句子替换碎片化翻译: '{self.english_sentence_buffer}' -> '{sentence}'")
                        self.english_sentence_buffer = sentence
                    else:
                        # 如果新句子不更完整，则追加到现有句子后
                        self.english_sentence_buffer += " " + sentence
                        logger.info(f"将新句子追加到现有句子后: '{self.english_sentence_buffer}'")
                else:
                    # 没有缓存句子，直接设置新句子
                    self.english_sentence_buffer = sentence
                    logger.info(f"提取到英文句子: {sentence}")
                
                # 更新已处理长度（加上提取的句子长度）
                self.english_processed_length += len(sentence)
                remaining_text = remaining
            else:
                # 如果没有完整句子，检查是否有缓存句子可以追加
                if self.english_sentence_buffer and remaining_text.strip():
                    # 有缓存句子且还有剩余文本，将剩余文本追加到缓存句子后
                    self.english_sentence_buffer += " " + remaining_text.strip()
                    logger.info(f"将碎片化翻译追加到完整句子后: '{self.english_sentence_buffer}'")
                    # 更新已处理长度（加上剩余文本长度）
                    self.english_processed_length += len(remaining_text)
                else:
                    # 如果没有缓存句子，将剩余文本作为新缓存
                    if remaining_text.strip():
                        self.english_sentence_buffer = remaining_text.strip()
                        logger.info(f"设置新缓存句子: '{self.english_sentence_buffer}'")
                        self.english_processed_length += len(remaining_text)
                    else:
                        # 如果没有完整句子，等待更多文本
                        logger.info(f"未找到完整英文句子，等待更多文本: {remaining_text}")
                break
        
        # 注意：显示更新逻辑现在在update_english_text方法中统一处理

    def try_pair_sentences(self):
        """尝试配对中英文句子"""
        if self.chinese_sentence_buffer and self.english_sentence_buffer:
            # 如果中英文都有完整的句子，进行配对
            chinese_sentence = self.chinese_sentence_buffer
            english_sentence = self.english_sentence_buffer
            
            # 添加到配对队列
            self.paired_sentence_queue.append((chinese_sentence, english_sentence))
            logger.info(f"配对成功: 中文='{chinese_sentence}', 英文='{english_sentence}'")
            
            # 清空缓存
            self.chinese_sentence_buffer = ""
            self.english_sentence_buffer = ""
            
            # 保存最后的句子用于可能的单独显示
            self.last_chinese_sentence = chinese_sentence
            self.last_english_sentence = english_sentence
            
        elif self.chinese_sentence_buffer and not self.english_sentence_buffer:
            # 只有中文句子，等待英文
            logger.info(f"等待英文翻译: {self.chinese_sentence_buffer}")
            
        elif not self.chinese_sentence_buffer and self.english_sentence_buffer:
            # 只有英文句子，等待中文
            logger.info(f"等待中文原文: {self.english_sentence_buffer}")

    def clear_text(self):
        """清空所有文本和缓存"""
        # 清空显示内容
        self.chinese_label.setText("")
        self.english_label.setText("")
        
        # 清空文本缓冲区
        self.chinese_text_buffer = ""
        self.english_text_buffer = ""
        
        # 清空句子缓存
        self.chinese_sentence_buffer = ""
        self.english_sentence_buffer = ""
        
        # 清空句子队列
        self.paired_sentence_queue.clear()
        self.chinese_sentence_queue.clear()
        self.english_sentence_queue.clear()
        
        # 清空当前显示的句子
        self.current_chinese_sentence = ""
        self.current_english_sentence = ""
        
        # 清空最后的句子缓存
        self.last_chinese_sentence = ""
        self.last_english_sentence = ""
        
        # 重置处理长度
        self.chinese_processed_length = 0
        self.english_processed_length = 0
        
        # 重置显示状态
        self.is_showing_sentence = False
        self.is_showing_long_sentence = False
        
        # 清空文本时恢复默认窗口宽度
        self.restore_default_width()
        
        logger.info("副字幕窗口内容已完全清空")

    def showEvent(self, a0):
        """窗口显示时确保置顶"""
        super().showEvent(a0)
        self.raise_()
        self.activateWindow()
    
    def mousePressEvent(self, a0: QMouseEvent):
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = a0.globalPos() - self.frameGeometry().topLeft()
            a0.accept()
    
    def mouseMoveEvent(self, a0: QMouseEvent):
        if a0 is not None and self.dragging and bool(a0.buttons() & Qt.MouseButton.LeftButton):
            self.move(a0.globalPos() - self.drag_position)
            a0.accept()
    
    def mouseReleaseEvent(self, a0: QMouseEvent):
        if a0 is not None:
            self.dragging = False
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        if event is None:
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
        
        # 透明度调节菜单项
        opacity_menu = menu.addMenu("🎨 透明度调节")
        if opacity_menu is not None:
            for opacity in [0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]:
                action = opacity_menu.addAction(f"{opacity*100:.0f}% 透明度")
                if action is not None:
                    action.triggered.connect(lambda checked, o=opacity: self.set_opacity(o))
        
        # 字体大小调节菜单项
        font_menu = menu.addMenu("🔤 字体大小")
        if font_menu is not None:
            for size in [18, 20, 24, 28, 32, 36, 40]:
                action = font_menu.addAction(f"{size}px")
                if action is not None:
                    action.triggered.connect(lambda checked, s=size: self.set_font_size(s))
        
        menu.addSeparator()
        
        # 关闭菜单项
        close_action = menu.addAction("❌ 关闭副字幕")
        if close_action is not None:
            close_action.triggered.connect(self.handle_close)
        
        menu.exec_(event.globalPos())
    
    def set_opacity(self, opacity):
        self.opacity = opacity
        self.setWindowOpacity(opacity)
    
    def set_font_size(self, size):
        self.font_size = size
        font = QFont("Microsoft YaHei")
        font.setPointSize(size)
        font.setBold(True)
        self.chinese_label.setFont(font)
        
        english_font = QFont("Arial")
        english_font.setPointSize(size)
        english_font.setBold(True)
        self.english_label.setFont(english_font)

    def handle_close(self):
        """处理关闭操作，先通知主窗口更新按钮状态"""
        if self.on_close_callback:
            self.on_close_callback()  # 通知主窗口更新按钮状态
        self.close()  # 关闭副字幕窗口
    
