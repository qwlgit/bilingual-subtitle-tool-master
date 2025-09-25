"""
通用工具函数模块
Common Utilities Module
"""

import os
import json
import datetime
from typing import Any, Dict, List, Optional, Union


def ensureDirectory(dirPath: str) -> bool:
    """
    确保目录存在，不存在则创建
    
    Args:
        dirPath: 目录路径
        
    Returns:
        目录是否存在或创建成功
    """
    try:
        if not os.path.exists(dirPath):
            os.makedirs(dirPath, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败 {dirPath}: {e}")
        return False


def safeJsonLoad(filePath: str, default: Any = None) -> Any:
    """
    安全加载JSON文件
    
    Args:
        filePath: JSON文件路径
        default: 加载失败时的默认值
        
    Returns:
        JSON数据或默认值
    """
    try:
        if os.path.exists(filePath):
            with open(filePath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败 {filePath}: {e}")
    return default


def safeJsonSave(data: Any, filePath: str, indent: int = 2) -> bool:
    """
    安全保存JSON文件
    
    Args:
        data: 要保存的数据
        filePath: 文件路径
        indent: 缩进空格数
        
    Returns:
        保存是否成功
    """
    try:
        # 确保目录存在
        dirPath = os.path.dirname(filePath)
        if dirPath:
            ensureDirectory(dirPath)
        
        with open(filePath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        print(f"保存JSON文件失败 {filePath}: {e}")
        return False


def formatBytes(byteCount: int) -> str:
    """
    格式化字节数为人类可读格式
    
    Args:
        byteCount: 字节数
        
    Returns:
        格式化后的字符串
    """
    size = float(byteCount)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def formatDuration(seconds: float) -> str:
    """
    格式化时长为人类可读格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的时长字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.1f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}小时{minutes}分{secs:.1f}秒"


def getCurrentTimestamp() -> str:
    """
    获取当前时间戳字符串
    
    Returns:
        格式化的时间戳
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def getFileTimestamp() -> str:
    """
    获取适合文件名的时间戳
    
    Returns:
        适合文件名的时间戳
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def clampValue(value: Union[int, float], minVal: Union[int, float], maxVal: Union[int, float]) -> Union[int, float]:
    """
    将值限制在指定范围内
    
    Args:
        value: 要限制的值
        minVal: 最小值
        maxVal: 最大值
        
    Returns:
        限制后的值
    """
    return max(minVal, min(value, maxVal))


def splitList(lst: List[Any], chunkSize: int) -> List[List[Any]]:
    """
    将列表分割为指定大小的块
    
    Args:
        lst: 要分割的列表
        chunkSize: 每块的大小
        
    Returns:
        分割后的列表
    """
    return [lst[i:i + chunkSize] for i in range(0, len(lst), chunkSize)]


def filterDict(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """
    过滤字典，只保留指定的键
    
    Args:
        data: 原始字典
        keys: 要保留的键列表
        
    Returns:
        过滤后的字典
    """
    return {k: v for k, v in data.items() if k in keys}


def mergeDict(dict1: Dict[str, Any], dict2: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
    """
    合并两个字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        overwrite: 是否覆盖重复的键
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    if overwrite:
        result.update(dict2)
    else:
        for k, v in dict2.items():
            if k not in result:
                result[k] = v
    return result


class SingletonMeta(type):
    """单例模式元类"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, configFile: str):
        self.configFile = configFile
        self.config = self.loadConfig()
    
    def loadConfig(self) -> Dict[str, Any]:
        """加载配置"""
        return safeJsonLoad(self.configFile, {})
    
    def saveConfig(self) -> bool:
        """保存配置"""
        return safeJsonSave(self.config, self.configFile)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def update(self, newConfig: Dict[str, Any]) -> None:
        """更新配置"""
        self.config = mergeDict(self.config, newConfig)


def debounce(waitTime: float):
    """
    防抖装饰器
    
    Args:
        waitTime: 等待时间（秒）
    """
    def decorator(func):
        import threading
        timer = None
        
        def wrapper(*args, **kwargs):
            nonlocal timer
            if timer:
                timer.cancel()
            timer = threading.Timer(waitTime, func, args, kwargs)
            timer.start()
        
        return wrapper
    return decorator


def retry(maxAttempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        maxAttempts: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 要捕获的异常类型
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(maxAttempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == maxAttempts - 1:
                        raise e
                    import time
                    time.sleep(delay)
            return None
        return wrapper
    return decorator