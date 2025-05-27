"""
Extremely simple Flask application with basic login functionality.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Fixed key for testing

# Simple user database (in a real app, this would be in a database)
users = {
    'student@example.com': {
        'password': 'password123',
        'name': 'Student User',
        'role': 'student'
    },
    'teacher@example.com': {
        'password': 'password123',
        'name': 'Teacher User',
        'role': 'teacher'
    }
}

@app.route('/')
def index():
    return render_template('basic_login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Print login attempt for debugging
    print(f"Login attempt - Email: {email}, Password: {password}")
    
    # Check if user exists and password is correct
    if email in users and users[email]['password'] == password:
        # Store user info in session
        session['user'] = {
            'email': email,
            'name': users[email]['name'],
            'role': users[email]['role']
        }
        return redirect(url_for('dashboard'))
    else:
        # For debugging, print why login failed
        if email not in users:
            print(f"Login failed: Email {email} not found in users database")
        else:
            print(f"Login failed: Password incorrect for {email}")
        
        return render_template('basic_login.html', error='Invalid email or password')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    return render_template('basic_dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8087)
