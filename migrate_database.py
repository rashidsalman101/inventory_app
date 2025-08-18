#!/usr/bin/env python3
"""
Database migration script to add new columns to existing database
"""

from app import app, db
from sqlalchemy import text
import os

def migrate_database():
    """Add new columns to existing database"""
    print("🔄 Starting database migration...")
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            purchase_columns = [col['name'] for col in inspector.get_columns('purchase')]
            sale_columns = [col['name'] for col in inspector.get_columns('sale')]
            
            print(f"Current purchase columns: {purchase_columns}")
            print(f"Current sale columns: {sale_columns}")
            
            # Add missing columns to purchase table
            if 'supplier_id' not in purchase_columns:
                print("Adding supplier_id column to purchase table...")
                db.session.execute(text("ALTER TABLE purchase ADD COLUMN supplier_id INTEGER REFERENCES supplier(id)"))
                print("✓ supplier_id column added")
            
            if 'bill_number' not in purchase_columns:
                print("Adding bill_number column to purchase table...")
                db.session.execute(text("ALTER TABLE purchase ADD COLUMN bill_number VARCHAR(50)"))
                print("✓ bill_number column added")
            
            # Add missing columns to sale table
            if 'bill_number' not in sale_columns:
                print("Adding bill_number column to sale table...")
                db.session.execute(text("ALTER TABLE sale ADD COLUMN bill_number VARCHAR(50)"))
                print("✓ bill_number column added")
            
            # Check if supplier table exists
            if not inspector.has_table('supplier'):
                print("Creating supplier table...")
                db.create_all()
                print("✓ supplier table created")
            
            # Commit changes
            db.session.commit()
            print("\n🎉 Database migration completed successfully!")
            
            # Verify the changes
            inspector = db.inspect(db.engine)
            purchase_columns = [col['name'] for col in inspector.get_columns('purchase')]
            sale_columns = [col['name'] for col in inspector.get_columns('sale')]
            
            print(f"\nUpdated purchase columns: {purchase_columns}")
            print(f"Updated sale columns: {sale_columns}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    migrate_database() 