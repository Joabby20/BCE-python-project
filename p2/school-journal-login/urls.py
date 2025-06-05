from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from business import handle_login, handle_register, handle_profile_update
from database import (
    get_db,
    get_user_by_id,
    create_user,
    create_journal_entry,
    get_journal_entries,
    update_journal_entry,
    delete_journal_entry,
    close_db,
    get_courses_by_user,
    add_course,
    delete_course
)
import logging
import sqlite3


# Setup logger
logger = logging.getLogger(__name__)

# Create a Blueprint for URLs
main = Blueprint('main', __name__)

# Define URL patterns
@main.route('/')
def home():
    return render_template('home.html')

@main.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    courses = get_courses_by_user(session['user_id'])
    return render_template('dashboard.html', 
                        user=session['user'],
                        courses=courses)

@main.route('/courses', methods=['GET', 'POST'])
def courses():
    if 'user' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        if name:
            add_course(session['user_id'], name, code)

    user_courses = get_courses_by_user(session['user_id'])
    return render_template('courses.html', courses=user_courses)

@main.route('/courses/delete/<int:course_id>', methods=['POST'])
def delete_course_route(course_id):
    if 'user' not in session:
        return redirect(url_for('main.login'))

    delete_course(session['user_id'], course_id)
    return redirect(url_for('main.courses'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            logger.debug(f"Login attempt for username: {username}")
            
            # Validate input
            if not username or not password:
                logger.debug("Login failed: missing username or password")
                flash('Please enter both username and password', 'error')
                return render_template('login.html')
            
            # Try to log in
            user = handle_login(username, password)
            logger.debug(f"handle_login returned: {user}")
            
            if user:
                # Set session variables
                session.permanent = True
                session['user'] = username
                session['user_id'] = user['id']
                
                logger.debug(f"Login successful for user: {username}")
                logger.debug(f"Session contents after login: {dict(session)}")
                
                flash('Welcome back!', 'success')
                logger.debug("Redirecting to dashboard page")
                return redirect(url_for('main.dashboard'))
            else:
                logger.debug(f"Login failed for username: {username}")
                flash('Invalid username or password', 'error')
                return render_template('login.html')
        
        # Check if user is already logged in
        if 'user' in session:
            logger.debug(f"User already logged in: {session['user']}")
            flash('You are already logged in', 'info')
            return redirect(url_for('main.journal'))
        
        logger.debug("Rendering login page")
        return render_template('login.html')
    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        flash('An unexpected error occurred. Please try again later.', 'error')
        return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            logger.debug(f"Registration attempt for username: {username}")
            logger.debug(f"Form data: first_name={first_name}, last_name={last_name}, email={email}, username={username}")
            
            # Validate input
            if not all([first_name, last_name, username, email, password, confirm_password]):
                logger.debug("Registration failed: missing required fields")
                flash('Please fill in all fields', 'error')
                return render_template('register.html')
            
            if not username.isalnum() and '_' not in username:
                logger.debug(f"Registration failed: invalid username format: {username}")
                flash('Username can only contain letters, numbers, and underscores', 'error')
                return render_template('register.html')
            
            if len(password) < 8:
                logger.debug(f"Registration failed: password too short")
                flash('Password must be at least 8 characters long', 'error')
                return render_template('register.html')
            
            # Try to register user
            success = handle_register(first_name, last_name, username, email, password, confirm_password)
            logger.debug(f"handle_register returned: {success}")
            
            if success:
                logger.debug(f"Registration successful for user: {username}")
                flash('Registration successful! You can now start adding journal entries.', 'success')
                return redirect(url_for('main.login'))
            else:
                logger.debug(f"Registration failed for user: {username}")
                flash('Registration failed. Please try again.', 'error')
                return render_template('register.html')
        
        # Check if user is already logged in
        if 'user' in session:
            logger.debug(f"User already logged in: {session['user']}")
            flash('You are already logged in', 'info')
            return redirect(url_for('main.journal'))
        
        logger.debug("Rendering register page")
        return render_template('register.html')
    except Exception as e:
        logger.error(f'Registration error: {str(e)}', exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return render_template('register.html')

@main.route('/profile')
def profile():
    return render_template('profile.html')

@main.route('/journal')
def journal():
    try:
        if 'user' not in session:
            logger.debug("User not logged in")
            flash('Please log in first', 'error')
            return redirect(url_for('main.login'))
        
        # Get journal entries
        with get_db() as conn:
            c = conn.cursor()
            entries = c.execute('''
                SELECT * FROM journal_entries 
                WHERE user_id = ?
                ORDER BY date DESC
            ''', (session['user_id'],)).fetchall()
            
            if entries:
                logger.debug(f"Fetched {len(entries)} journal entries for user {session['user_id']}")
            else:
                logger.debug(f"No journal entries found for user {session['user_id']}")

        # Get courses
        courses = get_courses_by_user(session['user_id'])
        
        return render_template('journal.html', entries=entries, courses=courses)
        
    except sqlite3.Error as e:
        logger.error(f"Database error while fetching journal entries: {str(e)}", exc_info=True)
        flash('Database error occurred', 'error')
        return redirect(url_for('main.login'))
    except Exception as e:
        logger.error(f"Journal page error: {str(e)}", exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return render_template('error.html', error=str(e)), 500

@main.route('/journal/delete/<int:idx>', methods=['POST'])
def delete_entry(idx):
    try:
        if 'user' not in session:
            logger.debug("User not logged in")
            flash('Please log in first', 'error')
            return redirect(url_for('main.login'))
        
        try:
            if delete_journal_entry(idx, session['user_id']):
                logger.debug(f"Successfully deleted journal entry {idx}")
                flash('Journal entry deleted successfully', 'success')
            else:
                logger.error(f"Failed to delete journal entry {idx}")
                flash('Failed to delete journal entry', 'error')
        except sqlite3.Error as e:
            logger.error(f"Database error while deleting journal entry: {str(e)}")
            flash('Database error occurred', 'error')
        
    except Exception as e:
        logger.error(f"Delete entry error: {str(e)}")
        flash('An unexpected error occurred', 'error')
    
    return redirect(url_for('main.journal'))

@main.route('/edit/<int:idx>', methods=['GET', 'POST'])
def edit_entry(idx):
    try:
        if 'user' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('main.login'))
        
        try:
            entries = get_journal_entries(session['user_id'])
            courses = get_courses(session['user_id'])
            if idx >= len(entries):
                flash('Entry not found', 'error')
                return redirect(url_for('main.journal'))
            
            entry = entries[idx]
            
            if request.method == 'POST':
                course_id = request.form.get('course_id')
                date = request.form.get('date')
                subject = request.form.get('subject')
                learnt = request.form.get('learnt')
                challenges = request.form.get('challenges')
                schedule = request.form.get('schedule')
                
                if not all([course_id, date, subject, learnt, challenges, schedule]):
                    flash('Please fill in all fields', 'error')
                    return render_template('journal.html', 
                                        user=session['user'],
                                        entries=entries,
                                        courses=courses,
                                        editing=True,
                                        current_idx=idx)
                
                if update_journal_entry(entry[0], session['user_id'], course_id, date, subject, learnt, challenges, schedule):
                    flash('Entry updated successfully', 'success')
                else:
                    flash('Failed to update entry', 'error')
                
                return redirect(url_for('main.journal'))
            return redirect(url_for('main.journal'))
        finally:
            close_db(conn)
            
    except Exception as e:
        logger.error(f"Edit entry error: {str(e)}")
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('main.journal'))

@main.route('/logout')
def logout():
    try:
        # Clear all session data
        session.clear()
        
        logger.debug("User logged out successfully")
        flash('You have been logged out', 'info')
        return redirect(url_for('main.home'))
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        flash('An error occurred while logging out', 'error')
        return redirect(url_for('main.home'))
