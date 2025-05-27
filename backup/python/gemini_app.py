"""
Flask application that uses Gemini API for essay scoring.
This provides a simpler alternative to the full ML-based scoring system.
"""

import os
import json
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from gemini_service import GeminiService
from models import db, User, Course, Question, Exam, ExamSubmission, Answer
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aes_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS
CORS(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Gemini service (will use GEMINI_API_KEY environment variable)
gemini_service = None
try:
    gemini_service = GeminiService()
    print("Gemini service initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini service: {str(e)}")
    print("Gemini features will be disabled")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    # Validate input data
    if not data.get('email') or not data.get('password') or not data.get('name'):
        if request.is_json:
            return jsonify({'error': 'Missing required fields'}), 400
        else:
            return render_template('login.html', register_error='Missing required fields')
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        if request.is_json:
            return jsonify({'error': 'Email already registered'}), 400
        else:
            return render_template('login.html', register_error='Email already registered')
    
    # Create new user
    new_user = User(
        email=data['email'],
        name=data['name'],
        role=data.get('role', 'student'),
        matric_number=data.get('matric_number')
    )
    new_user.set_password(data['password'])
    
    # Save to database
    db.session.add(new_user)
    db.session.commit()
    
    # Log in the new user
    login_user(new_user)
    
    if request.is_json:
        return jsonify({'message': 'Registration successful', 'user_id': new_user.id}), 201
    else:
        return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    """Login a user"""
    if request.is_json:
        data = request.json
    else:
        data = request.form
    
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user)
        
        if request.is_json:
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role
                }
            })
        else:
            return redirect(url_for('dashboard'))
    
    if request.is_json:
        return jsonify({'error': 'Invalid email or password'}), 401
    else:
        return render_template('login.html', login_error='Invalid email or password')

@app.route('/logout')
def logout():
    """Logout a user"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Render the main page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard"""
    return render_template('dashboard.html', user=current_user)

# Essay scoring with Gemini API
@app.route('/api/score-essay', methods=['POST'])
def score_essay():
    """Score an essay using Gemini API"""
    if not gemini_service:
        return jsonify({
            'error': 'Gemini service not available. Please set GEMINI_API_KEY environment variable.'
        }), 503
    
    data = request.json
    
    # Validate input
    if not data.get('essay'):
        return jsonify({'error': 'Essay text is required'}), 400
    
    prompt = data.get('prompt', 'Write an essay on the given topic.')
    rubric = data.get('rubric', gemini_service.get_default_rubric())
    essay_set = data.get('essay_set', 1)
    
    try:
        # Score the essay
        result = gemini_service.score_essay(data['essay'], prompt, rubric, essay_set)
        
        # Generate detailed feedback if requested
        if data.get('detailed_feedback', False):
            feedback = gemini_service.generate_detailed_feedback(data['essay'], result)
            result['detailed_feedback'] = feedback
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Simple essay scoring endpoint (fallback if Gemini API is not available)
@app.route('/api/simple-score', methods=['POST'])
def simple_score():
    """Provide a simple scoring response without requiring Gemini API"""
    data = request.json
    
    # Validate input
    if not data.get('essay'):
        return jsonify({'error': 'Essay text is required'}), 400
    
    # Calculate a simple score based on essay length and complexity
    essay = data['essay']
    word_count = len(essay.split())
    
    # Very basic scoring logic
    score_percentage = min(0.9, max(0.3, word_count / 500))  # Between 0.3 and 0.9 based on length
    
    # Add some basic feedback
    strengths = ["Your essay addresses the topic"]
    improvements = ["Consider adding more supporting evidence"]
    
    if word_count < 200:
        improvements.append("Your essay is quite short. Consider expanding your ideas.")
    elif word_count > 800:
        strengths.append("You've written a comprehensive response with substantial content.")
    
    # Check for basic structure elements
    if "conclusion" in essay.lower() or "in summary" in essay.lower():
        strengths.append("Your essay includes a conclusion section.")
    else:
        improvements.append("Consider adding a clear conclusion to summarize your main points.")
    
    # Simple scoring response
    return jsonify({
        'overall_score': score_percentage,
        'total_points': int(score_percentage * 100),
        'max_points': 100,
        'word_count': word_count,
        'strengths': strengths,
        'areas_for_improvement': improvements,
        'overall_feedback': "Thank you for submitting your essay. See the feedback for areas to improve."
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8088)
