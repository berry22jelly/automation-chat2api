from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import time

@dataclass
class ChatMessage:
    message_id: int
    parent_id: Optional[int]
    model: str
    role: str
    thinking_enabled: bool
    ban_edit: bool
    ban_regenerate: bool
    status: str
    accumulated_token_usage: int
    files: List[Any] = field(default_factory=list)
    inserted_at: float = 0.0
    search_enabled: bool = False
    feedback: Optional[Any] = None
    content: str = ""
    thinking_content: Optional[str] = None
    thinking_elapsed_secs: Optional[float] = None
    tips: List[Any] = field(default_factory=list)
    search_status: Optional[Any] = None
    search_results: Optional[Any] = None

@dataclass
class ChatSession:
    id: str
    seq_id: int
    agent: str
    character: Optional[str]
    title: str
    title_type: str
    version: int
    current_message_id: int
    pinned: bool
    inserted_at: float
    updated_at: float

@dataclass
class BizData:
    chat_session: ChatSession
    chat_messages: List[ChatMessage] = field(default_factory=list)
    cache_valid: bool = False
    route_id: Optional[str] = None

@dataclass
class DataClass:
    biz_code: int = 0
    biz_msg: str = ""
    biz_data: Optional[BizData] = None

@dataclass
class ChatHistoryResponse:
    code: int = 0
    msg: str = ""
    data: Optional[DataClass] = None

    @classmethod
    def from_json(cls, json_str: str) -> "ChatHistoryResponse":
        """从JSON字符串反序列化为ChatResponse对象"""
        data = json.loads(json_str)
        return cls._deserialize(data)
    
    @classmethod
    def _deserialize(cls, data: Dict) -> "ChatHistoryResponse":
        """递归反序列化嵌套结构"""
        
        response = cls(
            code=data.get("code", 0),
            msg=data.get("msg", ""),
            data=None
        )
        
        
        if "data" in data:
            data_obj = data["data"]
            response.data = DataClass(
                biz_code=data_obj.get("biz_code", 0),
                biz_msg=data_obj.get("biz_msg", "")
            )
            
            
            if "biz_data" in data_obj:
                biz_data = data_obj["biz_data"]
                biz_data_obj = BizData(
                    chat_session=None,  
                    chat_messages=[],  
                    cache_valid=biz_data.get("cache_valid", False),
                    route_id=biz_data.get("route_id")
                )
                
                
                if "chat_session" in biz_data:
                    session_data = biz_data["chat_session"]
                    biz_data_obj.chat_session = ChatSession(
                        id=session_data["id"],
                        seq_id=session_data["seq_id"],
                        agent=session_data["agent"],
                        character=session_data.get("character"),
                        title=session_data["title"],
                        title_type=session_data["title_type"],
                        version=session_data["version"],
                        current_message_id=session_data["current_message_id"],
                        pinned=session_data["pinned"],
                        inserted_at=session_data["inserted_at"],
                        updated_at=session_data["updated_at"]
                    )
                
                
                if "chat_messages" in biz_data:
                    for msg_data in biz_data["chat_messages"]:
                        biz_data_obj.chat_messages.append(ChatMessage(
                            message_id=msg_data["message_id"],
                            parent_id=msg_data.get("parent_id"),
                            model=msg_data.get("model", ""),
                            role=msg_data["role"],
                            thinking_enabled=msg_data["thinking_enabled"],
                            ban_edit=msg_data["ban_edit"],
                            ban_regenerate=msg_data["ban_regenerate"],
                            status=msg_data["status"],
                            accumulated_token_usage=msg_data["accumulated_token_usage"],
                            files=msg_data.get("files", []),
                            inserted_at=msg_data.get("inserted_at", 0.0),
                            search_enabled=msg_data.get("search_enabled", False),
                            feedback=msg_data.get("feedback"),
                            content=msg_data.get("content", ""),
                            thinking_content=msg_data.get("thinking_content"),
                            thinking_elapsed_secs=msg_data.get("thinking_elapsed_secs"),
                            tips=msg_data.get("tips", []),
                            search_status=msg_data.get("search_status"),
                            search_results=msg_data.get("search_results")
                        ))
                
                response.data.biz_data = biz_data_obj
        
        return response

    def get_session_title(self) -> Optional[str]:
        """获取会话标题"""
        if (self.data and self.data.biz_data and 
            self.data.biz_data.chat_session):
            return self.data.biz_data.chat_session.title
        return None

    def get_last_message(self) -> Optional[ChatMessage]:
        """获取最后一条消息"""
        if (self.data and self.data.biz_data and 
            self.data.biz_data.chat_messages):
            return self.data.biz_data.chat_messages[-1]
        return None

    def format_inserted_at(self, timestamp: float) -> str:
        """格式化时间戳为可读格式"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


if __name__ == "__main__":
    json_str = '''{"code":0,"msg":"","data":{"biz_code":0,"biz_msg":"","biz_data":{
        "chat_session":{"id":"uuid","seq_id":123456,
        "agent":"chat","character":null,"title":"Python事件处理器设计与实现","title_type":"SYSTEM",
        "version":7,"current_message_id":22,"pinned":false,"inserted_at":1754950000.000,
        "updated_at":1754900000.000},
        "chat_messages":[
            {"message_id":1,"parent_id":null,"model":"","role":"USER","thinking_enabled":false,
            "ban_edit":false,"ban_regenerate":false,"status":"FINISHED","accumulated_token_usage":123,
            "files":[],"inserted_at":175490000.000,"search_enabled":false,"feedback":null,
            "content":"test","thinking_content":null,"thinking_elapsed_secs":null,"tips":[],
            "search_status":null,"search_results":null},
            {"message_id":2,"parent_id":1,"model":"","role":"ASSISTANT","thinking_enabled":false,
            "ban_edit":false,"ban_regenerate":false,"status":"FINISHED","accumulated_token_usage":123,
            "files":[],"inserted_at":1754950000.000,"search_enabled":false,"feedback":null,
            "content":"test","thinking_content":null,"thinking_elapsed_secs":null,"tips":[],
            "search_status":null,"search_results":null}
        ],
        "cache_valid":false,"route_id":null}}}'''
    
    
    chat_data = ChatHistoryResponse.from_json(json_str)
    
    
    print("会话标题:", chat_data.get_session_title())
    print("消息数量:", len(chat_data.data.biz_data.chat_messages))
    
    last_msg = chat_data.get_last_message()
    if last_msg:
        print("最后一条消息:")
        print(f"  ID: {last_msg.message_id}, 角色: {last_msg.role}")
        print(f"  内容: {last_msg.content}")
        print(f"  发送时间: {chat_data.format_inserted_at(last_msg.inserted_at)}")
    
    
    session = chat_data.data.biz_data.chat_session
    print("\n会话信息:")
    print(f"  创建时间: {chat_data.format_inserted_at(session.inserted_at)}")
    print(f"  最后更新: {chat_data.format_inserted_at(session.updated_at)}")
    print(f"  当前消息ID: {session.current_message_id}")