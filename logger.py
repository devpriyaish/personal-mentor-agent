"""
Logging configuration for Personal Mentor Agent
Implements Singleton Pattern for logger
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class LoggerConfig:
    """Logger configuration - Singleton Pattern"""
    _instance: Optional['LoggerConfig'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup logging configuration"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self._logger = logging.getLogger("PersonalMentor")
        self._logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self._logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler
        log_file = log_dir / f"mentor_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Error file handler
        error_log_file = log_dir / f"mentor_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Add handlers
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        self._logger.addHandler(error_handler)
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance"""
        return self._logger


class StructuredLogger:
    """
    Structured logging for better log analysis
    Implements Decorator Pattern
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log structured event"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log structured error"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "user_id": user_id,
            **kwargs
        }
        self.logger.error(json.dumps(error_data))
    
    def log_metric(
        self,
        metric_name: str,
        metric_value: float,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """Log metric for monitoring"""
        metric_data = {
            "timestamp": datetime.now().isoformat(),
            "metric_name": metric_name,
            "metric_value": metric_value,
            "user_id": user_id,
            **kwargs
        }
        self.logger.info(json.dumps(metric_data))


# Global logger instance
logger_config = LoggerConfig()
app_logger = logger_config.logger
structured_logger = StructuredLogger(app_logger)


def log_execution_time(func):
    """Decorator to log function execution time"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            structured_logger.log_metric(
                metric_name=f"{func.__name__}_execution_time",
                metric_value=execution_time,
                status="success"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            structured_logger.log_error(
                error_type=f"{func.__name__}_error",
                error_message=str(e),
                execution_time=execution_time
            )
            raise
    
    return wrapper


def log_user_action(action_type: str):
    """Decorator to log user actions"""
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract user_id from args or kwargs
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            
            structured_logger.log_event(
                event_type=action_type,
                user_id=str(user_id) if user_id else None,
                function=func.__name__
            )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example usage:
# from logger import app_logger, log_execution_time, log_user_action
#
# @log_execution_time
# @log_user_action("user_login")
# def login_user(user_id: str):
#     app_logger.info(f"User {user_id} logged in")