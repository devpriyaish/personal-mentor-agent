"""
Personal Mentor Agent using LangChain
Implements Chain of Responsibility and Template Method patterns
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

from config import Config
from database import DatabaseManager
from memory_manager import MemoryManager, MemoryRetriever
from models import Conversation, DailyReflection, InteractionType


class BaseAgent(ABC):
    """Abstract base class for agents - Template Method Pattern"""
    
    def __init__(self, config: Config, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.llm = ChatOpenAI(
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            api_key=config.llm.api_key
        )
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        pass
    
    @abstractmethod
    def process(self, user_id: str, input_text: str, context: Dict[str, Any]) -> str:
        """Process user input and return response"""
        pass


class MentorAgent(BaseAgent):
    """Main mentor agent for daily interactions"""
    
    def __init__(
        self, 
        config: Config, 
        db_manager: DatabaseManager,
        memory_manager: MemoryManager
    ):
        super().__init__(config, db_manager)
        self.memory_manager = memory_manager
        self.memory_retriever = MemoryRetriever(memory_manager, db_manager)
    
    def get_system_prompt(self) -> str:
        """Get mentor system prompt"""
        return """You are a compassionate and insightful personal mentor AI. Your role is to:

1. Support the user's personal growth journey
2. Remember and reference their past goals, struggles, and achievements
3. Provide thoughtful, personalized advice based on their history
4. Celebrate their wins and help them navigate challenges
5. Ask meaningful questions to deepen understanding
6. Offer actionable suggestions and encouragement
7. Track their progress and provide reflections

Guidelines:
- Be warm, empathetic, and non-judgmental
- Use their past context to make connections and insights
- Keep responses concise but meaningful (2-4 paragraphs typically)
- Focus on growth mindset and positive reinforcement
- When appropriate, ask clarifying questions
- Acknowledge their emotions and validate their experiences
- Provide specific, actionable advice when requested

Remember: You are a supportive companion on their personal development journey."""
    
    def _build_context(self, user_id: str, current_input: str) -> str:
        """Build comprehensive context for the agent"""
        # Get journey summary
        journey_data = self.memory_retriever.get_journey_summary(user_id, days=30)
        journey_context = self.memory_retriever.format_journey_for_llm(journey_data)
        
        # Get relevant memories
        relevant_memories = self.memory_manager.get_contextual_memories(
            user_id=user_id,
            current_context=current_input,
            max_memories=self.config.app.max_memory_context
        )
        
        context_parts = [
            "=== USER'S JOURNEY CONTEXT ===",
            journey_context,
            "\n=== RELEVANT PAST CONVERSATIONS ===",
            relevant_memories
        ]
        
        return "\n\n".join(context_parts)
    
    def process(
        self, 
        user_id: str, 
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process user input and generate mentor response"""
        # Store user message in memory
        self.memory_manager.categorize_and_store(user_id, input_text)
        
        # Build context
        context_str = self._build_context(user_id, input_text)
        
        # Get conversation history
        recent_conversations = self.db_manager.get_conversation_history(
            user_id, limit=10
        )
        
        # Build messages
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            SystemMessage(content=f"Context about the user:\n{context_str}")
        ]
        
        # Add recent conversation history
        for conv in recent_conversations[-6:]:  # Last 3 exchanges
            if conv.role == "user":
                messages.append(HumanMessage(content=conv.content))
            elif conv.role == "assistant":
                messages.append(AIMessage(content=conv.content))
        
        # Add current message
        messages.append(HumanMessage(content=input_text))
        
        # Get response
        response = self.llm.invoke(messages)
        response_text = response.content
        
        # Store conversation
        self._save_conversation(user_id, input_text, response_text)
        
        return response_text
    
    def _save_conversation(self, user_id: str, user_input: str, assistant_response: str):
        """Save conversation to database"""
        # Save user message
        self.db_manager.save_conversation(
            Conversation(
                message_id=str(uuid.uuid4()),
                user_id=user_id,
                role="user",
                content=user_input,
                timestamp=datetime.now()
            )
        )
        
        # Save assistant message
        self.db_manager.save_conversation(
            Conversation(
                message_id=str(uuid.uuid4()),
                user_id=user_id,
                role="assistant",
                content=assistant_response,
                timestamp=datetime.now()
            )
        )


class ReflectionAgent(BaseAgent):
    """Agent specialized in generating daily reflections"""
    
    def __init__(
        self,
        config: Config,
        db_manager: DatabaseManager,
        memory_manager: MemoryManager
    ):
        super().__init__(config, db_manager)
        self.memory_manager = memory_manager
        self.memory_retriever = MemoryRetriever(memory_manager, db_manager)
    
    def get_system_prompt(self) -> str:
        """Get reflection system prompt"""
        return """You are a reflective personal mentor AI specializing in generating insightful daily reflections.

Your task is to:
1. Analyze the user's recent journey, activities, and progress
2. Identify key patterns, wins, and growth areas
3. Generate a meaningful reflection that connects past and present
4. Provide 3-5 actionable suggestions or motivational nudges
5. Highlight their strengths and progress

Format your response as:
**Daily Reflection**
[2-3 paragraphs of thoughtful reflection]

**Key Insights**
- [Insight 1]
- [Insight 2]
- [Insight 3]

**Suggestions for Today**
- [Actionable suggestion 1]
- [Actionable suggestion 2]
- [Actionable suggestion 3]

Be encouraging, specific, and connect to their stated goals and values."""
    
    def generate_daily_reflection(self, user_id: str) -> DailyReflection:
        """Generate a comprehensive daily reflection"""
        # Get journey data
        journey_data = self.memory_retriever.get_journey_summary(user_id, days=7)
        journey_context = self.memory_retriever.format_journey_for_llm(journey_data)
        
        # Get recent conversations
        recent_convs = self.db_manager.get_conversation_history(user_id, limit=20)
        conv_summary = self._summarize_conversations(recent_convs)
        
        # Build prompt
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on this user's recent journey, generate a meaningful daily reflection:

{journey_context}

Recent conversation themes: {conv_summary}

Generate a reflection that acknowledges their progress, addresses challenges, and provides encouragement.""")
        ]
        
        # Generate reflection
        response = self.llm.invoke(messages)
        reflection_content = response.content
        
        # Parse key insights and suggestions
        key_insights, suggestions = self._parse_reflection(reflection_content)
        
        # Create and save reflection
        reflection = DailyReflection(
            reflection_id=str(uuid.uuid4()),
            user_id=user_id,
            content=reflection_content,
            key_insights=key_insights,
            suggestions=suggestions,
            created_at=datetime.now()
        )
        
        self.db_manager.create_reflection(reflection)
        
        return reflection
    
    def _summarize_conversations(self, conversations: List[Conversation]) -> str:
        """Summarize recent conversation themes"""
        if not conversations:
            return "No recent conversations"
        
        user_messages = [c.content for c in conversations if c.role == "user"]
        if not user_messages:
            return "No recent user messages"
        
        # Simple keyword extraction
        keywords = []
        for msg in user_messages[-5:]:
            words = msg.lower().split()
            keywords.extend([w for w in words if len(w) > 5])
        
        return ", ".join(list(set(keywords))[:10]) if keywords else "General conversation"
    
    def _parse_reflection(self, content: str) -> tuple[List[str], List[str]]:
        """Parse key insights and suggestions from reflection"""
        insights = []
        suggestions = []
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'Key Insights' in line:
                current_section = 'insights'
            elif 'Suggestions' in line:
                current_section = 'suggestions'
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if current_section == 'insights' and item:
                    insights.append(item)
                elif current_section == 'suggestions' and item:
                    suggestions.append(item)
        
        return insights, suggestions
    
    def process(
        self,
        user_id: str,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process reflection request"""
        reflection = self.generate_daily_reflection(user_id)
        return reflection.content


class AgentOrchestrator:
    """Orchestrates different agents - Facade Pattern"""
    
    def __init__(
        self,
        config: Config,
        db_manager: DatabaseManager,
        memory_manager: MemoryManager
    ):
        self.config = config
        self.db_manager = db_manager
        self.memory_manager = memory_manager
        
        # Initialize agents
        self.mentor_agent = MentorAgent(config, db_manager, memory_manager)
        self.reflection_agent = ReflectionAgent(config, db_manager, memory_manager)
    
    def chat(self, user_id: str, message: str) -> str:
        """Handle chat interaction"""
        return self.mentor_agent.process(user_id, message)
    
    def generate_reflection(self, user_id: str) -> DailyReflection:
        """Generate daily reflection"""
        return self.reflection_agent.generate_daily_reflection(user_id)
    
    def get_journey_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get journey summary"""
        return self.memory_manager.memory_retriever.get_journey_summary(
            user_id, days
        )