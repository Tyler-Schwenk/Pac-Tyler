import subprocess
import sys
import os

# Install requirements
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# Add current directory to PYTHONPATH
env = os.environ.copy()
env["PYTHONPATH"] = os.path.abspath(".")

# Run main script
subprocess.check_call([sys.executable, "src/main.py"], env=env)
