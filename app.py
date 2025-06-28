from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from io import BytesIO
import json
from fpdf import FPDF
from openpyxl import Workbook

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    models = db.relationship('Model', backref='brand', lazy=True)

class Distributor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ShopKeeper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    shop_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.Text)
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributor.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specs = db.Column(db.Text)
    price = db.Column(db.Float, nullable=True)  # Default price for this model
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    distributor = db.relationship('Distributor', backref='models')

class InventoryTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributor.id'), nullable=False)
    shop_keeper_id = db.Column(db.Integer, db.ForeignKey('shop_keeper.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'purchase', 'sale', 'return', 'shop_sale'
    date = db.Column(db.DateTime, default=datetime.utcnow)
    buyer_name = db.Column(db.String(100))
    is_paid = db.Column(db.Boolean, default=False)
    return_reason = db.Column(db.Text)  # For return transactions
    model = db.relationship('Model', backref='transactions')
    distributor = db.relationship('Distributor', backref='transactions')
    shop_keeper = db.relationship('ShopKeeper', backref='transactions')

class IMEI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    imei_number = db.Column(db.String(15), unique=True, nullable=False)
    status = db.Column(db.String(20), default='available')  # 'available', 'sold', 'returned'
    price = db.Column(db.Float)
    buyer_name = db.Column(db.String(100))
    sold_on = db.Column(db.DateTime)
    returned_on = db.Column(db.DateTime)
    transaction_id = db.Column(db.Integer, db.ForeignKey('inventory_transaction.id'))
    return_transaction_id = db.Column(db.Integer, db.ForeignKey('inventory_transaction.id'))
    model = db.relationship('Model', backref='imeis')
    transaction = db.relationship('InventoryTransaction', backref='imeis', foreign_keys=[transaction_id])
    return_transaction = db.relationship('InventoryTransaction', backref='returned_imeis', foreign_keys=[return_transaction_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor to provide 'now' function to templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# Routes
@app.route('/')
@login_required
def dashboard():
    """Dashboard with summary statistics"""
    # Get summary data
    total_purchases = db.session.query(db.func.sum(InventoryTransaction.price * InventoryTransaction.quantity)).filter_by(type='purchase').scalar() or 0
    total_sales = db.session.query(db.func.sum(InventoryTransaction.price * InventoryTransaction.quantity)).filter_by(type='sale').scalar() or 0
    total_shop_sales = db.session.query(db.func.sum(InventoryTransaction.price * InventoryTransaction.quantity)).filter_by(type='shop_sale').scalar() or 0
    total_returns = db.session.query(db.func.sum(InventoryTransaction.price * InventoryTransaction.quantity)).filter_by(type='return').scalar() or 0
    
    gross_profit = total_sales + total_shop_sales - total_purchases - total_returns
    
    # Get recent transactions
    recent_transactions = InventoryTransaction.query.order_by(InventoryTransaction.date.desc()).limit(10).all()
    
    # Get pending payments (both regular sales and shop sales)
    pending_sales = InventoryTransaction.query.filter_by(type='sale', is_paid=False).all()
    pending_shop_sales = InventoryTransaction.query.filter_by(type='shop_sale', is_paid=False).all()
    total_pending = sum(t.price * t.quantity for t in pending_sales + pending_shop_sales)
    
    # Get shop keeper statistics
    total_shop_keepers = ShopKeeper.query.count()
    active_shop_keepers = db.session.query(ShopKeeper).join(InventoryTransaction).distinct().count()
    
    # Get IMEI statistics
    total_imeis = IMEI.query.count()
    available_imeis = IMEI.query.filter_by(status='available').count()
    sold_imeis = IMEI.query.filter_by(status='sold').count()
    returned_imeis = IMEI.query.filter_by(status='returned').count()
    
    return render_template('dashboard.html', 
                         total_purchases=total_purchases,
                         total_sales=total_sales,
                         total_shop_sales=total_shop_sales,
                         total_returns=total_returns,
                         gross_profit=gross_profit,
                         recent_transactions=recent_transactions,
                         pending_payments=pending_sales + pending_shop_sales,
                         total_pending=total_pending,
                         total_shop_keepers=total_shop_keepers,
                         active_shop_keepers=active_shop_keepers,
                         total_imeis=total_imeis,
                         available_imeis=available_imeis,
                         sold_imeis=sold_imeis,
                         returned_imeis=returned_imeis)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
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
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html')
        
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/transactions')
@login_required
def transactions():
    transactions = InventoryTransaction.query.order_by(InventoryTransaction.date.desc()).all()
    distributors = Distributor.query.all()
    models = Model.query.all()
    brands = Brand.query.all()
    imeis = IMEI.query.join(Model).join(Brand).join(Distributor).order_by(IMEI.id.desc()).all()
    return render_template('transactions.html', transactions=transactions, distributors=distributors, models=models, brands=brands, imeis=imeis)

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ['model_id', 'distributor_id', 'quantity', 'price', 'type']):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    try:
        transaction = InventoryTransaction(
            model_id=data['model_id'],
            distributor_id=data['distributor_id'],
            quantity=data['quantity'],
            price=data['price'],
            type=data['type'],
            buyer_name=data.get('buyer_name'),
            is_paid=data.get('is_paid', False)
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # If it's a sale, add IMEIs
        if data['type'] == 'sale' and data.get('imeis'):
            for imei_number in data['imeis']:
                imei_number = imei_number.strip()
                if imei_number:
                    # Check if IMEI exists and is available
                    existing_imei = IMEI.query.filter_by(imei_number=imei_number, status='available').first()
                    if existing_imei:
                        existing_imei.status = 'sold'
                        existing_imei.buyer_name = data.get('buyer_name')
                        existing_imei.sold_on = datetime.utcnow()
                        existing_imei.transaction_id = transaction.id
                    else:
                        # Create new IMEI entry for sale
                        imei = IMEI(
                            model_id=data['model_id'],
                            imei_number=imei_number,
                            status='sold',
                            buyer_name=data.get('buyer_name'),
                            sold_on=datetime.utcnow(),
                            transaction_id=transaction.id
                        )
                        db.session.add(imei)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pending_payments')
@login_required
def pending_payments():
    pending_sales = InventoryTransaction.query.filter_by(type='sale', is_paid=False).all()
    pending_shop_sales = InventoryTransaction.query.filter_by(type='shop_sale', is_paid=False).all()
    pending = pending_sales + pending_shop_sales
    total_pending = sum(t.price * t.quantity for t in pending)
    return render_template('pending_payments.html', pending=pending, total_pending=total_pending)

@app.route('/mark_paid/<int:transaction_id>', methods=['POST'])
@login_required
def mark_paid(transaction_id):
    try:
        transaction = InventoryTransaction.query.get_or_404(transaction_id)
        transaction.is_paid = True
        db.session.commit()
        
        # Check if request expects JSON response
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True})
        else:
            flash('Payment marked as received', 'success')
            return redirect(url_for('pending_payments'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'error': str(e)})
        else:
            flash(f'Error marking payment: {str(e)}', 'error')
            return redirect(url_for('pending_payments'))

@app.route('/distributors')
@login_required
def distributors():
    distributors = Distributor.query.all()
    return render_template('distributors.html', distributors=distributors)

@app.route('/add_distributor', methods=['POST'])
@login_required
def add_distributor():
    name = request.form['name']
    contact_info = request.form.get('contact_info', '')
    
    distributor = Distributor(name=name, contact_info=contact_info)
    db.session.add(distributor)
    db.session.commit()
    flash('Distributor added successfully!', 'success')
    return redirect(url_for('distributors'))

@app.route('/edit_distributor/<int:distributor_id>', methods=['POST'])
@login_required
def edit_distributor(distributor_id):
    try:
        distributor = Distributor.query.get_or_404(distributor_id)
        
        distributor.name = request.form['name']
        distributor.contact_info = request.form.get('contact_info', '')
        
        db.session.commit()
        flash('Distributor updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating distributor: {str(e)}', 'error')
    
    return redirect(url_for('distributors'))

@app.route('/delete_distributor/<int:distributor_id>', methods=['POST'])
@login_required
def delete_distributor(distributor_id):
    try:
        distributor = Distributor.query.get_or_404(distributor_id)
        
        # Check if distributor has any models or transactions
        if distributor.models or distributor.transactions:
            flash('Cannot delete distributor with existing models or transactions', 'error')
            return redirect(url_for('distributors'))
        
        db.session.delete(distributor)
        db.session.commit()
        flash('Distributor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting distributor: {str(e)}', 'error')
    
    return redirect(url_for('distributors'))

@app.route('/models')
@login_required
def models():
    models = Model.query.join(Brand).join(Distributor).all()
    brands = Brand.query.all()
    distributors = Distributor.query.all()
    return render_template('models.html', models=models, brands=brands, distributors=distributors)

@app.route('/add_model', methods=['POST'])
@login_required
def add_model():
    brand_id = request.form['brand_id']
    distributor_id = request.form['distributor_id']
    name = request.form['name']
    specs = request.form.get('specs', '')
    price = float(request.form.get('price', 0)) if request.form.get('price') else None
    
    model = Model(
        brand_id=brand_id,
        distributor_id=distributor_id,
        name=name,
        specs=specs,
        price=price
    )
    db.session.add(model)
    db.session.commit()
    flash('Model added successfully!', 'success')
    return redirect(url_for('models'))

@app.route('/edit_model/<int:model_id>', methods=['POST'])
@login_required
def edit_model(model_id):
    try:
        model = Model.query.get_or_404(model_id)
        
        model.brand_id = request.form['brand_id']
        model.distributor_id = request.form['distributor_id']
        model.name = request.form['name']
        model.specs = request.form.get('specs', '')
        model.price = float(request.form.get('price', 0)) if request.form.get('price') else None
        
        db.session.commit()
        flash('Model updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating model: {str(e)}', 'error')
    
    return redirect(url_for('models'))

@app.route('/delete_model/<int:model_id>', methods=['POST'])
@login_required
def delete_model(model_id):
    try:
        model = Model.query.get_or_404(model_id)
        
        # Check if model has any transactions or IMEIs
        if model.transactions or model.imeis:
            flash('Cannot delete model with existing transactions or IMEIs', 'error')
            return redirect(url_for('models'))
        
        db.session.delete(model)
        db.session.commit()
        flash('Model deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting model: {str(e)}', 'error')
    
    return redirect(url_for('models'))

@app.route('/export_excel')
@login_required
def export_excel():
    transactions = InventoryTransaction.query.all()
    data = []
    for t in transactions:
        data.append([
            t.date.strftime('%Y-%m-%d %H:%M'),
            t.type.title(),
            t.model.name,
            t.distributor.name,
            t.quantity,
            t.price,
            t.price * t.quantity,
            t.buyer_name or '',
            'Yes' if t.is_paid else 'No'
        ])
    headers = ['Date', 'Type', 'Model', 'Distributor', 'Quantity', 'Price', 'Total', 'Buyer', 'Paid']
    wb = Workbook()
    ws = wb.active
    ws.title = 'Transactions'
    ws.append(headers)
    for row in data:
        ws.append(row)
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True, download_name='inventory_report.xlsx')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.name = request.form['name']
    current_user.email = request.form['email']
    
    if request.form.get('new_password'):
        current_user.password_hash = generate_password_hash(request.form['new_password'])
    
    # Handle avatar upload
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.avatar = filename
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/api/models/<int:distributor_id>')
@login_required
def get_models_by_distributor(distributor_id):
    models = Model.query.filter_by(distributor_id=distributor_id).all()
    return jsonify([{'id': m.id, 'name': m.name} for m in models])

@app.route('/add_device', methods=['GET'])
@login_required
def add_device():
    brands = Brand.query.all()
    distributors = Distributor.query.all()
    return render_template('add_device.html', brands=brands, distributors=distributors)

@app.route('/add_single_device', methods=['POST'])
@login_required
def add_single_device():
    try:
        model_id = request.form['model_id']
        distributor_id = request.form['distributor_id']
        price = float(request.form['price'])
        imei_number = request.form['imei_number'].strip()
        
        # Validate IMEI format (basic validation)
        if len(imei_number) < 10 or len(imei_number) > 15:
            flash('IMEI must be between 10-15 characters', 'error')
            return redirect(url_for('add_device'))
        
        # Check for duplicate IMEI
        if IMEI.query.filter_by(imei_number=imei_number).first():
            flash('IMEI already exists in database', 'error')
            return redirect(url_for('add_device'))
        
        # Create transaction
        transaction = InventoryTransaction(
            model_id=model_id,
            distributor_id=distributor_id,
            quantity=1,
            price=price,
            type='purchase',
            date=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Add IMEI
        imei = IMEI(
            model_id=model_id,
            imei_number=imei_number,
            status='available',
            price=price,
            transaction_id=transaction.id
        )
        db.session.add(imei)
        db.session.commit()
        
        flash('Device added successfully!', 'success')
        return redirect(url_for('add_device'))
        
    except (ValueError, KeyError) as e:
        flash('Invalid data provided', 'error')
        return redirect(url_for('add_device'))

@app.route('/add_bulk_devices', methods=['POST'])
@login_required
def add_bulk_devices():
    try:
        model_id = request.form['model_id']
        distributor_id = request.form['distributor_id']
        price = float(request.form['price'])
        imeis = request.form.getlist('imeis[]')
        
        if not imeis:
            flash('No IMEIs provided', 'error')
            return redirect(url_for('add_device'))
        
        # Validate and check for duplicates
        valid_imeis = []
        duplicate_imeis = []
        
        for imei in imeis:
            imei = imei.strip()
            if len(imei) < 10 or len(imei) > 15:
                continue  # Skip invalid IMEIs
            
            if IMEI.query.filter_by(imei_number=imei).first():
                duplicate_imeis.append(imei)
            else:
                valid_imeis.append(imei)
        
        if not valid_imeis:
            flash('No valid IMEIs provided', 'error')
            return redirect(url_for('add_device'))
        
        if duplicate_imeis:
            flash(f'Duplicate IMEIs found: {", ".join(duplicate_imeis)}', 'warning')
        
        # Add each device separately
        added_count = 0
        for imei_number in valid_imeis:
            # Create transaction for each device
            transaction = InventoryTransaction(
                model_id=model_id,
                distributor_id=distributor_id,
                quantity=1,
                price=price,
                type='purchase',
                date=datetime.utcnow()
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Add IMEI
            imei = IMEI(
                model_id=model_id,
                imei_number=imei_number,
                status='available',
                price=price,
                transaction_id=transaction.id
            )
            db.session.add(imei)
            added_count += 1
        
        db.session.commit()
        flash(f'{added_count} devices added successfully!', 'success')
        return redirect(url_for('add_device'))
        
    except (ValueError, KeyError) as e:
        flash('Invalid data provided', 'error')
        return redirect(url_for('add_device'))

@app.route('/api/models_by_brand/<int:brand_id>')
@login_required
def api_models_by_brand(brand_id):
    models = Model.query.filter_by(brand_id=brand_id).all()
    return jsonify([{'id': m.id, 'name': m.name, 'price': m.price} for m in models])

@app.route('/api/model/<int:model_id>')
@login_required
def api_model_details(model_id):
    model = Model.query.get_or_404(model_id)
    return jsonify({
        'id': model.id,
        'name': model.name,
        'price': model.price,
        'specs': model.specs,
        'brand_name': model.brand.name,
        'distributor_name': model.distributor.name
    })

@app.route('/edit_imei/<int:imei_id>', methods=['GET', 'POST'])
@login_required
def edit_imei(imei_id):
    imei = IMEI.query.get_or_404(imei_id)
    if request.method == 'POST':
        imei.price = float(request.form['price'])
        db.session.commit()
        flash('IMEI price updated!', 'success')
        return redirect(url_for('transactions'))
    return render_template('edit_imei.html', imei=imei)

@app.route('/brands')
@login_required
def brands():
    brands = Brand.query.all()
    return render_template('brands.html', brands=brands)

@app.route('/add_brand', methods=['POST'])
@login_required
def add_brand():
    name = request.form['name']
    
    if Brand.query.filter_by(name=name).first():
        flash('Brand already exists!', 'error')
    else:
        brand = Brand(name=name)
        db.session.add(brand)
        db.session.commit()
        flash('Brand added successfully!', 'success')
    
    return redirect(url_for('brands'))

@app.route('/edit_brand/<int:brand_id>', methods=['POST'])
@login_required
def edit_brand(brand_id):
    try:
        brand = Brand.query.get_or_404(brand_id)
        name = request.form['name']
        
        # Check if name already exists (excluding current brand)
        existing_brand = Brand.query.filter_by(name=name).first()
        if existing_brand and existing_brand.id != brand_id:
            flash('Brand name already exists!', 'error')
            return redirect(url_for('brands'))
        
        brand.name = name
        db.session.commit()
        flash('Brand updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating brand: {str(e)}', 'error')
    
    return redirect(url_for('brands'))

@app.route('/delete_brand/<int:brand_id>', methods=['POST'])
@login_required
def delete_brand(brand_id):
    try:
        brand = Brand.query.get_or_404(brand_id)
        
        # Check if brand has any models
        if brand.models:
            flash('Cannot delete brand with existing models', 'error')
            return redirect(url_for('brands'))
        
        db.session.delete(brand)
        db.session.commit()
        flash('Brand deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting brand: {str(e)}', 'error')
    
    return redirect(url_for('brands'))

@app.route('/api/available_devices')
@login_required
def api_available_devices():
    """Get all available devices for sale"""
    available_imeis = IMEI.query.filter_by(status='available').all()
    devices = []
    
    for imei in available_imeis:
        devices.append({
            'id': imei.id,
            'brand_id': imei.model.brand.id,
            'brand_name': imei.model.brand.name,
            'model_id': imei.model.id,
            'model_name': imei.model.name,
            'imei_number': imei.imei_number,
            'purchase_price': imei.price or 0
        })
    
    return jsonify(devices)

@app.route('/add_sale_transaction', methods=['POST'])
@login_required
def add_sale_transaction():
    """Handle sale transactions with device selection"""
    data = request.get_json()
    
    try:
        buyer_name = data.get('buyer_name', '').strip()
        is_paid = data.get('is_paid', False)
        devices = data.get('devices', [])
        
        if not buyer_name:
            return jsonify({'success': False, 'error': 'Buyer name is required'})
        
        if not devices:
            return jsonify({'success': False, 'error': 'No devices selected'})
        
        # Create sale transaction
        total_quantity = len(devices)
        total_amount = sum(device['selling_price'] for device in devices)
        
        transaction = InventoryTransaction(
            model_id=1,  # Will be updated based on selected devices
            distributor_id=1,  # Will be updated based on selected devices
            quantity=total_quantity,
            price=total_amount / total_quantity,  # Average price
            type='sale',
            buyer_name=buyer_name,
            is_paid=is_paid,
            date=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Update IMEI status and create sale records
        for device_data in devices:
            imei_id = device_data['device_id']
            selling_price = device_data['selling_price']
            
            imei = IMEI.query.get(imei_id)
            if imei and imei.status == 'available':
                imei.status = 'sold'
                imei.buyer_name = buyer_name
                imei.sold_on = datetime.utcnow()
                imei.transaction_id = transaction.id
                imei.price = selling_price  # Update to selling price
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export_comprehensive_report')
@login_required
def export_comprehensive_report():
    """Export comprehensive report with all stats and data"""
    try:
        transactions = InventoryTransaction.query.order_by(InventoryTransaction.date.desc()).all()
        recent_transactions = InventoryTransaction.query.order_by(InventoryTransaction.date.desc()).limit(5).all()
        brands = Brand.query.all()
        imeis = IMEI.query.all()
        purchases = InventoryTransaction.query.filter_by(type='purchase').all()
        sales = InventoryTransaction.query.filter_by(type='sale').all()
        total_revenue = sum(s.price * s.quantity for s in sales) if sales else 0
        total_cost = sum(p.price * p.quantity for p in purchases) if purchases else 0
        gross_profit = total_revenue - total_cost
        total_purchases = sum(p.quantity for p in purchases) if purchases else 0
        total_sales = sum(s.quantity for s in sales) if sales else 0
        available_devices = IMEI.query.filter_by(status='available').count()
        total_imeis = IMEI.query.count()
        total_brands = Brand.query.count()
        total_models = Model.query.count()
        total_distributors = Distributor.query.count()
        wb = Workbook()
        # 1. Dashboard Summary Sheet
        ws1 = wb.active
        ws1.title = 'Dashboard Summary'
        ws1.append(['Metric', 'Value'])
        summary_rows = [
            ['Total Profit', f"PKR {gross_profit:,.2f}"],
            ['Total Revenue', f"PKR {total_revenue:,.2f}"],
            ['Total Cost', f"PKR {total_cost:,.2f}"],
            ['Total Devices Purchased', total_purchases],
            ['Total Devices Sold', total_sales],
            ['Available Devices', available_devices],
            ['Total IMEIs', total_imeis],
            ['Total Brands', total_brands],
            ['Total Models', total_models],
            ['Total Distributors', total_distributors],
        ]
        for row in summary_rows:
            ws1.append(row)
        # 2. All Transactions Sheet
        ws2 = wb.create_sheet('All Transactions')
        ws2.append(['Date', 'Type', 'Brand', 'Model', 'Distributor', 'Quantity', 'Price per Unit', 'Total Amount', 'Buyer Name', 'Payment Status'])
        for t in transactions:
            ws2.append([
                t.date.strftime('%Y-%m-%d %H:%M'),
                t.type.title(),
                t.model.brand.name,
                t.model.name,
                t.distributor.name,
                t.quantity,
                f"PKR {t.price:.2f}",
                f"PKR {t.price * t.quantity:.2f}",
                t.buyer_name or 'N/A',
                'Paid' if t.is_paid else 'Pending' if t.type == 'sale' else 'N/A'
            ])
        # 3. Device Inventory Sheet
        ws3 = wb.create_sheet('Device Inventory')
        ws3.append(['Brand', 'Model', 'Distributor', 'IMEI', 'Status', 'Price', 'Buyer Name', 'Sold On'])
        for imei in imeis:
            ws3.append([
                imei.model.brand.name,
                imei.model.name,
                imei.model.distributor.name,
                imei.imei_number,
                imei.status.title(),
                f"PKR {imei.price:.2f}" if imei.price else 'N/A',
                imei.buyer_name or 'N/A',
                imei.sold_on.strftime('%Y-%m-%d %H:%M') if imei.sold_on else 'N/A'
            ])
        # 4. Brands and Models Sheet
        ws4 = wb.create_sheet('Brands & Models')
        ws4.append(['Brand', 'Model', 'Distributor', 'Specifications', 'Created Date'])
        for brand in brands:
            for model in brand.models:
                ws4.append([
                    brand.name,
                    model.name,
                    model.distributor.name,
                    model.specs or 'N/A',
                    model.created_at.strftime('%Y-%m-%d')
                ])
        # 5. Profit Analysis Sheet
        ws5 = wb.create_sheet('Profit Analysis')
        ws5.append(['Sale Date', 'Model', 'Quantity', 'Selling Price', 'Purchase Price', 'Total Revenue', 'Total Cost', 'Profit/Loss', 'Profit Margin %'])
        for t in transactions:
            if t.type == 'sale':
                purchase_price = 0
                purchase_transaction = InventoryTransaction.query.filter_by(model_id=t.model_id, type='purchase').first()
                if purchase_transaction:
                    purchase_price = purchase_transaction.price
                profit = (t.price - purchase_price) * t.quantity
                ws5.append([
                    t.date.strftime('%Y-%m-%d'),
                    t.model.name,
                    t.quantity,
                    f"PKR {t.price:.2f}",
                    f"PKR {purchase_price:.2f}",
                    f"PKR {t.price * t.quantity:.2f}",
                    f"PKR {purchase_price * t.quantity:.2f}",
                    f"PKR {profit:.2f}",
                    f"{((t.price - purchase_price) / purchase_price * 100):.1f}%" if purchase_price > 0 else 'N/A'
                ])
        # 6. Recent Activity Sheet
        ws6 = wb.create_sheet('Recent Activity')
        ws6.append(['Date', 'Activity', 'Amount', 'Type'])
        for t in recent_transactions:
            ws6.append([
                t.date.strftime('%Y-%m-%d %I:%M %p'),
                f"{t.type.title()} - {t.model.name}",
                f"PKR {t.price * t.quantity:.2f}",
                t.type.title()
            ])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/reports')
@login_required
def reports():
    """Generate PDF reports"""
    try:
        # Get all data for the report
        transactions = InventoryTransaction.query.order_by(InventoryTransaction.date.desc()).all()
        brands = Brand.query.all()
        imeis = IMEI.query.all()
        
        # Calculate statistics
        purchases = InventoryTransaction.query.filter_by(type='purchase').all()
        sales = InventoryTransaction.query.filter_by(type='sale').all()
        
        total_revenue = sum(s.price * s.quantity for s in sales)
        total_cost = sum(p.price * p.quantity for p in purchases)
        gross_profit = total_revenue - total_cost
        
        total_purchases = sum(p.quantity for p in purchases)
        total_sales = sum(s.quantity for s in sales)
        available_devices = IMEI.query.filter_by(status='available').count()
        
        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Inventory Management Report', ln=True, align='C')
        pdf.ln(10)
        
        # Summary Statistics
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Summary Statistics', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'Total Revenue: PKR {total_revenue:,.2f}', ln=True)
        pdf.cell(0, 8, f'Total Cost: PKR {total_cost:,.2f}', ln=True)
        pdf.cell(0, 8, f'Gross Profit: PKR {gross_profit:,.2f}', ln=True)
        pdf.cell(0, 8, f'Total Devices Purchased: {total_purchases}', ln=True)
        pdf.cell(0, 8, f'Total Devices Sold: {total_sales}', ln=True)
        pdf.cell(0, 8, f'Available Devices: {available_devices}', ln=True)
        pdf.ln(10)
        
        # Recent Transactions
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Recent Transactions', ln=True)
        pdf.ln(5)
        
        # Table header
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 8, 'Date', 1)
        pdf.cell(20, 8, 'Type', 1)
        pdf.cell(40, 8, 'Model', 1)
        pdf.cell(20, 8, 'Qty', 1)
        pdf.cell(30, 8, 'Price', 1)
        pdf.cell(30, 8, 'Total', 1)
        pdf.ln()
        
        # Table data
        pdf.set_font('Arial', '', 9)
        for t in transactions[:20]:  # Show last 20 transactions
            pdf.cell(30, 8, t.date.strftime('%Y-%m-%d'), 1)
            pdf.cell(20, 8, t.type.title(), 1)
            pdf.cell(40, 8, t.model.name[:18], 1)  # Truncate long names
            pdf.cell(20, 8, str(t.quantity), 1)
            pdf.cell(30, 8, f'PKR {t.price:.2f}', 1)
            pdf.cell(30, 8, f'PKR {t.price * t.quantity:.2f}', 1)
            pdf.ln()
        
        # Save PDF to memory
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        
        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Shop Keeper Management Routes
@app.route('/shop_keepers')
@login_required
def shop_keepers():
    """Manage shop keepers"""
    shop_keepers = ShopKeeper.query.order_by(ShopKeeper.created_at.desc()).all()
    return render_template('shop_keepers.html', shop_keepers=shop_keepers)

@app.route('/add_shop_keeper', methods=['POST'])
@login_required
def add_shop_keeper():
    """Add a new shop keeper"""
    try:
        name = request.form['name']
        shop_name = request.form['shop_name']
        contact_info = request.form.get('contact_info', '')
        address = request.form.get('address', '')
        
        shop_keeper = ShopKeeper(
            name=name,
            shop_name=shop_name,
            contact_info=contact_info,
            address=address
        )
        
        db.session.add(shop_keeper)
        db.session.commit()
        
        flash('Shop keeper added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding shop keeper: {str(e)}', 'error')
    
    return redirect(url_for('shop_keepers'))

@app.route('/edit_shop_keeper/<int:shop_keeper_id>', methods=['POST'])
@login_required
def edit_shop_keeper(shop_keeper_id):
    """Edit shop keeper details"""
    try:
        shop_keeper = ShopKeeper.query.get_or_404(shop_keeper_id)
        
        shop_keeper.name = request.form['name']
        shop_keeper.shop_name = request.form['shop_name']
        shop_keeper.contact_info = request.form.get('contact_info', '')
        shop_keeper.address = request.form.get('address', '')
        
        db.session.commit()
        flash('Shop keeper updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating shop keeper: {str(e)}', 'error')
    
    return redirect(url_for('shop_keepers'))

@app.route('/delete_shop_keeper/<int:shop_keeper_id>', methods=['POST'])
@login_required
def delete_shop_keeper(shop_keeper_id):
    """Delete a shop keeper"""
    try:
        shop_keeper = ShopKeeper.query.get_or_404(shop_keeper_id)
        
        # Check if shop keeper has any transactions
        if shop_keeper.transactions:
            flash('Cannot delete shop keeper with existing transactions', 'error')
            return redirect(url_for('shop_keepers'))
        
        db.session.delete(shop_keeper)
        db.session.commit()
        flash('Shop keeper deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting shop keeper: {str(e)}', 'error')
    
    return redirect(url_for('shop_keepers'))

# Return Management Routes
@app.route('/returns')
@login_required
def returns():
    """View and manage returns"""
    return_transactions = InventoryTransaction.query.filter_by(type='return').order_by(InventoryTransaction.date.desc()).all()
    sold_imeis = IMEI.query.filter_by(status='sold').all()
    return render_template('returns.html', return_transactions=return_transactions, sold_imeis=sold_imeis)

@app.route('/process_return', methods=['POST'])
@login_required
def process_return():
    """Process a return transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['imei_numbers', 'return_reason']):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        imei_numbers = data['imei_numbers']
        return_reason = data['return_reason']
        
        # Process each IMEI return
        for imei_number in imei_numbers:
            imei_number = imei_number.strip()
            if imei_number:
                # Find the sold IMEI
                imei = IMEI.query.filter_by(imei_number=imei_number, status='sold').first()
                if not imei:
                    return jsonify({'success': False, 'error': f'IMEI {imei_number} not found or not sold'})
                
                # Create return transaction
                return_transaction = InventoryTransaction(
                    model_id=imei.model_id,
                    distributor_id=imei.model.distributor_id,
                    quantity=1,
                    price=imei.price or 0,
                    type='return',
                    buyer_name=imei.buyer_name,
                    return_reason=return_reason,
                    is_paid=True  # Returns are typically processed immediately
                )
                
                db.session.add(return_transaction)
                db.session.flush()  # Get the transaction ID
                
                # Update IMEI status
                imei.status = 'returned'
                imei.returned_on = datetime.utcnow()
                imei.return_transaction_id = return_transaction.id
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sold_imeis')
@login_required
def api_sold_imeis():
    """API endpoint to get sold IMEIs for return processing"""
    sold_imeis = IMEI.query.filter_by(status='sold').join(Model).join(Brand).all()
    
    imei_data = []
    for imei in sold_imeis:
        imei_data.append({
            'id': imei.id,
            'imei_number': imei.imei_number,
            'model_name': imei.model.name,
            'brand_name': imei.model.brand.name,
            'buyer_name': imei.buyer_name,
            'sold_on': imei.sold_on.strftime('%Y-%m-%d %H:%M') if imei.sold_on else 'N/A',
            'price': imei.price
        })
    
    return jsonify(imei_data)

# Shop Sale Routes
@app.route('/shop_sales')
@login_required
def shop_sales():
    shop_sales = InventoryTransaction.query.filter_by(type='shop_sale').order_by(InventoryTransaction.date.desc()).all()
    shop_keepers = ShopKeeper.query.all()
    models = Model.query.all()
    brands = Brand.query.all()
    return render_template('shop_sales.html', shop_sales=shop_sales, shop_keepers=shop_keepers, models=models, brands=brands)

@app.route('/add_shop_sale', methods=['POST'])
@login_required
def add_shop_sale():
    """Add a shop sale transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['model_id', 'shop_keeper_id', 'quantity', 'price', 'imeis']):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Create shop sale transaction
        transaction = InventoryTransaction(
            model_id=data['model_id'],
            distributor_id=Model.query.get(data['model_id']).distributor_id,
            shop_keeper_id=data['shop_keeper_id'],
            quantity=data['quantity'],
            price=data['price'],
            type='shop_sale',
            buyer_name=ShopKeeper.query.get(data['shop_keeper_id']).name,
            is_paid=data.get('is_paid', False)
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Process IMEIs
        for imei_number in data['imeis']:
            imei_number = imei_number.strip()
            if imei_number:
                # Check if IMEI exists and is available
                existing_imei = IMEI.query.filter_by(imei_number=imei_number, status='available').first()
                if existing_imei:
                    existing_imei.status = 'sold'
                    existing_imei.buyer_name = transaction.buyer_name
                    existing_imei.sold_on = datetime.utcnow()
                    existing_imei.transaction_id = transaction.id
                else:
                    # Create new IMEI entry for sale
                    imei = IMEI(
                        model_id=data['model_id'],
                        imei_number=imei_number,
                        status='sold',
                        buyer_name=transaction.buyer_name,
                        sold_on=datetime.utcnow(),
                        transaction_id=transaction.id
                    )
                    db.session.add(imei)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8080) 