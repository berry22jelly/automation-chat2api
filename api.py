from fastapi import FastAPI, HTTPException, Response,status
from datetime import datetime
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import StreamingResponse, JSONResponse
from openai.types.chat.completion_create_params import CompletionCreateParamsNonStreaming
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from ChatProxy import create_and_get_chat_response

from utils import simulate_streaming, simulate_streaming_pp


app = FastAPI()


@app.post("/chat/completions",)
async def create_chat_completions(d:dict):
    data:CompletionCreateParamsNonStreaming=d
    
    if data.get("functions"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Functions are not supported in this endpoint.")
    if data.get("tools"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tools are not supported in this endpoint.")
    
    if data.get("response_format") == "json_object":
        raise NotImplementedError("JSON object response format is not supported.")
        return create_and_get_typed_response()
    
    if data.get("stream"):
        resp =create_and_get_chat_response(data.get("messages", []))
        
        return StreamingResponse(
            simulate_streaming(resp),
            media_type="text/event-stream"
        )

    
    resp =create_and_get_chat_response(data.get("messages", []))
    return resp

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="127.0.0.1", port=38000, log_level="debug")