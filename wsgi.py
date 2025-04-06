import sys
import os

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Add the src directory to the path
src_dir = os.path.join(project_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import the Flask application
from src.app import app as application
