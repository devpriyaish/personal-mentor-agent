"""
Data models for Personal Mentor Agent
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class InteractionType(Enum):
    """Types of user interactions"""
    GOAL = "goal"
    STRUGGLE = "struggle"
    ACHIEVEMENT = "achievement"
    REFLECTION = "reflection"
    CONVERSATION = "conversation"
    HABIT_LOG = "habit_log"


class HabitFrequency(Enum):
    """Habit tracking frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class User:
    """User profile data model"""
    user_id: str
    name: str
    email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    timezone: str = "UTC"
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    """Memory record for vector storage"""
    memory_id: str
    user_id: str
    content: str
    interaction_type: InteractionType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class Habit:
    """Habit tracking model"""
    habit_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    frequency: HabitFrequency = HabitFrequency.DAILY
    target_value: Optional[float] = None
    unit: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class HabitLog:
    """Habit log entry"""
    log_id: str
    habit_id: str
    user_id: str
    value: float
    notes: Optional[str] = None
    logged_at: datetime = field(default_factory=datetime.now)


@dataclass
class Goal:
    """Goal tracking model"""
    goal_id: str
    user_id: str
    title: str
    description: str
    target_date: Optional[datetime] = None
    status: str = "active"  # active, completed, abandoned
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class DailyReflection:
    """Daily reflection model"""
    reflection_id: str
    user_id: str
    content: str
    sentiment_score: Optional[float] = None
    key_insights: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """Conversation message model"""
    message_id: str
    user_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)