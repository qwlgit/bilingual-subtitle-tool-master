"""
应用配置模块
Application Configuration Module
"""

import argparse
import logging
import os
from .constants import (
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_AUDIO_FS, DEFAULT_CHUNK_SIZE,
    DEFAULT_LOG_LEVEL, DEFAULT_TIMEOUT_SECONDS, SUPPORTED_AUDIO_SOURCES
)


class AppConfig:
    """应用配置类"""
    
    def __init__(self):
        self.host = DEFAULT_HOST
        self.port = DEFAULT_PORT
        self.audio_fs = DEFAULT_AUDIO_FS
        self.chunk_size = DEFAULT_CHUNK_SIZE
        self.log_level = DEFAULT_LOG_LEVEL
        self.timeout_seconds = DEFAULT_TIMEOUT_SECONDS
        self.audio_source = "microphone"
        self.translate_api = "http://localhost:8000/translate"
        
        # WebSocket相关
        self.ssl = 1
        self.use_itn = 1
        self.mode = "2pass"
        
        # 音频处理相关
        self.encoder_chunk_look_back = 15
        self.decoder_chunk_look_back = 0
        self.chunk_interval = 1
        
        # 热词和输出
        self.hotword = "歌尔 30"
        self.output_dir = None


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="智能语音识别翻译系统")
    
    # WebSocket服务器参数
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, 
                       help="服务器地址")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, 
                       help="服务器端口")
    
    # 音频处理参数
    parser.add_argument("--chunk_size", type=str, default=DEFAULT_CHUNK_SIZE, 
                       help="音频块大小")
    parser.add_argument("--encoder_chunk_look_back", type=int, default=15, 
                       help="编码器回看块数")
    parser.add_argument("--decoder_chunk_look_back", type=int, default=0, 
                       help="解码器回看块数")
    parser.add_argument("--chunk_interval", type=int, default=1, 
                       help="块间隔")
    parser.add_argument("--audio_fs", type=int, default=DEFAULT_AUDIO_FS, 
                       help="目标采样率")
    
    # 热词参数
    parser.add_argument("--hotword", type=str, default="歌尔 30", 
                       help="热词配置")
    
    # 系统参数
    parser.add_argument("--output_dir", type=str, default=None, 
                       help="输出目录")
    parser.add_argument("--ssl", type=int, default=1, 
                       help="是否使用SSL连接")
    parser.add_argument("--use_itn", type=int, default=1, 
                       help="是否使用ITN")
    parser.add_argument("--mode", type=str, default="2pass", 
                       help="识别模式")
    
    # 翻译参数
    parser.add_argument("--translate_api", type=str, 
                       default="http://localhost:8000/translate", 
                       help="翻译API地址")
    parser.add_argument("--timeout_seconds", type=int, 
                       default=DEFAULT_TIMEOUT_SECONDS, 
                       help="翻译超时秒数")
    
    # 音频设备参数
    parser.add_argument("--audio_source", type=str, default="microphone", 
                       choices=SUPPORTED_AUDIO_SOURCES, 
                       help="音频源类型")
    
    # 日志参数
    parser.add_argument("--log_level", type=str, default=DEFAULT_LOG_LEVEL, 
                       help="日志级别")
    
    args = parser.parse_args()
    
    # 后处理参数
    args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
    
    return args


def setup_logging(args):
    """设置日志配置"""
    log_level = getattr(logging, args.log_level.upper())
    
    # 清除现有的处理器以避免冲突
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 重新配置日志
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("client.log", encoding="utf-8", mode='a')
        ],
        force=True
    )
    
    logger = logging.getLogger("SubtitleApp")
    logger.setLevel(log_level)
    logger.info("启动参数: %s", args)
    return logger


def validate_arguments(args):
    """验证参数有效性"""
    # 检查输出目录
    if args.output_dir is not None:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
    
    # 检查热词文件
    if args.hotword.strip() != "" and not os.path.exists(args.hotword):
        logging.warning(f"热词文件不存在: {args.hotword}")
    
    return args