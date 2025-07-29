from app import app, db

def create_tables():
    """Create all database tables"""
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create new tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Create default admin user
        from app import User
        from werkzeug.security import generate_password_hash
        
        admin_user = User.query.filter_by(email='admin@mobileshop.com').first()
        if not admin_user:
            admin_user = User(
                name='Admin User',
                email='admin@mobileshop.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created!")
            print("Email: admin@mobileshop.com")
            print("Password: admin123")

if __name__ == '__main__':
    create_tables() 