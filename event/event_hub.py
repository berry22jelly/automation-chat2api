import asyncio
import inspect
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Optional, Union, List, Dict
from functools import partial
from .exceptions import EventTimeout, EventExecutionError

logger = logging.getLogger(__name__)

class EventHub:
    def __init__(self, max_workers: int = 10, mode: str = 'auto'):
        """
        Initialize the event hub.
        
        :param max_workers: Max threads for thread pool (when using threaded mode)
        :param mode: 'auto' (detect async), 'async' or 'threaded'
        """
        self._events: Dict[str, List[Dict]] = {}
        self._once_events: Dict[str, List[Dict]] = {}
        self._mode = mode
        self._loop = asyncio.get_event_loop() if mode != 'threaded' else None
        self._executor = ThreadPoolExecutor(max_workers=max_workers) if mode != 'async' else None
        self._default_timeout = 60
        
        
    def on(self, 
           event_name: str, 
           handler: Callable, 
           priority: int = 0, 
           is_async: Optional[bool] = None):
        """
        Register an event handler.
        
        :param event_name: Name of the event to listen to
        :param handler: Callable to handle the event
        :param priority: Higher priority handlers execute first
        :param is_async: Whether handler is async (None for auto-detect)
        """
        if is_async is None:
            is_async = inspect.iscoroutinefunction(handler)
            
        self._events.setdefault(event_name, []).append({
            'handler': handler,
            'priority': priority,
            'is_async': is_async
        })
        
        self._events[event_name].sort(key=lambda x: -x['priority'])
        
    def once(self, 
             event_name: str, 
             handler: Callable, 
             priority: int = 0, 
             is_async: Optional[bool] = None):
        """
        Register a one-time event handler.
        """
        if is_async is None:
            is_async = inspect.iscoroutinefunction(handler)
            
        self._once_events.setdefault(event_name, []).append({
            'handler': handler,
            'priority': priority,
            'is_async': is_async
        })
        
        self._once_events[event_name].sort(key=lambda x: -x['priority'])
        
    def off(self, event_name: str, handler: Optional[Callable] = None):
        """
        Remove event handler(s).
        
        :param event_name: Event name to remove handlers from
        :param handler: Specific handler to remove (None for all)
        """
        if handler is None:
            self._events.pop(event_name, None)
        else:
            handlers = self._events.get(event_name, [])
            self._events[event_name] = [h for h in handlers if h['handler'] != handler]
            
    async def emit(self, 
                   event_name: str, 
                   *args, 
                   timeout: Optional[float] = None,
                   **kwargs) -> List[Any]:
        """
        Emit an event and return results from all handlers.
        
        :param event_name: Name of event to emit
        :param timeout: Max time to wait for handlers (None for no timeout)
        :return: List of results from handlers
        """
        if timeout is None:
            timeout = self._default_timeout
            
        
        all_handlers = self._events.get(event_name, []) + self._once_events.pop(event_name, [])
        
        if not all_handlers:
            return []
            
        results = []
        
        for handler_info in all_handlers:
            try:
                result = await self._execute_handler(
                    handler_info['handler'],
                    handler_info['is_async'],
                    *args,
                    timeout=timeout,
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing handler for event {event_name}: {str(e)}")
                raise EventExecutionError(f"Handler failed for event {event_name}") from e
                
        return results
        
    async def _execute_handler(self, 
                              handler: Callable, 
                              is_async: bool, 
                              *args, 
                              timeout: float,
                              **kwargs) -> Any:
        """
        Execute a single handler with proper async/threaded handling.
        """
        if self._mode == 'auto':
            mode = 'async' if is_async else 'threaded'
        else:
            mode = self._mode
            
        if mode == 'async':
            if not is_async:
                
                async def wrapped():
                    return handler(*args, **kwargs)
                return await asyncio.wait_for(wrapped(), timeout=timeout)
            else:
                return await asyncio.wait_for(handler(*args, **kwargs), timeout=timeout)
        else:
            
            loop = asyncio.get_running_loop()
            func = partial(handler, *args, **kwargs)
            return await loop.run_in_executor(
                self._executor,
                func
            )
            
    def set_default_timeout(self, timeout: float):
        """Set default timeout for event handlers."""
        self._default_timeout = timeout
        
    def get_registered_events(self) -> List[str]:
        """Get list of all registered event names."""
        return list(self._events.keys())
        
    def has_listeners(self, event_name: str) -> bool:
        """Check if an event has any listeners."""
        return (event_name in self._events and bool(self._events[event_name])) or \
               (event_name in self._once_events and bool(self._once_events[event_name]))
               
    async def close(self):
        """Cleanup resources."""
        if self._executor:
            self._executor.shutdown(wait=True)
    
    def emit_nowait(self, event_name: str, *args, **kwargs) -> None:
        """
        Emit an event without waiting for handlers to complete.
        Can be used in synchronous context.
        
        :param event_name: Name of event to emit
        """
        if not self.has_listeners(event_name):
            return
            
        
        all_handlers = self._events.get(event_name, []) + self._once_events.pop(event_name, [])
        
        for handler_info in all_handlers:
            try:
                if self._mode == 'async' or (self._mode == 'auto' and handler_info['is_async']):
                    
                    if self._loop is None:
                        self._loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self._loop)
                    
                    coro = handler_info['handler'](*args, **kwargs)
                    asyncio.run_coroutine_threadsafe(coro, self._loop)
                else:
                    
                    if self._executor is None:
                        self._executor = ThreadPoolExecutor()
                    
                    self._executor.submit(
                        handler_info['handler'],
                        *args,
                        **kwargs
                    )
            except Exception as e:
                logger.error(f"Error scheduling handler for event {event_name}: {str(e)}")