# 🚀 Quick cPanel Deployment Guide

## 📋 **Prerequisites**
- cPanel hosting with Python support enabled
- FTP/SFTP access to your hosting account
- Python 3.8+ support on your hosting

## 🔧 **Step 1: cPanel Database Setup**

### **1.1 Create MySQL Database**
1. Login to cPanel
2. Go to **phpMyAdmin**
3. Click **New** to create a new database
4. Enter database name: `mobile_inventory`
5. Click **Create**

### **1.2 Create Database User**
1. In phpMyAdmin, go to **User accounts** tab
2. Click **Add user account**
3. Create a new user with:
   - **Username**: `inventory_user` (or your preferred name)
   - **Host name**: `localhost`
   - **Password**: Generate a strong password
4. **Global privileges**: Select `ALL PRIVILEGES`
5. Click **Go**

### **1.3 Grant Database Permissions**
1. Select your new user
2. Click **Edit privileges**
3. Select your `mobile_inventory` database
4. Grant **ALL PRIVILEGES**
5. Click **Go**

## 🔧 **Step 2: Prepare Files for Upload**

### **2.1 Files to Upload**
Upload these files to your cPanel hosting:

```
📁 Your Project Folder/
├── 📄 app.py                    # Main Flask application
├── 📄 passenger_wsgi.py         # WSGI entry point
├── 📄 requirements.txt          # Python dependencies
├── 📄 env_production.txt        # Environment template (rename to .env)
├── 📁 templates/                # HTML templates
├── 📁 static/                   # CSS, JS, images
├── 📄 migrate_purchase_payment_fields.py  # Migration script
└── 📄 CPANEL_QUICK_DEPLOY.md   # This guide
```

### **2.2 Create Production .env File**
1. Rename `env_production.txt` to `.env`
2. Update with your actual database credentials:
```bash
DATABASE_URL=mysql+pymysql://inventory_user:your_password@localhost/mobile_inventory
SECRET_KEY=your-super-secure-production-secret-key-change-this
FLASK_DEBUG=False
FLASK_ENV=production
```

## 🔧 **Step 3: cPanel Python App Setup**

### **3.1 Enable Python App**
1. In cPanel, go to **Setup Python App**
2. Click **Create Application**
3. Configure:
   - **Python version**: 3.8 or higher
   - **Application root**: Your domain or subdomain
   - **Application startup file**: `passenger_wsgi.py`
   - **Application entry point**: `application`
4. Click **Create**

### **3.2 Install Dependencies**
1. In your Python app, click **Install App**
2. Wait for installation to complete
3. Check the logs for any errors

## 🔧 **Step 4: Database Setup on cPanel**

### **4.1 Create Tables**
1. SSH into your hosting (if available) or use cPanel Terminal
2. Navigate to your app directory
3. Run the migration script:
```bash
python migrate_purchase_payment_fields.py
```

### **4.2 Alternative: Manual Table Creation**
If SSH is not available, run this in cPanel Terminal:
```bash
cd /home/username/public_html/your_app_folder
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Tables created successfully!')
"
```

## 🔧 **Step 5: Test Your Application**

### **5.1 Check Application Status**
1. Go to your domain
2. Verify the application loads
3. Check for any error messages

### **5.2 Test Database Operations**
1. Try to register a new user
2. Test adding brands/models
3. Verify data is saved to MySQL

## 🚨 **Troubleshooting Common Issues**

### **Issue 1: Database Connection Error**
**Error**: `Can't connect to MySQL server`

**Solution**:
- Verify database credentials in `.env` file
- Check if database user has proper permissions
- Ensure database exists in phpMyAdmin

### **Issue 2: Module Not Found**
**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
- Check if dependencies are installed
- Verify Python app is properly configured
- Check cPanel Python app logs

### **Issue 3: Permission Denied**
**Error**: `Permission denied` or `Access denied`

**Solution**:
- Check file permissions (should be 644 for files, 755 for directories)
- Verify database user permissions
- Check cPanel file manager permissions

## 📱 **File Upload Methods**

### **Option A: cPanel File Manager**
1. Go to **File Manager** in cPanel
2. Navigate to your domain folder
3. Upload files using the upload button
4. Extract ZIP files if needed

### **Option B: FTP/SFTP Client**
1. Use FileZilla, WinSCP, or similar
2. Connect using your cPanel FTP credentials
3. Upload files to your domain folder

### **Option C: Git (if available)**
1. Clone your repository to cPanel
2. Update with latest changes
3. Pull from your repository

## 🎯 **Quick Deployment Checklist**

- [ ] Database created in phpMyAdmin
- [ ] Database user created with proper permissions
- [ ] Files uploaded to cPanel
- [ ] Python app configured in cPanel
- [ ] Dependencies installed
- [ ] Database tables created
- [ ] Application tested and working

## 🚀 **After Deployment**

1. **Set up SSL certificate** for HTTPS
2. **Configure domain/subdomain** routing
3. **Set up automated backups**
4. **Monitor performance** and optimize

---

## 🎉 **You're Ready to Deploy!**

**No local testing required** - deploy directly to cPanel and set up everything there!

**Estimated time**: 15-30 minutes for complete setup
**Difficulty**: Easy to Moderate
**Support**: cPanel has excellent documentation and support

**Good luck with your deployment! 🚀** 