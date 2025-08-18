#!/usr/bin/env python3
"""
Database initialization script for Mobile Shop Manager
Run this script to create all database tables and add initial data.
"""

from app import app, db
from app import User, Brand, Model, Purchase, Sale, Shop, Payment, Incentive, Supplier
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def create_tables():
    """Create all database tables"""
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if os.path.exists(db_path):
        print(f"Database already exists at {db_path}. Skipping table creation and seeding.")
        return True
    print("Creating database tables...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ All tables created successfully!")
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(email='admin@mobileshop.com').first()
        if not admin_user:
            # Create default admin user
            admin_user = User(
                name='Admin User',
                email='admin@mobileshop.com',
                password_hash=generate_password_hash('admin123'),
                created_at=datetime.utcnow()
            )
            db.session.add(admin_user)
            print("✓ Default admin user created (email: admin@mobileshop.com, password: admin123)")
        
        # Add some sample brands if they don't exist
        sample_brands = [
            'Samsung',
            'Apple',
            'Xiaomi',
            'OPPO',
            'Vivo',
            'OnePlus',
            'Huawei',
            'Nokia',
            'Motorola',
            'Realme'
        ]
        
        for brand_name in sample_brands:
            existing_brand = Brand.query.filter_by(name=brand_name).first()
            if not existing_brand:
                brand = Brand(name=brand_name, created_at=datetime.utcnow())
                db.session.add(brand)
                print(f"✓ Added sample brand: {brand_name}")
        
        # Add some sample models for each brand
        sample_models = [
            ('Samsung', 'Galaxy S21'),
            ('Samsung', 'Galaxy A52'),
            ('Samsung', 'Galaxy Note 20'),
            ('Apple', 'iPhone 13'),
            ('Apple', 'iPhone 12'),
            ('Apple', 'iPhone 11'),
            ('Xiaomi', 'Mi 11'),
            ('Xiaomi', 'Redmi Note 10'),
            ('OPPO', 'Find X3'),
            ('OPPO', 'Reno 6'),
            ('Vivo', 'X60'),
            ('Vivo', 'Y53s'),
            ('OnePlus', '9 Pro'),
            ('OnePlus', 'Nord 2'),
            ('Huawei', 'P40 Pro'),
            ('Huawei', 'Mate 40'),
            ('Nokia', '8.3'),
            ('Motorola', 'Edge'),
            ('Realme', 'GT'),
            ('Realme', '8 Pro')
        ]
        
        for brand_name, model_name in sample_models:
            brand = Brand.query.filter_by(name=brand_name).first()
            if brand:
                existing_model = Model.query.filter_by(brand_id=brand.id, name=model_name).first()
                if not existing_model:
                    model = Model(
                        brand_id=brand.id,
                        name=model_name,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(model)
                    print(f"✓ Added sample model: {brand_name} {model_name}")
        
        # Add some sample suppliers if they don't exist
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
            },
            {
                'name': 'Digital Devices Co',
                'contact_info': 'Phone: +92-300-3333333\nEmail: contact@digitaldevices.pk',
                'address': '789 Digital Avenue, Islamabad, Pakistan'
            },
            {
                'name': 'Smart Phone Suppliers',
                'contact_info': 'Phone: +92-300-4444444\nEmail: info@smartphonesuppliers.pk',
                'address': '321 Smart Street, Rawalpindi, Pakistan'
            },
            {
                'name': 'Electronics Hub',
                'contact_info': 'Phone: +92-300-5555555\nEmail: sales@electronicshub.pk',
                'address': '654 Electronics Road, Faisalabad, Pakistan'
            }
        ]
        
        for supplier_data in sample_suppliers:
            existing_supplier = Supplier.query.filter_by(name=supplier_data['name']).first()
            if not existing_supplier:
                supplier = Supplier(
                    name=supplier_data['name'],
                    contact_info=supplier_data['contact_info'],
                    address=supplier_data['address'],
                    created_at=datetime.utcnow()
                )
                db.session.add(supplier)
                print(f"✓ Added sample supplier: {supplier_data['name']}")
        
        # Add some sample shops if they don't exist
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
            },
            {
                'name': 'Tech Shop',
                'owner_name': 'Usman Hassan',
                'contact_info': 'Phone: +92-300-9876543\nEmail: usman@techshop.com',
                'address': '789 Pine Road, Islamabad, Pakistan'
            },
            {
                'name': 'Digital Mobile',
                'owner_name': 'Ayesha Malik',
                'contact_info': 'Phone: +92-300-1112223\nEmail: ayesha@digitalmobile.com',
                'address': '321 Tech Street, Rawalpindi, Pakistan'
            },
            {
                'name': 'Smart Phones',
                'owner_name': 'Bilal Ahmed',
                'contact_info': 'Phone: +92-300-4445556\nEmail: bilal@smartphones.com',
                'address': '654 Innovation Road, Faisalabad, Pakistan'
            }
        ]
        
        for shop_data in sample_shops:
            existing_shop = Shop.query.filter_by(name=shop_data['name']).first()
            if not existing_shop:
                shop = Shop(
                    name=shop_data['name'],
                    owner_name=shop_data['owner_name'],
                    contact_info=shop_data['contact_info'],
                    address=shop_data['address'],
                    created_at=datetime.utcnow()
                )
                db.session.add(shop)
                print(f"✓ Added sample shop: {shop_data['name']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n🎉 Database initialization completed successfully!")
            print("\nDefault login credentials:")
            print("Email: admin@mobileshop.com")
            print("Password: admin123")
            print("\n⚠️  IMPORTANT: Change the default password after first login!")
            print("\nSample data added:")
            print("- 10 Brands (Samsung, Apple, Xiaomi, etc.)")
            print("- 20 Models (Galaxy S21, iPhone 13, etc.)")
            print("- 5 Suppliers (Tech Suppliers Pakistan, Mobile Importers Ltd, etc.)")
            print("- 5 Shops (Mobile World, Phone Store, etc.)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during database initialization: {e}")
            return False
    
    return True

def reset_database():
    """Drop all tables and recreate them (WARNING: This will delete all data)"""
    print("⚠️  WARNING: This will delete all existing data!")
    confirm = input("Are you sure you want to reset the database? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Database reset cancelled.")
        return False
    
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("✓ All tables dropped!")
        
        # Recreate tables and add sample data
        return create_tables()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        create_tables() 