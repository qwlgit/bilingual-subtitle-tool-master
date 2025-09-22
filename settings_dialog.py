# -*- coding: utf-8 -*-
"""
设置对话框模块 - 支持参数动态调整
"""

import os
import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
                             QComboBox, QCheckBox, QPushButton, QMessageBox,
                             QTabWidget, QFormLayout, QWidget)  # 添加 QWidget 导入
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """设置对话框类，支持运行时参数动态调整"""
    
    def __init__(self, args, parent=None):
        """
        初始化设置对话框
        
        Args:
            args: 命令行参数对象
            parent: 父窗口
        """
        super().__init__(parent)
        self.args = args
        self.current_settings = {}
        
        self.setWindowTitle("参数设置")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 音频设置选项卡
        audio_tab = self.create_audio_tab()
        tab_widget.addTab(audio_tab, "音频设置")
        
        # 识别设置选项卡
        recognition_tab = self.create_recognition_tab()
        tab_widget.addTab(recognition_tab, "识别设置")
        
        # 翻译设置选项卡
        translation_tab = self.create_translation_tab()
        tab_widget.addTab(translation_tab, "翻译设置")
        
        # 系统设置选项卡
        system_tab = self.create_system_tab()
        tab_widget.addTab(system_tab, "系统设置")
        
        main_layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        self.apply_button = QPushButton("应用")
        self.apply_button.clicked.connect(self.apply_settings)
        
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
    
    def create_audio_tab(self):
        """创建音频设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 音频源设置
        audio_source_group = QGroupBox("音频源设置")
        audio_source_layout = QFormLayout(audio_source_group)
        
        self.audio_source_combo = QComboBox()
        self.audio_source_combo.addItems(["default", "麦克风阵列", "线路输入"])
        audio_source_layout.addRow("音频源:", self.audio_source_combo)
        
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(512, 8192)
        self.chunk_size_spin.setSingleStep(256)
        audio_source_layout.addRow("块大小:", self.chunk_size_spin)
        
        # 添加chunk_interval设置
        self.chunk_interval_spin = QSpinBox()
        self.chunk_interval_spin.setRange(1, 10)
        self.chunk_interval_spin.setSingleStep(1)
        audio_source_layout.addRow("块间隔:", self.chunk_interval_spin)
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(8000, 48000)
        self.sample_rate_spin.setSingleStep(1000)
        audio_source_layout.addRow("采样率:", self.sample_rate_spin)
        
        layout.addWidget(audio_source_group)
        
        # 音频处理设置
        audio_processing_group = QGroupBox("音频处理设置")
        audio_processing_layout = QFormLayout(audio_processing_group)
        
        self.silence_threshold_spin = QDoubleSpinBox()
        self.silence_threshold_spin.setRange(0.1, 1.0)
        self.silence_threshold_spin.setSingleStep(0.1)
        self.silence_threshold_spin.setDecimals(1)
        audio_processing_layout.addRow("静音阈值:", self.silence_threshold_spin)
        
        self.energy_threshold_spin = QSpinBox()
        self.energy_threshold_spin.setRange(100, 1000)
        self.energy_threshold_spin.setSingleStep(50)
        audio_processing_layout.addRow("能量阈值:", self.energy_threshold_spin)
        
        self.pause_threshold_spin = QDoubleSpinBox()
        self.pause_threshold_spin.setRange(0.5, 5.0)
        self.pause_threshold_spin.setSingleStep(0.5)
        self.pause_threshold_spin.setDecimals(1)
        audio_processing_layout.addRow("暂停阈值:", self.pause_threshold_spin)
        
        layout.addWidget(audio_processing_group)
        
        layout.addStretch()
        return tab
    
    def create_recognition_tab(self):
        """创建识别设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 语音识别设置
        recognition_group = QGroupBox("语音识别设置")
        recognition_layout = QFormLayout(recognition_group)
        
        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(["tiny", "base", "small", "medium", "large"])
        recognition_layout.addRow("模型大小:", self.model_size_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh", "en", "ja", "ko", "auto"])
        recognition_layout.addRow("识别语言:", self.language_combo)
        
        self.beam_size_spin = QSpinBox()
        self.beam_size_spin.setRange(1, 10)
        recognition_layout.addRow("束搜索大小:", self.beam_size_spin)
        
        layout.addWidget(recognition_group)
        
        # 热词设置
        hotword_group = QGroupBox("热词设置")
        hotword_layout = QFormLayout(hotword_group)
        
        self.hotword_edit = QLineEdit()
        hotword_layout.addRow("热词:", self.hotword_edit)
        
        self.hotword_prob_spin = QDoubleSpinBox()
        self.hotword_prob_spin.setRange(0.1, 1.0)
        self.hotword_prob_spin.setSingleStep(0.1)
        self.hotword_prob_spin.setDecimals(1)
        hotword_layout.addRow("热词概率:", self.hotword_prob_spin)
        
        layout.addWidget(hotword_group)
        
        layout.addStretch()
        return tab
    
    def create_translation_tab(self):
        """创建翻译设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 翻译服务设置
        translation_group = QGroupBox("翻译服务设置")
        translation_layout = QFormLayout(translation_group)
        
        self.translate_api_combo = QComboBox()
        self.translate_api_combo.addItems(["google", "baidu", "youdao", "deepl", "openai"])
        translation_layout.addRow("翻译API:", self.translate_api_combo)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        translation_layout.addRow("API密钥:", self.api_key_edit)
        
        self.api_secret_edit = QLineEdit()
        self.api_secret_edit.setEchoMode(QLineEdit.Password)
        translation_layout.addRow("API密钥:", self.api_secret_edit)
        
        layout.addWidget(translation_group)
        
        # 翻译参数设置
        translation_params_group = QGroupBox("翻译参数设置")
        translation_params_layout = QFormLayout(translation_params_group)
        
        self.translation_delay_spin = QSpinBox()
        self.translation_delay_spin.setRange(0, 5000)
        self.translation_delay_spin.setSingleStep(100)
        translation_params_layout.addRow("翻译延迟(ms):", self.translation_delay_spin)
        
        self.max_translation_length_spin = QSpinBox()
        self.max_translation_length_spin.setRange(100, 2000)
        self.max_translation_length_spin.setSingleStep(100)
        translation_params_layout.addRow("最大翻译长度:", self.max_translation_length_spin)
        
        layout.addWidget(translation_params_group)
        
        layout.addStretch()
        return tab
    
    def create_system_tab(self):
        """创建系统设置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # WebSocket设置
        websocket_group = QGroupBox("WebSocket设置")
        websocket_layout = QFormLayout(websocket_group)
        
        self.host_edit = QLineEdit()
        websocket_layout.addRow("主机地址:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        websocket_layout.addRow("端口:", self.port_spin)
        
        layout.addWidget(websocket_group)
        
        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("日志级别:", self.log_level_combo)
        
        self.log_file_edit = QLineEdit()
        log_layout.addRow("日志文件:", self.log_file_edit)
        
        layout.addWidget(log_group)
        
        # 其他设置
        other_group = QGroupBox("其他设置")
        other_layout = QFormLayout(other_group)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(1, 10)
        other_layout.addRow("最大重试次数:", self.max_retries_spin)
        
        self.request_timeout_spin = QSpinBox()
        self.request_timeout_spin.setRange(5, 60)
        other_layout.addRow("请求超时(秒):", self.request_timeout_spin)
        
        layout.addWidget(other_group)
        
        layout.addStretch()
        return tab
    
    def load_settings(self):
        """从args加载当前设置"""
        try:
            # 音频设置
            self.audio_source_combo.setCurrentText(getattr(self.args, 'audio_source', 'default'))
            # chunk_size是列表类型，需要特殊处理
            chunk_size_value = getattr(self.args, 'chunk_size', [3, 6, 3])
            if isinstance(chunk_size_value, list) and len(chunk_size_value) > 0:
                self.chunk_size_spin.setValue(chunk_size_value[0])  # 使用第一个值
            else:
                self.chunk_size_spin.setValue(1024)
            self.sample_rate_spin.setValue(getattr(self.args, 'sample_rate', 16000))
            self.silence_threshold_spin.setValue(getattr(self.args, 'silence_threshold', 0.5))
            self.energy_threshold_spin.setValue(getattr(self.args, 'energy_threshold', 300))
            self.pause_threshold_spin.setValue(getattr(self.args, 'pause_threshold', 0.8))
            self.chunk_interval_spin.setValue(getattr(self.args, 'chunk_interval', 1))
            
            # 识别设置
            self.model_size_combo.setCurrentText(getattr(self.args, 'model_size', 'base'))
            self.language_combo.setCurrentText(getattr(self.args, 'language', 'zh'))
            self.beam_size_spin.setValue(getattr(self.args, 'beam_size', 5))
            self.hotword_edit.setText(getattr(self.args, 'hotword', ''))
            self.hotword_prob_spin.setValue(getattr(self.args, 'hotword_probability', 0.5))
            
            # 翻译设置
            self.translate_api_combo.setCurrentText(getattr(self.args, 'translate_api', 'google'))
            self.api_key_edit.setText(getattr(self.args, 'api_key', ''))
            self.api_secret_edit.setText(getattr(self.args, 'api_secret', ''))
            self.translation_delay_spin.setValue(getattr(self.args, 'translation_delay', 1000))
            self.max_translation_length_spin.setValue(getattr(self.args, 'max_translation_length', 500))
            
            # 系统设置
            self.host_edit.setText(getattr(self.args, 'host', '127.0.0.1'))
            self.port_spin.setValue(getattr(self.args, 'port', 8765))
            self.log_level_combo.setCurrentText(getattr(self.args, 'log_level', 'INFO'))
            self.log_file_edit.setText(getattr(self.args, 'log_file', 'client.log'))
            self.max_retries_spin.setValue(getattr(self.args, 'max_retries', 3))
            self.request_timeout_spin.setValue(getattr(self.args, 'request_timeout', 30))
            
        except Exception as e:
            logger.error(f"加载设置时发生错误: {e}")
            QMessageBox.warning(self, "加载错误", f"加载设置时发生错误: {e}")

    def get_current_settings(self):
        """获取当前对话框中的设置"""
        return self.current_settings

    def apply_settings(self):
        """应用当前设置"""
        try:
            # 收集所有设置
            settings = {}
            
            # 音频设置
            settings['audio_source'] = self.audio_source_combo.currentText()
            settings['chunk_size'] = [self.chunk_size_spin.value(), 6, 3]  # 保持为列表格式，使用默认值填充其他元素
            settings['chunk_interval'] = self.chunk_interval_spin.value()
            settings['sample_rate'] = self.sample_rate_spin.value()
            settings['silence_threshold'] = self.silence_threshold_spin.value()
            settings['energy_threshold'] = self.energy_threshold_spin.value()
            settings['pause_threshold'] = self.pause_threshold_spin.value()
            
            # 识别设置
            settings['model_size'] = self.model_size_combo.currentText()
            settings['language'] = self.language_combo.currentText()
            settings['beam_size'] = self.beam_size_spin.value()
            settings['hotword'] = self.hotword_edit.text()
            settings['hotword_probability'] = self.hotword_prob_spin.value()
            
            # 翻译设置
            settings['translate_api'] = self.translate_api_combo.currentText()
            settings['api_key'] = self.api_key_edit.text()
            settings['api_secret'] = self.api_secret_edit.text()
            settings['translation_delay'] = self.translation_delay_spin.value()
            settings['max_translation_length'] = self.max_translation_length_spin.value()
            
            # 系统设置
            settings['host'] = self.host_edit.text()
            settings['port'] = self.port_spin.value()
            settings['log_level'] = self.log_level_combo.currentText()
            settings['log_file'] = self.log_file_edit.text()
            settings['max_retries'] = self.max_retries_spin.value()
            settings['request_timeout'] = self.request_timeout_spin.value()
            
            # 验证设置
            if not self.validate_settings(settings):
                return
            
            # 保存当前设置
            self.current_settings = settings
            
            QMessageBox.information(self, "设置应用", "设置已成功应用！")
            
        except Exception as e:
            logger.error(f"应用设置时发生错误: {e}")
            QMessageBox.critical(self, "应用错误", f"应用设置时发生错误: {e}")

    def validate_settings(self, settings):
        """验证设置的有效性"""
        # 检查端口范围
        if not (1000 <= settings['port'] <= 65535):
            QMessageBox.warning(self, "验证错误", "端口号必须在1000-65535范围内")
            return False
        
        # 检查采样率
        if settings['sample_rate'] not in [8000, 16000, 32000, 44100, 48000]:
            QMessageBox.warning(self, "验证错误", "采样率必须是标准值: 8000, 16000, 32000, 44100, 48000")
            return False
        
        # 检查块大小
        if settings['chunk_size'][0] % 256 != 0:  # 检查列表中的第一个值
            QMessageBox.warning(self, "验证错误", "块大小必须是256的倍数")
            return False
        
        return True

    def reset_to_default(self):
        """重置为默认设置"""
        reply = QMessageBox.question(self, "确认重置", 
                                   "确定要重置所有设置为默认值吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 重置所有控件到默认值
            self.audio_source_combo.setCurrentText("default")
            self.chunk_size_spin.setValue(1024)
            self.chunk_interval_spin.setValue(1)
            self.sample_rate_spin.setValue(16000)
            self.silence_threshold_spin.setValue(0.5)
            self.energy_threshold_spin.setValue(300)
            self.pause_threshold_spin.setValue(0.8)
            
            self.model_size_combo.setCurrentText("base")
            self.language_combo.setCurrentText("zh")
            self.beam_size_spin.setValue(5)
            self.hotword_edit.setText("")
            self.hotword_prob_spin.setValue(0.5)
            
            self.translate_api_combo.setCurrentText("google")
            self.api_key_edit.setText("")
            self.api_secret_edit.setText("")
            self.translation_delay_spin.setValue(1000)
            self.max_translation_length_spin.setValue(500)
            
            self.host_edit.setText("127.0.0.1")
            self.port_spin.setValue(8765)
            self.log_level_combo.setCurrentText("INFO")
            self.log_file_edit.setText("client.log")
            self.max_retries_spin.setValue(3)
            self.request_timeout_spin.setValue(30)
            
            QMessageBox.information(self, "重置成功", "所有设置已重置为默认值！")
    
    def accept(self):
        """确定按钮处理"""
        try:
            # 收集所有设置
            settings = {}
            
            # 音频设置
            settings['audio_source'] = self.audio_source_combo.currentText()
            settings['chunk_size'] = [self.chunk_size_spin.value(), 6, 3]  # 保持为列表格式，使用默认值填充其他元素
            settings['chunk_interval'] = self.chunk_interval_spin.value()
            settings['sample_rate'] = self.sample_rate_spin.value()
            settings['silence_threshold'] = self.silence_threshold_spin.value()
            settings['energy_threshold'] = self.energy_threshold_spin.value()
            settings['pause_threshold'] = self.pause_threshold_spin.value()
            
            # 识别设置
            settings['model_size'] = self.model_size_combo.currentText()
            settings['language'] = self.language_combo.currentText()
            settings['beam_size'] = self.beam_size_spin.value()
            settings['hotword'] = self.hotword_edit.text()
            settings['hotword_probability'] = self.hotword_prob_spin.value()
            
            # 翻译设置
            settings['translate_api'] = self.translate_api_combo.currentText()
            settings['api_key'] = self.api_key_edit.text()
            settings['api_secret'] = self.api_secret_edit.text()
            settings['translation_delay'] = self.translation_delay_spin.value()
            settings['max_translation_length'] = self.max_translation_length_spin.value()
            
            # 系统设置
            settings['host'] = self.host_edit.text()
            settings['port'] = self.port_spin.value()
            settings['log_level'] = self.log_level_combo.currentText()
            settings['log_file'] = self.log_file_edit.text()
            settings['max_retries'] = self.max_retries_spin.value()
            settings['request_timeout'] = self.request_timeout_spin.value()
            
            # 验证设置
            if not self.validate_settings(settings):
                return
            
            # 保存当前设置
            self.current_settings = settings
            
            super().accept()
            
        except Exception as e:
            logger.error(f"确定按钮处理时发生错误: {e}")
            QMessageBox.critical(self, "处理错误", f"确定按钮处理时发生错误: {e}")

if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    class MockArgs:
        def __init__(self):
            self.audio_source = "default"
            self.chunk_size = 1024
            self.sample_rate = 16000
            self.silence_threshold = 0.5
            self.energy_threshold = 300
            self.pause_threshold = 0.8
            self.model_size = "base"
            self.language = "zh"
            self.beam_size = 5
            self.hotword = ""
            self.hotword_probability = 0.5
            self.translate_api = "google"
            self.api_key = ""
            self.api_secret = ""
            self.translation_delay = 1000
            self.max_translation_length = 500
            self.host = "127.0.0.1"
            self.port = 8765
            self.log_level = "INFO"
            self.log_file = "client.log"
            self.max_retries = 3
            self.request_timeout = 30
    
    app = QApplication(sys.argv)
    args = MockArgs()
    dialog = SettingsDialog(args)
    dialog.show()
    sys.exit(app.exec_())
