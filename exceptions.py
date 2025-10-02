"""
Custom exceptions for Personal Mentor Agent
Implements Exception Hierarchy Pattern
"""
from typing import Optional, Dict, Any


class MentorException(Exception):
    """Base exception for all mentor application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Database Exceptions
class DatabaseException(MentorException):
    """Base exception for database errors"""
    pass


class ConnectionException(DatabaseException):
    """Database connection error"""
    
    def __init__(self, message: str = "Failed to connect to database", **kwargs):
        super().__init__(message, **kwargs)


class DataNotFoundException(DatabaseException):
    """Requested data not found"""
    
    def __init__(self, entity: str, identifier: str, **kwargs):
        message = f"{entity} with identifier '{identifier}' not found"
        super().__init__(message, **kwargs)


class DuplicateDataException(DatabaseException):
    """Duplicate data error"""
    
    def __init__(self, entity: str, field: str, value: str, **kwargs):
        message = f"{entity} with {field}='{value}' already exists"
        super().__init__(message, **kwargs)


class DatabaseIntegrityException(DatabaseException):
    """Database integrity constraint violation"""
    pass


# User Exceptions
class UserException(MentorException):
    """Base exception for user-related errors"""
    pass


class UserNotFoundException(UserException):
    """User not found"""
    
    def __init__(self, user_id: str, **kwargs):
        message = f"User '{user_id}' not found"
        super().__init__(message, error_code="USER_NOT_FOUND", **kwargs)


class UserAlreadyExistsException(UserException):
    """User already exists"""
    
    def __init__(self, user_id: str, **kwargs):
        message = f"User '{user_id}' already exists"
        super().__init__(message, error_code="USER_EXISTS", **kwargs)


class InvalidUserDataException(UserException):
    """Invalid user data provided"""
    
    def __init__(self, field: str, reason: str, **kwargs):
        message = f"Invalid user data - {field}: {reason}"
        super().__init__(message, error_code="INVALID_USER_DATA", **kwargs)


# Memory Exceptions
class MemoryException(MentorException):
    """Base exception for memory-related errors"""
    pass


class EmbeddingException(MemoryException):
    """Error generating embeddings"""
    
    def __init__(self, reason: str, **kwargs):
        message = f"Failed to generate embedding: {reason}"
        super().__init__(message, error_code="EMBEDDING_ERROR", **kwargs)


class VectorSearchException(MemoryException):
    """Error during vector search"""
    
    def __init__(self, reason: str, **kwargs):
        message = f"Vector search failed: {reason}"
        super().__init__(message, error_code="SEARCH_ERROR", **kwargs)


# LLM Exceptions
class LLMException(MentorException):
    """Base exception for LLM-related errors"""
    pass


class APIKeyException(LLMException):
    """API key missing or invalid"""
    
    def __init__(self, **kwargs):
        message = "OpenAI API key is missing or invalid"
        super().__init__(message, error_code="INVALID_API_KEY", **kwargs)


class RateLimitException(LLMException):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, error_code="RATE_LIMIT", **kwargs)


class ModelException(LLMException):
    """Model error"""
    
    def __init__(self, model_name: str, reason: str, **kwargs):
        message = f"Model '{model_name}' error: {reason}"
        super().__init__(message, error_code="MODEL_ERROR", **kwargs)


class ResponseGenerationException(LLMException):
    """Error generating response"""
    
    def __init__(self, reason: str, **kwargs):
        message = f"Failed to generate response: {reason}"
        super().__init__(message, error_code="GENERATION_ERROR", **kwargs)


# Habit Tracking Exceptions
class HabitException(MentorException):
    """Base exception for habit tracking errors"""
    pass


class HabitNotFoundException(HabitException):
    """Habit not found"""
    
    def __init__(self, habit_id: str, **kwargs):
        message = f"Habit '{habit_id}' not found"
        super().__init__(message, error_code="HABIT_NOT_FOUND", **kwargs)


class InvalidHabitDataException(HabitException):
    """Invalid habit data"""
    
    def __init__(self, field: str, reason: str, **kwargs):
        message = f"Invalid habit data - {field}: {reason}"
        super().__init__(message, error_code="INVALID_HABIT_DATA", **kwargs)


class HabitLogException(HabitException):
    """Error logging habit"""
    
    def __init__(self, reason: str, **kwargs):
        message = f"Failed to log habit: {reason}"
        super().__init__(message, error_code="HABIT_LOG_ERROR", **kwargs)


# Goal Exceptions
class GoalException(MentorException):
    """Base exception for goal-related errors"""
    pass


class GoalNotFoundException(GoalException):
    """Goal not found"""
    
    def __init__(self, goal_id: str, **kwargs):
        message = f"Goal '{goal_id}' not found"
        super().__init__(message, error_code="GOAL_NOT_FOUND", **kwargs)


class InvalidGoalDataException(GoalException):
    """Invalid goal data"""
    
    def __init__(self, field: str, reason: str, **kwargs):
        message = f"Invalid goal data - {field}: {reason}"
        super().__init__(message, error_code="INVALID_GOAL_DATA", **kwargs)


# Validation Exceptions
class ValidationException(MentorException):
    """Base exception for validation errors"""
    pass


class InputValidationException(ValidationException):
    """Input validation failed"""
    
    def __init__(self, field: str, reason: str, **kwargs):
        message = f"Validation failed for '{field}': {reason}"
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class DataValidationException(ValidationException):
    """Data validation failed"""
    
    def __init__(self, reason: str, **kwargs):
        message = f"Data validation failed: {reason}"
        super().__init__(message, error_code="DATA_VALIDATION_ERROR", **kwargs)


# Configuration Exceptions
class ConfigurationException(MentorException):
    """Configuration error"""
    
    def __init__(self, setting: str, reason: str, **kwargs):
        message = f"Configuration error for '{setting}': {reason}"
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


# Error Handler
class ErrorHandler:
    """
    Centralized error handler - Strategy Pattern
    Handles different types of errors with appropriate responses
    """
    
    @staticmethod
    def handle_database_error(error: Exception) -> str:
        """Handle database errors"""
        if isinstance(error, ConnectionException):
            return "Unable to connect to database. Please try again later."
        elif isinstance(error, DataNotFoundException):
            return str(error.message)
        elif isinstance(error, DuplicateDataException):
            return str(error.message)
        else:
            return "A database error occurred. Please contact support."
    
    @staticmethod
    def handle_llm_error(error: Exception) -> str:
        """Handle LLM errors"""
        if isinstance(error, APIKeyException):
            return "API configuration error. Please check your settings."
        elif isinstance(error, RateLimitException):
            return "Too many requests. Please wait a moment and try again."
        elif isinstance(error, ResponseGenerationException):
            return "Failed to generate response. Please try rephrasing your message."
        else:
            return "An AI service error occurred. Please try again."
    
    @staticmethod
    def handle_validation_error(error: Exception) -> str:
        """Handle validation errors"""
        if isinstance(error, ValidationException):
            return str(error.message)
        else:
            return "Invalid input. Please check your data and try again."
    
    @staticmethod
    def handle_generic_error(error: Exception) -> str:
        """Handle generic errors"""
        if isinstance(error, MentorException):
            return str(error.message)
        else:
            return "An unexpected error occurred. Please try again."
    
    @classmethod
    def handle_error(cls, error: Exception) -> str:
        """Main error handling dispatch"""
        if isinstance(error, DatabaseException):
            return cls.handle_database_error(error)
        elif isinstance(error, LLMException):
            return cls.handle_llm_error(error)
        elif isinstance(error, ValidationException):
            return cls.handle_validation_error(error)
        else:
            return cls.handle_generic_error(error)


# Decorator for error handling
def handle_exceptions(user_friendly: bool = True):
    """
    Decorator to handle exceptions in functions
    
    Args:
        user_friendly: If True, returns user-friendly error messages
    """
    from functools import wraps
    from logger import app_logger
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MentorException as e:
                app_logger.error(f"Application error in {func.__name__}: {e.to_dict()}")
                if user_friendly:
                    raise MentorException(ErrorHandler.handle_error(e))
                raise
            except Exception as e:
                app_logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                if user_friendly:
                    raise MentorException(ErrorHandler.handle_generic_error(e))
                raise
        
        return wrapper
    return decorator


# Example usage:
# from exceptions import handle_exceptions, UserNotFoundException
#
# @handle_exceptions(user_friendly=True)
# def get_user(user_id: str):
#     if not user_exists(user_id):
#         raise UserNotFoundException(user_id)
#     return fetch_user(user_id)