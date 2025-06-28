from app import app, db, User, Brand, Distributor, ShopKeeper, Model, InventoryTransaction, IMEI
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create user
        user = User(
            name='Admin User',
            email='admin@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        
        # Create one brand
        brand = Brand(name='Samsung')
        db.session.add(brand)
        
        # Create one distributor
        distributor = Distributor(
            name='Tech Distributors Inc.', 
            contact_info='Phone: 555-0101\nEmail: info@techdist.com'
        )
        db.session.add(distributor)
        
        # Create one shop keeper
        shop_keeper = ShopKeeper(
            name='John Smith',
            shop_name='Smith Mobile Store',
            contact_info='Phone: 555-1001\nEmail: john@smithmobile.com',
            address='123 Main St, Downtown'
        )
        db.session.add(shop_keeper)
        
        db.session.commit()
        
        # Create one model
        model = Model(
            brand_id=1, 
            distributor_id=1, 
            name='Galaxy S23', 
            specs='6.1" Display, 128GB Storage', 
            price=80000.00  # PKR price
        )
        db.session.add(model)
        
        db.session.commit()
        
        # Create one purchase transaction
        purchase = InventoryTransaction(
            model_id=1, 
            distributor_id=1, 
            quantity=5, 
            price=80000.00, 
            type='purchase', 
            is_paid=True
        )
        db.session.add(purchase)
        
        db.session.commit()
        
        # Create IMEIs for the purchase
        for i in range(5):
            imei = IMEI(
                model_id=1,
                imei_number=f"12345678901234{i+1:03d}",
                status='available',
                price=80000.00
            )
            db.session.add(imei)
        
        db.session.commit()
        
        print("Seed data created successfully!")
        print(f"Created 1 brand: {brand.name}")
        print(f"Created 1 distributor: {distributor.name}")
        print(f"Created 1 shop keeper: {shop_keeper.name}")
        print(f"Created 1 model: {model.name}")
        print(f"Created 1 purchase transaction")
        print(f"Created {IMEI.query.count()} IMEIs")

if __name__ == '__main__':
    seed_data() 