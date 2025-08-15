import json
from typing import List, Dict, Any, Optional

class ChatSession:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.seq_id = data.get("seq_id")
        self.title = data.get("title")
        self.title_type = data.get("title_type")
        self.updated_at = data.get("updated_at")
        self.pinned = data.get("pinned")
        self.agent = data.get("agent")
        self.version = data.get("version")
        self.current_message_id = data.get("current_message_id")
        self.inserted_at = data.get("inserted_at")
        self.character = data.get("character")

    def __repr__(self):
        return f"ChatSession(id={self.id}, title={self.title}, updated_at={self.updated_at})"

class BizData:
    def __init__(self, data: Dict[str, Any]):
        self.chat_sessions = [ChatSession(session) for session in data.get("chat_sessions", [])]
        self.has_more = data.get("has_more", False)

class Data:
    def __init__(self, data: Dict[str, Any]):
        self.biz_code = data.get("biz_code")
        self.biz_msg = data.get("biz_msg")
        self.biz_data = BizData(data.get("biz_data", {}))

class Response:
    def __init__(self, data: Dict[str, Any]):
        self.code = data.get("code")
        self.msg = data.get("msg")
        self.data = Data(data.get("data", {}))

    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(data)

    def __repr__(self):
        return f"Response(code={self.code}, msg={self.msg}, sessions_count={len(self.data.biz_data.chat_sessions)})"

if __name__ == "__main__":
    
    json_str = '''{
    "code": 0,
    "msg": "",
    "data": {
        "biz_code": 0,
        "biz_msg": "",
        "biz_data": {
        "chat_sessions": [
            {
            "id": "uuid",
            "seq_id": 1234567,
            "title": "text",
            "title_type": "SYSTEM",
            "updated_at": 1754950000.000,
            "pinned": false,
            "agent": "chat",
            "version": 26,
            "current_message_id": 25,
            "inserted_at": 1754950000.000,
            "character": null
            }
        ],
        "has_more": true
        }
    }
    }'''

    response = Response.from_json(json_str)
    print(response)
    print(response.data.biz_data.chat_sessions[0])