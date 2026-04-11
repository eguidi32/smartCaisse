-- Database migration script to add account lockout columns
-- Run with: sqlite3 instance/smartcaisse.db < migrate_add_account_lockout.sql

-- Add failed_login_attempts column if it doesn't exist
-- SQLite doesn't have IF NOT EXISTS for ALTER TABLE, so we ignore the error if column exists
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;

-- Add locked_until column if it doesn't exist
ALTER TABLE users ADD COLUMN locked_until DATETIME;
