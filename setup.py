"""
Setup script for Personal Mentor Agent
Automates installation and configuration
"""
import os
import sys
import subprocess
from pathlib import Path


class SetupManager:
    """Manages the setup process"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"
    
    def print_step(self, step: str):
        """Print setup step"""
        print(f"\n{'='*60}")
        print(f"  {step}")
        print(f"{'='*60}\n")
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        self.print_step("Checking Python version")
        
        if sys.version_info < (3, 9):
            print("❌ Python 3.9 or higher is required")
            print(f"   Current version: {sys.version}")
            sys.exit(1)
        
        print(f"✅ Python version: {sys.version}")
    
    def create_virtual_environment(self):
        """Create virtual environment"""
        self.print_step("Creating virtual environment")
        
        if self.venv_path.exists():
            print("⚠️  Virtual environment already exists")
            response = input("   Recreate? (y/n): ")
            if response.lower() == 'y':
                import shutil
                shutil.rmtree(self.venv_path)
            else:
                print("✅ Using existing virtual environment")
                return
        
        subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)])
        print("✅ Virtual environment created")
    
    def get_pip_command(self):
        """Get pip command for the virtual environment"""
        if sys.platform == "win32":
            return str(self.venv_path / "Scripts" / "pip")
        return str(self.venv_path / "bin" / "pip")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_step("Installing dependencies")
        
        pip_cmd = self.get_pip_command()
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            sys.exit(1)
        
        print("Installing packages...")
        subprocess.run([pip_cmd, "install", "-r", str(requirements_file)])
        print("✅ Dependencies installed")
    
    def setup_environment_file(self):
        """Setup .env file"""
        self.print_step("Setting up environment variables")
        
        if self.env_file.exists():
            print("⚠️  .env file already exists")
            response = input("   Overwrite? (y/n): ")
            if response.lower() != 'y':
                print("✅ Using existing .env file")
                return
        
        # Copy from example
        if self.env_example.exists():
            with open(self.env_example, 'r') as f:
                env_content = f.read()
        else:
            env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Configuration (for local deployment)
QDRANT_HOST=localhost
QDRANT_PORT=6333
"""
        
        # Get OpenAI API key
        print("\nPlease enter your OpenAI API key")
        print("(You can get one at: https://platform.openai.com/api-keys)")
        api_key = input("API Key: ").strip()
        
        if api_key and api_key != "your_openai_api_key_here":
            env_content = env_content.replace("your_openai_api_key_here", api_key)
        
        # Write .env file
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created")
    
    def create_directories(self):
        """Create necessary directories"""
        self.print_step("Creating directories")
        
        directories = ['data', 'logs']
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created {dir_name}/ directory")
    
    def check_docker(self):
        """Check if Docker is available"""
        self.print_step("Checking Docker")
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Docker installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        print("⚠️  Docker not found")
        print("   Docker is recommended for running Qdrant locally")
        print("   You can:")
        print("   1. Install Docker: https://docs.docker.com/get-docker/")
        print("   2. Use Qdrant Cloud (free tier available): https://cloud.qdrant.io/")
        return False
    
    def start_qdrant(self):
        """Start Qdrant with Docker"""
        self.print_step("Starting Qdrant")
        
        if not self.check_docker():
            print("\n⚠️  Skipping Qdrant setup")
            print("   Please set up Qdrant manually or use Qdrant Cloud")
            return
        
        print("\nStarting Qdrant container...")
        try:
            # Check if container already exists
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=mentor_qdrant", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            
            if "mentor_qdrant" in result.stdout:
                print("⚠️  Qdrant container already exists")
                response = input("   Restart it? (y/n): ")
                if response.lower() == 'y':
                    subprocess.run(["docker", "rm", "-f", "mentor_qdrant"])
                else:
                    subprocess.run(["docker", "start", "mentor_qdrant"])
                    print("✅ Qdrant container started")
                    return
            
            # Start new container
            subprocess.run([
                "docker", "run", "-d",
                "--name", "mentor_qdrant",
                "-p", "6333:6333",
                "-p", "6334:6334",
                "qdrant/qdrant"
            ])
            print("✅ Qdrant container started")
            
        except Exception as e:
            print(f"❌ Failed to start Qdrant: {e}")
            print("   Please start Qdrant manually")
    
    def display_next_steps(self):
        """Display next steps"""
        self.print_step("Setup Complete!")
        
        print("🎉 Installation successful!\n")
        print("Next steps:")
        print("\n1. Activate the virtual environment:")
        
        if sys.platform == "win32":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("\n2. Start the application:")
        print("   streamlit run app.py")
        
        print("\n3. Open your browser and navigate to:")
        print("   http://localhost:8501")
        
        print("\n4. (Optional) Start with Docker Compose:")
        print("   docker-compose up")
        
        print("\n📚 For more information, see README.md")
        print("\n💡 Tips:")
        print("   - Make sure Qdrant is running before starting the app")
        print("   - Check logs/ directory for application logs")
        print("   - Your data is stored in data/ and mentor_data.db")
    
    def run(self):
        """Run the complete setup process"""
        print("\n" + "="*60)
        print("  Personal Mentor Agent - Setup")
        print("="*60)
        
        try:
            self.check_python_version()
            self.create_virtual_environment()
            self.install_dependencies()
            self.setup_environment_file()
            self.create_directories()
            
            # Ask about Qdrant
            print("\n" + "="*60)
            response = input("Would you like to start Qdrant now? (y/n): ")
            if response.lower() == 'y':
                self.start_qdrant()
            
            self.display_next_steps()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    setup = SetupManager()
    setup.run()


if __name__ == "__main__":
    main()