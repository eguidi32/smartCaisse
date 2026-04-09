# SmartCaisse - PythonAnywhere Deployment Guide

## Pre-Deployment Checklist

- [x] All code committed to GitHub
- [x] Local tests passing
- [x] requirements.txt up to date
- [x] Database models defined
- [x] All features implemented and tested

## Step-by-Step Deployment Instructions

### Step 1: Set Up PythonAnywhere Account
1. Log in to your PythonAnywhere account (https://www.pythonanywhere.com/)
2. Go to "Web" tab
3. Click "Add a new web app"
4. Choose "Flask"
5. Choose Python 3.10 (or latest available)

### Step 2: Clone the Repository
1. Open a Bash console in PythonAnywhere
2. Navigate to home directory: `cd ~`
3. Clone your repository:
   ```bash
   git clone https://github.com/eguidi32/smartCaisse.git
   cd smartCaisse
   ```

### Step 3: Set Up Virtual Environment
1. Create virtualenv:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 smartcaisse
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 4: Configure PythonAnywhere WSGI File
1. Go to Web tab → Your web app
2. Click on the WSGI configuration file link
3. Replace the Flask section with:
   ```python
   import sys
   
   # Add your project to path
   project_home = '/home/yourusername/smartCaisse'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)
   
   # Set environment variables
   import os
   os.environ['FLASK_ENV'] = 'production'
   
   from app import create_app
   
   app = create_app()
   ```

### Step 5: Configure Environment Variables
1. Go to Web tab → Your web app
2. Scroll down to "Web app" section
3. Add environment variables in your project directory
4. Create `.env` file with:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-very-secret-key-change-this
   DATABASE_URL=sqlite:///smartcaisse.db
   ```

### Step 6: Initialize Database
1. Open a Bash console
2. Navigate to project:
   ```bash
   cd /home/yourusername/smartCaisse
   workon smartcaisse
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
   ```

### Step 7: Reload Web App
1. Go to Web tab
2. Click "Reload" button next to your web app

### Step 8: Add Static Files (if needed)
1. Go to Web tab → Your web app
2. Under "Static files", add if you have custom static files

---

## Testing After Deployment

### Test Authentication
- Visit: `https://yourusername.pythonanywhere.com/auth/login`
- Should see login page

### Create an Admin User (via Bash)
```bash
cd /home/yourusername/smartCaisse
workon smartcaisse
python << 'EOF'
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: admin / admin123")
    else:
        print("Admin user already exists")
EOF
```

### Test Core Features
1. **Login**: Use admin credentials
2. **Dashboard**: `/admin/` - Should show admin dashboard
3. **Audit Logs**: `/admin/audit-logs` - View audit logs
4. **Analytics**: `/admin/analytics` - View charts
5. **Users**: `/admin/users` - Manage users
6. **Transactions**: `/transactions/` - Manage transactions
7. **Inventory**: `/inventory/` - Manage inventory
8. **Invoices**: `/invoices/` - Manage invoices

### Test Export Features
1. Go to `/admin/analytics`
2. Click "Exporter CSV" button
3. Click "Exporter PDF" button
4. Both should download successfully

### Test User Activity Report
1. Go to `/admin/users`
2. Click on any user
3. Click "Activité" button
4. Should see user's activity timeline

### Monitoring
- Check `/admin/analytics` regularly for activity trends
- Monitor `/admin/audit-logs` for any errors
- Watch transaction and inventory operations

---

## Troubleshooting

### 502 Bad Gateway Error
- Check error log: Web tab → "Error log"
- Common issues:
  - Import errors (check dependencies in WSGI file)
  - Database file permissions
  - Missing environment variables

### Database Issues
- Reset database:
  ```bash
  rm smartcaisse.db
  python -c "from app import create_app, db; app = create_app(); db.create_all()"
  ```

### Static Files Not Loading
- Add to Web tab under "Static files":
  - URL: `/static/`
  - Directory: `/home/yourusername/smartCaisse/app/static/`

### Email Configuration Issues
- For development, email output goes to logs
- For production, configure SMTP in environment variables

---

## Security Considerations

1. **Change SECRET_KEY**: Generate a secure random key
2. **Use HTTPS**: PythonAnywhere provides free HTTPS
3. **Set FLASK_ENV=production**: Disable debug mode
4. **Create strong admin password**: Don't use default
5. **Configure MAIL_USERNAME/PASSWORD** if email needed
6. **Use database backup**: Export audit logs regularly

---

## Performance Tips

1. **Enable caching**: For frequently accessed pages
2. **Monitor database**: Use `/admin/analytics` to identify bottlenecks
3. **Archive old audit logs**: Periodically export and clean old logs
4. **Limit results**: Pagination is already implemented

---

## Next Steps After Deployment

1. Create test accounts
2. Test all CRUD operations
3. Verify audit logging captures actions
4. Test PDF and CSV exports
5. Monitor analytics dashboard
6. Backup database regularly

