from typing import TypedDict


class ChatStartedEvent(TypedDict):
    """
    聊天开始事件定义
    """
    chat_start_time: float
    """聊天开始时间戳"""
    proxy_uuid: str
    """代理UUID"""

class ChatGeneratingEvent(TypedDict):
    """
    聊天生成事件定义
    """
    uuid: str
    """聊天会话UUID"""
    proxy_uuid: str
    """代理UUID"""
    chat_start_time: float
    """聊天开始时间戳"""