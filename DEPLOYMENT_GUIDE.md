# Deployment Guide: Fix SQLAlchemy Python 3.13 Compatibility Issue

## Summary
The production environment (PythonAnywhere) is experiencing import errors due to SQLAlchemy version incompatibility with Python 3.13. This guide provides step-by-step instructions to resolve the issue.

## Root Cause
- **Problem**: SQLAlchemy 2.0.23 has compatibility issues with Python 3.13
- **Error**: `AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly but has additional attributes`
- **Solution**: Upgrade SQLAlchemy to 2.2.25 and Flask-SQLAlchemy to 3.3.1, then run database migration

## What's Been Done Locally
✓ Updated `requirements.txt` with newer package versions
✓ Created two migration scripts for adding missing database columns:
  - `migrate_add_account_lockout.py` - Python script for database migration
  - `migrate_add_account_lockout.sql` - SQL script (alternative method)
✓ Pushed all changes to GitHub

## Deployment Steps on PythonAnywhere

### Step 1: Pull Latest Code
1. Go to **Consoles** → **Bash console**
2. Navigate to your project directory:
   ```bash
   cd ~/smartCaisse
   git pull
   ```

### Step 2: Upgrade Dependencies
1. In the same Bash console:
   ```bash
   pip install -r requirements.txt --upgrade
   ```
2. Wait for pip to complete (this will install SQLAlchemy 2.2.25 and Flask-SQLAlchemy 3.3.1)
3. Verify the upgrade:
   ```bash
   pip show SQLAlchemy | grep Version
   ```

### Step 3: Run Database Migration
```bash
python migrate_add_account_lockout.py
```

### Step 4: Restart Web App
1. Go to **Web** tab in PythonAnywhere
2. Click the green **Reload** button
3. Wait 30-60 seconds for the web app to restart

### Step 5: Verify Fix
1. Test login at your PythonAnywhere domain
2. Application should work without import errors

## If Something Goes Wrong

### Still getting import errors after reload
- Go to **Web** tab and click **Reload** again
- Wait a full minute for Python to reload packages
- Try again

### Migration script fails
- Try the SQL script instead: `sqlite3 instance/smartcaisse.db < migrate_add_account_lockout.sql`
- Check PythonAnywhere error logs for details

## Testing Security Features

Once deployment is complete:

1. **Test account lockout**: Try 5 failed logins, should lock account for 15 minutes
2. **Test password requirements**: Passwords must be 12+ chars with uppercase, lowercase, digit, and special character
3. **Test security headers**: Check that response headers include X-Content-Type-Options, X-Frame-Options, etc.

## All Security Fixes Summary
1. ✅ Removed exposed Gmail credentials
2. ✅ Disabled debug mode in production
3. ✅ Fixed open redirect vulnerability
4. ✅ Fixed CSV injection vulnerabilities
5. ✅ Strengthened password requirements
6. ✅ Removed temporary passwords from logs
7. ✅ Reduced session timeout to 1 hour
8. ✅ Implemented account lockout
9. ✅ Added security headers
10. ✅ Fixed SQLAlchemy Python 3.13 compatibility
