#!/usr/bin/env python3
"""
SQLite to MySQL Migration Script
This script helps migrate data from SQLite to MySQL for cPanel hosting.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def export_sqlite_data():
    """Export data from SQLite database to JSON files."""
    try:
        # Temporarily use SQLite configuration
        os.environ['DATABASE_URL'] = ''
        
        from app import app, db, User, Brand, Model, Supplier, Purchase, Shop, Sale, Payment, Incentive
        
        with app.app_context():
            print("📤 Exporting data from SQLite...")
            
            # Export all data to JSON files
            data = {}
            
            # Users
            users = User.query.all()
            data['users'] = [{
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat() if user.created_at else None
            } for user in users]
            
            # Brands
            brands = Brand.query.all()
            data['brands'] = [{
                'id': brand.id,
                'name': brand.name,
                'created_at': brand.created_at.isoformat() if brand.created_at else None
            } for brand in brands]
            
            # Models
            models = Model.query.all()
            data['models'] = [{
                'id': model.id,
                'brand_id': model.brand_id,
                'name': model.name,
                'created_at': model.created_at.isoformat() if model.created_at else None
            } for model in models]
            
            # Suppliers
            suppliers = Supplier.query.all()
            data['suppliers'] = [{
                'id': supplier.id,
                'name': supplier.name,
                'contact_info': supplier.contact_info,
                'address': supplier.address,
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None
            } for supplier in suppliers]
            
            # Shops
            shops = Shop.query.all()
            data['shops'] = [{
                'id': shop.id,
                'name': shop.name,
                'owner_name': shop.owner_name,
                'contact_info': shop.contact_info,
                'address': shop.address,
                'credit_limit': float(shop.credit_limit) if shop.credit_limit else 0.0,
                'created_at': shop.created_at.isoformat() if shop.created_at else None
            } for shop in shops]
            
            # Purchases
            purchases = Purchase.query.all()
            data['purchases'] = [{
                'id': purchase.id,
                'model_id': purchase.model_id,
                'inventory_type': purchase.inventory_type,
                'quantity': purchase.quantity,
                'purchase_price': float(purchase.purchase_price),
                'imei_numbers': purchase.imei_numbers,
                'supplier_id': purchase.supplier_id,
                'bill_number': purchase.bill_number,
                'date': purchase.date.isoformat() if purchase.date else None,
                'user_id': purchase.user_id
            } for purchase in purchases]
            
            # Sales
            sales = Sale.query.all()
            data['sales'] = [{
                'id': sale.id,
                'model_id': sale.model_id,
                'imei_number': sale.imei_number,
                'sale_price': float(sale.sale_price),
                'purchase_price': float(sale.purchase_price),
                'profit': float(sale.profit),
                'inventory_type': sale.inventory_type,
                'customer_type': sale.customer_type,
                'shop_id': sale.shop_id,
                'customer_name': sale.customer_name,
                'payment_status': sale.payment_status,
                'paid_amount': float(sale.paid_amount),
                'due_amount': float(sale.due_amount),
                'due_date': sale.due_date.isoformat() if sale.due_date else None,
                'bill_number': sale.bill_number,
                'date': sale.date.isoformat() if sale.date else None,
                'user_id': sale.user_id
            } for sale in sales]
            
            # Payments
            payments = Payment.query.all()
            data['payments'] = [{
                'id': payment.id,
                'shop_id': payment.shop_id,
                'amount': float(payment.amount),
                'date': payment.date.isoformat() if payment.date else None,
                'user_id': payment.user_id
            } for payment in payments]
            
            # Incentives
            incentives = Incentive.query.all()
            data['incentives'] = [{
                'id': incentive.id,
                'brand_id': incentive.brand_id,
                'amount': float(incentive.amount),
                'date': incentive.date.isoformat() if incentive.date else None,
                'user_id': incentive.user_id
            } for incentive in incentives]
            
            # Save to JSON file
            with open('sqlite_export.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Data exported successfully!")
            print(f"📊 Records exported:")
            for table, records in data.items():
                print(f"   - {table}: {len(records)} records")
            
            return data
            
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return None

def import_to_mysql():
    """Import data from JSON to MySQL database."""
    try:
        # Check if export file exists
        if not os.path.exists('sqlite_export.json'):
            print("❌ Export file not found. Run export first.")
            return False
        
        # Load exported data
        with open('sqlite_export.json', 'r') as f:
            data = json.load(f)
        
        # Set MySQL configuration
        if not os.getenv('DATABASE_URL'):
            print("❌ DATABASE_URL not set. Please configure MySQL connection.")
            return False
        
        from app import app, db, User, Brand, Model, Supplier, Purchase, Shop, Sale, Payment, Incentive
        
        with app.app_context():
            print("📥 Importing data to MySQL...")
            
            # Clear existing data (optional - comment out if you want to keep existing data)
            # db.drop_all()
            # db.create_all()
            
            # Import users
            print("   - Importing users...")
            for user_data in data['users']:
                user = User(**user_data)
                db.session.add(user)
            db.session.commit()
            
            # Import brands
            print("   - Importing brands...")
            for brand_data in data['brands']:
                brand = Brand(**brand_data)
                db.session.add(brand)
            db.session.commit()
            
            # Import models
            print("   - Importing models...")
            for model_data in data['models']:
                model = Model(**model_data)
                db.session.add(model)
            db.session.commit()
            
            # Import suppliers
            print("   - Importing suppliers...")
            for supplier_data in data['suppliers']:
                supplier = Supplier(**supplier_data)
                db.session.add(supplier)
            db.session.commit()
            
            # Import shops
            print("   - Importing shops...")
            for shop_data in data['shops']:
                shop = Shop(**shop_data)
                db.session.add(shop)
            db.session.commit()
            
            # Import purchases
            print("   - Importing purchases...")
            for purchase_data in data['purchases']:
                purchase = Purchase(**purchase_data)
                db.session.add(purchase)
            db.session.commit()
            
            # Import sales
            print("   - Importing sales...")
            for sale_data in data['sales']:
                sale = Sale(**sale_data)
                db.session.add(sale)
            db.session.commit()
            
            # Import payments
            print("   - Importing payments...")
            for payment_data in data['payments']:
                payment = Payment(**payment_data)
                db.session.add(payment)
            db.session.commit()
            
            # Import incentives
            print("   - Importing incentives...")
            for incentive_data in data['incentives']:
                incentive = Incentive(**incentive_data)
                db.session.add(incentive)
            db.session.commit()
            
            print("✅ Data imported successfully to MySQL!")
            return True
            
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        return False

if __name__ == "__main__":
    print("🔄 SQLite to MySQL Migration Tool")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate_to_mysql.py export  # Export from SQLite")
        print("  python migrate_to_mysql.py import  # Import to MySQL")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'export':
        export_sqlite_data()
    elif command == 'import':
        import_to_mysql()
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'export' or 'import'")
        sys.exit(1) 