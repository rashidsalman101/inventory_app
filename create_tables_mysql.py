#!/usr/bin/env python3
"""
MySQL Database Creation Script for cPanel Hosting
This script creates all necessary tables for the mobile inventory system.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

def create_mysql_tables():
    """Create all MySQL tables for the inventory system."""
    try:
        with app.app_context():
            print("🔧 Creating MySQL tables...")
            
            # Create all tables
            db.create_all()
            
            print("✅ All tables created successfully!")
            print("\n📋 Tables created:")
            
            # List all tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            for table in tables:
                print(f"   - {table}")
                
            print(f"\n🎯 Total tables: {len(tables)}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Ensure MySQL server is running")
        print("3. Verify database credentials")
        print("4. Check if database exists")
        return False
    
    return True

def check_database_connection():
    """Check if database connection is working."""
    try:
        with app.app_context():
            # Try to execute a simple query
            result = db.session.execute('SELECT 1')
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MySQL Database Setup for Mobile Inventory System")
    print("=" * 50)
    
    # Check connection first
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection.")
        sys.exit(1)
    
    # Create tables
    if create_mysql_tables():
        print("\n🎉 Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Run 'python seed_data.py' to add sample data")
        print("2. Test your application")
    else:
        print("\n❌ Database setup failed. Please check the errors above.")
        sys.exit(1) 