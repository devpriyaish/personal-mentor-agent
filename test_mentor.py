"""
Unit tests for Personal Mentor Agent
Run with: python -m pytest test_mentor.py -v
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from config import Config
from models import (
    User, Habit, HabitLog, Goal, Memory, 
    InteractionType, HabitFrequency
)
from database import DatabaseManager, SQLiteDatabase
from memory_manager import MemoryManager
from habit_tracker import HabitTracker
from utils import DateUtils, TextUtils, ValidationUtils


# Fixtures
@pytest.fixture
def config():
    """Create test configuration"""
    config = Config()
    config.database.sqlite_db_path = ":memory:"  # In-memory database for testing
    return config


@pytest.fixture
def db_manager(config):
    """Create test database manager"""
    db_manager = DatabaseManager(config)
    db_manager.sqlite_db.initialize()
    return db_manager


@pytest.fixture
def test_user():
    """Create test user"""
    return User(
        user_id="test_user_123",
        name="Test User",
        email="test@example.com",
        created_at=datetime.now()
    )


@pytest.fixture
def test_habit(test_user):
    """Create test habit"""
    return Habit(
        habit_id=str(uuid.uuid4()),
        user_id=test_user.user_id,
        name="Exercise",
        description="Daily exercise routine",
        frequency=HabitFrequency.DAILY,
        target_value=30.0,
        unit="minutes"
    )


# Database Tests
class TestDatabase:
    """Test database operations"""
    
    def test_create_user(self, db_manager, test_user):
        """Test user creation"""
        created_user = db_manager.create_user(test_user)
        
        assert created_user.user_id == test_user.user_id
        assert created_user.name == test_user.name
        
        # Retrieve and verify
        retrieved_user = db_manager.get_user(test_user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.name == test_user.name
    
    def test_get_nonexistent_user(self, db_manager):
        """Test retrieving non-existent user"""
        user = db_manager.get_user("nonexistent_user")
        assert user is None
    
    def test_create_habit(self, db_manager, test_user, test_habit):
        """Test habit creation"""
        # Create user first
        db_manager.create_user(test_user)
        
        # Create habit
        created_habit = db_manager.create_habit(test_habit)
        
        assert created_habit.habit_id == test_habit.habit_id
        assert created_habit.name == test_habit.name
        
        # Retrieve and verify
        habits = db_manager.get_user_habits(test_user.user_id)
        assert len(habits) == 1
        assert habits[0].name == test_habit.name
    
    def test_log_habit(self, db_manager, test_user, test_habit):
        """Test habit logging"""
        # Setup
        db_manager.create_user(test_user)
        db_manager.create_habit(test_habit)
        
        # Create habit log
        habit_log = HabitLog(
            log_id=str(uuid.uuid4()),
            habit_id=test_habit.habit_id,
            user_id=test_user.user_id,
            value=45.0,
            notes="Great workout!"
        )
        
        logged = db_manager.log_habit(habit_log)
        assert logged.value == 45.0
        
        # Retrieve logs
        logs = db_manager.get_habit_logs(test_user.user_id, test_habit.habit_id)
        assert len(logs) == 1
        assert logs[0].value == 45.0
    
    def test_create_goal(self, db_manager, test_user):
        """Test goal creation"""
        db_manager.create_user(test_user)
        
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            user_id=test_user.user_id,
            title="Learn Python",
            description="Complete Python course",
            target_date=datetime.now() + timedelta(days=30),
            status="active"
        )
        
        created_goal = db_manager.create_goal(goal)
        assert created_goal.title == goal.title
        
        # Retrieve goals
        goals = db_manager.get_user_goals(test_user.user_id)
        assert len(goals) == 1
        assert goals[0].title == "Learn Python"


# Habit Tracker Tests
class TestHabitTracker:
    """Test habit tracking functionality"""
    
    @pytest.fixture
    def habit_tracker(self, db_manager):
        """Create habit tracker"""
        return HabitTracker(db_manager)
    
    def test_create_habit(self, habit_tracker, test_user, db_manager):
        """Test habit creation through tracker"""
        db_manager.create_user(test_user)
        
        habit = habit_tracker.create_habit(
            user_id=test_user.user_id,
            name="Reading",
            description="Daily reading",
            frequency=HabitFrequency.DAILY,
            target_value=30.0,
            unit="pages"
        )
        
        assert habit.name == "Reading"
        assert habit.target_value == 30.0
    
    def test_calculate_streak(self, habit_tracker, db_manager, test_user, test_habit):
        """Test streak calculation"""
        # Setup
        db_manager.create_user(test_user)
        db_manager.create_habit(test_habit)
        
        # Log habits for consecutive days
        for i in range(5):
            habit_log = HabitLog(
                log_id=str(uuid.uuid4()),
                habit_id=test_habit.habit_id,
                user_id=test_user.user_id,
                value=30.0,
                logged_at=datetime.now() - timedelta(days=i)
            )
            db_manager.log_habit(habit_log)
        
        streak = habit_tracker.calculate_streak(test_user.user_id, test_habit.habit_id)
        assert streak == 5
    
    def test_habit_statistics(self, habit_tracker, db_manager, test_user, test_habit):
        """Test habit statistics calculation"""
        # Setup
        db_manager.create_user(test_user)
        db_manager.create_habit(test_habit)
        
        # Log some habits
        for i in range(7):
            habit_tracker.log_habit(
                user_id=test_user.user_id,
                habit_id=test_habit.habit_id,
                value=float(25 + i * 2)
            )
        
        stats = habit_tracker.get_habit_statistics(
            test_user.user_id,
            test_habit.habit_id,
            days=7
        )
        
        assert stats['total_logs'] == 7
        assert stats['average_value'] > 0
        assert 'completion_rate' in stats


# Utility Tests
class TestUtils:
    """Test utility functions"""
    
    def test_date_relative_format(self):
        """Test relative date formatting"""
        now = datetime.now()
        
        # Today
        assert "ago" in DateUtils.format_relative_date(now - timedelta(minutes=30))
        
        # Yesterday
        assert "yesterday" in DateUtils.format_relative_date(now - timedelta(days=1))
        
        # Days ago
        assert "days ago" in DateUtils.format_relative_date(now - timedelta(days=3))
    
    def test_days_until(self):
        """Test days until calculation"""
        future_date = datetime.now() + timedelta(days=10)
        days = DateUtils.days_until(future_date)
        assert days == 10
    
    def test_text_truncate(self):
        """Test text truncation"""
        long_text = "This is a very long text that needs to be truncated"
        truncated = TextUtils.truncate(long_text, max_length=20)
        
        assert len(truncated) <= 20
        assert truncated.endswith("...")
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = "I want to learn Python programming and build web applications"
        keywords = TextUtils.extract_keywords(text)
        
        assert "learn" in keywords or "python" in keywords or "programming" in keywords
    
    def test_email_validation(self):
        """Test email validation"""
        assert ValidationUtils.is_valid_email("test@example.com")
        assert ValidationUtils.is_valid_email("user.name@domain.co.uk")
        assert not ValidationUtils.is_valid_email("invalid-email")
        assert not ValidationUtils.is_valid_email("@example.com")
    
    def test_user_id_validation(self):
        """Test user ID validation"""
        assert ValidationUtils.is_valid_user_id("user_john_doe")
        assert ValidationUtils.is_valid_user_id("user_123")
        assert not ValidationUtils.is_valid_user_id("john_doe")
        assert not ValidationUtils.is_valid_user_id("user with spaces")


# Memory Manager Tests (Mocked)
class TestMemoryManager:
    """Test memory management functionality"""
    
    @pytest.fixture
    def mock_memory_manager(self, db_manager, config):
        """Create memory manager with mocked embeddings"""
        with patch('memory_manager.SentenceTransformer'):
            memory_manager = MemoryManager(db_manager, config)
            # Mock the encode method
            memory_manager.embedding_strategy.encode = Mock(return_value=[0.1] * 384)
            return memory_manager
    
    def test_create_memory(self, mock_memory_manager, test_user):
        """Test memory creation"""
        memory = mock_memory_manager.create_memory(
            user_id=test_user.user_id,
            content="I want to learn Python",
            interaction_type=InteractionType.GOAL
        )
        
        assert memory.user_id == test_user.user_id
        assert memory.content == "I want to learn Python"
        assert memory.interaction_type == InteractionType.GOAL
        assert memory.embedding is not None


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_user_journey_workflow(self, db_manager, test_user):
        """Test complete user journey workflow"""
        # 1. Create user
        db_manager.create_user(test_user)
        
        # 2. Create goal
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            user_id=test_user.user_id,
            title="Get fit",
            description="Exercise regularly",
            status="active"
        )
        db_manager.create_goal(goal)
        
        # 3. Create habit
        habit = Habit(
            habit_id=str(uuid.uuid4()),
            user_id=test_user.user_id,
            name="Morning run",
            frequency=HabitFrequency.DAILY,
            target_value=5.0,
            unit="km"
        )
        db_manager.create_habit(habit)
        
        # 4. Log habit
        habit_log = HabitLog(
            log_id=str(uuid.uuid4()),
            habit_id=habit.habit_id,
            user_id=test_user.user_id,
            value=5.2
        )
        db_manager.log_habit(habit_log)
        
        # 5. Verify everything
        retrieved_user = db_manager.get_user(test_user.user_id)
        assert retrieved_user is not None
        
        goals = db_manager.get_user_goals(test_user.user_id)
        assert len(goals) == 1
        
        habits = db_manager.get_user_habits(test_user.user_id)
        assert len(habits) == 1
        
        logs = db_manager.get_habit_logs(test_user.user_id)
        assert len(logs) == 1


# Performance Tests
class TestPerformance:
    """Performance tests"""
    
    def test_bulk_habit_logs(self, db_manager, test_user, test_habit):
        """Test bulk habit log creation"""
        import time
        
        db_manager.create_user(test_user)
        db_manager.create_habit(test_habit)
        
        start_time = time.time()
        
        # Create 100 habit logs
        for i in range(100):
            habit_log = HabitLog(
                log_id=str(uuid.uuid4()),
                habit_id=test_habit.habit_id,
                user_id=test_user.user_id,
                value=float(i)
            )
            db_manager.log_habit(habit_log)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert duration < 5.0
        
        # Verify all logs were created
        logs = db_manager.get_habit_logs(test_user.user_id)
        assert len(logs) == 100


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])