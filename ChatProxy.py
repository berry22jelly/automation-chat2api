from queue import Queue
import threading
import uuid
import selenium
import time
import json
from openai.types.chat.completion_create_params import CompletionCreateParamsNonStreaming
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
import logging as logger

import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from typing import Any, Dict, List, Optional, Literal, Union, TypedDict
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion

from ChatHistoryResponse import ChatHistoryResponse
from ChatProxyEvent import ChatGeneratingEvent, ChatStartedEvent
from ChatProxyUtils import convert_to_chat_completion
from JSCode import ChatHistoryCode, ChatListCode, ChatMutationCode
from config import CHAT_URL, FIREFOX_BINARY, PROFILE_PATH



request_queue = Queue()
driver_lock = threading.Lock()
processing_event = threading.Event()


def init_driver():
    options = webdriver.FirefoxOptions()
    options.binary_location = FIREFOX_BINARY
    options.add_argument("-profile")
    options.add_argument(PROFILE_PATH)
    driver = webdriver.Firefox(options=options)
    driver.get(CHAT_URL)
    return driver


driver = None


def request_worker():
    global driver
    logger.info("Starting request worker thread")
    
    while True:
        
        request = request_queue.get()
        if request is None:  
            break
            
        try:
            
            result = process_request_by_mutation(request)
            time.sleep(1)  
            
            request["result"] = result
            request["exception"] = None
        except Exception as e:
            request["exception"] = e
        finally:
            
            request["event"].set()
            
    logger.info("Request worker thread exiting")


worker_thread = threading.Thread(target=request_worker, daemon=True)
worker_thread.start()

def create_and_get_chat_response(messages: List[ChatCompletionMessageParam]) -> ChatCompletion:
    """
    线程安全的聊天响应创建方法
    """
    
    request = {
        "id": str(uuid.uuid4()),
        "messages": messages,
        "event": threading.Event(),
        "result": None,
        "exception": None
    }
    
    logger.info(f"Adding request {request['id']} to queue")
    
    
    request_queue.put(request)
    
    
    request["event"].wait()
    
    
    if request["exception"]:
        raise request["exception"]
    
    return request["result"]

def process_request(request: Dict[str, Any]) -> ChatCompletion:
    """
    处理单个聊天请求
    """
    global driver
    
    
    with driver_lock:
        
        if driver is None:
            driver = init_driver()
            logger.info("WebDriver initialized")
        
        
        chat_start_time = time.time()
        
        
        send_chat_message(request["messages"])
        
        
        chat_uuid = get_chat_uuid_by_create_time(chat_start_time)
        if not chat_uuid:
            raise Exception("Failed to get chat UUID")
        
        logger.info(f"Chat generating started, UUID: {chat_uuid}")
        
        
        return poll_for_chat_completion(chat_uuid, chat_start_time)

def process_request_by_mutation(request: Dict[str, Any]) -> ChatCompletion:
    global driver
    
    
    with driver_lock:
        
        if driver is None:
            driver = init_driver()
            logger.info("WebDriver initialized")

        
        send_chat_message(request["messages"])

        for i in range(2):
            chat_path = driver.execute_async_script(ChatMutationCode)
            """
            pathname like /chat/xxxx-xxxx-xxxx-xxxx
            """

            chat_uuid = chat_path.split("/")[-1] if chat_path else None

            if not chat_uuid:
                raise Exception("Failed to get chat UUID from mutation")
            
            logger.info(f"Chat generating started via mutation, UUID: {chat_uuid}")

            chat_history = get_chat_history(chat_uuid)
            if not chat_history:
                continue

            return convert_to_chat_completion(chat_uuid, chat_history)
        raise Exception("Failed to get chat history after mutation")






def send_chat_message(messages: List[ChatCompletionMessageParam]):
    """发送消息到聊天界面"""
    
    if driver.current_url != CHAT_URL:
        driver.get(CHAT_URL)
    
    
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.ID, "chat-input"))
    )
    
    
    input_box = driver.find_element(By.ID, "chat-input")
    input_text = "\n".join([msg["content"] for msg in messages])
    
    
    input_box.send_keys(input_text)
    input_box.send_keys(Keys.RETURN)
    
    
    time.sleep(3 + random.random())

def get_chat_uuid_by_create_time(chat_create_time: float) -> Optional[str]:
    """根据创建时间查找聊天会话UUID"""
    
    if not driver.current_url.startswith(CHAT_URL):
        driver.get(CHAT_URL)
    
    
    chat_list = driver.execute_async_script(ChatListCode)
    
    
    from ChatListResponse import Response
    response = Response(chat_list)
    
    
    for chat in response.data.biz_data.chat_sessions:
        if abs(chat_create_time - chat.inserted_at) < 5:
            return chat.id
    
    logger.warning(f"No chat session found near timestamp {chat_create_time}")
    return None

def get_chat_history(chat_uuid: str) -> Optional[ChatHistoryResponse]:
    """获取指定聊天会话的历史记录"""
    
    if not driver.current_url.startswith(CHAT_URL):
        driver.get(CHAT_URL)
    
    
    chat_history = driver.execute_async_script(ChatHistoryCode, chat_uuid)
    
    
    if chat_history:
        return ChatHistoryResponse.from_json(json.dumps(chat_history))
    return None

def poll_for_chat_completion(chat_uuid: str, start_time: float) -> ChatCompletion:
    """轮询等待聊天完成"""
    timeout = 240  
    poll_interval = 5  
    
    while time.time() - start_time < timeout:
        
        chat_history = get_chat_history(chat_uuid)
        
        if chat_history and chat_history.data.biz_data.chat_messages:
            last_message = chat_history.data.biz_data.chat_messages[-1]
            
            
            if last_message.status == "FINISHED":
                logger.info(f"Chat completed: {chat_uuid}")
                return convert_to_chat_completion(chat_uuid, chat_history)
        
        
        time.sleep(poll_interval)
    
    
    raise TimeoutError(f"Chat completion timed out after {timeout} seconds")

def shutdown():
    """清理资源"""
    global driver
    
    
    request_queue.put(None)
    worker_thread.join()
    
    
    if driver:
        driver.quit()
        driver = None
        logger.info("WebDriver closed")
