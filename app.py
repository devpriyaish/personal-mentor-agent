"""
Streamlit UI for Personal Mentor Agent
Main application entry point
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()


import uuid
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

from config import Config
from database import DatabaseManager
from memory_manager import MemoryManager
from mentor_agent import AgentOrchestrator
from habit_tracker import HabitTracker, HabitAnalytics, HabitStreakObserver
from models import User, Goal, HabitFrequency, InteractionType


# Page configuration
st.set_page_config(
    page_title="Personal Mentor Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


class MentorApp:
    """Main application class - Facade Pattern"""
    
    def __init__(self):
        self.initialize_session_state()
        self.config = Config.load_from_env()
        
        # Initialize components
        if "initialized" not in st.session_state:
            self.db_manager = DatabaseManager(self.config)
            self.db_manager.initialize_all()
            
            self.memory_manager = MemoryManager(self.db_manager, self.config)
            self.agent_orchestrator = AgentOrchestrator(
                self.config, self.db_manager, self.memory_manager
            )
            self.habit_tracker = HabitTracker(self.db_manager)
            self.habit_analytics = HabitAnalytics(self.db_manager)
            
            # Attach observers
            self.habit_tracker.attach_observer(HabitStreakObserver())
            
            # Store in session state
            st.session_state.db_manager = self.db_manager
            st.session_state.memory_manager = self.memory_manager
            st.session_state.agent_orchestrator = self.agent_orchestrator
            st.session_state.habit_tracker = self.habit_tracker
            st.session_state.habit_analytics = self.habit_analytics
            st.session_state.initialized = True
        else:
            self.db_manager = st.session_state.db_manager
            self.memory_manager = st.session_state.memory_manager
            self.agent_orchestrator = st.session_state.agent_orchestrator
            self.habit_tracker = st.session_state.habit_tracker
            self.habit_analytics = st.session_state.habit_analytics
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
    
    def run(self):
        """Run the application"""
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .stat-card {
            background-color: #f0f2f6;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1f77b4;
        }
        .stat-label {
            font-size: 1rem;
            color: #666;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        if st.session_state.user_id is None:
            self.render_welcome_page()
        else:
            self.render_main_app()
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.markdown("# 🧠 Personal Mentor")
            st.markdown("---")
            
            if st.session_state.user_id:
                user = self.db_manager.get_user(st.session_state.user_id)
                st.markdown(f"### Welcome, {user.name}!")
                
                st.markdown("---")
                st.markdown("### Navigation")
                
                page = st.radio(
                    "Go to",
                    ["💬 Chat", "📊 Dashboard", "🎯 Goals", "📈 Habits", "🔮 Reflections"],
                    label_visibility="collapsed"
                )
                
                st.session_state.current_page = page
                
                st.markdown("---")
                if st.button("🚪 Logout"):
                    st.session_state.user_id = None
                    st.session_state.chat_messages = []
                    st.rerun()
            else:
                st.info("Please login or create an account to continue.")
    
    def render_welcome_page(self):
        """Render welcome/login page"""
        st.markdown('<p class="main-header">Welcome to Your Personal Mentor Agent</p>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        Your AI-powered companion for personal growth and development.
        
        **Features:**
        - 💬 Daily mentoring conversations with memory
        - 🎯 Goal setting and tracking
        - 📈 Habit tracking with analytics
        - 🔮 Personalized daily reflections
        - 📊 Progress visualization
        """)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🔑 Login")
            login_name = st.text_input("Your Name", key="login_name")
            if st.button("Login"):
                if login_name:
                    # Simple login - in production, use proper authentication
                    user_id = f"user_{login_name.lower().replace(' ', '_')}"
                    user = self.db_manager.get_user(user_id)
                    
                    if user:
                        st.session_state.user_id = user_id
                        st.success(f"Welcome back, {user.name}!")
                        st.rerun()
                    else:
                        st.error("User not found. Please create an account.")
        
        with col2:
            st.markdown("### ✨ Create Account")
            new_name = st.text_input("Your Name", key="new_name")
            new_email = st.text_input("Email (optional)", key="new_email")
            if st.button("Create Account"):
                if new_name:
                    user_id = f"user_{new_name.lower().replace(' ', '_')}"
                    
                    # Check if user exists
                    existing_user = self.db_manager.get_user(user_id)
                    if existing_user:
                        st.error("User already exists. Please login.")
                    else:
                        # Create new user
                        user = User(
                            user_id=user_id,
                            name=new_name,
                            email=new_email if new_email else None,
                            created_at=datetime.now()
                        )
                        self.db_manager.create_user(user)
                        st.session_state.user_id = user_id
                        st.success(f"Account created! Welcome, {new_name}!")
                        st.rerun()
    
    def render_main_app(self):
        """Render main application based on selected page"""
        page = st.session_state.get("current_page", "💬 Chat")
        
        if page == "💬 Chat":
            self.render_chat_page()
        elif page == "📊 Dashboard":
            self.render_dashboard_page()
        elif page == "🎯 Goals":
            self.render_goals_page()
        elif page == "📈 Habits":
            self.render_habits_page()
        elif page == "🔮 Reflections":
            self.render_reflections_page()
    
    def render_chat_page(self):
        """Render chat interface"""
        st.markdown('<p class="main-header">💬 Chat with Your Mentor</p>', 
                   unsafe_allow_html=True)
        
        # Load conversation history
        if not st.session_state.chat_messages:
            history = self.db_manager.get_conversation_history(
                st.session_state.user_id, limit=20
            )
            st.session_state.chat_messages = [
                {"role": conv.role, "content": conv.content}
                for conv in history
            ]
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Share your thoughts, goals, or challenges..."):
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self.agent_orchestrator.chat(
                        st.session_state.user_id, prompt
                    )
                    st.markdown(response)
            
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": response}
            )
            
            st.rerun()
    
    def render_dashboard_page(self):
        """Render dashboard with overview"""
        st.markdown('<p class="main-header">📊 Your Dashboard</p>', 
                   unsafe_allow_html=True)
        
        user_id = st.session_state.user_id
        
        # Statistics row
        col1, col2, col3, col4 = st.columns(4)
        
        # Active goals
        goals = self.db_manager.get_user_goals(user_id, status="active")
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(goals)}</div>
                <div class="stat-label">Active Goals</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Active habits
        habits = self.habit_tracker.get_user_habits(user_id)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(habits)}</div>
                <div class="stat-label">Active Habits</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Weekly logs
        weekly_summary = self.habit_analytics.get_weekly_summary(user_id)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{weekly_summary['total_logs']}</div>
                <div class="stat-label">Logs This Week</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Reflections
        reflections = self.db_manager.get_recent_reflections(user_id, days=7)
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{len(reflections)}</div>
                <div class="stat-label">Recent Reflections</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Recent activity
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📈 Recent Activity")
            
            if habits:
                for habit in habits[:3]:
                    stats = self.habit_tracker.get_habit_statistics(
                        user_id, habit.habit_id, days=7
                    )
                    
                    st.markdown(f"**{habit.name}**")
                    progress = min(stats['completion_rate'], 100)
                    st.progress(progress / 100)
                    st.caption(f"Completion: {progress:.1f}% | Streak: {stats['streak']} days")
            else:
                st.info("No habits tracked yet. Create one in the Habits section!")
        
        with col2:
            st.markdown("### 🎯 Quick Actions")
            if st.button("📝 Log Habit", use_container_width=True):
                st.session_state.current_page = "📈 Habits"
                st.rerun()
            if st.button("🎯 Add Goal", use_container_width=True):
                st.session_state.current_page = "🎯 Goals"
                st.rerun()
            if st.button("🔮 Generate Reflection", use_container_width=True):
                with st.spinner("Generating reflection..."):
                    reflection = self.agent_orchestrator.generate_reflection(user_id)
                    st.success("Reflection generated!")
                    st.session_state.current_page = "🔮 Reflections"
                    st.rerun()
    
    def render_goals_page(self):
        """Render goals management page"""
        st.markdown('<p class="main-header">🎯 Your Goals</p>', 
                   unsafe_allow_html=True)
        
        user_id = st.session_state.user_id
        
        # Add new goal
        with st.expander("➕ Add New Goal"):
            with st.form("new_goal_form"):
                goal_title = st.text_input("Goal Title")
                goal_description = st.text_area("Description")
                target_date = st.date_input("Target Date (optional)")
                
                submitted = st.form_submit_button("Create Goal")
                if submitted and goal_title:
                    goal = Goal(
                        goal_id=str(uuid.uuid4()),
                        user_id=user_id,
                        title=goal_title,
                        description=goal_description,
                        target_date=datetime.combine(target_date, datetime.min.time()) if target_date else None,
                        status="active",
                        created_at=datetime.now()
                    )
                    self.db_manager.create_goal(goal)
                    
                    # Store in memory
                    self.memory_manager.create_memory(
                        user_id=user_id,
                        content=f"New goal: {goal_title}. {goal_description}",
                        interaction_type=InteractionType.GOAL
                    )
                    
                    st.success("Goal created!")
                    st.rerun()
        
        # Display goals
        tabs = st.tabs(["Active", "Completed", "All"])
        
        with tabs[0]:
            goals = self.db_manager.get_user_goals(user_id, status="active")
            self.display_goals(goals)
        
        with tabs[1]:
            goals = self.db_manager.get_user_goals(user_id, status="completed")
            self.display_goals(goals)
        
        with tabs[2]:
            goals = self.db_manager.get_user_goals(user_id)
            self.display_goals(goals)
    
    def display_goals(self, goals: list):
        """Display list of goals"""
        if not goals:
            st.info("No goals yet. Create your first goal above!")
            return
        
        for goal in goals:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    status_emoji = "✅" if goal.status == "completed" else "🎯"
                    st.markdown(f"### {status_emoji} {goal.title}")
                    st.markdown(goal.description)
                    
                    if goal.target_date:
                        days_left = (goal.target_date.date() - datetime.now().date()).days
                        if days_left > 0:
                            st.caption(f"📅 Target: {goal.target_date.strftime('%Y-%m-%d')} ({days_left} days left)")
                        else:
                            st.caption(f"📅 Target: {goal.target_date.strftime('%Y-%m-%d')} (Overdue)")
                
                with col2:
                    if goal.status == "active":
                        if st.button("Mark Complete", key=f"complete_{goal.goal_id}"):
                            self.db_manager.update_goal_status(goal.goal_id, "completed")
                            
                            # Store achievement
                            self.memory_manager.create_memory(
                                user_id=goal.user_id,
                                content=f"Completed goal: {goal.title}",
                                interaction_type=InteractionType.ACHIEVEMENT
                            )
                            
                            st.success("Goal completed! 🎉")
                            st.rerun()
                
                st.markdown("---")
    
    def render_habits_page(self):
        """Render habits tracking page"""
        st.markdown('<p class="main-header">📈 Habit Tracker</p>', 
                   unsafe_allow_html=True)
        
        user_id = st.session_state.user_id
        
        # Add new habit
        with st.expander("➕ Create New Habit"):
            with st.form("new_habit_form"):
                habit_name = st.text_input("Habit Name")
                habit_description = st.text_area("Description (optional)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    frequency = st.selectbox(
                        "Frequency",
                        options=[f.value for f in HabitFrequency]
                    )
                with col2:
                    target_value = st.number_input("Target Value (optional)", min_value=0.0)
                with col3:
                    unit = st.text_input("Unit (e.g., minutes, pages)")
                
                submitted = st.form_submit_button("Create Habit")
                if submitted and habit_name:
                    habit = self.habit_tracker.create_habit(
                        user_id=user_id,
                        name=habit_name,
                        description=habit_description,
                        frequency=HabitFrequency(frequency),
                        target_value=target_value if target_value > 0 else None,
                        unit=unit if unit else None
                    )
                    st.success(f"Habit '{habit_name}' created!")
                    st.rerun()
        
        # Display habits
        habits = self.habit_tracker.get_user_habits(user_id)
        
        if not habits:
            st.info("No habits yet. Create your first habit above!")
            return
        
        # Habit tabs
        habit_tabs = st.tabs([h.name for h in habits])
        
        for i, habit in enumerate(habits):
            with habit_tabs[i]:
                self.render_habit_detail(habit)
    
    def render_habit_detail(self, habit):
        """Render detailed habit view"""
        user_id = st.session_state.user_id
        
        # Log entry
        with st.form(f"log_habit_{habit.habit_id}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                value = st.number_input(
                    f"Log {habit.unit or 'value'} for {habit.name}",
                    min_value=0.0,
                    step=0.1
                )
            with col2:
                notes = st.text_input("Notes (optional)")
            
            if st.form_submit_button("Log Entry"):
                self.habit_tracker.log_habit(
                    user_id=user_id,
                    habit_id=habit.habit_id,
                    value=value,
                    notes=notes
                )
                st.success("Logged!")
                st.rerun()
        
        # Statistics
        stats = self.habit_tracker.get_habit_statistics(
            user_id, habit.habit_id, days=30
        )
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Streak", f"{stats['streak']} days")
        with col2:
            st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
        with col3:
            st.metric("Average", f"{stats['average_value']:.1f} {habit.unit or ''}")
        with col4:
            trend_emoji = "📈" if stats['trend'] == "improving" else "📉" if stats['trend'] == "declining" else "➡️"
            st.metric("Trend", f"{trend_emoji} {stats['trend']}")
        
        # Chart
        st.markdown("### 📊 Progress Chart")
        df = self.habit_analytics.prepare_habit_chart_data(
            user_id, habit.habit_id, days=30
        )
        
        if not df.empty:
            fig = px.line(
                df, x="date", y="value",
                title=f"{habit.name} - Last 30 Days",
                labels={"value": habit.unit or "Value", "date": "Date"}
            )
            fig.update_traces(line_color='#1f77b4', line_width=2)
            if habit.target_value:
                fig.add_hline(
                    y=habit.target_value,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Target"
                )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data to display yet. Start logging!")
    
    def render_reflections_page(self):
        """Render reflections page"""
        st.markdown('<p class="main-header">🔮 Daily Reflections</p>', 
                   unsafe_allow_html=True)
        
        user_id = st.session_state.user_id
        
        # Generate new reflection
        if st.button("✨ Generate New Reflection"):
            with st.spinner("Reflecting on your journey..."):
                reflection = self.agent_orchestrator.generate_reflection(user_id)
                st.success("Reflection generated!")
                st.rerun()
        
        st.markdown("---")
        
        # Display recent reflections
        reflections = self.db_manager.get_recent_reflections(user_id, days=30)
        
        if not reflections:
            st.info("No reflections yet. Generate your first reflection above!")
            return
        
        for reflection in reflections:
            with st.expander(
                f"🔮 Reflection from {reflection.created_at.strftime('%B %d, %Y')}",
                expanded=(reflection == reflections[0])
            ):
                st.markdown(reflection.content)
                
                if reflection.key_insights:
                    st.markdown("**Key Insights:**")
                    for insight in reflection.key_insights:
                        st.markdown(f"- {insight}")
                
                if reflection.suggestions:
                    st.markdown("**Suggestions:**")
                    for suggestion in reflection.suggestions:
                        st.markdown(f"- {suggestion}")


def main():
    """Main application entry point"""
    app = MentorApp()
    app.run()


if __name__ == "__main__":
    main()