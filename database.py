"""
Database management for Personal Mentor Agent
Implements Repository Pattern and DAO Pattern
"""
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import json

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from models import (
    User, Memory, Habit, HabitLog, Goal, DailyReflection, 
    Conversation, InteractionType, HabitFrequency
)
from config import Config


class DatabaseInterface(ABC):
    """Abstract base class for database operations"""
    
    @abstractmethod
    def connect(self):
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection"""
        pass
    
    @abstractmethod
    def initialize(self):
        """Initialize database schema"""
        pass


class SQLiteDatabase(DatabaseInterface):
    """SQLite database manager - Singleton Pattern"""
    _instance = None
    
    def __new__(cls, db_path: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path
            cls._instance.connection = None
        return cls._instance
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def initialize(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    timezone TEXT DEFAULT 'UTC',
                    preferences TEXT
                )
            """)
            
            # Habits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS habits (
                    habit_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    frequency TEXT NOT NULL,
                    target_value REAL,
                    unit TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Habit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS habit_logs (
                    log_id TEXT PRIMARY KEY,
                    habit_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    value REAL NOT NULL,
                    notes TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (habit_id) REFERENCES habits(habit_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Goals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Daily reflections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_reflections (
                    reflection_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sentiment_score REAL,
                    key_insights TEXT,
                    suggestions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    message_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            conn.commit()


class QdrantDatabase(DatabaseInterface):
    """Qdrant vector database manager"""
    
    def __init__(self, host: str, port: int, collection_name: str, vector_size: int):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = None
    
    def connect(self):
        """Establish Qdrant connection"""
        self.client = QdrantClient(host=self.host, port=self.port)
        return self.client
    
    def disconnect(self):
        """Close Qdrant connection"""
        if self.client:
            self.client.close()
            self.client = None
    
    def initialize(self):
        """Initialize Qdrant collection"""
        if not self.client:
            self.connect()
        
        collections = self.client.get_collections().collections
        collection_exists = any(col.name == self.collection_name for col in collections)
        
        if not collection_exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
    
    def add_memory(self, memory: Memory):
        """Add memory to vector database"""
        if not memory.embedding:
            raise ValueError("Memory must have an embedding")
        
        point = PointStruct(
            id=memory.memory_id,
            vector=memory.embedding,
            payload={
                "user_id": memory.user_id,
                "content": memory.content,
                "interaction_type": memory.interaction_type.value,
                "timestamp": memory.timestamp.isoformat(),
                "metadata": memory.metadata
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    def search_memories(
        self, 
        query_vector: List[float], 
        user_id: str, 
        limit: int = 10,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]
        
        if interaction_type:
            filter_conditions.append(
                FieldCondition(
                    key="interaction_type", 
                    match=MatchValue(value=interaction_type.value)
                )
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=filter_conditions),
            limit=limit
        )
        
        return [
            {
                "memory_id": result.id,
                "score": result.score,
                **result.payload
            }
            for result in results
        ]


class DatabaseManager:
    """Main database manager - Facade Pattern"""
    
    def __init__(self, config: Config):
        self.config = config
        self.sqlite_db = SQLiteDatabase(config.database.sqlite_db_path)
        self.vector_db = QdrantDatabase(
            host=config.database.qdrant_host,
            port=config.database.qdrant_port,
            collection_name=config.database.qdrant_collection,
            vector_size=config.database.vector_size
        )
    
    def initialize_all(self):
        """Initialize all databases"""
        self.sqlite_db.initialize()
        self.vector_db.initialize()
    
    # User operations
    def create_user(self, user: User) -> User:
        """Create a new user"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, name, email, created_at, timezone, preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user.user_id, user.name, user.email, 
                user.created_at, user.timezone, json.dumps(user.preferences)
            ))
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row["user_id"],
                    name=row["name"],
                    email=row["email"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    timezone=row["timezone"],
                    preferences=json.loads(row["preferences"]) if row["preferences"] else {}
                )
        return None
    
    # Habit operations
    def create_habit(self, habit: Habit) -> Habit:
        """Create a new habit"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO habits (habit_id, user_id, name, description, frequency, 
                                   target_value, unit, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                habit.habit_id, habit.user_id, habit.name, habit.description,
                habit.frequency.value, habit.target_value, habit.unit,
                habit.created_at, habit.is_active
            ))
        return habit
    
    def get_user_habits(self, user_id: str, active_only: bool = True) -> List[Habit]:
        """Get all habits for a user"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM habits WHERE user_id = ?"
            params = [user_id]
            
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                Habit(
                    habit_id=row["habit_id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    description=row["description"],
                    frequency=HabitFrequency(row["frequency"]),
                    target_value=row["target_value"],
                    unit=row["unit"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    is_active=bool(row["is_active"])
                )
                for row in rows
            ]
    
    def log_habit(self, habit_log: HabitLog) -> HabitLog:
        """Log a habit entry"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO habit_logs (log_id, habit_id, user_id, value, notes, logged_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                habit_log.log_id, habit_log.habit_id, habit_log.user_id,
                habit_log.value, habit_log.notes, habit_log.logged_at
            ))
        return habit_log
    
    def get_habit_logs(
        self, 
        user_id: str, 
        habit_id: Optional[str] = None,
        days: int = 30
    ) -> List[HabitLog]:
        """Get habit logs for a user"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM habit_logs 
                WHERE user_id = ? 
                AND logged_at >= datetime('now', '-' || ? || ' days')
            """
            params = [user_id, days]
            
            if habit_id:
                query += " AND habit_id = ?"
                params.append(habit_id)
            
            query += " ORDER BY logged_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                HabitLog(
                    log_id=row["log_id"],
                    habit_id=row["habit_id"],
                    user_id=row["user_id"],
                    value=row["value"],
                    notes=row["notes"],
                    logged_at=datetime.fromisoformat(row["logged_at"])
                )
                for row in rows
            ]
    
    # Goal operations
    def create_goal(self, goal: Goal) -> Goal:
        """Create a new goal"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO goals (goal_id, user_id, title, description, target_date, 
                                  status, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal.goal_id, goal.user_id, goal.title, goal.description,
                goal.target_date, goal.status, goal.created_at, goal.completed_at
            ))
        return goal
    
    def delete_goal(self, goal_id: str) -> None:
      """Delete a goal"""
      with self.sqlite_db.get_connection() as conn:
          cursor = conn.cursor()
          cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))

    def update_goal(self, goal: Goal) -> None:
      """Update an existing goal"""
      with self.sqlite_db.get_connection() as conn:
          cursor = conn.cursor()
          cursor.execute("""
              UPDATE goals 
              SET title = ?, description = ?, target_date = ?, 
                  status = ?, completed_at = ?
              WHERE goal_id = ?
          """, (
              goal.title, goal.description, goal.target_date,
              goal.status, goal.completed_at, goal.goal_id
          ))
    
    def get_user_goals(self, user_id: str, status: Optional[str] = None) -> List[Goal]:
        """Get goals for a user"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM goals WHERE user_id = ?"
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                Goal(
                    goal_id=row["goal_id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    description=row["description"],
                    target_date=datetime.fromisoformat(row["target_date"]) if row["target_date"] else None,
                    status=row["status"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
                )
                for row in rows
            ]
    
    def update_goal_status(self, goal_id: str, status: str) -> None:
        """Update goal status"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            completed_at = datetime.now() if status == "completed" else None
            cursor.execute("""
                UPDATE goals SET status = ?, completed_at = ?
                WHERE goal_id = ?
            """, (status, completed_at, goal_id))
    
    # Reflection operations
    def create_reflection(self, reflection: DailyReflection) -> DailyReflection:
        """Create a daily reflection"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_reflections 
                (reflection_id, user_id, content, sentiment_score, key_insights, suggestions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                reflection.reflection_id, reflection.user_id, reflection.content,
                reflection.sentiment_score, json.dumps(reflection.key_insights),
                json.dumps(reflection.suggestions), reflection.created_at
            ))
        return reflection
    
    def get_recent_reflections(self, user_id: str, days: int = 7) -> List[DailyReflection]:
        """Get recent reflections"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_reflections 
                WHERE user_id = ? 
                AND created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            """, (user_id, days))
            rows = cursor.fetchall()
            
            return [
                DailyReflection(
                    reflection_id=row["reflection_id"],
                    user_id=row["user_id"],
                    content=row["content"],
                    sentiment_score=row["sentiment_score"],
                    key_insights=json.loads(row["key_insights"]) if row["key_insights"] else [],
                    suggestions=json.loads(row["suggestions"]) if row["suggestions"] else [],
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                for row in rows
            ]
    
    # Conversation operations
    def save_conversation(self, conversation: Conversation) -> Conversation:
        """Save a conversation message"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (message_id, user_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conversation.message_id, conversation.user_id, conversation.role,
                conversation.content, conversation.timestamp, json.dumps(conversation.metadata)
            ))
        return conversation
    
    def get_conversation_history(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Conversation]:
        """Get conversation history"""
        with self.sqlite_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            
            conversations = [
                Conversation(
                    message_id=row["message_id"],
                    user_id=row["user_id"],
                    role=row["role"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                )
                for row in rows
            ]
            
            return list(reversed(conversations))
    
    # Vector database operations
    def add_memory_vector(self, memory: Memory):
        """Add memory to vector database"""
        self.vector_db.add_memory(memory)
    
    def search_similar_memories(
        self,
        query_vector: List[float],
        user_id: str,
        limit: int = 10,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        return self.vector_db.search_memories(
            query_vector, user_id, limit, interaction_type
        )