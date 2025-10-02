"""
Utility functions for Personal Mentor Agent
"""
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json


class DateUtils:
    """Date and time utility functions"""
    
    @staticmethod
    def get_date_range(days: int) -> tuple[datetime, datetime]:
        """Get date range for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    @staticmethod
    def format_relative_date(date: datetime) -> str:
        """Format date as relative time (e.g., '2 days ago')"""
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
    
    @staticmethod
    def is_today(date: datetime) -> bool:
        """Check if date is today"""
        return date.date() == datetime.now().date()
    
    @staticmethod
    def days_until(target_date: datetime) -> int:
        """Calculate days until target date"""
        return (target_date.date() - datetime.now().date()).days


class TextUtils:
    """Text processing utilities"""
    
    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 4) -> List[str]:
        """Extract keywords from text"""
        # Remove special characters and convert to lowercase
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out short words and common stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'from', 'by', 'as'
        }
        
        keywords = [
            word for word in words 
            if len(word) >= min_length and word not in stop_words
        ]
        
        return list(set(keywords))
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate simple word overlap similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        # Remove potentially dangerous characters
        text = re.sub(r'[<>]', '', text)
        # Limit length
        text = text[:5000]
        return text.strip()


class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        pattern = r'^user_[a-z0-9_]+$'
        return bool(re.match(pattern, user_id))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename"""
        # Remove potentially dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        return filename


class DataUtils:
    """Data processing utilities"""
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """Calculate percentage change"""
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def moving_average(values: List[float], window: int = 7) -> List[float]:
        """Calculate moving average"""
        if len(values) < window:
            return values
        
        result = []
        for i in range(len(values)):
            if i < window - 1:
                result.append(values[i])
            else:
                window_values = values[i - window + 1:i + 1]
                result.append(sum(window_values) / window)
        
        return result
    
    @staticmethod
    def group_by_date(
        items: List[Dict[str, Any]], 
        date_key: str = "date"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by date"""
        grouped = {}
        for item in items:
            date = item.get(date_key)
            if date:
                date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)
                if date_str not in grouped:
                    grouped[date_str] = []
                grouped[date_str].append(item)
        
        return grouped


class SecurityUtils:
    """Security-related utilities"""
    
    @staticmethod
    def hash_string(text: str, salt: str = "") -> str:
        """Hash a string using SHA-256"""
        return hashlib.sha256(f"{text}{salt}".encode()).hexdigest()
    
    @staticmethod
    def generate_token(user_id: str) -> str:
        """Generate a simple session token"""
        timestamp = datetime.now().isoformat()
        data = f"{user_id}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """Mask sensitive data (e.g., email, API keys)"""
        if len(data) <= visible_chars:
            return mask_char * len(data)
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)


class FormatUtils:
    """Formatting utilities"""
    
    @staticmethod
    def format_number(number: float, decimals: int = 2) -> str:
        """Format number with commas and decimals"""
        return f"{number:,.{decimals}f}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format value as percentage"""
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def format_list(items: List[str], conjunction: str = "and") -> str:
        """Format list as natural language string"""
        if not items:
            return ""
        elif len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, {conjunction} {items[-1]}"


class CacheUtils:
    """Simple caching utilities"""
    
    _cache: Dict[str, tuple[Any, datetime]] = {}
    
    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: int = 3600):
        """Set cache value with TTL"""
        expiry = datetime.now() + timedelta(seconds=ttl_seconds)
        cls._cache[key] = (value, expiry)
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get cache value if not expired"""
        if key not in cls._cache:
            return None
        
        value, expiry = cls._cache[key]
        if datetime.now() > expiry:
            del cls._cache[key]
            return None
        
        return value
    
    @classmethod
    def clear(cls, key: Optional[str] = None):
        """Clear cache"""
        if key:
            cls._cache.pop(key, None)
        else:
            cls._cache.clear()
    
    @classmethod
    def clear_expired(cls):
        """Clear all expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in cls._cache.items()
            if now > expiry
        ]
        for key in expired_keys:
            del cls._cache[key]


# Convenience functions
def format_goal_progress(current: float, target: float) -> str:
    """Format goal progress"""
    percentage = (current / target) * 100 if target > 0 else 0
    return f"{current}/{target} ({percentage:.1f}%)"


def calculate_streak_emoji(streak: int) -> str:
    """Get emoji based on streak length"""
    if streak >= 100:
        return "🏆"
    elif streak >= 50:
        return "🌟"
    elif streak >= 30:
        return "⭐"
    elif streak >= 14:
        return "🔥"
    elif streak >= 7:
        return "✨"
    elif streak >= 3:
        return "💪"
    else:
        return "🎯"


def get_motivational_message(completion_rate: float) -> str:
    """Get motivational message based on completion rate"""
    if completion_rate >= 90:
        return "Outstanding! You're crushing it! 🏆"
    elif completion_rate >= 75:
        return "Great work! Keep up the momentum! 🌟"
    elif completion_rate >= 60:
        return "You're doing well! Stay consistent! 💪"
    elif completion_rate >= 40:
        return "Good progress! Keep going! ✨"
    else:
        return "Every step counts! You've got this! 🎯"