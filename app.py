from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from io import BytesIO
import json
from fpdf import FPDF
from openpyxl import Workbook
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mobile_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simplified Models for new structure
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    models = db.relationship('Model', backref='brand', lazy=True)
    incentives = db.relationship('Incentive', backref='brand', lazy=True)

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    purchases = db.relationship('Purchase', backref='model', lazy=True)
    sales = db.relationship('Sale', backref='model', lazy=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    inventory_type = db.Column(db.String(10), nullable=False)  # 'new' or 'used'
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    imei_numbers = db.Column(db.Text, nullable=False)  # JSON string of IMEI numbers
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='purchases')

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.Text)
    address = db.Column(db.Text)
    credit_limit = db.Column(db.Float, default=0.0)  # Maximum credit allowed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sales = db.relationship('Sale', backref='shop', lazy=True)
    payments = db.relationship('Payment', backref='shop', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    imei_number = db.Column(db.String(15), nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)  # Auto-fetched from purchase
    profit = db.Column(db.Float, nullable=False)  # Calculated automatically
    inventory_type = db.Column(db.String(10), nullable=False)  # 'new' or 'used'
    customer_type = db.Column(db.String(20), nullable=False)  # 'individual' or 'shop'
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=True)  # NULL for individual
    customer_name = db.Column(db.String(100), nullable=True)  # For individual customers
    payment_status = db.Column(db.String(20), default='pending')  # 'paid', 'pending', 'partial'
    paid_amount = db.Column(db.Float, default=0.0)
    due_amount = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.DateTime, nullable=True)  # For shop payments
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='sales')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), default='cash')  # 'cash', 'bank_transfer', 'cheque'
    reference_number = db.Column(db.String(100), nullable=True)  # For bank transfers/cheques
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='payments')

class Incentive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='incentives')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with profit tracking"""
    try:
        # Calculate total profit including incentives
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get all sales profit (filtered by user)
        total_sales_profit = db.session.query(db.func.sum(Sale.profit)).filter(
            Sale.user_id == current_user.id
        ).scalar() or 0
        
        # Get monthly sales profit (filtered by user)
        monthly_sales_profit = db.session.query(db.func.sum(Sale.profit)).filter(
            Sale.user_id == current_user.id,
            db.extract('month', Sale.date) == current_month,
            db.extract('year', Sale.date) == current_year
        ).scalar() or 0
        
        # Get incentives (filtered by user)
        total_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
            Incentive.user_id == current_user.id
        ).scalar() or 0
        monthly_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
            Incentive.user_id == current_user.id,
            Incentive.month == current_month,
            Incentive.year == current_year
        ).scalar() or 0
        
        # Calculate total profits
        total_profit_with_incentives = total_sales_profit + total_incentives
        monthly_profit_with_incentives = monthly_sales_profit + monthly_incentives
        
        # Get recent transactions (filtered by user)
        recent_sales = Sale.query.filter_by(user_id=current_user.id).order_by(Sale.date.desc()).limit(5).all()
        recent_purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.date.desc()).limit(5).all()
        
        # Get inventory stats (filtered by user)
        total_devices_purchased = db.session.query(db.func.sum(Purchase.quantity)).filter(
            Purchase.user_id == current_user.id
        ).scalar() or 0
        total_devices_sold = Sale.query.filter_by(user_id=current_user.id).count() or 0
        available_devices = total_devices_purchased - total_devices_sold
        
        return render_template('dashboard.html',
                             total_profit=total_profit_with_incentives,
                             monthly_profit=monthly_profit_with_incentives,
                             total_sales_profit=total_sales_profit,
                             monthly_sales_profit=monthly_sales_profit,
                             total_incentives=total_incentives,
                             monthly_incentives=monthly_incentives,
                             recent_sales=recent_sales,
                             recent_purchases=recent_purchases,
                             total_devices_purchased=total_devices_purchased,
                             total_devices_sold=total_devices_sold,
                             available_devices=available_devices)
    except Exception as e:
        # Return a simple dashboard with default values if there's an error
        return render_template('dashboard.html',
                             total_profit=0,
                             monthly_profit=0,
                             total_sales_profit=0,
                             monthly_sales_profit=0,
                             total_incentives=0,
                             monthly_incentives=0,
                             recent_sales=[],
                             recent_purchases=[],
                             total_devices_purchased=0,
                             total_devices_sold=0,
                             available_devices=0)

@app.route('/inventory_type')
@login_required
def inventory_type():
    """Inventory type selector - Used or New"""
    return render_template('inventory_type.html')

@app.route('/brands')
@login_required  
def brands():
    """Brand management and selection"""
    brands = Brand.query.all()
    
    # Prepare models data with stock information (filtered by user)
    models_data = {}
    for brand in brands:
        models_data[brand.id] = []
        for model in brand.models:
            # Calculate stock for this model (filtered by user)
            total_stock = db.session.query(db.func.sum(Purchase.quantity)).filter(
                Purchase.model_id == model.id,
                Purchase.user_id == current_user.id
            ).scalar() or 0
            
            sold_stock = Sale.query.filter_by(
                model_id=model.id,
                user_id=current_user.id
            ).count()
            available_stock = total_stock - sold_stock
            
            models_data[brand.id].append({
                'id': model.id,
                'name': model.name,
                'total_stock': total_stock,
                'available_stock': available_stock,
                'sold_stock': sold_stock
            })
    
    return render_template('brands.html', brands=brands, models_data=models_data)

@app.route('/add_brand', methods=['POST'])
@login_required
def add_brand():
    name = request.form.get('name')
    if name:
        brand = Brand(name=name)
        db.session.add(brand)
        db.session.commit()
        flash('Brand added successfully!', 'success')
    return redirect(url_for('brands'))

# @app.route('/models/<int:brand_id>')
# @login_required
# def models(brand_id):
#     """Model selection for a specific brand"""
#     brand = Brand.query.get_or_404(brand_id)
#     models = Model.query.filter_by(brand_id=brand_id).all()
#     return render_template('models.html', brand=brand, models=models)

@app.route('/add_model', methods=['POST'])
@login_required
def add_model():
    brand_id = request.form.get('brand_id')
    name = request.form.get('name')
    if brand_id and name:
        model = Model(brand_id=brand_id, name=name)
        db.session.add(model)
        db.session.commit()
        flash('Model added successfully!', 'success')
    
    # Always redirect to brands page
    return redirect(url_for('brands'))

@app.route('/purchase/<int:model_id>')
@login_required
def new_purchase(model_id):
    """New purchase entry form"""
    model = Model.query.get_or_404(model_id)
    return render_template('new_purchase.html', model=model)

@app.route('/add_purchase', methods=['POST'])
@login_required
def add_purchase():
    """Add new purchase"""
    model_id = request.form.get('model_id')
    inventory_type = request.form.get('inventory_type')
    quantity = int(request.form.get('quantity'))
    purchase_price = float(request.form.get('purchase_price'))
    imei_numbers = request.form.get('imei_numbers')  # Textarea with IMEIs
    
    # Process IMEI numbers (split by newlines and clean)
    imei_list = [imei.strip() for imei in imei_numbers.split('\n') if imei.strip()]
    
    if len(imei_list) != quantity:
        flash(f'Number of IMEIs ({len(imei_list)}) must match quantity ({quantity})', 'error')
        return redirect(url_for('new_purchase', model_id=model_id))
    
    # Save purchase
    purchase = Purchase(
        model_id=model_id,
        inventory_type=inventory_type,
        quantity=quantity,
        purchase_price=purchase_price,
        imei_numbers=json.dumps(imei_list),
        user_id=current_user.id
    )
    db.session.add(purchase)
    db.session.commit()
    
    flash('Purchase added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/sale')
@login_required
def sale_module():
    """Sale module - search by IMEI"""
    return render_template('sale_module.html')

@app.route('/search_imei', methods=['POST'])
@login_required
def search_imei():
    """Search for device by IMEI"""
    imei = request.form.get('imei')
    
    # Find the purchase containing this IMEI
    purchases = Purchase.query.all()
    found_purchase = None
    
    for purchase in purchases:
        imei_list = json.loads(purchase.imei_numbers)
        if imei in imei_list:
            # Check if already sold
            existing_sale = Sale.query.filter_by(imei_number=imei).first()
            if existing_sale:
                flash('This IMEI has already been sold!', 'error')
                return redirect(url_for('sale_module'))
            
            found_purchase = purchase
            break
    
    if not found_purchase:
        flash('IMEI not found in inventory!', 'error')
        return redirect(url_for('sale_module'))
    
    shops = Shop.query.all()
    return render_template('sale_form.html', purchase=found_purchase, imei=imei, shops=shops)

@app.route('/add_sale', methods=['POST'])
@login_required
def add_sale():
    """Process sale"""
    model_id = request.form.get('model_id')
    imei_number = request.form.get('imei_number')
    sale_price = float(request.form.get('sale_price'))
    purchase_price = float(request.form.get('purchase_price'))
    inventory_type = request.form.get('inventory_type')
    customer_type = request.form.get('customer_type')
    
    profit = sale_price - purchase_price
    
    # Initialize payment tracking
    payment_status = 'paid'
    paid_amount = sale_price
    due_amount = 0
    shop_id = None
    customer_name = None
    due_date = None
    
    if customer_type == 'individual':
        customer_name = request.form.get('customer_name')
        # Individual customers pay immediately
        payment_status = 'paid'
        paid_amount = sale_price
        due_amount = 0
    elif customer_type == 'shop':
        shop_id = request.form.get('shop_id')
        due_date_str = request.form.get('due_date')
        
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        
        # Get amount paid by shop (if any)
        paid_amount = float(request.form.get('paid_amount') or 0)
        
        # Calculate due amount
        due_amount = sale_price - paid_amount
        
        # Set payment status based on amount paid
        if paid_amount >= sale_price:
            payment_status = 'paid'
            due_amount = 0
        elif paid_amount > 0:
            payment_status = 'partial'
        else:
            payment_status = 'pending'
    
    sale = Sale(
        model_id=model_id,
        imei_number=imei_number,
        sale_price=sale_price,
        purchase_price=purchase_price,
        profit=profit,
        inventory_type=inventory_type,
        customer_type=customer_type,
        shop_id=shop_id,
        customer_name=customer_name,
        payment_status=payment_status,
        paid_amount=paid_amount,
        due_amount=due_amount,
        due_date=due_date,
        user_id=current_user.id
    )
    db.session.add(sale)
    db.session.commit()
    
    if payment_status == 'paid':
        flash(f'Sale completed! Profit: PKR {profit:.2f}', 'success')
    else:
        flash(f'Credit sale completed! Due amount: PKR {due_amount:.2f}', 'warning')
    
    return redirect(url_for('generate_bill', sale_id=sale.id))

@app.route('/bill/<int:sale_id>')
@login_required
def generate_bill(sale_id):
    """Generate bill for sale"""
    sale = Sale.query.filter_by(id=sale_id, user_id=current_user.id).first_or_404()
    return render_template('bill.html', sale=sale)

@app.route('/internal_report/<int:sale_id>')
@login_required
def internal_report(sale_id):
    """Internal report with profit details for business analysis"""
    sale = Sale.query.filter_by(id=sale_id, user_id=current_user.id).first_or_404()
    return render_template('internal_report.html', sale=sale)

@app.route('/incentives')
@login_required
def incentives():
    """Incentive management"""
    brands = Brand.query.all()
    incentives = Incentive.query.filter_by(user_id=current_user.id).order_by(Incentive.date.desc()).all()
    
    # Calculate incentive totals (filtered by user)
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    total_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
        Incentive.user_id == current_user.id
    ).scalar() or 0
    monthly_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
        Incentive.user_id == current_user.id,
        Incentive.month == current_month,
        Incentive.year == current_year
    ).scalar() or 0
    
    return render_template('incentives.html', 
                         brands=brands, 
                         incentives=incentives,
                         total_incentives=total_incentives,
                         monthly_incentives=monthly_incentives,
                         now=datetime.now())

@app.route('/shops')
@login_required
def shops():
    """Shop management"""
    try:
        shops = Shop.query.all()
        
        # Calculate financial data for each shop (filtered by user)
        for shop in shops:
            shop.total_sales = db.session.query(db.func.sum(Sale.sale_price)).filter(
                Sale.shop_id == shop.id,
                Sale.user_id == current_user.id
            ).scalar() or 0
            
            shop.total_paid = db.session.query(db.func.sum(Sale.paid_amount)).filter(
                Sale.shop_id == shop.id,
                Sale.user_id == current_user.id
            ).scalar() or 0
            
            shop.total_due = db.session.query(db.func.sum(Sale.due_amount)).filter(
                Sale.shop_id == shop.id,
                Sale.user_id == current_user.id
            ).scalar() or 0
        
        return render_template('shops.html', shops=shops)
    except Exception as e:
        # Return empty shops list if there's an error
        return render_template('shops.html', shops=[])

@app.route('/add_shop', methods=['POST'])
@login_required
def add_shop():
    """Add new shop"""
    name = request.form.get('name')
    owner_name = request.form.get('owner_name')
    contact_info = request.form.get('contact_info')
    address = request.form.get('address')
    
    shop = Shop(
        name=name,
        owner_name=owner_name,
        contact_info=contact_info,
        address=address
    )
    db.session.add(shop)
    db.session.commit()
    
    flash('Shop added successfully!', 'success')
    return redirect(url_for('shops'))

@app.route('/shop/<int:shop_id>')
@login_required
def shop_details(shop_id):
    """Shop details with payment history"""
    # Check if user has any sales with this shop
    shop = Shop.query.get_or_404(shop_id)
    user_has_sales = Sale.query.filter_by(shop_id=shop_id, user_id=current_user.id).first() is not None
    if not user_has_sales:
        flash('Access denied. You can only view shops you have sales with.', 'error')
        return redirect(url_for('shops'))
    
    # Calculate shop's financial summary (filtered by user)
    total_sales = db.session.query(db.func.sum(Sale.sale_price)).filter(
        Sale.shop_id == shop_id,
        Sale.user_id == current_user.id
    ).scalar() or 0
    
    total_paid = db.session.query(db.func.sum(Sale.paid_amount)).filter(
        Sale.shop_id == shop_id,
        Sale.user_id == current_user.id
    ).scalar() or 0
    
    total_due = db.session.query(db.func.sum(Sale.due_amount)).filter(
        Sale.shop_id == shop_id,
        Sale.user_id == current_user.id
    ).scalar() or 0
    
    # Get recent sales and payments (filtered by user)
    recent_sales = Sale.query.filter_by(
        shop_id=shop_id,
        user_id=current_user.id
    ).order_by(Sale.date.desc()).limit(10).all()
    recent_payments = Payment.query.filter_by(
        shop_id=shop_id,
        user_id=current_user.id
    ).order_by(Payment.payment_date.desc()).limit(10).all()
    
    return render_template('shop_details.html', 
                         shop=shop,
                         total_sales=total_sales,
                         total_paid=total_paid,
                         total_due=total_due,
                         recent_sales=recent_sales,
                         recent_payments=recent_payments)

@app.route('/add_payment', methods=['POST'])
@login_required
def add_payment():
    """Add payment for a shop"""
    shop_id = request.form.get('shop_id')
    amount = float(request.form.get('amount'))
    payment_method = request.form.get('payment_method')
    reference_number = request.form.get('reference_number')
    notes = request.form.get('notes')
    
    payment = Payment(
        shop_id=shop_id,
        amount=amount,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes,
        user_id=current_user.id
    )
    db.session.add(payment)
    db.session.commit()
    
    # Update shop's due amounts
    shop = Shop.query.get(shop_id)
    if shop:
        # Find pending sales and apply payment
        pending_sales = Sale.query.filter_by(
            shop_id=shop_id, 
            payment_status='pending'
        ).order_by(Sale.date.asc()).all()
        
        remaining_amount = amount
        for sale in pending_sales:
            if remaining_amount <= 0:
                break
                
            if sale.due_amount > 0:
                payment_amount = min(remaining_amount, sale.due_amount)
                sale.paid_amount += payment_amount
                sale.due_amount -= payment_amount
                
                if sale.due_amount == 0:
                    sale.payment_status = 'paid'
                else:
                    sale.payment_status = 'partial'
                
                remaining_amount -= payment_amount
        
        db.session.commit()
    
    flash(f'Payment of PKR {amount:,.2f} added successfully!', 'success')
    return redirect(url_for('shop_details', shop_id=shop_id))

@app.route('/pending_payments')
@login_required
def pending_payments():
    """View all pending payments"""
    try:
        # Get all shops with pending payments (filtered by user)
        shops_with_pending = db.session.query(Shop).join(Sale).filter(
            Sale.payment_status.in_(['pending', 'partial']),
            Sale.user_id == current_user.id
        ).distinct().all()
        
        # Calculate pending amounts for each shop (filtered by user)
        shop_pending_data = []
        for shop in shops_with_pending:
            total_due = db.session.query(db.func.sum(Sale.due_amount)).filter(
                Sale.shop_id == shop.id,
                Sale.user_id == current_user.id
            ).scalar() or 0
            
            overdue_sales = Sale.query.filter(
                Sale.shop_id == shop.id,
                Sale.user_id == current_user.id,
                Sale.due_amount > 0,
                Sale.due_date < datetime.now()
            ).count()
            
            shop_pending_data.append({
                'shop': shop,
                'total_due': total_due,
                'overdue_sales': overdue_sales
            })
        
        return render_template('pending_payments.html', shop_pending_data=shop_pending_data)
    except Exception as e:
        # Return empty data if there's an error
        return render_template('pending_payments.html', shop_pending_data=[])

@app.route('/add_incentive', methods=['POST'])
@login_required
def add_incentive():
    """Add brand incentive"""
    brand_id = request.form.get('brand_id')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    month = int(request.form.get('month'))
    year = int(request.form.get('year'))
    
    incentive = Incentive(
        brand_id=brand_id,
        amount=amount,
        description=description,
        month=month,
        year=year,
        user_id=current_user.id
    )
    db.session.add(incentive)
    db.session.commit()
    
    flash('Incentive added successfully!', 'success')
    return redirect(url_for('incentives'))

@app.route('/ledger')
@login_required
def shop_ledger():
    """Shop ledger with all transactions"""
    brand_filter = request.args.get('brand')
    model_filter = request.args.get('model')
    
    # Get all transactions (filtered by user)
    purchases = Purchase.query.filter_by(user_id=current_user.id)
    sales = Sale.query.filter_by(user_id=current_user.id)
    
    if brand_filter:
        purchases = purchases.join(Model).filter(Model.brand_id == brand_filter)
        sales = sales.join(Model).filter(Model.brand_id == brand_filter)
    
    if model_filter:
        purchases = purchases.filter(Purchase.model_id == model_filter)
        sales = sales.filter(Sale.model_id == model_filter)
    
    purchases = purchases.order_by(Purchase.date.desc()).all()
    sales = sales.order_by(Sale.date.desc()).all()
    
    brands = Brand.query.all()
    models = Model.query.all()
    
    # Calculate profit totals (filtered by user)
    total_sales_profit = db.session.query(db.func.sum(Sale.profit)).filter(
        Sale.user_id == current_user.id
    ).scalar() or 0
    total_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
        Incentive.user_id == current_user.id
    ).scalar() or 0
    
    return render_template('ledger.html', 
                         purchases=purchases, 
                         sales=sales, 
                         brands=brands, 
                         models=models,
                         selected_brand=brand_filter,
                         selected_model=model_filter,
                         total_sales_profit=total_sales_profit,
                         total_incentives=total_incentives)

@app.route('/export_report')
@login_required
def export_report():
    """Generate and export PDF report"""
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Mobile Shop Inventory Report', ln=True, align='C')
    pdf.ln(10)
    
    # Summary
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    total_sales_profit = db.session.query(db.func.sum(Sale.profit)).filter(
        Sale.user_id == current_user.id
    ).scalar() or 0
    monthly_sales_profit = db.session.query(db.func.sum(Sale.profit)).filter(
        Sale.user_id == current_user.id,
        db.extract('month', Sale.date) == current_month,
        db.extract('year', Sale.date) == current_year
    ).scalar() or 0
    
    total_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
        Incentive.user_id == current_user.id
    ).scalar() or 0
    monthly_incentives = db.session.query(db.func.sum(Incentive.amount)).filter(
        Incentive.user_id == current_user.id,
        Incentive.month == current_month,
        Incentive.year == current_year
    ).scalar() or 0
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Profit Summary', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Total Sales Profit: PKR {total_sales_profit:,.2f}', ln=True)
    pdf.cell(0, 8, f'Monthly Sales Profit: PKR {monthly_sales_profit:,.2f}', ln=True)
    pdf.cell(0, 8, f'Total Incentives: PKR {total_incentives:,.2f}', ln=True)
    pdf.cell(0, 8, f'Monthly Incentives: PKR {monthly_incentives:,.2f}', ln=True)
    pdf.cell(0, 8, f'Total Profit (including incentives): PKR {(total_sales_profit + total_incentives):,.2f}', ln=True)
    pdf.ln(10)
    
    # Recent Sales
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Recent Sales', ln=True)
    pdf.set_font('Arial', '', 10)
    
    recent_sales = Sale.query.order_by(Sale.date.desc()).limit(10).all()
    for sale in recent_sales:
        pdf.cell(0, 6, f'{sale.date.strftime("%Y-%m-%d")} - {sale.model.brand.name} {sale.model.name} - IMEI: {sale.imei_number} - Profit: PKR {sale.profit:.2f}', ln=True)
    
    # Save PDF
    pdf_buffer = BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin-1')
    pdf_buffer.write(pdf_content)
    pdf_buffer.seek(0)
    
    return send_file(pdf_buffer, 
                     as_attachment=True, 
                     download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.pdf',
                     mimetype='application/pdf')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 