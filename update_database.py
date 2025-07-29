from app import app, db
from datetime import datetime

def update_database():
    with app.app_context():
        # Create new tables
        db.create_all()
        print("Database updated successfully!")

if __name__ == "__main__":
    update_database() 