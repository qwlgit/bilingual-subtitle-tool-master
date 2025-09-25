#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能语音识别翻译系统 - 主入口文件
Intelligent Speech Recognition and Translation System - Main Entry Point

这是重构后的主入口文件，负责应用程序的初始化和启动。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入配置模块
from src.config.app_config import parse_arguments, setup_logging, validate_arguments

# 导入工具模块
from src.utils.logger import getLogger


def main():
    """主函数"""
    try:
        # 解析和验证命令行参数
        args = parse_arguments()
        args = validate_arguments(args)
        
        # 设置日志
        logger = setup_logging(args)
        logger.info("="*50)
        logger.info("启动智能语音识别翻译系统 v2.0")
        logger.info("="*50)
        
        # 尝试导入PyQt5
        try:
            from PyQt5.QtWidgets import QApplication
            
            # 导入UI模块
            from src.ui.main_window import MainWindow
            
            # 导入核心模块
            from src.core.speech_recognition import SpeechRecognitionWorker
            
            # 创建Qt应用
            app = QApplication(sys.argv)
            app.setApplicationName("智能语音识别翻译系统")
            app.setApplicationVersion("2.0.0")
            
            # 创建主窗口
            mainWindow = MainWindow(args, SpeechRecognitionWorker)
            mainWindow.show()
            
            logger.info("应用程序启动成功")
            
            # 启动事件循环
            exitCode = app.exec_()
            
            logger.info("应用程序退出，退出码: %d", exitCode)
            return exitCode
            
        except ImportError as e:
            logger.error(f"PyQt5导入失败: {e}")
            print(f"错误: PyQt5库未安装或导入失败: {e}")
            print("请安装PyQt5: pip install PyQt5")
            return 1
            
    except KeyboardInterrupt:
        print("\n用户中断程序")
        return 1
    except Exception as e:
        print(f"启动错误: {e}")
        try:
            import logging
            logging.error(f"启动错误: {e}", exc_info=True)
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())