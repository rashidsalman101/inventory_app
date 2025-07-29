from app import app, db, User, Brand, Model, Shop
from werkzeug.security import generate_password_hash

def add_sample_data():
    with app.app_context():
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@mobileshop.com').first()
        if not admin:
            admin = User(
                name='Admin User',
                email='admin@mobileshop.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        
        # Create sample brands
        brands_data = ['Samsung', 'Apple', 'Huawei', 'Xiaomi']
        for brand_name in brands_data:
            brand = Brand.query.filter_by(name=brand_name).first()
            if not brand:
                brand = Brand(name=brand_name)
                db.session.add(brand)
                print(f"Brand '{brand_name}' created")
        
        # Create sample models
        models_data = [
            ('Samsung', 'Galaxy S21'),
            ('Samsung', 'Galaxy A52'),
            ('Apple', 'iPhone 13'),
            ('Apple', 'iPhone 12'),
            ('Huawei', 'P40 Pro'),
            ('Xiaomi', 'Mi 11')
        ]
        
        for brand_name, model_name in models_data:
            brand = Brand.query.filter_by(name=brand_name).first()
            if brand:
                model = Model.query.filter_by(brand_id=brand.id, name=model_name).first()
                if not model:
                    model = Model(brand_id=brand.id, name=model_name)
                    db.session.add(model)
                    print(f"Model '{brand_name} {model_name}' created")
        
        # Create sample shops
        shops_data = [
            ('Mobile World', 'Ahmed Khan', '0300-1234567', 'Karachi', 50000),
            ('Phone Store', 'Fatima Ali', '0300-7654321', 'Lahore', 30000),
            ('Tech Shop', 'Usman Hassan', '0300-9876543', 'Islamabad', 40000)
        ]
        
        for shop_name, owner, contact, address, credit_limit in shops_data:
            shop = Shop.query.filter_by(name=shop_name).first()
            if not shop:
                shop = Shop(
                    name=shop_name,
                    owner_name=owner,
                    contact_info=contact,
                    address=address,
                    credit_limit=credit_limit
                )
                db.session.add(shop)
                print(f"Shop '{shop_name}' created")
        
        db.session.commit()
        print("Sample data added successfully!")

if __name__ == "__main__":
    add_sample_data() 