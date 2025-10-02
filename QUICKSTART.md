# 🚀 Quick Start Guide - Personal Mentor Agent

Get up and running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Docker (optional, but recommended)

## Option 1: Automated Setup (Recommended)

### Step 1: Run Setup Script

```bash
# Download the project
git clone <repository-url>
cd personal-mentor-agent

# Run automated setup
python setup.py
```

The setup script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Configure environment variables
- ✅ Create necessary directories
- ✅ Start Qdrant (if Docker is available)

### Step 2: Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 3: Start the Application

```bash
streamlit run app.py
```

Open your browser at: http://localhost:8501

## Option 2: Docker Compose (Easiest)

### Step 1: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your favorite editor
```

### Step 2: Start Everything

```bash
docker-compose up
```

That's it! The app will be available at: http://localhost:8501

## Option 3: Manual Setup

### Step 1: Create Virtual Environment

```bash
python -m venv venv

# Activate it
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Qdrant

**Option A: Docker (Recommended)**
```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

**Option B: Qdrant Cloud (Free Tier)**
1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. Create a cluster
3. Update `.env` with your cluster URL and API key

### Step 4: Configure Environment

```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
EOF
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

## Using Makefile (Optional)

If you have `make` installed:

```bash
# View all available commands
make help

# Complete setup
make setup

# Start application
make run

# Start with Docker
make docker-up

# Run tests
make test

# View logs
make logs
```

## First-Time Usage

### 1. Create Your Account

- Enter your name on the welcome screen
- Optionally provide your email
- Click "Create Account"

### 2. Start Your First Conversation

- Navigate to the "Chat" section
- Share your goals, challenges, or just say hello
- The AI mentor will respond with personalized advice

### 3. Set Your First Goal

- Go to the "Goals" section
- Click "Add New Goal"
- Enter your goal title and description
- Set a target date (optional)

### 4. Create Your First Habit

- Navigate to "Habits"
- Click "Create New Habit"
- Name your habit and set tracking parameters
- Start logging daily!

### 5. Generate Your First Reflection

- Go to "Reflections"
- Click "Generate New Reflection"
- Review your personalized daily reflection

## Common Commands

```bash
# Start the app
streamlit run app.py

# Start with Docker
docker-compose up

# Stop Docker services
docker-compose down

# View logs
tail -f logs/mentor_$(date +%Y%m%d).log

# Backup database
cp mentor_data.db backups/mentor_data_backup.db

# Run tests
python -m pytest test_mentor.py -v
```

## Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:** Make sure your `.env` file exists and contains:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Issue: "Cannot connect to Qdrant"

**Solution 1 - Check if Qdrant is running:**
```bash
curl http://localhost:6333/
```

**Solution 2 - Restart Qdrant:**
```bash
docker restart mentor_qdrant
```

**Solution 3 - Use Qdrant Cloud:**
Update `.env` with Qdrant Cloud credentials

### Issue: "Port 8501 already in use"

**Solution:** Run on a different port:
```bash
streamlit run app.py --server.port=8502
```

### Issue: "ModuleNotFoundError"

**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: Database errors

**Solution:** Reinitialize the database:
```bash
rm mentor_data.db
python -c "from database import DatabaseManager; from config import Config; DatabaseManager(Config()).initialize_all()"
```

## Configuration Options

### Change AI Model

Edit `config.py`:
```python
@dataclass
class LLMConfig:
    model_name: str = "gpt-4"  # or "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
```

### Change Database Location

Edit `config.py`:
```python
@dataclass
class DatabaseConfig:
    sqlite_db_path: str = "data/mentor.db"  # Custom location
```

### Change Port

```bash
streamlit run app.py --server.port=9000
```

## Directory Structure

```
personal-mentor-agent/
├── app.py                  # Main application
├── config.py              # Configuration
├── models.py              # Data models
├── database.py            # Database layer
├── memory_manager.py      # Memory system
├── mentor_agent.py        # AI agent
├── habit_tracker.py       # Habit tracking
├── logger.py              # Logging
├── utils.py               # Utilities
├── exceptions.py          # Error handling
├── requirements.txt       # Dependencies
├── .env                   # Environment variables (create this)
├── data/                  # Data directory
├── logs/                  # Log files
└── mentor_data.db         # SQLite database
```

## What's Next?

1. **Explore Features**: Try all sections (Chat, Goals, Habits, Dashboard, Reflections)
2. **Daily Check-ins**: Make it a habit to log your progress daily
3. **Review Reflections**: Generate weekly reflections to track your journey
4. **Customize**: Adjust settings in `config.py` to fit your needs
5. **Contribute**: Check out the full documentation in `README.md`

## Getting Help

- **Documentation**: See `README.md` for detailed information
- **Issues**: Check logs in `logs/` directory
- **Testing**: Run `python -m pytest test_mentor.py -v`
- **Community**: Open an issue on GitHub

## Key Features to Try

### 💬 Contextual Conversations
The AI remembers your entire journey and provides personalized advice based on your history.

### 🎯 Smart Goal Tracking
Set goals with deadlines and track your progress automatically.

### 📈 Advanced Analytics
View streak counts, completion rates, and trend analysis for your habits.

### 🔮 AI-Generated Reflections
Get daily insights and suggestions based on your activities and progress.

### 📊 Comprehensive Dashboard
See all your stats and progress in one place.

## Tips for Best Experience

1. **Be Consistent**: Log your habits daily for accurate tracking
2. **Be Honest**: Share your real challenges with the AI mentor
3. **Set Realistic Goals**: Start small and build up
4. **Review Regularly**: Check your reflections weekly
5. **Stay Engaged**: Chat with your mentor regularly

## Example Workflow

```
Morning:
1. Open the app
2. Log yesterday's habits
3. Check dashboard
4. Set intentions for the day

During the Day:
5. Chat with mentor when needed
6. Log habits as you complete them

Evening:
7. Review progress
8. Generate daily reflection
9. Plan for tomorrow
```

---

**Ready to start your personal growth journey?** 🚀

Open the app and create your account now!

```bash
streamlit run app.py
```

Then visit: http://localhost:8501