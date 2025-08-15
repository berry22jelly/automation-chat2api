class EventError(Exception):
    """Base exception for event hub errors"""
    pass

class EventTimeout(EventError):
    """Raised when event handling times out"""
    pass

class EventExecutionError(EventError):
    """Raised when event handler fails"""
    pass