"""
Memory management for Personal Mentor Agent
Implements Strategy Pattern for different embedding strategies
FIXED: Added fallback for SentenceTransformer loading issues
"""
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib

from models import Memory, InteractionType
from database import DatabaseManager
from config import Config


class EmbeddingStrategy(ABC):
    """Abstract base class for embedding strategies - Strategy Pattern"""
    
    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """Encode text to embedding vector"""
        pass
    
    @abstractmethod
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts to embedding vectors"""
        pass


class SentenceTransformerEmbedding(EmbeddingStrategy):
    """Sentence Transformer embedding implementation with fallback"""
    
    def __init__(self, model_name: str):
        self.model = None
        self.model_loaded = False
        
        try:
            import torch
            # Try to load with explicit device
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"Loading embedding model on {device}...")
            
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, device=device)
            self.model_loaded = True
            print(f"✓ Embedding model loaded successfully")
            
        except ImportError as e:
            print(f"⚠ Warning: Required packages not installed: {e}")
            print(f"⚠ Run: pip install torch sentence-transformers")
            print(f"⚠ Falling back to simple hash-based embeddings")
            
        except Exception as e:
            print(f"⚠ Warning: Could not load SentenceTransformer model: {e}")
            print(f"⚠ Falling back to simple hash-based embeddings")
    
    def encode(self, text: str) -> List[float]:
        """Encode single text"""
        if self.model_loaded and self.model is not None:
            try:
                import numpy as np
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                print(f"⚠ Encoding error, using fallback: {e}")
                return self._fallback_encode(text)
        else:
            return self._fallback_encode(text)
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts"""
        if self.model_loaded and self.model is not None:
            try:
                import numpy as np
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                print(f"⚠ Batch encoding error, using fallback: {e}")
                return [self._fallback_encode(text) for text in texts]
        else:
            return [self._fallback_encode(text) for text in texts]
    
    def _fallback_encode(self, text: str) -> List[float]:
        """Fallback encoding using simple hashing (not ideal but works)"""
        # Create a simple 384-dimensional vector from text hash
        # This is a fallback and won't have semantic meaning, but allows the app to work
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Extend hash to 384 dimensions by repeating
        vector = []
        for i in range(384):
            byte_idx = i % len(hash_bytes)
            vector.append(float(hash_bytes[byte_idx]) / 255.0)
        
        return vector


class MemoryManager:
    """Manages user memories with semantic search capabilities"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db_manager = db_manager
        self.config = config
        
        # Try to initialize embedding strategy
        try:
            self.embedding_strategy = SentenceTransformerEmbedding(
                config.database.embedding_model
            )
        except Exception as e:
            print(f"⚠ Warning: Error initializing embeddings: {e}")
            print(f"⚠ Memory search will work with reduced accuracy")
            # Create a minimal fallback that doesn't require torch
            self.embedding_strategy = None
    
    def create_memory(
        self,
        user_id: str,
        content: str,
        interaction_type: InteractionType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Create and store a new memory"""
        memory_id = str(uuid.uuid4())
        
        try:
            if self.embedding_strategy is not None:
                embedding = self.embedding_strategy.encode(content)
            else:
                # Use fallback hash-based embedding
                embedding = self._create_fallback_embedding(content)
        except Exception as e:
            print(f"⚠ Error creating embedding: {e}")
            # Create a zero vector as fallback
            embedding = [0.0] * 384
        
        memory = Memory(
            memory_id=memory_id,
            user_id=user_id,
            content=content,
            interaction_type=interaction_type,
            timestamp=datetime.now(),
            metadata=metadata or {},
            embedding=embedding
        )
        
        # Store in vector database
        try:
            self.db_manager.add_memory_vector(memory)
        except Exception as e:
            print(f"⚠ Warning: Could not store in vector DB: {e}")
            # Continue without vector storage
        
        return memory
    
    def _create_fallback_embedding(self, text: str) -> List[float]:
        """Create a simple hash-based embedding when torch is not available"""
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Extend hash to 384 dimensions by repeating
        vector = []
        for i in range(384):
            byte_idx = i % len(hash_bytes)
            vector.append(float(hash_bytes[byte_idx]) / 255.0)
        
        return vector
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories using semantic similarity"""
        try:
            if self.embedding_strategy is not None:
                query_vector = self.embedding_strategy.encode(query)
            else:
                query_vector = self._create_fallback_embedding(query)
            
            results = self.db_manager.search_similar_memories(
                query_vector=query_vector,
                user_id=user_id,
                limit=limit,
                interaction_type=interaction_type
            )
            
            return results
        except Exception as e:
            print(f"⚠ Memory search error: {e}")
            return []
    
    def get_contextual_memories(
        self,
        user_id: str,
        current_context: str,
        max_memories: int = 10
    ) -> str:
        """Get relevant memories formatted as context for LLM"""
        try:
            memories = self.search_memories(
                user_id=user_id,
                query=current_context,
                limit=max_memories
            )
            
            if not memories:
                return "No relevant past memories found."
            
            context_parts = ["Relevant past memories:"]
            for i, mem in enumerate(memories, 1):
                timestamp = mem.get("timestamp", "Unknown time")
                content = mem.get("content", "")
                interaction_type = mem.get("interaction_type", "")
                
                context_parts.append(
                    f"\n{i}. [{interaction_type.upper()}] ({timestamp}): {content}"
                )
            
            return "\n".join(context_parts)
        except Exception as e:
            print(f"⚠ Error getting contextual memories: {e}")
            return "Unable to retrieve past memories at this time."
    
    def categorize_and_store(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Automatically categorize and store user input
        Uses keyword matching as a simple classification strategy
        """
        content_lower = content.lower()
        
        # Simple keyword-based categorization
        if any(word in content_lower for word in ["goal", "want to", "plan to", "aim to", "target"]):
            interaction_type = InteractionType.GOAL
        elif any(word in content_lower for word in ["struggle", "difficult", "hard", "challenge", "problem"]):
            interaction_type = InteractionType.STRUGGLE
        elif any(word in content_lower for word in ["achieved", "completed", "accomplished", "success", "won"]):
            interaction_type = InteractionType.ACHIEVEMENT
        elif any(word in content_lower for word in ["habit", "tracked", "logged", "daily"]):
            interaction_type = InteractionType.HABIT_LOG
        else:
            interaction_type = InteractionType.CONVERSATION
        
        return self.create_memory(user_id, content, interaction_type, metadata)


class MemoryRetriever:
    """Handles complex memory retrieval operations - Composite Pattern"""
    
    def __init__(self, memory_manager: MemoryManager, db_manager: DatabaseManager):
        self.memory_manager = memory_manager
        self.db_manager = db_manager
    
    def get_journey_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get a comprehensive summary of user's journey"""
        # Get goals
        goals = self.db_manager.get_user_goals(user_id)
        active_goals = [g for g in goals if g.status == "active"]
        completed_goals = [g for g in goals if g.status == "completed"]
        
        # Get recent habit logs
        habit_logs = self.db_manager.get_habit_logs(user_id, days=days)
        
        # Get reflections
        reflections = self.db_manager.get_recent_reflections(user_id, days=days)
        
        # Search for achievements
        try:
            achievement_memories = self.memory_manager.search_memories(
                user_id=user_id,
                query="achievements and successes",
                limit=5,
                interaction_type=InteractionType.ACHIEVEMENT
            )
        except:
            achievement_memories = []
        
        # Search for struggles
        try:
            struggle_memories = self.memory_manager.search_memories(
                user_id=user_id,
                query="challenges and difficulties",
                limit=5,
                interaction_type=InteractionType.STRUGGLE
            )
        except:
            struggle_memories = []
        
        return {
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "recent_habit_logs": habit_logs,
            "recent_reflections": reflections,
            "achievements": achievement_memories,
            "struggles": struggle_memories,
            "summary_period_days": days
        }
    
    def format_journey_for_llm(self, journey_data: Dict[str, Any]) -> str:
        """Format journey data for LLM consumption"""
        parts = []
        
        # Active goals
        if journey_data["active_goals"]:
            parts.append("**Current Active Goals:**")
            for goal in journey_data["active_goals"]:
                target = f" (Target: {goal.target_date.strftime('%Y-%m-%d')})" if goal.target_date else ""
                parts.append(f"- {goal.title}: {goal.description}{target}")
        
        # Completed goals
        if journey_data["completed_goals"]:
            parts.append("\n**Recently Completed Goals:**")
            for goal in journey_data["completed_goals"][:3]:
                parts.append(f"- {goal.title}")
        
        # Recent achievements
        if journey_data["achievements"]:
            parts.append("\n**Recent Achievements:**")
            for ach in journey_data["achievements"][:3]:
                parts.append(f"- {ach['content']}")
        
        # Recent struggles
        if journey_data["struggles"]:
            parts.append("\n**Recent Challenges:**")
            for struggle in journey_data["struggles"][:3]:
                parts.append(f"- {struggle['content']}")
        
        # Habit tracking summary
        if journey_data["recent_habit_logs"]:
            parts.append(f"\n**Habit Tracking:** Logged {len(journey_data['recent_habit_logs'])} habit entries in the last {journey_data['summary_period_days']} days")
        
        return "\n".join(parts) if parts else "No significant journey data yet."