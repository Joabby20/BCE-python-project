from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATA_FILE = 'users_data.json'

@app.route('/')
def home():
    return render_template('home page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('journal'))
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = load_data()
        if username in data and data[username]['password'] == password:
            session['user'] = username
            return redirect(url_for('journal'))  # <-- This line opens the journal page after login
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = load_data()
        if username in data:
            error = 'Username already exists.'
        else:
            data[username] = {'password': password, 'entries': []}
            save_data(data)
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    msg = ''
    if request.method == 'POST':
        new_password = request.form['new_password']
        data = load_data()
        data[session['user']]['password'] = new_password
        save_data(data)
        msg = 'Password changed successfully.'
    return render_template('profile.html', user=session['user'], msg=msg)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    user = session['user']
    today = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        entry = {
            'date': request.form['date'],
            'subject': request.form['subject'],
            'learnt': request.form['learnt'],
            'challenges': request.form['challenges'],
            'schedule': request.form['schedule']
        }
        data[user]['entries'].append(entry)
        save_data(data)
        return redirect(url_for('journal'))
    entries = list(enumerate(data[user]['entries']))
    search_date = request.args.get('search_date', '').strip()
    search_subject = request.args.get('search_subject', '').strip().lower()
    if search_date:
        entries = [e for e in entries if e[1]['date'] == search_date]
    if search_subject:
        entries = [e for e in entries if search_subject in e[1]['subject'].lower()]
    entries = reversed(entries)
    return render_template('journal.html', user=user, entries=entries, today=today, request=request)

@app.route('/delete_entry/<int:idx>')
def delete_entry(idx):
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    user = session['user']
    if 0 <= idx < len(data[user]['entries']):
        del data[user]['entries'][idx]
        save_data(data)
    return redirect(url_for('journal'))

@app.route('/edit_entry/<int:idx>', methods=['GET', 'POST'])
def edit_entry(idx):
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    user = session['user']
    if not (0 <= idx < len(data[user]['entries'])):
        return redirect(url_for('journal'))
    entry = data[user]['entries'][idx]
    if request.method == 'POST':
        entry['date'] = request.form['date']
        entry['subject'] = request.form['subject']
        entry['learnt'] = request.form['learnt']
        entry['challenges'] = request.form['challenges']
        entry['schedule'] = request.form['schedule']
        save_data(data)
        return redirect(url_for('journal'))
    return render_template('edit_entry.html', entry=entry)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
# To run the application, save this code in a file named app.py and run it using:
# python app.py

