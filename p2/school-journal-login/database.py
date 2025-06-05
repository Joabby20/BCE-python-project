from flask import g
import sqlite3
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)

# Global variables
DB_FILE = Path('school_journal.db')
SCHEMA_FILE = 'schema.sql'

def init_db():
    """Initialize the database with required tables."""
    try:
        logger.debug("Initializing database...")
        conn = sqlite3.connect(DB_FILE)
        with open(SCHEMA_FILE, 'r') as f:
            sql = f.read()
            # Split SQL into individual statements
            statements = sql.split(';')
            cursor = conn.cursor()
            for statement in statements:
                if statement.strip():
                    logger.debug(f"Executing SQL statement: {statement.strip()}")
                    cursor.execute(statement)
            conn.commit()
            logger.info("Database initialized successfully!")
            return True
    except FileNotFoundError as e:
        logger.error(f"Schema file not found: {str(e)}")
        raise Exception("Schema file not found")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {str(e)}")
        raise Exception("SQLite error occurred")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise Exception("Database initialization failed")
    finally:
        if conn:
            conn.close()

def get_db():
    """Get database connection."""
    try:
        logger.debug("Getting database connection")
        conn = sqlite3.connect(str(DB_FILE))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise Exception("Failed to connect to database")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception("Database error occurred")

def close_db(conn):
    """Close database connection."""
    try:
        if conn:
            logger.debug("Closing database connection")
            conn.close()
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")

def get_user_by_username(username):
    conn = get_db()
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    close_db(conn)
    return user

def create_user(first_name, last_name, username, email, password):
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Check if username or email already exists
        if c.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone():
            close_db(conn)
            return False
        
        # Create user
        c.execute('INSERT INTO users (first_name, last_name, username, email, password) VALUES (?, ?, ?, ?, ?)',
                 (first_name, last_name, username, email, generate_password_hash(password)))
        conn.commit()
        close_db(conn)
        return True
    except Exception as e:
        close_db(conn)
        return False

def create_journal_entry(user_id, date, subject, learnt, challenges, schedule):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO journal_entries (user_id, date, subject, learnt, challenges, schedule) VALUES (?, ?, ?, ?, ?, ?)',
                 (user_id, date, subject, learnt, challenges, schedule))
        conn.commit()
        close_db(conn)
        return True
    except Exception as e:
        close_db(conn)
        return False

def get_journal_entries(user_id):
    """Get journal entries for a user with course information."""
    try:
        conn = get_db()
        c = conn.cursor()
        entries = c.execute('''
            SELECT je.*, c.course_name 
            FROM journal_entries je
            LEFT JOIN courses c ON je.course_id = c.id
            WHERE je.user_id = ?
            ORDER BY je.date DESC
        ''', (user_id,)).fetchall()
        return entries
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching journal entries: {str(e)}")
        raise
    finally:
        close_db(conn)

def create_journal_entry(user_id, course_id, date, subject, learnt, challenges, schedule):
    """Create a new journal entry."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO journal_entries (user_id, course_id, date, subject, learnt, challenges, schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, course_id, date, subject, learnt, challenges, schedule))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error while creating journal entry: {str(e)}")
        raise
    finally:
        close_db(conn)

def update_journal_entry(entry_id, user_id, course_id, date, subject, learnt, challenges, schedule):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            UPDATE journal_entries 
            SET course_id = ?, date = ?, subject = ?, learnt = ?, challenges = ?, schedule = ?
            WHERE id = ? AND user_id = ?
        ''', (course_id, date, subject, learnt, challenges, schedule, entry_id, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error while updating journal entry: {str(e)}")
        raise
    finally:
        close_db(conn)

def get_courses_by_user(user_id):
    """Get all courses for a user."""
    try:
        conn = get_db()
        c = conn.cursor()
        courses = c.execute('''
            SELECT * FROM courses 
            WHERE user_id = ?
            ORDER BY name
        ''', (user_id,)).fetchall()
        return courses
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching courses: {str(e)}")
        raise
    finally:
        close_db(conn)

def add_course(user_id, name, code):
    """Add a new course for a user."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO courses (user_id, name, code)
            VALUES (?, ?, ?)
        ''', (user_id, name, code))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error while adding course: {str(e)}")
        raise
    finally:
        close_db(conn)

def delete_course(course_id, user_id):
    """Delete a course for a user."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            DELETE FROM courses 
            WHERE id = ? AND user_id = ?
        ''', (course_id, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        # First check if the course belongs to the user
        course = c.execute('''
            SELECT * FROM courses WHERE id = ? AND user_id = ?
        ''', (course_id, user_id)).fetchone()
        if not course:
            return False
        
        c.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error while deleting course: {str(e)}")
        raise
    finally:
        close_db(conn)

def update_journal_entry(entry_id, user_id, date, subject, learnt, challenges, schedule):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE journal_entries SET date = ?, subject = ?, learnt = ?, challenges = ?, schedule = ? WHERE id = ? AND user_id = ?',
                 (date, subject, learnt, challenges, schedule, entry_id, user_id))
        conn.commit()
        close_db(conn)
        return True
    except Exception as e:
        close_db(conn)
        return False

def delete_journal_entry(entry_id, user_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM journal_entries WHERE id = ? AND user_id = ?', (entry_id, user_id))
        conn.commit()
        close_db(conn)
        return True
    except Exception as e:
        close_db(conn)
        return False

if __name__ == '__main__':
    init_db()
