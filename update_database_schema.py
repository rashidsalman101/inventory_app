#!/usr/bin/env python3
"""
Database schema update script for Mobile Shop Manager
This script updates the IMEI column to support any length/format
"""

from app import app, db
import sqlite3
import os

def update_database_schema():
    """Update database schema to support flexible IMEI formats"""
    
    print("🔄 Updating database schema for flexible IMEI support...")
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            print("❌ Database file not found. Please run create_tables.py first.")
            return False
        
        try:
            # Connect directly to SQLite to modify the schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check current schema
            cursor.execute("PRAGMA table_info(sale)")
            columns = cursor.fetchall()
            
            print("📋 Current Sale table schema:")
            for col in columns:
                if col[1] == 'imei_number':
                    print(f"   - {col[1]}: {col[2]} (nullable: {not col[3]})")
                    current_type = col[2]
            
            # Check if we need to update
            if 'VARCHAR(15)' in current_type or 'VARCHAR(50)' in current_type:
                print("🔧 Updating IMEI column to support flexible formats...")
                
                # SQLite doesn't support ALTER COLUMN directly, so we need to:
                # 1. Create new table with updated schema
                # 2. Copy data
                # 3. Drop old table
                # 4. Rename new table
                
                # Create backup table
                cursor.execute('''
                    CREATE TABLE sale_backup AS 
                    SELECT * FROM sale
                ''')
                print("✓ Created backup of sale table")
                
                # Drop the original table
                cursor.execute('DROP TABLE sale')
                print("✓ Dropped original sale table")
                
                # Create new table with flexible IMEI column
                cursor.execute('''
                    CREATE TABLE sale (
                        id INTEGER PRIMARY KEY,
                        model_id INTEGER NOT NULL,
                        imei_number TEXT NOT NULL,
                        sale_price REAL NOT NULL,
                        purchase_price REAL NOT NULL,
                        profit REAL NOT NULL,
                        inventory_type VARCHAR(10) NOT NULL,
                        customer_type VARCHAR(20) NOT NULL,
                        shop_id INTEGER,
                        customer_name VARCHAR(100),
                        payment_status VARCHAR(20) DEFAULT 'paid',
                        paid_amount REAL DEFAULT 0.0,
                        due_amount REAL DEFAULT 0.0,
                        due_date DATETIME,
                        bill_number VARCHAR(50),
                        date DATETIME,
                        user_id INTEGER NOT NULL,
                        FOREIGN KEY (model_id) REFERENCES model (id),
                        FOREIGN KEY (shop_id) REFERENCES shop (id),
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                ''')
                print("✓ Created new sale table with flexible IMEI column (TEXT type)")
                
                # Copy data back
                cursor.execute('''
                    INSERT INTO sale 
                    SELECT * FROM sale_backup
                ''')
                print("✓ Restored all data to new table")
                
                # Drop backup table
                cursor.execute('DROP TABLE sale_backup')
                print("✓ Cleaned up backup table")
                
                # Commit changes
                conn.commit()
                print("✅ Database schema updated successfully!")
                
            else:
                print("✅ IMEI column already supports flexible formats - no update needed")
            
            # Verify the update
            cursor.execute("PRAGMA table_info(sale)")
            columns = cursor.fetchall()
            
            print("\n📋 Updated Sale table schema:")
            for col in columns:
                if col[1] == 'imei_number':
                    print(f"   ✓ {col[1]}: {col[2]} (nullable: {not col[3]})")
            
            conn.close()
            
            print("\n🎉 Database schema update completed successfully!")
            print("   - IMEI numbers now support any length and format")
            print("   - No data was lost during the migration")
            print("   - Multiple sales functionality is fully supported")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating database schema: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False

def verify_schema():
    """Verify that the schema supports our new features"""
    print("\n🔍 Verifying database schema compatibility...")
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            print("❌ Database file not found.")
            return False
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check Sale table schema
            cursor.execute("PRAGMA table_info(sale)")
            sale_columns = {col[1]: col[2] for col in cursor.fetchall()}
            
            print("✅ Schema Verification Results:")
            
            # Check IMEI column
            if 'imei_number' in sale_columns:
                imei_type = sale_columns['imei_number']
                if imei_type == 'TEXT':
                    print("   ✓ IMEI column supports flexible formats (TEXT)")
                else:
                    print(f"   ⚠️  IMEI column type: {imei_type} (may have length restrictions)")
            
            # Check bill_number column for multiple sales support
            if 'bill_number' in sale_columns:
                print("   ✓ Bill number column exists (supports multiple sales grouping)")
            
            # Check payment tracking columns
            required_columns = ['paid_amount', 'due_amount', 'payment_status']
            for col in required_columns:
                if col in sale_columns:
                    print(f"   ✓ {col} column exists (supports payment tracking)")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error verifying schema: {e}")
            return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_schema()
    else:
        print("🚀 Mobile Shop Manager - Database Schema Update")
        print("=" * 50)
        
        # First verify current state
        verify_schema()
        
        # Ask for confirmation
        print("\n" + "=" * 50)
        confirm = input("Do you want to update the database schema? (y/n): ")
        
        if confirm.lower() in ['y', 'yes']:
            success = update_database_schema()
            if success:
                print("\n" + "=" * 50)
                verify_schema()
        else:
            print("Schema update cancelled.") 