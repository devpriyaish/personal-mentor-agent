"""
Personal Mentor Agent using LangChain with TOOLS
Implements Chain of Responsibility and Template Method patterns
FIXED: Now uses LangChain tools to interact with the database
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import Config
from database import DatabaseManager
from memory_manager import MemoryManager, MemoryRetriever
from models import Conversation, DailyReflection, InteractionType, Goal, Habit, HabitLog, HabitFrequency


class MentorTools:
    """Tools for the mentor agent to interact with the system"""
    
    def __init__(self, db_manager: DatabaseManager, memory_manager: MemoryManager):
        self.db_manager = db_manager
        self.memory_manager = memory_manager
    
    def create_goal(self, user_id: str, title: str, description: str = "", target_date: str = "") -> str:
        """Create a new goal for the user"""
        try:
            from datetime import datetime
            
            goal = Goal(
                goal_id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                description=description,
                target_date=datetime.fromisoformat(target_date) if target_date else None,
                status="active"
            )
            
            self.db_manager.create_goal(goal)
            
            # Store in memory
            self.memory_manager.create_memory(
                user_id=user_id,
                content=f"Created goal: {title}. {description}",
                interaction_type=InteractionType.GOAL
            )
            
            return f"✅ Goal '{title}' created successfully! You can view it in the Goals section."
        except Exception as e:
            return f"❌ Error creating goal: {str(e)}"
    
    def list_goals(self, user_id: str, status: str = "active") -> str:
        """List user's goals"""
        try:
            goals = self.db_manager.get_user_goals(user_id, status=status if status != "all" else None)
            
            if not goals:
                return f"You have no {status} goals yet."
            
            result = [f"Your {status} goals:"]
            for i, goal in enumerate(goals, 1):
                target = f" (Target: {goal.target_date.strftime('%Y-%m-%d')})" if goal.target_date else ""
                result.append(f"{i}. {goal.title}{target}")
                if goal.description:
                    result.append(f"   {goal.description}")
            
            return "\n".join(result)
        except Exception as e:
            return f"❌ Error listing goals: {str(e)}"
    
    def create_habit(self, user_id: str, name: str, description: str = "", frequency: str = "daily", 
                    target_value: float = 0, unit: str = "") -> str:
        """Create a new habit for tracking"""
        try:
            from habit_tracker import HabitTracker
            
            habit_tracker = HabitTracker(self.db_manager)
            
            freq_map = {
                "daily": HabitFrequency.DAILY,
                "weekly": HabitFrequency.WEEKLY,
                "monthly": HabitFrequency.MONTHLY
            }
            
            habit = habit_tracker.create_habit(
                user_id=user_id,
                name=name,
                description=description,
                frequency=freq_map.get(frequency.lower(), HabitFrequency.DAILY),
                target_value=target_value if target_value > 0 else None,
                unit=unit if unit else None
            )
            
            return f"✅ Habit '{name}' created successfully! You can track it in the Habits section."
        except Exception as e:
            return f"❌ Error creating habit: {str(e)}"
    
    def log_habit(self, user_id: str, habit_name: str, value: float, notes: str = "") -> str:
        """Log a habit entry"""
        try:
            from habit_tracker import HabitTracker
            
            # Find habit by name
            habits = self.db_manager.get_user_habits(user_id)
            habit = next((h for h in habits if h.name.lower() == habit_name.lower()), None)
            
            if not habit:
                return f"❌ Habit '{habit_name}' not found. Available habits: {', '.join([h.name for h in habits])}"
            
            habit_tracker = HabitTracker(self.db_manager)
            habit_tracker.log_habit(user_id, habit.habit_id, value, notes)
            
            return f"✅ Logged {value} {habit.unit or 'units'} for '{habit_name}'!"
        except Exception as e:
            return f"❌ Error logging habit: {str(e)}"
    
    def get_progress_summary(self, user_id: str) -> str:
        """Get user's progress summary"""
        try:
            from memory_manager import MemoryRetriever
            
            retriever = MemoryRetriever(self.memory_manager, self.db_manager)
            journey_data = retriever.get_journey_summary(user_id, days=7)
            
            result = ["📊 Your Progress Summary (Last 7 days):"]
            
            # Active goals
            if journey_data["active_goals"]:
                result.append(f"\n🎯 Active Goals: {len(journey_data['active_goals'])}")
                for goal in journey_data["active_goals"][:3]:
                    result.append(f"  • {goal.title}")
            
            # Recent achievements
            if journey_data["achievements"]:
                result.append(f"\n🏆 Recent Achievements:")
                for ach in journey_data["achievements"][:3]:
                    result.append(f"  • {ach['content']}")
            
            # Habit logs
            if journey_data["recent_habit_logs"]:
                result.append(f"\n📈 Habit Logs: {len(journey_data['recent_habit_logs'])} entries")
            
            return "\n".join(result)
        except Exception as e:
            return f"❌ Error getting progress: {str(e)}"


class MentorAgent:
    """Main mentor agent with integrated tools"""
    
    def __init__(
        self, 
        config: Config, 
        db_manager: DatabaseManager,
        memory_manager: MemoryManager
    ):
        self.config = config
        self.db_manager = db_manager
        self.memory_manager = memory_manager
        self.memory_retriever = MemoryRetriever(memory_manager, db_manager)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            api_key=config.llm.api_key
        )
        
        # Initialize tools
        self.mentor_tools = MentorTools(db_manager, memory_manager)
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent"""
        return [
            Tool(
                name="create_goal",
                func=lambda args: self._parse_and_call(self.mentor_tools.create_goal, args),
                description="""Create a new goal for the user. 
                Input should be JSON string with: user_id, title, description (optional), target_date (optional, format: YYYY-MM-DD).
                Example: '{"user_id": "user_123", "title": "Learn Python", "description": "Complete Python course", "target_date": "2025-12-31"}'"""
            ),
            Tool(
                name="list_goals",
                func=lambda args: self._parse_and_call(self.mentor_tools.list_goals, args),
                description="""List user's goals. 
                Input should be JSON string with: user_id, status (optional: 'active', 'completed', or 'all').
                Example: '{"user_id": "user_123", "status": "active"}'"""
            ),
            Tool(
                name="create_habit",
                func=lambda args: self._parse_and_call(self.mentor_tools.create_habit, args),
                description="""Create a new habit for tracking.
                Input should be JSON string with: user_id, name, description (optional), frequency (daily/weekly/monthly), target_value (optional), unit (optional).
                Example: '{"user_id": "user_123", "name": "Exercise", "description": "Daily workout", "frequency": "daily", "target_value": 30, "unit": "minutes"}'"""
            ),
            Tool(
                name="log_habit",
                func=lambda args: self._parse_and_call(self.mentor_tools.log_habit, args),
                description="""Log a habit entry.
                Input should be JSON string with: user_id, habit_name, value, notes (optional).
                Example: '{"user_id": "user_123", "habit_name": "Exercise", "value": 45, "notes": "Great workout!"}'"""
            ),
            Tool(
                name="get_progress",
                func=lambda args: self._parse_and_call(self.mentor_tools.get_progress_summary, args),
                description="""Get user's progress summary including goals, achievements, and habits.
                Input should be JSON string with: user_id.
                Example: '{"user_id": "user_123"}'"""
            )
        ]
    
    def _parse_and_call(self, func, args_str: str):
        """Parse JSON arguments and call function"""
        import json
        try:
            args = json.loads(args_str)
            return func(**args)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON format. Expected JSON string."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent with tools"""
        system_prompt = """You are a compassionate and insightful personal mentor AI assistant. You have access to tools that let you interact with the user's goals, habits, and progress directly in this application.

IMPORTANT: You are NOT just a chatbot - you are an INTEGRATED AGENT with the ability to:
- CREATE goals directly in the Goals section using the create_goal tool
- LIST the user's current goals using the list_goals tool
- CREATE habits for tracking using the create_habit tool
- LOG habit entries using the log_habit tool
- CHECK user's progress using the get_progress tool

When a user asks about goals or habits, USE YOUR TOOLS to interact with the system directly rather than just suggesting they do it manually.

For example:
- User: "Can you set a goal for me to exercise daily?"
- You: Use the create_goal tool to actually create the goal, then confirm it was created

- User: "What are my current goals?"
- You: Use the list_goals tool to show them their actual goals from the system

- User: "Where can I set goals?"
- You: "You can set goals right here! Just tell me what goal you'd like to create and I'll add it to your Goals section."

Your role is to:
1. Support the user's personal growth journey
2. Remember and reference their past goals, struggles, and achievements
3. Provide thoughtful, personalized advice based on their history
4. USE YOUR TOOLS to interact with goals, habits, and progress directly
5. Celebrate their wins and help them navigate challenges
6. Ask meaningful questions to deepen understanding
7. Offer actionable suggestions and encouragement

Guidelines:
- Be warm, empathetic, and non-judgmental
- Use their past context to make connections and insights
- Keep responses concise but meaningful (2-4 paragraphs typically)
- Focus on growth mindset and positive reinforcement
- When appropriate, ask clarifying questions
- Acknowledge their emotions and validate their experiences
- Provide specific, actionable advice when requested
- ALWAYS use your tools when the user wants to interact with goals/habits/progress

Remember: You are a supportive companion on their personal development journey with direct access to their tracking system."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
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
        
        # Build chat history for agent
        chat_history = []
        for conv in recent_conversations[-6:]:
            if conv.role == "user":
                chat_history.append(HumanMessage(content=conv.content))
            elif conv.role == "assistant":
                chat_history.append(AIMessage(content=conv.content))
        
        # Prepare input with context
        full_input = f"{context_str}\n\nUser's current message: {input_text}"
        
        # Get response from agent
        try:
            response = self.agent_executor.invoke({
                "input": full_input,
                "chat_history": chat_history
            })
            response_text = response["output"]
        except Exception as e:
            response_text = f"I apologize, but I encountered an error: {str(e)}. Let me try to help you anyway. {input_text}"
        
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


class ReflectionAgent:
    """Agent specialized in generating daily reflections - NOW INCLUDES CHAT HISTORY"""
    
    def __init__(
        self,
        config: Config,
        db_manager: DatabaseManager,
        memory_manager: MemoryManager
    ):
        self.config = config
        self.db_manager = db_manager
        self.memory_manager = memory_manager
        self.memory_retriever = MemoryRetriever(memory_manager, db_manager)
        
        self.llm = ChatOpenAI(
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            api_key=config.llm.api_key
        )
    
    def get_system_prompt(self) -> str:
        """Get reflection system prompt"""
        return """You are a reflective personal mentor AI specializing in generating insightful daily reflections.

Your task is to:
1. Analyze the user's recent journey, activities, conversations, and progress
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
        """Generate a comprehensive daily reflection including chat history"""
        # Get journey data from SQLite
        journey_data = self.memory_retriever.get_journey_summary(user_id, days=7)
        journey_context = self.memory_retriever.format_journey_for_llm(journey_data)
        
        # Get recent conversations
        recent_convs = self.db_manager.get_conversation_history(user_id, limit=20)
        conv_summary = self._summarize_conversations(recent_convs)
        
        # Get recent chat themes from vector memory
        chat_memories = self.memory_manager.search_memories(
            user_id=user_id,
            query="recent conversations and discussions",
            limit=10
        )
        
        chat_themes = "\n".join([
            f"- {mem['content']}" for mem in chat_memories[:5]
        ]) if chat_memories else "No recent chat history"
        
        # Build comprehensive prompt
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on this user's recent journey, generate a meaningful daily reflection:

=== GOALS & HABITS (from tracking system) ===
{journey_context}

=== RECENT CONVERSATIONS (chat history) ===
{conv_summary}

=== KEY DISCUSSION THEMES ===
{chat_themes}

Generate a reflection that:
1. Acknowledges their progress in both tracked goals AND conversation topics
2. Identifies patterns between what they discuss and what they track
3. Provides encouragement based on their complete journey
4. Offers suggestions that connect their conversations with their actions""")
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
        
        # Get last 10 messages
        recent_msgs = user_messages[-10:]
        return "Recent discussion topics:\n" + "\n".join([f"- {msg[:100]}..." for msg in recent_msgs])
    
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
        return self.mentor_agent.memory_retriever.get_journey_summary(user_id, days)