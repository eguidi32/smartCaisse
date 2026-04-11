#!/usr/bin/env python
"""
Database migration script to add account lockout columns to users table.
Run this after upgrading dependencies: python migrate_add_account_lockout.py
"""
import sqlite3
import os
import sys

def migrate():
    """Add failed_login_attempts and locked_until columns to users table if they don't exist"""
    db_path = os.environ.get('DATABASE_PATH', 'instance/smartcaisse.db')

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

        if 'failed_login_attempts' not in columns:
            print("Adding failed_login_attempts column...")
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN failed_login_attempts INTEGER DEFAULT 0
            """)
            print("✓ Added failed_login_attempts column")
        else:
            print("✓ failed_login_attempts column already exists")

        if 'locked_until' not in columns:
            print("Adding locked_until column...")
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN locked_until DATETIME
            """)
            print("✓ Added locked_until column")
        else:
            print("✓ locked_until column already exists")

        conn.commit()
        conn.close()
        print("\n✓ Migration completed successfully!")
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
