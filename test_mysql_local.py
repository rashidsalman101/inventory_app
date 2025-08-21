#!/usr/bin/env python3
"""
Local MySQL Testing Script
Test MySQL connection and basic operations before deploying to cPanel.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mysql_connection():
    """Test MySQL connection and basic operations."""
    try:
        # Check if DATABASE_URL is set
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in .env file")
            print("Please create a .env file with your MySQL connection string")
            return False
        
        print(f"🔍 Testing connection to: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
        
        # Import Flask app
        from app import app, db
        
        with app.app_context():
            # Test basic connection
            print("🔌 Testing database connection...")
            result = db.session.execute('SELECT 1 as test')
            print("✅ Basic connection successful!")
            
            # Test table creation
            print("🔧 Testing table creation...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # List tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables found: {len(tables)}")
            for table in tables:
                print(f"   - {table}")
            
            # Test basic insert/select
            print("📝 Testing basic operations...")
            from app import User, Brand
            
            # Test brand creation
            test_brand = Brand(name="Test Brand")
            db.session.add(test_brand)
            db.session.commit()
            print("✅ Brand creation successful!")
            
            # Test brand retrieval
            brand = Brand.query.filter_by(name="Test Brand").first()
            if brand:
                print(f"✅ Brand retrieval successful: {brand.name}")
                
                # Clean up test data
                db.session.delete(brand)
                db.session.commit()
                print("✅ Test data cleaned up!")
            else:
                print("❌ Brand retrieval failed")
                return False
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed all requirements:")
        print("pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check if MySQL server is running")
        print("2. Verify database credentials in .env file")
        print("3. Ensure database exists")
        print("4. Check if PyMySQL is installed")
        return False

def check_environment():
    """Check if environment is properly configured."""
    print("🔍 Environment Check")
    print("=" * 30)
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        print("   Create a .env file with your MySQL connection string")
        return False
    
    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print("✅ DATABASE_URL is set")
        if 'mysql' in database_url:
            print("✅ MySQL connection string detected")
        else:
            print("⚠️  Not a MySQL connection string")
    else:
        print("❌ DATABASE_URL not set")
        return False
    
    # Check required packages
    try:
        import pymysql
        print("✅ PyMySQL package found")
    except ImportError:
        print("❌ PyMySQL package not found")
        print("   Run: pip install PyMySQL")
        return False
    
    try:
        import flask_sqlalchemy
        print("✅ Flask-SQLAlchemy package found")
    except ImportError:
        print("❌ Flask-SQLAlchemy package not found")
        print("   Run: pip install Flask-SQLAlchemy")
        return False
    
    return True

def create_sample_env():
    """Create a sample .env file if it doesn't exist."""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    sample_content = """# Local MySQL Development Environment
# Update these values with your local MySQL credentials

# Database Configuration
DATABASE_URL=mysql+pymysql://root:@localhost/mobile_inventory

# Flask Configuration
SECRET_KEY=your-local-secret-key-change-this
FLASK_DEBUG=True
FLASK_ENV=development

# Example for different MySQL user:
# DATABASE_URL=mysql+pymysql://username:password@localhost/mobile_inventory
"""
    
    with open('.env', 'w') as f:
        f.write(sample_content)
    
    print("📝 Created sample .env file")
    print("⚠️  Please update the DATABASE_URL with your actual MySQL credentials")

if __name__ == "__main__":
    print("🧪 MySQL Local Testing Tool")
    print("=" * 40)
    
    # Check environment first
    if not check_environment():
        print("\n🔧 Setting up environment...")
        create_sample_env()
        print("\n📝 Please update your .env file and run this script again")
        sys.exit(1)
    
    print("\n🚀 Starting MySQL tests...")
    
    # Test connection
    if test_mysql_connection():
        print("\n🎉 All tests passed! MySQL is working correctly.")
        print("\n📝 Next steps:")
        print("1. Your local MySQL setup is ready")
        print("2. You can now run: python app.py")
        print("3. Test your application locally")
        print("4. When ready, deploy to cPanel")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        print("\n🔍 Common solutions:")
        print("1. Start MySQL service (XAMPP/MAMP)")
        print("2. Check database credentials")
        print("3. Ensure database exists")
        print("4. Install missing packages")
        sys.exit(1) 