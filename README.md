# 🧠 Personal Mentor Agent

A production-ready AI-powered personal development companion built with LangChain, Streamlit, and Qdrant. This agent remembers your journey, tracks your habits, and provides personalized mentorship every day.

## ✨ Features

### Core Capabilities
- **🤖 Intelligent Conversations**: Chat with an AI mentor that remembers your entire journey
- **🎯 Goal Tracking**: Set, track, and complete personal and professional goals
- **📈 Habit Analytics**: Track daily habits with streak counting and visualization
- **🔮 Daily Reflections**: AI-generated personalized reflections on your progress
- **📊 Progress Dashboard**: Comprehensive view of your personal development journey
- **💾 Semantic Memory**: Vector-based memory system for contextual conversations

### Technical Features
- **Object-Oriented Design**: Implements all major OOP concepts and design patterns
- **Vector Database**: Qdrant for semantic memory search
- **SQLite Storage**: Persistent storage for structured data
- **LangChain Integration**: Advanced AI agent capabilities
- **Streamlit UI**: Modern, responsive web interface
- **Production Ready**: Error handling, logging, and scalable architecture

## 🏗️ Architecture

### Design Patterns Implemented

1. **Singleton Pattern**: Config, Database managers
2. **Factory Pattern**: Agent creation
3. **Observer Pattern**: Habit tracking notifications
4. **Strategy Pattern**: Embedding strategies
5. **Facade Pattern**: Database and Agent orchestrators
6. **Repository Pattern**: Data access layer
7. **Template Method**: Base agent structure
8. **Chain of Responsibility**: Agent processing pipeline

### Project Structure

```
personal-mentor-agent/
├── app.py                  # Main Streamlit application
├── config.py              # Configuration management
├── models.py              # Data models
├── database.py            # Database managers (SQLite + Qdrant)
├── memory_manager.py      # Memory and embedding management
├── mentor_agent.py        # LangChain agent implementation
├── habit_tracker.py       # Habit tracking system
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Docker (optional, for Qdrant)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd personal-mentor-agent
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Qdrant (Vector Database)

#### Option A: Local Docker Deployment (Recommended for Development)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

#### Option B: Qdrant Cloud (Free Tier Available)

1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a cluster (free tier: 1GB storage)
3. Get your cluster URL and API key
4. Update `.env` with cloud credentials

### Step 5: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
# Required: OPENAI_API_KEY
# Optional: Qdrant cloud settings if not using local
```

Example `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Step 6: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### First-Time Setup

1. **Create Account**: Enter your name on the welcome screen
2. **Start Chatting**: Share your goals, challenges, and daily experiences
3. **Set Goals**: Navigate to the Goals section to create your first goal
4. **Track Habits**: Create habits you want to build or maintain
5. **Generate Reflections**: Get AI-generated insights on your journey

### Daily Workflow

1. **Morning Check-in**: Log your habits and review your goals
2. **Throughout the Day**: Chat with your mentor about challenges or wins
3. **Evening Reflection**: Generate a daily reflection to review your progress
4. **Weekly Review**: Check your dashboard for trends and statistics

## 🎯 Core Concepts

### Memory System

The agent uses a hybrid memory approach:

1. **Vector Memory (Qdrant)**: Semantic search for relevant past conversations
   - Uses sentence-transformers for embeddings
   - Enables contextual memory retrieval
   - Categorizes memories by type (goals, struggles, achievements)

2. **Structured Storage (SQLite)**: Persistent storage for:
   - User profiles
   - Goals and their status
   - Habit logs and streaks
   - Daily reflections
   - Conversation history

### Habit Tracking

- **Frequency Types**: Daily, Weekly, Monthly
- **Analytics**: Streaks, completion rates, trends
- **Visualizations**: 30-day progress charts with Plotly
- **Correlations**: Discover relationships between habits

### AI Agent

The mentor agent:
- Retrieves relevant past context for each conversation
- Provides personalized advice based on your history
- Celebrates achievements and helps navigate challenges
- Generates daily reflections with key insights

## 🔧 Configuration

### Model Configuration

Edit `config.py` to change:

```python
@dataclass
class LLMConfig:
    model_name: str = "gpt-3.5-turbo"  # or "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
```

### Embedding Model

To use a different embedding model:

```python
@dataclass
class DatabaseConfig:
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_size: int = 384  # Must match model output size
```

## 🧪 Testing

### Manual Testing Checklist

- [ ] User registration and login
- [ ] Chat conversation with context retention
- [ ] Goal creation and completion
- [ ] Habit logging and streak tracking
- [ ] Reflection generation
- [ ] Dashboard statistics display

### Example Test Flow

```python
# Test user creation
user = User(
    user_id="test_user",
    name="Test User",
    email="test@example.com"
)
db_manager.create_user(user)

# Test memory storage
memory_manager.create_memory(
    user_id="test_user",
    content="I want to learn Python",
    interaction_type=InteractionType.GOAL
)

# Test habit tracking
habit = habit_tracker.create_habit(
    user_id="test_user",
    name="Exercise",
    frequency=HabitFrequency.DAILY,
    target_value=30,
    unit="minutes"
)
```

## 📊 Database Schema

### SQLite Tables

```sql
-- Users
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP,
    timezone TEXT,
    preferences TEXT
);

-- Goals
CREATE TABLE goals (
    goal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    target_date TIMESTAMP,
    status TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Habits
CREATE TABLE habits (
    habit_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL,
    target_value REAL,
    unit TEXT,
    created_at TIMESTAMP,
    is_active BOOLEAN
);

-- Habit Logs
CREATE TABLE habit_logs (
    log_id TEXT PRIMARY KEY,
    habit_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    value REAL NOT NULL,
    notes TEXT,
    logged_at TIMESTAMP
);

-- Reflections
CREATE TABLE daily_reflections (
    reflection_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    sentiment_score REAL,
    key_insights TEXT,
    suggestions TEXT,
    created_at TIMESTAMP
);

-- Conversations
CREATE TABLE conversations (
    message_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP,
    metadata TEXT
);
```

### Qdrant Collection

```python
Collection: "mentor_memories"
Vector Size: 384 (all-MiniLM-L6-v2)
Distance: Cosine

Payload Fields:
- user_id: string
- content: string
- interaction_type: string
- timestamp: string (ISO format)
- metadata: object
```

## 🚀 Deployment

### Local Production Deployment

```bash
# Set production environment
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run with production settings
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

Build and run:

```bash
docker build -t personal-mentor-agent .
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key personal-mentor-agent
```

### Cloud Deployment Options

1. **Streamlit Cloud**: Free tier available, direct GitHub integration
2. **Heroku**: Easy deployment with Procfile
3. **AWS/GCP/Azure**: Full control with VM or container services
4. **Railway**: Simple deployment with automatic HTTPS

## 🔒 Security Considerations

### Production Checklist

- [ ] Use environment variables for all secrets
- [ ] Implement proper user authentication (e.g., OAuth, JWT)
- [ ] Add rate limiting for API calls
- [ ] Encrypt sensitive data in database
- [ ] Use HTTPS in production
- [ ] Implement input validation and sanitization
- [ ] Add error logging and monitoring
- [ ] Regular security audits
- [ ] Database backups

### Recommended Improvements

1. **Authentication**: Integrate with Auth0 or Firebase
2. **API Gateway**: Add rate limiting and API key management
3. **Monitoring**: Use services like Sentry for error tracking
4. **Analytics**: Track usage metrics with Mixpanel or similar
5. **Backups**: Automated daily backups of SQLite and Qdrant

## 🤝 Contributing

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all classes and methods
- Keep functions focused and small

### Adding New Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Implement with proper OOP design
3. Add tests if applicable
4. Update documentation
5. Submit pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- LangChain for AI agent framework
- Streamlit for the amazing UI framework
- Qdrant for vector database
- Sentence Transformers for embeddings
- OpenAI for LLM capabilities

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review code comments for implementation details

## 🗺️ Roadmap

### Planned Features

- [ ] Mobile app (React Native)
- [ ] Voice interaction support
- [ ] Integration with calendar apps
- [ ] Social features (accountability partners)
- [ ] Advanced analytics dashboard
- [ ] Export reports (PDF, Excel)
- [ ] Multi-language support
- [ ] Customizable AI personality
- [ ] Integration with fitness trackers
- [ ] Browser extension for quick logging

---

**Built with ❤️ for personal growth and development**