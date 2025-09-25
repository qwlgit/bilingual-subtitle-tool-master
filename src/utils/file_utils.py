"""
文件操作工具模块
File Utilities Module
"""

import os
import json
import csv
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器类"""
    
    def __init__(self, baseDirectory: str = "."):
        self.baseDirectory = os.path.abspath(baseDirectory)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保基础目录存在
        self.ensureDirectory(self.baseDirectory)
    
    def ensureDirectory(self, dirPath: str) -> bool:
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
                self.logger.info(f"创建目录: {dirPath}")
            return True
        except Exception as e:
            self.logger.error(f"创建目录失败 {dirPath}: {e}")
            return False
    
    def getRelativePath(self, filePath: str) -> str:
        """
        获取相对于基础目录的相对路径
        
        Args:
            filePath: 文件路径
            
        Returns:
            相对路径
        """
        return os.path.relpath(filePath, self.baseDirectory)
    
    def getAbsolutePath(self, relativePath: str) -> str:
        """
        获取绝对路径
        
        Args:
            relativePath: 相对路径
            
        Returns:
            绝对路径
        """
        return os.path.join(self.baseDirectory, relativePath)
    
    def fileExists(self, filePath: str) -> bool:
        """检查文件是否存在"""
        fullPath = self.getAbsolutePath(filePath)
        return os.path.isfile(fullPath)
    
    def directoryExists(self, dirPath: str) -> bool:
        """检查目录是否存在"""
        fullPath = self.getAbsolutePath(dirPath)
        return os.path.isdir(fullPath)
    
    def deleteFile(self, filePath: str) -> bool:
        """
        删除文件
        
        Args:
            filePath: 文件路径
            
        Returns:
            删除是否成功
        """
        try:
            fullPath = self.getAbsolutePath(filePath)
            if os.path.exists(fullPath):
                os.remove(fullPath)
                self.logger.info(f"删除文件: {fullPath}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"删除文件失败 {filePath}: {e}")
            return False
    
    def copyFile(self, sourcePath: str, destPath: str) -> bool:
        """
        复制文件
        
        Args:
            sourcePath: 源文件路径
            destPath: 目标文件路径
            
        Returns:
            复制是否成功
        """
        import shutil
        try:
            sourceFullPath = self.getAbsolutePath(sourcePath)
            destFullPath = self.getAbsolutePath(destPath)
            
            # 确保目标目录存在
            destDir = os.path.dirname(destFullPath)
            self.ensureDirectory(destDir)
            
            shutil.copy2(sourceFullPath, destFullPath)
            self.logger.info(f"复制文件: {sourceFullPath} -> {destFullPath}")
            return True
        except Exception as e:
            self.logger.error(f"复制文件失败 {sourcePath} -> {destPath}: {e}")
            return False
    
    def getFileSize(self, filePath: str) -> int:
        """
        获取文件大小
        
        Args:
            filePath: 文件路径
            
        Returns:
            文件大小（字节），-1表示文件不存在
        """
        try:
            fullPath = self.getAbsolutePath(filePath)
            if os.path.exists(fullPath):
                return os.path.getsize(fullPath)
            return -1
        except Exception as e:
            self.logger.error(f"获取文件大小失败 {filePath}: {e}")
            return -1
    
    def getFileModifiedTime(self, filePath: str) -> Optional[datetime]:
        """
        获取文件修改时间
        
        Args:
            filePath: 文件路径
            
        Returns:
            文件修改时间，None表示文件不存在
        """
        try:
            fullPath = self.getAbsolutePath(filePath)
            if os.path.exists(fullPath):
                timestamp = os.path.getmtime(fullPath)
                return datetime.fromtimestamp(timestamp)
            return None
        except Exception as e:
            self.logger.error(f"获取文件修改时间失败 {filePath}: {e}")
            return None


class JsonFileHandler:
    """JSON文件处理器"""
    
    def __init__(self, fileManager: FileManager):
        self.fileManager = fileManager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def saveJson(self, data: Any, filePath: str, indent: int = 2) -> bool:
        """
        保存JSON文件
        
        Args:
            data: 要保存的数据
            filePath: 文件路径
            indent: 缩进空格数
            
        Returns:
            保存是否成功
        """
        try:
            fullPath = self.fileManager.getAbsolutePath(filePath)
            
            # 确保目录存在
            dirPath = os.path.dirname(fullPath)
            self.fileManager.ensureDirectory(dirPath)
            
            with open(fullPath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            
            self.logger.info(f"保存JSON文件: {filePath}")
            return True
        except Exception as e:
            self.logger.error(f"保存JSON文件失败 {filePath}: {e}")
            return False
    
    def loadJson(self, filePath: str, default: Any = None) -> Any:
        """
        加载JSON文件
        
        Args:
            filePath: 文件路径
            default: 加载失败时的默认值
            
        Returns:
            JSON数据或默认值
        """
        try:
            fullPath = self.fileManager.getAbsolutePath(filePath)
            if os.path.exists(fullPath):
                with open(fullPath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"加载JSON文件: {filePath}")
                return data
        except Exception as e:
            self.logger.error(f"加载JSON文件失败 {filePath}: {e}")
        return default
    
    def updateJson(self, filePath: str, updates: Dict[str, Any]) -> bool:
        """
        更新JSON文件中的数据
        
        Args:
            filePath: 文件路径
            updates: 要更新的数据
            
        Returns:
            更新是否成功
        """
        try:
            data = self.loadJson(filePath, {})
            if isinstance(data, dict):
                data.update(updates)
                return self.saveJson(data, filePath)
            else:
                self.logger.error(f"JSON文件不是字典格式，无法更新: {filePath}")
                return False
        except Exception as e:
            self.logger.error(f"更新JSON文件失败 {filePath}: {e}")
            return False


class CsvFileHandler:
    """CSV文件处理器"""
    
    def __init__(self, fileManager: FileManager):
        self.fileManager = fileManager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def saveCsv(self, data: List[Dict[str, Any]], filePath: str, 
               fieldnames: Optional[List[str]] = None) -> bool:
        """
        保存CSV文件
        
        Args:
            data: 要保存的数据列表
            filePath: 文件路径
            fieldnames: 字段名列表
            
        Returns:
            保存是否成功
        """
        try:
            if not data:
                self.logger.warning(f"数据为空，无法保存CSV文件: {filePath}")
                return False
            
            fullPath = self.fileManager.getAbsolutePath(filePath)
            
            # 确保目录存在
            dirPath = os.path.dirname(fullPath)
            self.fileManager.ensureDirectory(dirPath)
            
            # 如果没有指定字段名，使用第一行数据的键
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
            with open(fullPath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"保存CSV文件: {filePath} ({len(data)} 行)")
            return True
        except Exception as e:
            self.logger.error(f"保存CSV文件失败 {filePath}: {e}")
            return False
    
    def loadCsv(self, filePath: str) -> List[Dict[str, Any]]:
        """
        加载CSV文件
        
        Args:
            filePath: 文件路径
            
        Returns:
            CSV数据列表
        """
        try:
            fullPath = self.fileManager.getAbsolutePath(filePath)
            if os.path.exists(fullPath):
                with open(fullPath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                self.logger.info(f"加载CSV文件: {filePath} ({len(data)} 行)")
                return data
        except Exception as e:
            self.logger.error(f"加载CSV文件失败 {filePath}: {e}")
        return []


class SubtitleFileHandler:
    """字幕文件处理器"""
    
    def __init__(self, fileManager: FileManager):
        self.fileManager = fileManager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def exportSubtitles(self, subtitlePairs: List[Any], filePath: str, 
                       format: str = "txt") -> bool:
        """
        导出字幕文件
        
        Args:
            subtitlePairs: 字幕对列表
            filePath: 文件路径
            format: 导出格式 (txt, srt, vtt, csv)
            
        Returns:
            导出是否成功
        """
        try:
            fullPath = self.fileManager.getAbsolutePath(filePath)
            
            # 确保目录存在
            dirPath = os.path.dirname(fullPath)
            self.fileManager.ensureDirectory(dirPath)
            
            if format.lower() == "txt":
                return self._exportAsTxt(subtitlePairs, fullPath)
            elif format.lower() == "srt":
                return self._exportAsSrt(subtitlePairs, fullPath)
            elif format.lower() == "vtt":
                return self._exportAsVtt(subtitlePairs, fullPath)
            elif format.lower() == "csv":
                return self._exportAsCsv(subtitlePairs, fullPath)
            else:
                self.logger.error(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            self.logger.error(f"导出字幕文件失败 {filePath}: {e}")
            return False
    
    def _exportAsTxt(self, subtitlePairs: List[Any], fullPath: str) -> bool:
        """导出为TXT格式"""
        with open(fullPath, 'w', encoding='utf-8') as f:
            f.write("=== 智能语音识别翻译系统 字幕导出 ===\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"字幕对数量: {len(subtitlePairs)}\n\n")
            
            for i, pair in enumerate(subtitlePairs, 1):
                f.write(f"[{i:03d}] {getattr(pair, 'chinese', {}).get('timestamp', '')}\n")
                f.write(f"中文: {getattr(pair, 'chinese', {}).get('text', '')}\n")
                f.write(f"英文: {getattr(pair, 'english', {}).get('text', '')}\n\n")
        
        self.logger.info(f"导出TXT字幕文件: {fullPath}")
        return True
    
    def _exportAsSrt(self, subtitlePairs: List[Any], fullPath: str) -> bool:
        """导出为SRT格式"""
        with open(fullPath, 'w', encoding='utf-8') as f:
            for i, pair in enumerate(subtitlePairs, 1):
                f.write(f"{i}\n")
                f.write("00:00:00,000 --> 00:00:05,000\n")
                f.write(f"{getattr(pair, 'chinese', {}).get('text', '')}\n")
                f.write(f"{getattr(pair, 'english', {}).get('text', '')}\n\n")
        
        self.logger.info(f"导出SRT字幕文件: {fullPath}")
        return True
    
    def _exportAsVtt(self, subtitlePairs: List[Any], fullPath: str) -> bool:
        """导出为VTT格式"""
        with open(fullPath, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for pair in subtitlePairs:
                f.write("00:00:00.000 --> 00:00:05.000\n")
                f.write(f"{getattr(pair, 'chinese', {}).get('text', '')}\n")
                f.write(f"{getattr(pair, 'english', {}).get('text', '')}\n\n")
        
        self.logger.info(f"导出VTT字幕文件: {fullPath}")
        return True
    
    def _exportAsCsv(self, subtitlePairs: List[Any], fullPath: str) -> bool:
        """导出为CSV格式"""
        data = []
        for i, pair in enumerate(subtitlePairs, 1):
            data.append({
                "序号": i,
                "时间戳": getattr(pair, 'chinese', {}).get('timestamp', ''),
                "中文": getattr(pair, 'chinese', {}).get('text', ''),
                "英文": getattr(pair, 'english', {}).get('text', ''),
                "配对ID": getattr(pair, 'pair_id', '')
            })
        
        csvHandler = CsvFileHandler(self.fileManager)
        return csvHandler.saveCsv(data, os.path.basename(fullPath))


class ConfigFileManager:
    """配置文件管理器"""
    
    def __init__(self, fileManager: FileManager, configFileName: str = "config.json"):
        self.fileManager = fileManager
        self.configFileName = configFileName
        self.jsonHandler = JsonFileHandler(fileManager)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 默认配置
        self.defaultConfig = {
            "ui": {
                "font_size": 24,
                "opacity": 0.95,
                "theme": "tech"
            },
            "audio": {
                "sample_rate": 16000,
                "channels": 2,
                "device_index": None
            },
            "translation": {
                "api_endpoint": "http://localhost:8000/translate",
                "timeout": 2,
                "cache_enabled": True
            },
            "subtitle": {
                "display_time": 5000,
                "auto_export": False,
                "export_format": "txt"
            }
        }
    
    def loadConfig(self) -> Dict[str, Any]:
        """加载配置"""
        config = self.jsonHandler.loadJson(self.configFileName, self.defaultConfig.copy())
        
        # 确保所有默认键都存在
        for key, value in self.defaultConfig.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict):
                for subKey, subValue in value.items():
                    if subKey not in config[key]:
                        config[key][subKey] = subValue
        
        return config
    
    def saveConfig(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        return self.jsonHandler.saveJson(config, self.configFileName)
    
    def updateConfig(self, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        return self.jsonHandler.updateJson(self.configFileName, updates)
    
    def resetConfig(self) -> bool:
        """重置为默认配置"""
        return self.saveConfig(self.defaultConfig.copy())


# 便捷函数
def getProjectFileManager(projectRoot: str = ".") -> FileManager:
    """获取项目文件管理器"""
    return FileManager(projectRoot)


def exportSubtitlesTo(subtitlePairs: List[Any], outputPath: str, 
                     format: str = "txt", projectRoot: str = ".") -> bool:
    """
    导出字幕到指定路径的便捷函数
    
    Args:
        subtitlePairs: 字幕对列表
        outputPath: 输出路径
        format: 导出格式
        projectRoot: 项目根目录
        
    Returns:
        导出是否成功
    """
    fileManager = getProjectFileManager(projectRoot)
    subtitleHandler = SubtitleFileHandler(fileManager)
    return subtitleHandler.exportSubtitles(subtitlePairs, outputPath, format)