import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from pathlib import Path
from urls import main
from database import init_db, get_db, close_db
from business import handle_login, handle_profile_update

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
DB_FILE = Path('school_journal.db')
SCHEMA_FILE = 'schema.sql'

# Ensure required directories exist
try:
    if not os.path.exists('templates'):
        logger.error("Templates directory not found")
        raise Exception("Templates directory not found")
    if not os.path.exists('static'):
        logger.error("Static directory not found")
        raise Exception("Static directory not found")
    if not os.path.exists(SCHEMA_FILE):
        logger.error(f"Schema file {SCHEMA_FILE} not found")
        raise Exception("Schema file not found")
except Exception as e:
    logger.error(f"Initialization error: {str(e)}")
    raise

app = Flask(__name__, static_folder='static', static_url_path='/static')
# Use environment variable for secret key in production
# For production, set this in your environment variables
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-very-secret-key-change-in-production')

# Ensure secret key is set
if not app.secret_key:
    raise ValueError("No secret key set for Flask application")
DB_FILE = 'school_journal.db'

# Configure session timeout
app.permanent_session_lifetime = timedelta(minutes=30)

# Register blueprints
from urls import main
app.register_blueprint(main)

# Set root route
@app.route('/')
def index():
    return redirect(url_for('main.home'))

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize application resources
def initialize_app():
    """Initialize application resources."""
    logger.info("Initializing application...")
    
    try:
        # Initialize database
        if not os.path.exists(DB_FILE):
            logger.info(f"Database file {DB_FILE} not found, initializing...")
            init_db()
            logger.info("Database initialized successfully")
        else:
            logger.info(f"Using existing database file: {DB_FILE}")
            
        logger.info("Using main blueprint")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise Exception("Failed to initialize application")

# Database connection
@app.before_request
def before_request():
    """Get database connection before each request."""
    try:
        g.db = get_db()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        flash('Database connection error. Please try again later.', 'error')
        return redirect(url_for('main.error'))

@app.teardown_appcontext
def teardown_appcontext(exception):
    """Close database connection after each request."""
    try:
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 error: {str(e)}")
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"500 error: {str(e)}")
    return render_template('error.html', error='Internal server error'), 500

# Database functions
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Remove this since we're using database.py's implementation
def init_db():
    conn = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        conn.executescript(f.read())
    close_db(conn)

# Initialize database if it doesn't exist
if not os.path.exists(DB_FILE):
    init_db()

# Blueprint already registered at the top of the file

# Business logic functions
@limiter.limit("5 per minute")
def handle_login(username, password):
    if not username or not password:
        flash('Please fill in both username and password', 'error')
        return False
    
    user = get_user_by_username(username)
    if user and check_password_hash(user[4], password):
        # Refresh session timeout
        session.permanent = True
        session['user'] = username
        session['user_id'] = user[0]
        return True
    
    flash('Invalid username or password', 'error')
    return False

def handle_register(first_name, last_name, username, email, password, confirm_password):
    try:
        # Validate inputs
        if not all([first_name, last_name, username, email, password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return False
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return False
        
        if len(first_name) < 2 or len(last_name) < 2:
            flash('First name and last name must be at least 2 characters long', 'error')
            return False
        
        if len(username) < 4 or len(username) > 20:
            flash('Username must be between 4 and 20 characters', 'error')
            return False
        
        if not username.isalnum() and '_' not in username:
            flash('Username can only contain letters, numbers, and underscores', 'error')
            return False
        
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address', 'error')
            return False
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return False
        
        if not any(c.isupper() for c in password):
            flash('Password must contain at least one uppercase letter', 'error')
            return False
        
        if not any(c.islower() for c in password):
            flash('Password must contain at least one lowercase letter', 'error')
            return False
        
        if not any(c.isdigit() for c in password):
            flash('Password must contain at least one number', 'error')
            return False
        
        if not any(c in '!@#$%^&*' for c in password):
            flash('Password must contain at least one special character (!@#$%^&*)', 'error')
            return False
        
        # Create user and redirect
        if create_user(first_name, last_name, username, email, password):
            # Get user ID
            conn = get_db()
            c = conn.cursor()
            user = c.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            close_db(conn)
            
            if user:
                # Set session
                session['user'] = username
                session['user_id'] = user[0]
                
                # Flash success message
                flash('Registration successful! You can now start adding journal entries.', 'success')
                return True
            else:
                flash('Failed to create user session', 'error')
                return False
        else:
            flash('Username or email already exists', 'error')
            return False
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return False

def handle_profile_update(new_password, confirm_password):
    if 'user' not in session:
        flash('Please log in first', 'error')
        return False
    
    if not new_password or not confirm_password:
        flash('Please enter both new password and confirmation', 'error')
        return False
        
    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return False
        
    try:
        # Update password in database
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE users SET password = ? WHERE username = ?', 
                 (generate_password_hash(new_password), session['user']))
        conn.commit()
        close_db(conn)
        
        flash('Password changed successfully', 'success')
        return True
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return False

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('main.login'))

    try:
        if request.method == 'POST':
            date = request.form.get('date')
            subject = request.form.get('subject')
            learnt = request.form.get('learnt')
            challenges = request.form.get('challenges')
            schedule = request.form.get('schedule')
            
            if not all([date, subject, learnt, challenges, schedule]):
                flash('Please fill in all fields', 'error')
                return redirect(url_for('main.journal'))
            
            if create_journal_entry(session['user_id'], date, subject, learnt, challenges, schedule):
                flash('Journal entry created successfully', 'success')
                return redirect(url_for('main.journal'))
            else:
                flash('Failed to create journal entry', 'error')
                return redirect(url_for('main.journal'))
        
        entries = get_journal_entries(session['user_id'])
        return render_template('journal.html', entries=entries, user_id=session['user_id'])
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.journal'))
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        date = request.form['date']
        subject = request.form['subject']
        learnt = request.form['learnt']
        challenges = request.form['challenges']
        schedule = request.form['schedule']
        
        create_journal_entry(session['user_id'], date, subject, learnt, challenges, schedule)
    
    entries = get_journal_entries(session['user_id'])
    
    search_date = request.args.get('search_date', '').strip()
    search_subject = request.args.get('search_subject', '').strip().lower()
    if search_date:
        entries = [e for e in entries if e[2] == search_date]
    if search_subject:
        entries = [e for e in entries if search_subject in e[3].lower()]
    entries = reversed(entries)
    
    return render_template('journal.html', entries=entries)

@app.route('/delete_entry/<int:idx>')
def delete_entry(idx):
    if 'user' not in session:
        return redirect(url_for('login'))
    entries = get_journal_entries(session['user_id'])
    if 0 <= idx < len(entries):
        delete_journal_entry(entries[idx][0], session['user_id'])
    return redirect(url_for('journal'))

@app.route('/edit_entry/<int:idx>', methods=['GET', 'POST'])
def edit_entry(idx):
    if 'user' not in session:
        return redirect(url_for('login'))
    entries = get_journal_entries(session['user_id'])
    if not (0 <= idx < len(entries)):
        return redirect(url_for('journal'))
    entry = entries[idx]
    if request.method == 'POST':
        date = request.form['date']
        subject = request.form['subject']
        learnt = request.form['learnt']
        challenges = request.form['challenges']
        schedule = request.form['schedule']
        update_journal_entry(entry[0], session['user_id'], date, subject, learnt, challenges, schedule)
        return redirect(url_for('journal'))
    return render_template('edit_entry.html', entry=entry)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.home'))

def get_user_by_username(username):
    """Get user by username."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    close_db(conn)
    return user

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    close_db(conn)
    return user

def create_user(first_name, last_name, username, email, password):
    """Create a new user."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (first_name, last_name, username, email, password)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, username, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        close_db(conn)

def create_journal_entry(user_id, date, subject, learnt, challenges, schedule):
    """Create a new journal entry."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO journal_entries (user_id, date, subject, learnt, challenges, schedule)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, date, subject, learnt, challenges, schedule))
    conn.commit()
    close_db(conn)

def get_journal_entries(user_id):
    """Get all journal entries for a user."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM journal_entries WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    entries = c.fetchall()
    close_db(conn)
    return entries

def update_journal_entry(entry_id, user_id, date, subject, learnt, challenges, schedule):
    """Update a journal entry."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        UPDATE journal_entries 
        SET date = ?, subject = ?, learnt = ?, challenges = ?, schedule = ?
        WHERE id = ? AND user_id = ?
    ''', (date, subject, learnt, challenges, schedule, entry_id, user_id))
    conn.commit()
    close_db(conn)

def delete_journal_entry(entry_id, user_id):
    """Delete a journal entry."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        DELETE FROM journal_entries WHERE id = ? AND user_id = ?
    ''', (entry_id, user_id))
    conn.commit()
    close_db(conn)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
# To run the application, save this code in a file named app.py and run it using:
# python app.py

