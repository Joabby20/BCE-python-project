from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

# Simple user for demonstration
USER = {'username': 'student', 'password': 'journal123'}

# HTML template for the journal page
JOURNAL_HTML = """<!DOCTYPE html><html lang="en"><head> <meta charset="UTF-8"><title>My Journal</title><style>body { font-family: Arial, sans-serif; background: #f0f4f8; }
        .container { max-width: 600px; margin: 40px auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);}
        h2 { color: #1976d2; }
        textarea { width: 100%; height: 120px; border-radius: 8px; border: 1px solid #b0bec5; padding: 1rem; font-size: 1rem; }
        button { background: #1976d2; color: #fff; border: none; border-radius: 8px; padding: 0.75rem 1.5rem; font-size: 1rem; margin-top: 1rem; cursor: pointer;}
        .entry { background: #e3f2fd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;}
        .logout { float: right; color: #1976d2; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <a href="{{ url_for('logout') }}" class="logout">Logout</a>
        <h2>Welcome, {{ user }}!</h2>
        <form method="post">
            <textarea name="entry" placeholder="Write your journal entry here..." required></textarea>
            <button type="submit">Save Entry</button>
        </form>
        <h3>Your Entries:</h3>
        {% for e in entries %}
            <div class="entry">{{ e }}</div>
        {% else %}
            <p>No entries yet.</p>
        {% endfor %}
    </div>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('journal'))
    error = ''
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == USER['username'] and password == USER['password']:
            session['user'] = username
            session['entries'] = []
            return redirect(url_for('journal'))
        else:
            error = 'Invalid username or password.'
    return '''
    <form method="post">
        <h2>Login to Your Journal</h2>
        <p style="color:red;">{}</p>
        <input name="username" placeholder="Username" required><br><br>
        <input name="password" type="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
    '''.format(error)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        entry = request.form.get('entry', '').strip()
        if entry:
            session['entries'].append(entry)
    return render_template_string(JOURNAL_HTML, user=session['user'], entries=session['entries'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
# To run the application, save this code in a file named app.py and run it using:
# python app.py  
