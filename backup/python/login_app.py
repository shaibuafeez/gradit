"""
Very simple Flask application with basic login functionality.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

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
    return render_template('login_page.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
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
        flash('Invalid email or password', 'error')
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    role = request.form.get('role', 'student')
    
    if email in users:
        flash('Email already registered', 'error')
        return redirect(url_for('index'))
    
    # Add user to our simple database
    users[email] = {
        'password': password,
        'name': name,
        'role': role
    }
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', user=session['user'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8086)
