#!/usr/bin/env python3
"""
Database initialization script for Mobile Shop Manager
Run this script to create all database tables and add initial data.
"""

from app import app, db
from app import User, Brand, Distributor, ShopKeeper, Model, InventoryTransaction, IMEI
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_tables():
    """Create all database tables"""
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
        
        # Add some sample distributors if they don't exist
        sample_distributors = [
            {'name': 'Tech Distributors Ltd', 'contact_info': 'Phone: +1234567890\nEmail: info@techdist.com'},
            {'name': 'Mobile Solutions Inc', 'contact_info': 'Phone: +0987654321\nEmail: sales@mobilesolutions.com'},
            {'name': 'Digital Devices Co', 'contact_info': 'Phone: +1122334455\nEmail: contact@digitaldevices.com'},
            {'name': 'Smart Phone Suppliers', 'contact_info': 'Phone: +1555666777\nEmail: info@smartphonesuppliers.com'}
        ]
        
        for dist_data in sample_distributors:
            existing_dist = Distributor.query.filter_by(name=dist_data['name']).first()
            if not existing_dist:
                distributor = Distributor(
                    name=dist_data['name'],
                    contact_info=dist_data['contact_info'],
                    created_at=datetime.utcnow()
                )
                db.session.add(distributor)
                print(f"✓ Added sample distributor: {dist_data['name']}")
        
        # Add some sample shop keepers if they don't exist
        sample_shop_keepers = [
            {
                'name': 'John Smith',
                'shop_name': 'Smith Mobile Store',
                'contact_info': 'Phone: +1112223333\nEmail: john@smithmobile.com',
                'address': '123 Main Street, Downtown, City'
            },
            {
                'name': 'Sarah Johnson',
                'shop_name': 'Johnson Electronics',
                'contact_info': 'Phone: +4445556666\nEmail: sarah@johnsonelectronics.com',
                'address': '456 Oak Avenue, Midtown, City'
            },
            {
                'name': 'Mike Wilson',
                'shop_name': 'Wilson Tech Shop',
                'contact_info': 'Phone: +7778889999\nEmail: mike@wilsonshop.com',
                'address': '789 Pine Road, Uptown, City'
            }
        ]
        
        for shop_data in sample_shop_keepers:
            existing_shop = ShopKeeper.query.filter_by(shop_name=shop_data['shop_name']).first()
            if not existing_shop:
                shop_keeper = ShopKeeper(
                    name=shop_data['name'],
                    shop_name=shop_data['shop_name'],
                    contact_info=shop_data['contact_info'],
                    address=shop_data['address'],
                    created_at=datetime.utcnow()
                )
                db.session.add(shop_keeper)
                print(f"✓ Added sample shop keeper: {shop_data['shop_name']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n🎉 Database initialization completed successfully!")
            print("\nDefault login credentials:")
            print("Email: admin@mobileshop.com")
            print("Password: admin123")
            print("\n⚠️  IMPORTANT: Change the default password after first login!")
            
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