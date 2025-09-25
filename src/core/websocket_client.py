"""
WebSocket客户端模块
WebSocket Client Module
"""

import asyncio
import json
import logging
import ssl
from typing import Optional, Dict, Any

try:
    import websockets
    from websockets.exceptions import ConnectionClosed, InvalidURI
except ImportError:
    websockets = None
    ConnectionClosed = Exception
    InvalidURI = Exception

from ..config.constants import (
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SSL_MODE, 
    DEFAULT_ITN_MODE, DEFAULT_RECOGNITION_MODE
)

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket客户端类"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.websocket = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def connect(self, **kwargs) -> bool:
        """
        建立WebSocket连接
        
        Returns:
            是否连接成功
        """
        if not websockets:
            self.logger.error("websockets库未安装，无法建立连接")
            return False
        
        try:
            ssl_mode = kwargs.get('ssl_mode', DEFAULT_SSL_MODE)
            uri = self._build_uri(**kwargs)
            
            self.logger.info(f"正在连接到WebSocket服务器: {uri}")
            
            if ssl_mode == 1:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self.websocket = await websockets.connect(uri, ssl=ssl_context)
            else:
                self.websocket = await websockets.connect(uri)
            
            self.logger.info("WebSocket连接建立成功")
            return True
            
        except ConnectionClosed:
            self.logger.error("WebSocket连接被关闭")
            return False
        except InvalidURI as e:
            uri = "未知URI"
            self.logger.error(f"无效的WebSocket URI: {uri}")
            return False
        except Exception as e:
            self.logger.error(f"WebSocket连接失败: {str(e)}")
            return False
    
    def _build_uri(self, **kwargs) -> str:
        """构建WebSocket URI"""
        ssl_mode = kwargs.get('ssl_mode', DEFAULT_SSL_MODE)
        itn_mode = kwargs.get('itn_mode', DEFAULT_ITN_MODE)
        mode = kwargs.get('mode', DEFAULT_RECOGNITION_MODE)
        audio_fs = kwargs.get('audio_fs', 16000)
        language = kwargs.get('language', 'zh-CN')
        
        protocol = "wss" if ssl_mode == 1 else "ws"
        
        uri = (f"{protocol}://{self.host}:{self.port}/ws/v1/rec?"
               f"itn={itn_mode}&mode={mode}&lang={language}&audio_fs={audio_fs}")
        
        return uri
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息
        
        Args:
            message: 要发送的消息字典
            
        Returns:
            是否发送成功
        """
        if not self.websocket:
            self.logger.error("WebSocket未连接")
            return False
        
        try:
            message_json = json.dumps(message, ensure_ascii=False)
            await self.websocket.send(message_json)
            return True
        except ConnectionClosed:
            self.logger.error("WebSocket连接已关闭，无法发送消息")
            return False
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            return False
    
    async def send_audio_data(self, audio_data: bytes) -> bool:
        """
        发送音频数据
        
        Args:
            audio_data: 音频二进制数据
            
        Returns:
            是否发送成功
        """
        if not self.websocket:
            self.logger.error("WebSocket未连接")
            return False
        
        try:
            await self.websocket.send(audio_data)
            return True
        except ConnectionClosed:
            self.logger.error("WebSocket连接已关闭，无法发送音频数据")
            return False
        except Exception as e:
            self.logger.error(f"发送音频数据失败: {str(e)}")
            return False
    
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        接收消息
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            接收到的消息字典或None
        """
        if not self.websocket:
            self.logger.error("WebSocket未连接")
            return None
        
        try:
            if timeout:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            else:
                message = await self.websocket.recv()
            
            if isinstance(message, str):
                return json.loads(message)
            else:
                self.logger.warning("接收到非文本消息")
                return None
                
        except asyncio.TimeoutError:
            return None
        except ConnectionClosed:
            self.logger.warning("WebSocket连接已关闭")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"接收消息失败: {str(e)}")
            return None
    
    async def close(self):
        """关闭WebSocket连接"""
        if self.websocket:
            try:
                await self.websocket.close()
                self.logger.info("WebSocket连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭WebSocket连接失败: {str(e)}")
            finally:
                self.websocket = None
    
    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.websocket is not None and not self.websocket.closed