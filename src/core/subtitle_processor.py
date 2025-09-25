"""
字幕处理核心模块
Subtitle Processing Core Module
"""

import logging
import time
from typing import List, Optional, Tuple, Dict, Any
from collections import deque
from dataclasses import dataclass

from ..models.subtitle_models import SubtitlePair, SubtitleText
from ..services.text_service import TextProcessingService

logger = logging.getLogger(__name__)


@dataclass
class SubtitleSegment:
    """字幕片段"""
    text: str
    language: str
    timestamp: float
    isComplete: bool = False
    isIncremental: bool = False


class SubtitleProcessor:
    """字幕处理器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.textService = TextProcessingService()
        self.subtitlePairs: List[SubtitlePair] = []
        self.currentChineseText = ""
        self.currentEnglishText = ""
        self.lastUpdateTime = time.time()
    
    def processChineseText(self, text: str) -> Optional[SubtitleSegment]:
        """
        处理中文文本
        
        Args:
            text: 中文文本
            
        Returns:
            字幕片段或None
        """
        if not text or not text.strip():
            return None
        
        self.currentChineseText = text.strip()
        self.lastUpdateTime = time.time()
        
        # 检查是否为完整句子
        sentence, remaining = self.textService.extract_complete_sentence(text)
        
        if sentence:
            self.logger.info(f"处理完整中文句子: {sentence}")
            segment = SubtitleSegment(
                text=sentence,
                language="zh",
                timestamp=self.lastUpdateTime,
                isComplete=True
            )
            return segment
        
        # 非完整句子，创建临时片段
        segment = SubtitleSegment(
            text=text,
            language="zh", 
            timestamp=self.lastUpdateTime,
            isComplete=False
        )
        return segment
    
    def processEnglishText(self, text: str, isIncremental: bool = False) -> Optional[SubtitleSegment]:
        """
        处理英文文本
        
        Args:
            text: 英文文本
            isIncremental: 是否为增量翻译
            
        Returns:
            字幕片段或None
        """
        if not text or not text.strip():
            return None
        
        self.currentEnglishText = text.strip()
        
        segment = SubtitleSegment(
            text=text,
            language="en",
            timestamp=time.time(),
            isComplete=not isIncremental,
            isIncremental=isIncremental
        )
        
        self.logger.info(f"处理英文文本: {text} (增量: {isIncremental})")
        return segment
    
    def createSubtitlePair(self, chineseSegment: SubtitleSegment, 
                          englishSegment: Optional[SubtitleSegment] = None) -> SubtitlePair:
        """
        创建字幕对
        
        Args:
            chineseSegment: 中文字幕片段
            englishSegment: 英文字幕片段
            
        Returns:
            字幕对
        """
        pairId = len(self.subtitlePairs) + 1
        chineseText = SubtitleText(
            text=chineseSegment.text,
            language=chineseSegment.language,
            is_complete=chineseSegment.isComplete
        )
        englishText = None
        if englishSegment:
            englishText = SubtitleText(
                text=englishSegment.text,
                language=englishSegment.language,
                is_complete=englishSegment.isComplete
            )
        else:
            englishText = SubtitleText(
                text="",
                language="en",
                is_complete=False
            )
        
        pair = SubtitlePair(
            chinese=chineseText,
            english=englishText,
            pair_id=pairId,
            create_time=time.time()
        )
        
        self.subtitlePairs.append(pair)
        self.logger.info(f"创建字幕对 #{pair.pair_id}: {chineseSegment.text}")
        
        return pair
    
    def updateSubtitlePair(self, pairId: int, englishSegment: SubtitleSegment) -> bool:
        """
        更新字幕对的英文部分
        
        Args:
            pairId: 字幕对ID
            englishSegment: 英文字幕片段
            
        Returns:
            是否更新成功
        """
        for pair in self.subtitlePairs:
            if pair.pair_id == pairId:
                pair.english = SubtitleText(
                    text=englishSegment.text,
                    language=englishSegment.language,
                    is_complete=englishSegment.isComplete
                )
                self.logger.info(f"更新字幕对 #{pairId} 英文内容: {englishSegment.text}")
                return True
        
        self.logger.warning(f"未找到字幕对 #{pairId}")
        return False
    
    def getRecentSubtitlePairs(self, count: int = 10) -> List[SubtitlePair]:
        """
        获取最近的字幕对
        
        Args:
            count: 获取数量
            
        Returns:
            字幕对列表
        """
        return self.subtitlePairs[-count:] if self.subtitlePairs else []
    
    def exportSubtitles(self, format: str = "srt") -> str:
        """
        导出字幕
        
        Args:
            format: 导出格式 (srt, txt, vtt)
            
        Returns:
            字幕内容字符串
        """
        if format.lower() == "srt":
            return self._exportSrt()
        elif format.lower() == "txt":
            return self._exportTxt()
        elif format.lower() == "vtt":
            return self._exportVtt()
        else:
            self.logger.error(f"不支持的导出格式: {format}")
            return ""
    
    def _exportSrt(self) -> str:
        """导出SRT格式字幕"""
        srt_content = []
        
        for i, pair in enumerate(self.subtitlePairs, 1):
            if pair.chinese and pair.chinese.is_complete:
                start_time = self._formatSrtTime(pair.create_time)
                end_time = self._formatSrtTime(pair.create_time + 3.0)  # 默认3秒显示时间
                
                srt_content.append(f"{i}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(pair.chinese.text)
                if pair.english and pair.english.text:
                    srt_content.append(pair.english.text)
                srt_content.append("")  # 空行
        
        return "\n".join(srt_content)
    
    def _exportTxt(self) -> str:
        """导出TXT格式字幕"""
        txt_content = []
        
        for pair in self.subtitlePairs:
            if pair.chinese and pair.chinese.isComplete:
                line = f"中文: {pair.chinese.text}"
                if pair.english and pair.english.text:
                    line += f"\n英文: {pair.english.text}"
                txt_content.append(line)
                txt_content.append("-" * 50)  # 分隔线
        
        return "\n".join(txt_content)
    
    def _exportVtt(self) -> str:
        """导出VTT格式字幕"""
        vtt_content = ["WEBVTT", ""]
        
        for pair in self.subtitlePairs:
            if pair.chinese and pair.chinese.is_complete:
                start_time = self._formatVttTime(pair.create_time)
                end_time = self._formatVttTime(pair.create_time + 3.0)
                
                vtt_content.append(f"{start_time} --> {end_time}")
                vtt_content.append(pair.chinese.text)
                if pair.english and pair.english.text:
                    vtt_content.append(pair.english.text)
                vtt_content.append("")
        
        return "\n".join(vtt_content)
    
    def _formatSrtTime(self, timestamp: float) -> str:
        """格式化SRT时间戳"""
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        milliseconds = int((timestamp % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _formatVttTime(self, timestamp: float) -> str:
        """格式化VTT时间戳"""
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = timestamp % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def clearSubtitles(self):
        """清空所有字幕"""
        self.subtitlePairs.clear()
        self.currentChineseText = ""
        self.currentEnglishText = ""
        self.logger.info("已清空所有字幕数据")
    
    def getStatistics(self) -> Dict[str, Any]:
        """
        获取字幕统计信息
        
        Returns:
            统计信息字典
        """
        total_pairs = len(self.subtitlePairs)
        complete_pairs = sum(1 for pair in self.subtitlePairs 
                           if pair.chinese and pair.chinese.is_complete)
        
        return {
            "totalPairs": total_pairs,
            "completePairs": complete_pairs,
            "currentChineseText": self.currentChineseText,
            "currentEnglishText": self.currentEnglishText,
            "lastUpdateTime": self.lastUpdateTime
        }