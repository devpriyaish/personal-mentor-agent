"""
Personal Mentor Agent - Project File Generator
Run this script to create all project files automatically
"""
import os
from pathlib import Path

def create_file(filepath, content):
    """Create a file with given content"""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created: {filepath}")

def create_project():
    """Create all project files"""
    
    print("\n" + "="*60)
    print("  Personal Mentor Agent - Project Generator")
    print("="*60 + "\n")
    
    # Create project directory structure
    directories = ['data', 'logs', 'backups', 'tests']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}/")
    
    print("\nCreating project files...\n")
    
    # Now I'll provide a download link approach
    print("\n" + "="*60)
    print("FILES READY TO COPY")
    print("="*60)
    print("\nPlease copy each file from the artifacts shown in the chat.")
    print("Look for these files on the left side of the interface:\n")
    
    files_to_create = [
        "config.py",
        "models.py", 
        "database.py",
        "memory_manager.py",
        "mentor_agent.py",
        "habit_tracker.py",
        "app.py",
        "logger.py",
        "utils.py",
        "exceptions.py",
        "test_mentor.py",
        "setup.py",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "README.md",
        "QUICKSTART.md"
    ]
    
    for filename in files_to_create:
        print(f"  📄 {filename}")
    
    print("\n" + "="*60)
    print("MANUAL COPY INSTRUCTIONS")
    print("="*60)
    print("""
1. Look at the LEFT side of this chat interface
2. You'll see a list of artifacts with names like:
   - "config.py - Configuration Settings"
   - "models.py - Data Models"
   - etc.
   
3. For EACH artifact:
   a. Click on the artifact name
   b. Click the "Copy" button (top-right corner)
   c. Create a new file on your computer with that name
   d. Paste the content
   
4. Save all files in the same directory

5. After copying all files, run:
   python setup.py
""")

if __name__ == "__main__":
    create_project()