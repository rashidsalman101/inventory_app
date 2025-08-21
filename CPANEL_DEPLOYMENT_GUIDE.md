# 🚀 cPanel Deployment Guide for Mobile Inventory System

This guide will help you deploy your Flask application to cPanel hosting with MySQL database.

## 📋 **Prerequisites**

- cPanel hosting with Python support enabled
- MySQL database access (via phpMyAdmin)
- FTP/SFTP access to your hosting account
- Python 3.8+ support on your hosting

## 🔧 **Step 1: Database Setup (phpMyAdmin)**

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

## 🔧 **Step 2: Local Environment Setup**

### **2.1 Install MySQL Locally (Optional but Recommended)**

#### **Option A: XAMPP (Windows)**
1. Download XAMPP from [https://www.apachefriends.org/](https://www.apachefriends.org/)
2. Install XAMPP
3. Start Apache and MySQL services
4. Access phpMyAdmin at `http://localhost/phpmyadmin`

#### **Option B: MAMP (macOS)**
1. Download MAMP from [https://www.mamp.info/](https://www.mamp.info/)
2. Install MAMP
3. Start MAMP services
4. Access phpMyAdmin at `http://localhost:8888/phpMyAdmin`

#### **Option C: LAMP Stack (Linux)**
```bash
sudo apt update
sudo apt install apache2 mysql-server php php-mysql
sudo mysql_secure_installation
```

### **2.2 Create Local .env File**
Create a `.env` file in your project root:

```bash
# Local Development (MySQL)
DATABASE_URL=mysql+pymysql://root:@localhost/mobile_inventory
SECRET_KEY=your-local-secret-key-here
FLASK_DEBUG=True

# Production (cPanel)
# DATABASE_URL=mysql+pymysql://username:password@localhost/dbname
# SECRET_KEY=your-production-secret-key-here
# FLASK_DEBUG=False
```

### **2.3 Install Dependencies**
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install new dependencies
pip install -r requirements.txt
```

## 🔧 **Step 3: Test Local MySQL Setup**

### **3.1 Test Database Connection**
```bash
python create_tables_mysql.py
```

### **3.2 Migrate Data (if you have existing SQLite data)**
```bash
# Export from SQLite
python migrate_to_mysql.py export

# Import to MySQL
python migrate_to_mysql.py import
```

### **3.3 Test Application Locally**
```bash
python app.py
```

## 🔧 **Step 4: Prepare Files for cPanel**

### **4.1 Files to Upload**
Upload these files to your cPanel hosting:

```
📁 Your Project Folder/
├── 📄 app.py                    # Main Flask application
├── 📄 passenger_wsgi.py         # WSGI entry point
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env                      # Environment variables (production)
├── 📁 templates/                # HTML templates
├── 📁 static/                   # CSS, JS, images
└── 📄 CPANEL_DEPLOYMENT_GUIDE.md
```

### **4.2 Create Production .env File**
Create a `.env` file for production with your cPanel database credentials:

```bash
# Production Environment Variables
DATABASE_URL=mysql+pymysql://inventory_user:your_password@localhost/mobile_inventory
SECRET_KEY=your-super-secure-production-secret-key
FLASK_DEBUG=False
FLASK_ENV=production
```

## 🔧 **Step 5: cPanel Python App Setup**

### **5.1 Enable Python App**
1. In cPanel, go to **Setup Python App**
2. Click **Create Application**
3. Configure:
   - **Python version**: 3.8 or higher
   - **Application root**: Your domain or subdomain
   - **Application startup file**: `passenger_wsgi.py`
   - **Application entry point**: `application`
4. Click **Create**

### **5.2 Install Dependencies**
1. In your Python app, click **Install App**
2. Wait for installation to complete
3. Check the logs for any errors

## 🔧 **Step 6: Database Setup on cPanel**

### **6.1 Create Tables**
1. SSH into your hosting (if available) or use cPanel Terminal
2. Navigate to your app directory
3. Run:
```bash
python create_tables_mysql.py
```

### **6.2 Verify Database**
1. Go to phpMyAdmin
2. Check your `mobile_inventory` database
3. Verify all tables are created

## 🔧 **Step 7: Test Your Application**

### **7.1 Check Application Status**
1. Go to your domain
2. Verify the application loads
3. Check for any error messages

### **7.2 Test Database Operations**
1. Try to register a new user
2. Test adding brands/models
3. Verify data is saved to MySQL

## 🚨 **Troubleshooting Common Issues**

### **Issue 1: Database Connection Error**
**Error**: `Can't connect to MySQL server`

**Solution**:
- Verify database credentials in `.env`
- Check if MySQL service is running
- Ensure database user has proper permissions

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

### **Issue 4: WSGI Configuration Error**
**Error**: `WSGI application not found`

**Solution**:
- Verify `passenger_wsgi.py` exists
- Check `application` variable is defined
- Ensure file paths are correct

## 📱 **Mobile Testing**

### **8.1 Test on Mobile Devices**
1. Access your app from mobile devices
2. Test responsive design
3. Verify touch interactions work properly

### **8.2 Performance Optimization**
1. Enable gzip compression in cPanel
2. Optimize images and static files
3. Consider CDN for static assets

## 🔒 **Security Considerations**

### **9.1 Environment Variables**
- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate secrets regularly

### **9.2 Database Security**
- Use dedicated database user (not root)
- Limit database user permissions
- Enable SSL connections if available

### **9.3 Application Security**
- Keep Flask and dependencies updated
- Use HTTPS (SSL certificate)
- Implement proper input validation

## 📊 **Monitoring and Maintenance**

### **10.1 Log Monitoring**
- Check cPanel error logs regularly
- Monitor application performance
- Set up error notifications

### **10.2 Database Maintenance**
- Regular database backups
- Monitor database size and performance
- Optimize queries as needed

### **10.3 Updates**
- Keep Python version updated
- Update dependencies regularly
- Monitor security advisories

## 🎯 **Next Steps After Deployment**

1. **Set up SSL certificate** for HTTPS
2. **Configure domain/subdomain** routing
3. **Set up automated backups**
4. **Monitor performance** and optimize
5. **Plan scaling** strategy

## 📞 **Support Resources**

- **cPanel Documentation**: [https://docs.cpanel.net/](https://docs.cpanel.net/)
- **Flask Documentation**: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- **MySQL Documentation**: [https://dev.mysql.com/doc/](https://dev.mysql.com/doc/)
- **Hosting Provider Support**: Contact your hosting provider for cPanel-specific issues

---

## 🚀 **Quick Deployment Checklist**

- [ ] Database created in phpMyAdmin
- [ ] Database user created with proper permissions
- [ ] Local MySQL testing completed
- [ ] Files uploaded to cPanel
- [ ] Python app configured in cPanel
- [ ] Dependencies installed
- [ ] Database tables created
- [ ] Application tested and working
- [ ] SSL certificate configured (optional)
- [ ] Domain routing configured

**🎉 Congratulations! Your Mobile Inventory System is now deployed on cPanel!** 