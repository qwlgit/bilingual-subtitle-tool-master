"""
配置参数解析模块
将参数解析逻辑从main.py中拆分出来
"""

import argparse
import logging
import os


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    
    # WebSocket服务器参数
    parser.add_argument("--host", type=str, default="localhost", required=False, help="host ip, localhost, 0.0.0.0")
    parser.add_argument("--port", type=int, default=10095, required=False, help="grpc server port")
    
    # 音频处理参数
    parser.add_argument("--chunk_size", type=str, default="3, 6, 3", help="chunk")
    parser.add_argument("--encoder_chunk_look_back", type=int, default=15, help="chunk")
    parser.add_argument("--decoder_chunk_look_back", type=int, default=0, help="chunk")
    parser.add_argument("--chunk_interval", type=int, default=1, help="chunk")
    parser.add_argument("--audio_fs", type=int, default=16000, help="audio_fs (目标采样率)")
    
    # 热词参数
    parser.add_argument("--hotword", type=str, default="歌尔 30", help="hotword file path, one hotword perline (e.g.:阿里巴巴 20)")
    
    # 系统参数
    parser.add_argument("--output_dir", type=str, default=None, help="output_dir")
    parser.add_argument("--ssl", type=int, default=1, help="1 for ssl connect, 0 for no ssl")
    parser.add_argument("--use_itn", type=int, default=1, help="1 for using itn, 0 for not itn")
    parser.add_argument("--mode", type=str, default="2pass", help="online, 2pass")
    
    # 翻译参数
    parser.add_argument("--translate_api", type=str, default="http://localhost:8000/translate", help="Translation API endpoint")
    parser.add_argument("--timeout_seconds", type=int, default=4, help="Seconds to wait before translating incomplete text")
    
    # 音频设备参数
    parser.add_argument("--audio_source", type=str, default="microphone", choices=["microphone", "system_audio"], help="Audio source: microphone or system_audio")
    
    # 日志参数
    parser.add_argument("--log_level", type=str, default="INFO", help="Log level: DEBUG, INFO, WARNING, ERROR")
    
    # 解析参数
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
            logging.FileHandler("client.log", encoding="utf-8", mode='a')  # 使用追加模式
        ],
        force=True  # 强制重新配置
    )
    
    logger = logging.getLogger("Client")
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
