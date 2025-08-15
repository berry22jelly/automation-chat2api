import json
import time
from typing import AsyncGenerator, Dict, Generator, List, Union
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.completion_create_params import CompletionCreateParamsStreaming
from openai.types.chat.chat_completion import ChatCompletion
from fastapi.responses import JSONResponse
def simulate_streaming(resp: ChatCompletion) -> Generator[Union[ChatCompletionChunk, bytes],None,None]:
    """将完整响应拆分为多个事件块来模拟流式API"""
    chunks = []
    
    
    content = resp.choices[0].message.content if resp.choices else ""
    
    response=resp.to_dict()
    
    
    yield "data: ".encode() + json.dumps({
        "id": f"simulated_{response['id']}",
        "object": "chat.completion.chunk",
        "created": response["created"],
        "model": response['model'],
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": None
            }
        ]
    }).encode('utf-8')+ "\n\n".encode('utf-8')
    
    
    yield "data: ".encode() + json.dumps({
        "id": f"simulated_{response['id']}",
        "object": "chat.completion.chunk",
        "created": response['created'],
        "model": response['model'],
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ]
    }).encode('utf-8')+ "\n\n".encode('utf-8')

    yield "data: [DONE]".encode('utf-8')+ "\n\n".encode('utf-8')

def simulate_streaming_pp(id) -> Generator[bytes,None,None]:
    """将完整响应拆分为多个事件块来模拟流式API"""

    
    
    yield "data: ".encode() + ChatCompletionChunk(
        id="id-test1",
        choices=[
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": "nice to meet you"
                },
                "finish_reason": None
            }
        ],
        created=int(time.time()),
        model="model",
        object="chat.completion.chunk"
    ).to_json(indent=None).encode('utf-8') + "\n\n".encode('utf-8')

    
    yield "data: ".encode() + ChatCompletionChunk(
        id="id-test1",
        choices=[
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ],
        created=int(time.time()),
        model="model",
        object="chat.completion.chunk"
    ).to_json(indent=None).encode('utf-8') + "\n\n".encode('utf-8')

    yield "data: [DONE]".encode('utf-8')
