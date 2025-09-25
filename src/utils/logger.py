"""
日志工具模块
Logger Utilities Module
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置类"""
    
    @staticmethod
    def setupLogger(name: str = "SubtitleApp", 
                   level: str = "INFO",
                   logFile: Optional[str] = None,
                   enableConsole: bool = True) -> logging.Logger:
        """
        设置并配置日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            logFile: 日志文件路径，None则不写入文件
            enableConsole: 是否启用控制台输出
            
        Returns:
            配置好的日志记录器
        """
        # 获取日志级别
        logLevel = getattr(logging, level.upper(), logging.INFO)
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(logLevel)
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 设置日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # 控制台处理器
        if enableConsole:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setLevel(logLevel)
            consoleHandler.setFormatter(formatter)
            logger.addHandler(consoleHandler)
        
        # 文件处理器
        if logFile:
            try:
                # 确保日志目录存在
                logDir = os.path.dirname(logFile)
                if logDir and not os.path.exists(logDir):
                    os.makedirs(logDir, exist_ok=True)
                
                fileHandler = logging.FileHandler(
                    logFile, encoding="utf-8", mode='a'
                )
                fileHandler.setLevel(logLevel)
                fileHandler.setFormatter(formatter)
                logger.addHandler(fileHandler)
                
            except Exception as e:
                logger.warning(f"无法创建日志文件处理器: {e}")
        
        logger.info(f"日志记录器 '{name}' 已配置，级别: {level}")
        return logger
    
    @staticmethod
    def getRotatingFileLogger(name: str,
                            logFile: str,
                            maxBytes: int = 10 * 1024 * 1024,  # 10MB
                            backupCount: int = 5) -> logging.Logger:
        """
        创建带文件轮转的日志记录器
        
        Args:
            name: 日志记录器名称
            logFile: 日志文件路径
            maxBytes: 单个日志文件最大字节数
            backupCount: 备份文件数量
            
        Returns:
            配置好的日志记录器
        """
        from logging.handlers import RotatingFileHandler
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建轮转文件处理器
        try:
            logDir = os.path.dirname(logFile)
            if logDir and not os.path.exists(logDir):
                os.makedirs(logDir, exist_ok=True)
            
            rotatingHandler = RotatingFileHandler(
                logFile, maxBytes=maxBytes, backupCount=backupCount,
                encoding="utf-8"
            )
            
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            rotatingHandler.setFormatter(formatter)
            logger.addHandler(rotatingHandler)
            
            # 添加控制台处理器
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(formatter)
            logger.addHandler(consoleHandler)
            
        except Exception as e:
            print(f"创建轮转日志文件失败: {e}")
            # 回退到基本配置
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(name)
        
        return logger


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.startTimes = {}
    
    def startTimer(self, operationName: str):
        """开始计时"""
        self.startTimes[operationName] = datetime.now()
        self.logger.debug(f"开始计时: {operationName}")
    
    def endTimer(self, operationName: str, logLevel: int = logging.INFO):
        """结束计时并记录"""
        if operationName in self.startTimes:
            endTime = datetime.now()
            duration = endTime - self.startTimes[operationName]
            self.logger.log(
                logLevel, 
                f"操作完成: {operationName}, 耗时: {duration.total_seconds():.3f}秒"
            )
            del self.startTimes[operationName]
        else:
            self.logger.warning(f"未找到计时器: {operationName}")
    
    def logMemoryUsage(self):
        """记录内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memoryInfo = process.memory_info()
            self.logger.info(
                f"内存使用: RSS={memoryInfo.rss / 1024 / 1024:.2f}MB, "
                f"VMS={memoryInfo.vms / 1024 / 1024:.2f}MB"
            )
        except ImportError:
            self.logger.debug("psutil库未安装，无法记录内存使用")
        except Exception as e:
            self.logger.warning(f"记录内存使用失败: {e}")


# 便捷函数
def getLogger(name: str = "SubtitleApp", level: str = "INFO") -> logging.Logger:
    """获取配置好的日志记录器"""
    return LoggerConfig.setupLogger(name, level)