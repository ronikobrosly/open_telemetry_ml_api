class ModelError(Exception):
    """Raised when model inference fails"""
    pass

class ModelTimeoutError(Exception):
    """Raised when model inference times out"""
    pass
