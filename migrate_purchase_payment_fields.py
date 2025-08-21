#!/usr/bin/env python3
"""
Migration Script: Add Payment Tracking Fields to Purchases
This script adds payment_status, paid_amount, due_amount, and due_date fields to existing purchases.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Purchase

def migrate_purchase_payment_fields():
    """Add payment tracking fields to existing purchases."""
    try:
        with app.app_context():
            print("🔧 Migrating purchase payment fields...")
            
            # Check if fields already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('purchase')]
            
            if 'payment_status' in columns and 'paid_amount' in columns and 'due_amount' in columns:
                print("✅ Payment fields already exist in purchase table")
                return True
            
            print("📝 Adding payment tracking fields to existing purchases...")
            
            # Get all existing purchases
            purchases = Purchase.query.all()
            print(f"📊 Found {len(purchases)} purchases to migrate")
            
            migrated_count = 0
            for purchase in purchases:
                try:
                    # Calculate total amount
                    total_amount = purchase.purchase_price * purchase.quantity
                    
                    # Set default payment status (assuming all existing purchases were paid)
                    if not hasattr(purchase, 'payment_status'):
                        purchase.payment_status = 'paid'
                    if not hasattr(purchase, 'paid_amount'):
                        purchase.paid_amount = total_amount
                    if not hasattr(purchase, 'due_amount'):
                        purchase.due_amount = 0.0
                    if not hasattr(purchase, 'due_date'):
                        purchase.due_date = None
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error migrating purchase {purchase.id}: {e}")
                    continue
            
            # Commit changes
            db.session.commit()
            print(f"✅ Successfully migrated {migrated_count} purchases")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

def create_supplier_payment_table():
    """Create the supplier_payment table if it doesn't exist."""
    try:
        with app.app_context():
            print("🔧 Creating supplier_payment table...")
            
            # Import the model to ensure table creation
            from app import SupplierPayment
            
            # Check if table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'supplier_payment' in tables:
                print("✅ supplier_payment table already exists")
                return True
            
            # Create the table
            db.create_all()
            print("✅ supplier_payment table created successfully")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating supplier_payment table: {e}")
        return False

def verify_migration():
    """Verify that all required fields and tables exist."""
    try:
        with app.app_context():
            print("🔍 Verifying migration...")
            
            # Check purchase table structure
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Check purchase table columns
            purchase_columns = [col['name'] for col in inspector.get_columns('purchase')]
            required_purchase_fields = ['payment_status', 'paid_amount', 'due_amount', 'due_date']
            
            missing_purchase_fields = [field for field in required_purchase_fields if field not in purchase_columns]
            if missing_purchase_fields:
                print(f"❌ Missing fields in purchase table: {missing_purchase_fields}")
                return False
            else:
                print("✅ All required purchase fields exist")
            
            # Check supplier_payment table
            tables = inspector.get_table_names()
            if 'supplier_payment' in tables:
                print("✅ supplier_payment table exists")
            else:
                print("❌ supplier_payment table missing")
                return False
            
            # Test a sample purchase
            sample_purchase = Purchase.query.first()
            if sample_purchase:
                print(f"✅ Sample purchase has payment_status: {sample_purchase.payment_status}")
                print(f"✅ Sample purchase has paid_amount: {sample_purchase.paid_amount}")
                print(f"✅ Sample purchase has due_amount: {sample_purchase.due_amount}")
            else:
                print("⚠️  No purchases found to verify")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Purchase Payment Fields Migration Tool")
    print("=" * 50)
    
    try:
        # Step 1: Create supplier_payment table
        if not create_supplier_payment_table():
            print("❌ Failed to create supplier_payment table")
            sys.exit(1)
        
        # Step 2: Migrate existing purchases
        if not migrate_purchase_payment_fields():
            print("❌ Failed to migrate purchase payment fields")
            sys.exit(1)
        
        # Step 3: Verify migration
        if not verify_migration():
            print("❌ Migration verification failed")
            sys.exit(1)
        
        print("\n🎉 Migration completed successfully!")
        print("\n📝 What was added:")
        print("   - payment_status field to purchases (default: 'paid')")
        print("   - paid_amount field to purchases (default: total amount)")
        print("   - due_amount field to purchases (default: 0)")
        print("   - due_date field to purchases (default: NULL)")
        print("   - supplier_payment table for tracking payments")
        
        print("\n🚀 Your purchase module now supports payment tracking!")
        print("   - Track how much you've paid to suppliers")
        print("   - Track remaining amounts due")
        print("   - Add payments to existing purchases")
        print("   - View payment status in transactions and dashboard")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1) 