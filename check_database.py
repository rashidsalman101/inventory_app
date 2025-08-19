#!/usr/bin/env python3
"""
Quick database check script for Mobile Shop Manager
This script checks if your database needs schema updates for the new features
"""

from app import app, db
import sqlite3
import os

def check_database_compatibility():
    """Check if database supports new features"""
    
    print("🔍 Mobile Shop Manager - Database Compatibility Check")
    print("=" * 55)
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            print("❌ Database file not found at:", db_path)
            print("   Run 'python create_tables.py' to create a new database")
            return False
        
        print(f"📁 Database location: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check Sale table schema
            cursor.execute("PRAGMA table_info(sale)")
            sale_columns = {col[1]: col[2] for col in cursor.fetchall()}
            
            print("\n📊 Database Schema Analysis:")
            print("-" * 30)
            
            # Check IMEI column compatibility
            if 'imei_number' in sale_columns:
                imei_type = sale_columns['imei_number']
                if imei_type == 'TEXT':
                    print("✅ IMEI Format: Flexible (any length/format supported)")
                elif 'VARCHAR(15)' in imei_type:
                    print("⚠️  IMEI Format: Limited to 15 characters")
                    print("   📝 Recommendation: Run 'python update_database_schema.py'")
                else:
                    print(f"⚠️  IMEI Format: {imei_type} (may have restrictions)")
            else:
                print("❌ IMEI column not found!")
            
            # Check multiple sales support
            if 'bill_number' in sale_columns:
                print("✅ Multiple Sales: Supported (bill_number column exists)")
            else:
                print("❌ Multiple Sales: Not supported (bill_number column missing)")
            
            # Check payment tracking
            payment_columns = ['paid_amount', 'due_amount', 'payment_status']
            missing_payment_cols = [col for col in payment_columns if col not in sale_columns]
            
            if not missing_payment_cols:
                print("✅ Payment Tracking: Fully supported")
            else:
                print(f"⚠️  Payment Tracking: Missing columns: {missing_payment_cols}")
            
            # Check for any existing data
            cursor.execute("SELECT COUNT(*) FROM sale")
            sale_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM purchase")
            purchase_count = cursor.fetchone()[0]
            
            print(f"\n📈 Current Data:")
            print(f"   - Sales: {sale_count}")
            print(f"   - Purchases: {purchase_count}")
            
            conn.close()
            
            # Overall assessment
            print("\n🎯 Compatibility Assessment:")
            print("-" * 30)
            
            if imei_type == 'TEXT' and 'bill_number' in sale_columns and not missing_payment_cols:
                print("✅ Your database is fully compatible with all new features!")
                print("   - Multiple IMEI sales ✓")
                print("   - Flexible IMEI formats ✓") 
                print("   - Grouped transactions ✓")
                print("   - Enhanced bill design ✓")
                print("   - Brand-wise inventory ✓")
            else:
                print("⚠️  Your database needs updates for full compatibility")
                print("\n🔧 Recommended Actions:")
                if imei_type != 'TEXT':
                    print("   1. Run: python update_database_schema.py")
                    print("      (Updates IMEI column for flexible formats)")
                if missing_payment_cols:
                    print("   2. Your database is missing payment tracking columns")
                    print("      Consider recreating with: python create_new_tables.py")
                
                print(f"\n⚠️  Note: You have {sale_count + purchase_count} existing records")
                print("   Make sure to backup your data before running updates!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            return False

if __name__ == '__main__':
    check_database_compatibility() 