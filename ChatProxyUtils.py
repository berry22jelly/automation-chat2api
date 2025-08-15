from openai.types.chat.completion_create_params import CompletionCreateParamsNonStreaming
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion

from ChatHistoryResponse import ChatHistoryResponse

def convert_to_chat_completion(chat_uuid, response:ChatHistoryResponse) -> ChatCompletion:
    return ChatCompletion(
        object="chat.completion",
        id=chat_uuid,  
        model="",  
        created=int(response.data.biz_data.chat_session.inserted_at),  
        request_id=None,  
        tool_choice=None,
        
        
        
        
        
        seed=None,  
        top_p=None,
        temperature=None,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        tools=None,
        metadata={},
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.data.biz_data.chat_messages[-1].content,
                    "reasioning_content": response.data.biz_data.chat_messages[-1].thinking_content if response.data.biz_data.chat_messages[-1].thinking_content else None,
                },
                "finish_reason": "stop",
                "tool_calls": None,
                "function_call": None
            }
        ],
        response_format=None
    )
