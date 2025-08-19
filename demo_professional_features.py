#!/usr/bin/env python3
"""
Demo script to showcase the new professional features of the Mobile Shop Management System
"""

from app import app, db
from app import User, Brand, Model, Purchase, Sale, Shop, Supplier
from datetime import datetime, timedelta
import json

def demo_professional_features():
    """Demonstrate the new professional features"""
    
    print("🚀 Mobile Shop Management System - Professional Features Demo")
    print("=" * 70)
    
    with app.app_context():
        try:
            # Check if we have sample data
            user = User.query.filter_by(email='admin@mobileshop.com').first()
            if not user:
                print("❌ No admin user found. Please run create_tables.py first.")
                return
            
            print("✅ Admin user found")
            
            # Create sample brands and models if they don't exist
            brands = Brand.query.all()
            if not brands:
                print("📱 Creating sample brands...")
                sample_brands = ['Samsung', 'Apple', 'Xiaomi', 'OPPO']
                for brand_name in sample_brands:
                    brand = Brand(name=brand_name, created_at=datetime.utcnow())
                    db.session.add(brand)
                db.session.commit()
                print("✅ Sample brands created")
            else:
                print(f"✅ Found {len(brands)} existing brands")
            
            # Create sample models
            models = Model.query.all()
            if not models:
                print("📱 Creating sample models...")
                brand_map = {brand.name: brand.id for brand in Brand.query.all()}
                
                sample_models = [
                    ('Samsung', 'Galaxy S21'),
                    ('Apple', 'iPhone 13'),
                    ('Xiaomi', 'Mi 11'),
                    ('OPPO', 'Find X3')
                ]
                
                for brand_name, model_name in sample_models:
                    if brand_name in brand_map:
                        model = Model(
                            brand_id=brand_map[brand_name],
                            name=model_name,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(model)
                db.session.commit()
                print("✅ Sample models created")
            else:
                print(f"✅ Found {len(models)} existing models")
            
            # Create sample suppliers
            suppliers = Supplier.query.all()
            if not suppliers:
                print("🏢 Creating sample suppliers...")
                sample_suppliers = [
                    {
                        'name': 'Tech Suppliers Pakistan',
                        'contact_info': 'Phone: +92-300-1111111\nEmail: info@techsuppliers.pk',
                        'address': '123 Tech Street, Karachi, Pakistan'
                    },
                    {
                        'name': 'Mobile Importers Ltd',
                        'contact_info': 'Phone: +92-300-2222222\nEmail: sales@mobileimporters.pk',
                        'address': '456 Import Road, Lahore, Pakistan'
                    }
                ]
                
                for supplier_data in sample_suppliers:
                    supplier = Supplier(
                        name=supplier_data['name'],
                        contact_info=supplier_data['contact_info'],
                        address=supplier_data['address'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(supplier)
                db.session.commit()
                print("✅ Sample suppliers created")
            else:
                print(f"✅ Found {len(suppliers)} existing suppliers")
            
            # Create sample shops
            shops = Shop.query.all()
            if not shops:
                print("🏪 Creating sample shops...")
                sample_shops = [
                    {
                        'name': 'Mobile World',
                        'owner_name': 'Ahmed Khan',
                        'contact_info': 'Phone: +92-300-1234567\nEmail: ahmed@mobileworld.com',
                        'address': '123 Main Street, Karachi, Pakistan'
                    },
                    {
                        'name': 'Phone Store',
                        'owner_name': 'Fatima Ali',
                        'contact_info': 'Phone: +92-300-7654321\nEmail: fatima@phonestore.com',
                        'address': '456 Oak Avenue, Lahore, Pakistan'
                    }
                ]
                
                for shop_data in sample_shops:
                    shop = Shop(
                        name=shop_data['name'],
                        owner_name=shop_data['owner_name'],
                        contact_info=shop_data['contact_info'],
                        address=shop_data['address'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(shop)
                db.session.commit()
                print("✅ Sample shops created")
            else:
                print(f"✅ Found {len(shops)} existing shops")
            
            # Create sample purchases
            purchases = Purchase.query.all()
            if not purchases:
                print("📦 Creating sample purchases...")
                model_map = {model.name: model.id for model in Model.query.all()}
                supplier_map = {supplier.name: supplier.id for supplier in Supplier.query.all()}
                
                sample_purchases = [
                    {
                        'model_name': 'Galaxy S21',
                        'inventory_type': 'new',
                        'quantity': 5,
                        'purchase_price': 85000.0,
                        'imei_numbers': json.dumps(['123456789012345', '123456789012346', '123456789012347', '123456789012348', '123456789012349']),
                        'supplier_name': 'Tech Suppliers Pakistan',
                        'bill_number': 'PURCHASE-20241201-0001'
                    },
                    {
                        'model_name': 'iPhone 13',
                        'inventory_type': 'new',
                        'quantity': 3,
                        'purchase_price': 120000.0,
                        'imei_numbers': json.dumps(['987654321098765', '987654321098766', '987654321098767']),
                        'supplier_name': 'Mobile Importers Ltd',
                        'bill_number': 'PURCHASE-20241201-0002'
                    }
                ]
                
                for purchase_data in sample_purchases:
                    if purchase_data['model_name'] in model_map:
                        supplier_id = None
                        if purchase_data['supplier_name'] in supplier_map:
                            supplier_id = supplier_map[purchase_data['supplier_name']]
                        
                        purchase = Purchase(
                            model_id=model_map[purchase_data['model_name']],
                            inventory_type=purchase_data['inventory_type'],
                            quantity=purchase_data['quantity'],
                            purchase_price=purchase_data['purchase_price'],
                            imei_numbers=purchase_data['imei_numbers'],
                            supplier_id=supplier_id,
                            bill_number=purchase_data['bill_number'],
                            date=datetime.utcnow(),
                            user_id=user.id
                        )
                        db.session.add(purchase)
                db.session.commit()
                print("✅ Sample purchases created")
            else:
                print(f"✅ Found {len(purchases)} existing purchases")
            
            # Create sample sales (including grouped sales)
            sales = Sale.query.all()
            if not sales:
                print("💰 Creating sample sales (including grouped sales)...")
                model_map = {model.name: model.id for model in Model.query.all()}
                shop_map = {shop.name: shop.id for shop in Shop.query.all()}
                
                # Create a grouped sale (multiple devices with same bill number)
                bill_number = 'BILL-20241201-0001'
                
                # Sale 1: Individual customer
                sale1 = Sale(
                    model_id=model_map['Galaxy S21'],
                    imei_number='123456789012345',
                    sale_price=95000.0,
                    purchase_price=85000.0,
                    profit=10000.0,
                    inventory_type='new',
                    customer_type='individual',
                    customer_name='Ali Hassan',
                    payment_status='paid',
                    paid_amount=95000.0,
                    due_amount=0.0,
                    bill_number=bill_number,
                    date=datetime.utcnow(),
                    user_id=user.id
                )
                db.session.add(sale1)
                
                # Sale 2: Same bill number (grouped sale)
                sale2 = Sale(
                    model_id=model_map['Galaxy S21'],
                    imei_number='123456789012346',
                    sale_price=95000.0,
                    purchase_price=85000.0,
                    profit=10000.0,
                    inventory_type='new',
                    customer_type='individual',
                    customer_name='Ali Hassan',
                    payment_status='paid',
                    paid_amount=95000.0,
                    due_amount=0.0,
                    bill_number=bill_number,
                    date=datetime.utcnow(),
                    user_id=user.id
                )
                db.session.add(sale2)
                
                # Sale 3: Shop customer with partial payment
                sale3 = Sale(
                    model_id=model_map['iPhone 13'],
                    imei_number='987654321098765',
                    sale_price=135000.0,
                    purchase_price=120000.0,
                    profit=15000.0,
                    inventory_type='new',
                    customer_type='shop',
                    shop_id=shop_map['Mobile World'],
                    payment_status='partial',
                    paid_amount=80000.0,
                    due_amount=55000.0,
                    due_date=datetime.utcnow() + timedelta(days=30),
                    bill_number='BILL-20241201-0002',
                    date=datetime.utcnow(),
                    user_id=user.id
                )
                db.session.add(sale3)
                
                db.session.commit()
                print("✅ Sample sales created (including grouped sales)")
            else:
                print(f"✅ Found {len(sales)} existing sales")
            
            print("\n🎉 Professional Features Demo Setup Complete!")
            print("\n📋 What's Been Created:")
            print("   - Sample brands and models")
            print("   - Sample suppliers and shops")
            print("   - Sample purchases with IMEI numbers")
            print("   - Sample sales including grouped transactions")
            print("   - Shop sales with partial payments")
            
            print("\n🚀 Professional Features to Test:")
            print("   1. 📄 Professional Invoice Generation:")
            print("      - Visit: /bill/<sale_id>")
            print("      - Features: Company branding, grouped sales, business info")
            
            print("   2. 📊 Business Reports:")
            print("      - Visit: /business_report/<sale_id>")
            print("      - Features: Financial analysis, payment charts, business insights")
            
            print("   3. 📈 Enhanced Transactions:")
            print("      - Visit: /transactions")
            print("      - Features: Grouped sales, professional styling, business metrics")
            
            print("   4. 🏪 Professional Inventory:")
            print("      - Visit: /inventory")
            print("      - Features: Business terminology, brand filtering, professional stats")
            
            print("\n💡 Key Professional Improvements:")
            print("   ✅ Traditional mobile shop invoice design")
            print("   ✅ Grouped transaction support with all IMEIs")
            print("   ✅ Professional business reports")
            print("   ✅ Business-focused terminology and styling")
            print("   ✅ Enhanced payment tracking and analysis")
            print("   ✅ Professional company branding")
            print("   ✅ Professional business layout and styling")
            
            print("\n🔧 Database Schema Updated:")
            print("   ✅ IMEI column supports any format/length")
            print("   ✅ Migration scripts available")
            print("   ✅ Compatibility check tools")
            
            print("\n🎯 The system now provides a professional, business-focused")
            print("   mobile shop management experience!")
            
        except Exception as e:
            print(f"❌ Error setting up demo: {e}")
            db.session.rollback()

if __name__ == '__main__':
    demo_professional_features() 