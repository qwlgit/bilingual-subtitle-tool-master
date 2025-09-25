"""
UI组件工具模块
UI Components Module
"""

import logging
from typing import Callable, Optional, Dict, Any
from PyQt5.QtWidgets import (QPushButton, QLabel, QComboBox, QTextEdit, 
                            QSlider, QSpinBox, QCheckBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..config.constants import (
    TECH_CYAN, TECH_MAGENTA, TECH_BLUE, TECH_GREEN,
    CHINESE_FONT_FAMILY, ENGLISH_FONT_FAMILY, DEFAULT_FONT_SIZE
)

logger = logging.getLogger(__name__)


class StyledButton(QPushButton):
    """自定义样式按钮"""
    
    def __init__(self, text: str, buttonType: str = "primary", parent=None):
        super().__init__(text, parent)
        self.buttonType = buttonType
        self._setupStyle()
    
    def _setupStyle(self):
        """设置按钮样式"""
        styles = {
            "primary": f"""
                QPushButton {{
                    background-color: rgba(0, 150, 0, 0.7);
                    color: #ffffff;
                    border: 2px solid rgba(0, 200, 0, 0.5);
                    border-radius: 6px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(0, 180, 0, 0.8);
                    border-color: rgba(0, 255, 100, 0.7);
                }}
                QPushButton:pressed {{
                    background-color: rgba(0, 120, 0, 0.9);
                }}
                QPushButton:disabled {{
                    background-color: rgba(100, 100, 100, 0.5);
                    color: rgba(255, 255, 255, 0.6);
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background-color: rgba(180, 0, 0, 0.7);
                    color: #ffffff;
                    border: 2px solid rgba(220, 0, 0, 0.5);
                    border-radius: 6px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(200, 0, 0, 0.8);
                    border-color: rgba(255, 50, 50, 0.7);
                }}
                QPushButton:pressed {{
                    background-color: rgba(150, 0, 0, 0.9);
                }}
                QPushButton:disabled {{
                    background-color: rgba(100, 100, 100, 0.5);
                    color: rgba(255, 255, 255, 0.6);
                }}
            """,
            "warning": f"""
                QPushButton {{
                    background-color: rgba(200, 120, 0, 0.7);
                    color: #ffffff;
                    border: 2px solid rgba(230, 150, 0, 0.5);
                    border-radius: 6px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(220, 140, 0, 0.8);
                    border-color: rgba(255, 180, 0, 0.7);
                }}
                QPushButton:pressed {{
                    background-color: rgba(180, 100, 0, 0.9);
                }}
                QPushButton:disabled {{
                    background-color: rgba(100, 100, 100, 0.5);
                    color: rgba(255, 255, 255, 0.6);
                }}
            """,
            "info": f"""
                QPushButton {{
                    background-color: rgba(0, 100, 200, 0.7);
                    color: #ffffff;
                    border: 2px solid rgba(0, 150, 255, 0.5);
                    border-radius: 6px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba(0, 120, 220, 0.8);
                    border-color: rgba(0, 200, 255, 0.7);
                }}
                QPushButton:pressed {{
                    background-color: rgba(0, 80, 180, 0.9);
                }}
                QPushButton:disabled {{
                    background-color: rgba(100, 100, 100, 0.5);
                    color: rgba(255, 255, 255, 0.6);
                }}
            """
        }
        
        self.setStyleSheet(styles.get(self.buttonType, styles["primary"]))


class StyledLabel(QLabel):
    """自定义样式标签"""
    
    def __init__(self, text: str = "", labelType: str = "default", parent=None):
        super().__init__(text, parent)
        self.labelType = labelType
        self._setupStyle()
    
    def _setupStyle(self):
        """设置标签样式"""
        styles = {
            "title": f"""
                QLabel {{
                    color: {TECH_CYAN};
                    background-color: rgba(0, 255, 255, 0.1);
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid rgba(0, 255, 255, 0.3);
                    font-size: 16px;
                    font-weight: bold;
                }}
            """,
            "subtitle": f"""
                QLabel {{
                    color: {TECH_CYAN};
                    background-color: rgba(0, 255, 255, 0.15);
                    padding: 8px;
                    border-radius: 6px;
                    border: 1px solid rgba(0, 255, 255, 0.3);
                    font-size: 14px;
                    font-weight: bold;
                }}
            """,
            "status": f"""
                QLabel {{
                    color: {TECH_GREEN};
                    font-size: 12px;
                    padding: 5px;
                }}
            """,
            "default": f"""
                QLabel {{
                    color: {TECH_CYAN};
                    font-size: 12px;
                    padding: 5px;
                }}
            """
        }
        
        self.setStyleSheet(styles.get(self.labelType, styles["default"]))
        
        # 设置字体
        if self.labelType == "title":
            self.setFont(QFont(CHINESE_FONT_FAMILY, 16, QFont.Bold))
        elif self.labelType == "subtitle":
            self.setFont(QFont(CHINESE_FONT_FAMILY, 14, QFont.Bold))


class StyledComboBox(QComboBox):
    """自定义样式下拉框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setupStyle()
    
    def _setupStyle(self):
        """设置下拉框样式"""
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(0, 255, 255, 0.1);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px;
                color: {TECH_CYAN};
                min-width: 200px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1a1a3a;
                color: {TECH_CYAN};
                selection-background-color: rgba(0, 255, 255, 0.3);
                border: 1px solid rgba(0, 255, 255, 0.2);
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                height: 25px;
                padding: 5px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: rgba(0, 255, 255, 0.3);
            }}
        """)


class StyledTextEdit(QTextEdit):
    """自定义样式文本编辑框"""
    
    def __init__(self, textType: str = "chinese", parent=None):
        super().__init__(parent)
        self.textType = textType
        self._setupStyle()
    
    def _setupStyle(self):
        """设置文本编辑框样式"""
        if self.textType == "chinese":
            borderColor = TECH_CYAN
            font = QFont(CHINESE_FONT_FAMILY, 20, QFont.Bold)
        else:
            borderColor = TECH_MAGENTA
            font = QFont(ENGLISH_FONT_FAMILY, 18, QFont.Bold)
        
        self.setFont(font)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid rgba({borderColor.replace('#', '')}, 0.2);
                border-radius: 8px;
                color: white;
                padding: 20px;
                selection-background-color: rgba({borderColor.replace('#', '')}, 0.3);
            }}
        """)


class StatusIndicator(QLabel):
    """状态指示器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.setStatus("disconnected")
    
    def setStatus(self, status: str):
        """设置状态"""
        colors = {
            "connected": "#00ff00",
            "connecting": "#ffff00", 
            "disconnected": "#ff0000",
            "error": "#ff6600"
        }
        
        color = colors.get(status, "#808080")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        
        self.setToolTip(f"状态: {status}")


class ProgressIndicator(QProgressBar):
    """进度指示器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setupStyle()
    
    def _setupStyle(self):
        """设置进度条样式"""
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 5px;
                text-align: center;
                color: {TECH_CYAN};
                background-color: rgba(0, 0, 0, 0.3);
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {TECH_CYAN}, stop: 1 {TECH_BLUE});
                border-radius: 3px;
            }}
        """)


class VolumeSlider(QSlider):
    """音量滑块"""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 100)
        self.setValue(80)
        self._setupStyle()
    
    def _setupStyle(self):
        """设置滑块样式"""
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid rgba(0, 255, 255, 0.3);
                height: 8px;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {TECH_CYAN};
                border: 1px solid rgba(0, 255, 255, 0.5);
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {TECH_BLUE};
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {TECH_CYAN}, stop: 1 {TECH_BLUE});
                border-radius: 4px;
            }}
        """)


class FontSizeSpinner(QSpinBox):
    """字体大小调节器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(12, 48)
        self.setValue(DEFAULT_FONT_SIZE)
        self.setSuffix("px")
        self._setupStyle()
    
    def _setupStyle(self):
        """设置样式"""
        self.setStyleSheet(f"""
            QSpinBox {{
                background-color: rgba(0, 255, 255, 0.1);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 4px;
                padding: 5px;
                color: {TECH_CYAN};
                font-weight: bold;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: rgba(0, 255, 255, 0.2);
                border: none;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: rgba(0, 255, 255, 0.4);
            }}
        """)


class StyledCheckBox(QCheckBox):
    """自定义样式复选框"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._setupStyle()
    
    def _setupStyle(self):
        """设置复选框样式"""
        self.setStyleSheet(f"""
            QCheckBox {{
                color: {TECH_CYAN};
                font-weight: bold;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: rgba(0, 0, 0, 0.3);
                border: 2px solid rgba(0, 255, 255, 0.3);
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {TECH_CYAN};
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 3px;
            }}
            QCheckBox::indicator:hover {{
                border-color: rgba(0, 255, 255, 0.7);
            }}
        """)


def createStyledButton(text: str, buttonType: str = "primary", 
                      onClick: Optional[Callable] = None) -> StyledButton:
    """
    创建样式化按钮的便捷函数
    
    Args:
        text: 按钮文本
        buttonType: 按钮类型
        onClick: 点击回调函数
        
    Returns:
        样式化按钮
    """
    button = StyledButton(text, buttonType)
    if onClick:
        button.clicked.connect(onClick)
    return button


def createStyledLabel(text: str, labelType: str = "default") -> StyledLabel:
    """
    创建样式化标签的便捷函数
    
    Args:
        text: 标签文本
        labelType: 标签类型
        
    Returns:
        样式化标签
    """
    return StyledLabel(text, labelType)


def applyTechTheme(widget, themeType: str = "default"):
    """
    为组件应用科技感主题
    
    Args:
        widget: 要应用主题的组件
        themeType: 主题类型
    """
    themes = {
        "default": f"""
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 8px;
            color: {TECH_CYAN};
        """,
        "container": f"""
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #1a1a3a, stop: 1 #0a0a2a);
            border: 2px solid {TECH_CYAN};
            border-radius: 10px;
        """
    }
    
    widget.setStyleSheet(themes.get(themeType, themes["default"]))