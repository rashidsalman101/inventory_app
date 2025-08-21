import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app import app

# For cPanel, we need to expose the app
application = app

if __name__ == "__main__":
    app.run() 