from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db
import logging
import sqlite3
from flask import g

logger = logging.getLogger(__name__)

def get_user_by_username(username):
    """Get user by username."""
    conn = None
    try:
        logger.debug(f"Getting user by username: {username}")
        conn = get_db()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        return user
    except sqlite3.Error as e:
        logger.error(f"Database error during get user by username: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting user by username: {str(e)}")
        return None
    finally:
        if conn:
            close_db(conn)

def handle_login(username, password):
    """Handle user login."""
    conn = None
    try:
        logger.debug(f"Attempting login for user: {username}")
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user from database
        user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            logger.info(f"Login successful for user: {username}")
            return user
        else:
            logger.warning(f"Login failed for user: {username}")
            return None
    except sqlite3.Error as e:
        logger.error(f"Database error during login: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return None
    finally:
        if conn:
            close_db(conn)

def handle_register(first_name, last_name, username, email, password, confirm_password):
    """Handle user registration."""
    try:
        logger.debug(f"Starting registration for user: {username}")
        logger.debug(f"Form data: first_name={first_name}, last_name={last_name}, email={email}, username={username}")
        
        # Validate password confirmation
        if password != confirm_password:
            logger.error("Password and confirmation do not match")
            return False
            
        conn = get_db()
        cursor = conn.cursor()
        logger.debug("Database connection established")
        
        # Validate inputs
        if not all([first_name, last_name, username, email, password]):
            logger.error("Missing required fields for registration")
            return False
            
        logger.debug("Validating password length")
        if len(password) < 8:
            logger.error("Password too short")
            return False
            
        logger.debug("Validating username format")
        if not username.isalnum() and '_' not in username:
            logger.error("Invalid username format")
            return False
            
        logger.debug("Checking for existing username/email")
        existing_user = cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            logger.error(f"Username or email already exists: {username}")
            return False
            
        logger.debug("Creating new user record")
        cursor.execute('INSERT INTO users (first_name, last_name, username, email, password) VALUES (?, ?, ?, ?, ?)',
                     (first_name, last_name, username, email, generate_password_hash(password)))
        conn.commit()
        close_db(conn)
        logger.info(f"User registered successfully: {username}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error during registration: {str(e)}", exc_info=True)
        close_db(conn)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        close_db(conn)
        return False
    finally:
        logger.debug("Registration process complete")

def handle_profile_update(user_id, first_name, last_name, username, email, password):
    """Update user profile."""
    conn = None
    try:
        logger.debug(f"Updating profile for user ID: {user_id}")
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate inputs
        if not all([user_id, first_name, last_name, username, email]):
            logger.error("Missing required fields for profile update")
            return False
            
        # Validate password length
        if password and len(password) < 8:
            logger.error("Password too short")
            return False
            
        # Validate username format
        if not username.isalnum() and '_' not in username:
            logger.error("Invalid username format")
            return False
            
        # Check if username or email exists for other users
        if cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, user_id)).fetchone():
            logger.error(f"Username already exists for another user: {username}")
            return False
        if cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id)).fetchone():
            logger.error(f"Email already exists for another user: {email}")
            return False
            
        # Update user
        if password:
            cursor.execute('''
                UPDATE users 
                SET first_name = ?, last_name = ?, username = ?, email = ?, password = ? 
                WHERE id = ?
            ''', (first_name, last_name, username, email, generate_password_hash(password), user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET first_name = ?, last_name = ?, username = ?, email = ? 
                WHERE id = ?
            ''', (first_name, last_name, username, email, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return False
    finally:
        if conn:
            close_db(conn)

if __name__ == '__main__':
    pass
