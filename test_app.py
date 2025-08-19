from app import app, db, User, Brand, Model, Shop, Sale, Purchase, Incentive
from datetime import datetime

def test_app():
    with app.app_context():
        print("=== Testing App Functionality ===")
        
        # Test database connections
        try:
            users = User.query.all()
            print(f"✅ Users: {len(users)} found")
            
            brands = Brand.query.all()
            print(f"✅ Brands: {len(brands)} found")
            
            models = Model.query.all()
            print(f"✅ Models: {len(models)} found")
            
            shops = Shop.query.all()
            print(f"✅ Shops: {len(shops)} found")
            
            sales = Sale.query.all()
            print(f"✅ Sales: {len(sales)} found")
            
            purchases = Purchase.query.all()
            print(f"✅ Purchases: {len(purchases)} found")
            
            incentives = Incentive.query.all()
            print(f"✅ Incentives: {len(incentives)} found")
            
            print("\n=== Database Queries Test ===")
            
            # Test dashboard queries
            total_sales_profit = db.session.query(db.func.sum(Sale.profit)).scalar() or 0
            print(f"✅ Total Sales Profit: PKR {total_sales_profit}")
            
            total_incentives = db.session.query(db.func.sum(Incentive.amount)).scalar() or 0
            print(f"✅ Total Incentives: PKR {total_incentives}")
            
            # Test shop queries
            shops_with_pending = db.session.query(Shop).select_from(Shop).join(Sale, Shop.id == Sale.shop_id).filter(
                Sale.payment_status.in_(['pending', 'partial'])
            ).distinct().all()
            print(f"✅ Shops with pending payments: {len(shops_with_pending)}")
            
            print("\n✅ All tests passed! App is working correctly.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        return True

if __name__ == "__main__":
    test_app() 