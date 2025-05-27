"""
Gradit - Automated Essay Scoring System
A Flask application that uses Google Gen AI API for essay scoring with teacher-student dashboards.
This version has minimal dependencies to ensure it works reliably.
"""

import os
import json
import requests
import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from routes.exam_routes import exam_bp

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")
    print("Please set it in the .env file or as an environment variable.")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))  # For session management

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///gradit.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS
CORS(app)

# Register blueprints
app.register_blueprint(exam_bp)

# Database models for user management
from models import db, User, CourseEnrollment, Course, Essay
from werkzeug.security import generate_password_hash, check_password_hash
import random
import datetime
from sample_data import add_sample_essays_if_needed

# Keep demo users for easy testing
demo_users = {
    "student@example.com": {
        "password": "password123",
        "name": "Student User",
        "role": "student"
    },
    "teacher@example.com": {
        "password": "password123",
        "name": "Teacher User",
        "role": "teacher"
    }
}

# Initialize the database
with app.app_context():
    db.init_app(app)
    db.create_all()
    
    # Add demo users to the database if they don't exist
    for email, user_data in demo_users.items():
        if not User.query.filter_by(email=email).first():
            new_user = User(
                email=email,
                password_hash=generate_password_hash(user_data['password']),
                name=user_data['name'],
                role=user_data['role']
            )
            db.session.add(new_user)
    
    # Add sample courses if they don't exist
    sample_courses = [
        {
            'code': 'ENG101',
            'title': 'Introduction to Academic Writing',
            'description': 'This course introduces students to the fundamentals of academic writing, including essay structure, critical thinking, and research methods.',
            'units': 3
        },
        {
            'code': 'ENG201',
            'title': 'Advanced Composition',
            'description': 'Building on ENG101, this course focuses on advanced writing techniques, rhetorical strategies, and in-depth research skills.',
            'units': 3
        },
        {
            'code': 'LIT305',
            'title': 'Contemporary Literature',
            'description': 'This course examines contemporary literary works and their cultural, social, and historical contexts.',
            'units': 3
        }
    ]
    
    for course_data in sample_courses:
        if not Course.query.filter_by(code=course_data['code']).first():
            new_course = Course(
                code=course_data['code'],
                title=course_data['title'],
                description=course_data['description'],
                units=course_data['units']
            )
            db.session.add(new_course)
    
    db.session.commit()
    
    # Add course enrollments for demo users
    student = User.query.filter_by(email='student@example.com').first()
    teacher = User.query.filter_by(email='teacher@example.com').first()
    
    if student and teacher:
        courses = Course.query.all()
        
        # Enroll student in all courses
        for course in courses:
            if not CourseEnrollment.query.filter_by(user_id=student.id, course_id=course.id).first():
                student_enrollment = CourseEnrollment(
                    user_id=student.id,
                    course_id=course.id,
                    role='student'
                )
                db.session.add(student_enrollment)
        
        # Enroll teacher in all courses
        for course in courses:
            if not CourseEnrollment.query.filter_by(user_id=teacher.id, course_id=course.id).first():
                teacher_enrollment = CourseEnrollment(
                    user_id=teacher.id,
                    course_id=course.id,
                    role='teacher'
                )
                db.session.add(teacher_enrollment)
    
    db.session.commit()

# Routes
@app.route('/')
def index():
    """Render the landing page"""
    # Check if user is logged in
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET'])
def login_page():
    """Redirect to index page with login modal"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    # Redirect to index page where the login modal can be shown
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    """Login a user"""
    # Check if the request is JSON or form data
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
    
    # Find user in database
    user = User.query.filter_by(email=email).first()
    
    # Check if user exists and password is correct
    if user and check_password_hash(user.password_hash, password):
        # Store user info in session
        session['user'] = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role
        }
        
        # Return success response
        return jsonify({
            'success': True,
            'redirect': url_for('dashboard'),
            'user': {
                'name': user.name,
                'role': user.role
            }
        })
    
    # Return error response
    return jsonify({
        'success': False,
        'error': 'Invalid email or password'
    }), 401

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    # Check if the request is JSON or form data
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role', 'student')  # Default to student role
        matric = data.get('matric', '')  # Matric number for students
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        role = request.form.get('role', 'student')
        matric = request.form.get('matric', '')
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            'success': False,
            'error': 'Email already registered'
        }), 400
    
    # Create new user in the database
    new_user = User(
        email=email,
        password_hash=generate_password_hash(password),
        name=name,
        role=role,
        matric_number=matric if role == 'student' else None
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in
        session['user'] = {
            'id': new_user.id,
            'email': new_user.email,
            'name': new_user.name,
            'role': new_user.role
        }
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'redirect': url_for('dashboard'),
            'user': {
                'name': new_user.name,
                'role': new_user.role
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }), 500

@app.route('/logout')
def logout():
    """Logout a user"""
    session.pop('user', None)
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'redirect': url_for('index')
        })
    
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Render the appropriate dashboard based on user role"""
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    user_obj = User.query.get(user['id'])
    
    # Add sample essays if none exist (for demonstration purposes)
    add_sample_essays_if_needed()
    
    # Render different dashboard templates based on user role
    if user['role'] == 'teacher':
        # Get teacher-specific dashboard data
        total_students = User.query.filter_by(role='student').count()
        total_essays = Essay.query.count()
        pending_essays = Essay.query.filter_by(is_graded=False).count()
        
        # Get recent submissions
        recent_submissions = Essay.query.order_by(Essay.submitted_at.desc()).limit(5).all()
        
        # Calculate average scores
        graded_essays = Essay.query.filter_by(is_graded=True).all()
        avg_score = sum([essay.overall_score for essay in graded_essays]) / len(graded_essays) if graded_essays else 0
        
        # Get students needing attention (those with low scores)
        students_needing_attention = []
        if graded_essays:
            # Get students with average score below 70
            low_performing_essays = Essay.query.filter(Essay.overall_score < 70, Essay.is_graded==True).all()
            student_ids = set([essay.student_id for essay in low_performing_essays])
            students_needing_attention = User.query.filter(User.id.in_(student_ids)).all() if student_ids else []
        
        # Get skill breakdown data for charts
        grammar_avg = sum([essay.grammar_score for essay in graded_essays]) / len(graded_essays) if graded_essays else 0
        content_avg = sum([essay.content_score for essay in graded_essays]) / len(graded_essays) if graded_essays else 0
        structure_avg = sum([essay.structure_score for essay in graded_essays]) / len(graded_essays) if graded_essays else 0
        
        # Format chart data as JSON
        performance_data = {
            'labels': ['Grammar', 'Content', 'Structure'],
            'datasets': [{
                'label': 'Average Scores',
                'data': [grammar_avg, content_avg, structure_avg],
                'backgroundColor': ['rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)'],
                'borderColor': ['rgba(75, 192, 192, 1)', 'rgba(54, 162, 235, 1)', 'rgba(153, 102, 255, 1)'],
                'borderWidth': 1
            }]
        }
        
        return render_template('teacher_dashboard.html', 
                              user=user, 
                              total_students=total_students,
                              total_essays=total_essays,
                              pending_essays=pending_essays,
                              avg_score=avg_score,
                              recent_submissions=recent_submissions,
                              students_needing_attention=students_needing_attention,
                              performance_data=performance_data)
    else:
        # Get student-specific dashboard data
        student_essays = Essay.query.filter_by(student_id=user['id']).all()
        total_essays = len(student_essays)
        
        # Calculate average scores
        graded_essays = [essay for essay in student_essays if essay.is_graded]
        avg_score = sum([essay.overall_score for essay in graded_essays]) / len(graded_essays) if graded_essays else 0
        
        # Get pending feedback count
        pending_feedback = Essay.query.filter_by(student_id=user['id'], is_graded=False).count()
        
        # Get recent essays
        recent_essays = Essay.query.filter_by(student_id=user['id']).order_by(Essay.submitted_at.desc()).limit(5).all()
        
        # Get skill breakdown data
        if graded_essays:
            grammar_avg = sum([essay.grammar_score for essay in graded_essays]) / len(graded_essays)
            content_avg = sum([essay.content_score for essay in graded_essays]) / len(graded_essays)
            structure_avg = sum([essay.structure_score for essay in graded_essays]) / len(graded_essays)
        else:
            grammar_avg = content_avg = structure_avg = 0
        
        # Get enrolled courses
        enrollments = CourseEnrollment.query.filter_by(user_id=user['id']).all()
        courses = [enrollment.course for enrollment in enrollments]
        
        # Format progress chart data
        progress_data = {
            'labels': ['Grammar', 'Content', 'Structure'],
            'datasets': [{
                'label': 'Your Scores',
                'data': [grammar_avg, content_avg, structure_avg],
                'backgroundColor': ['rgba(75, 192, 192, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(153, 102, 255, 0.2)'],
                'borderColor': ['rgba(75, 192, 192, 1)', 'rgba(54, 162, 235, 1)', 'rgba(153, 102, 255, 1)'],
                'borderWidth': 1
            }]
        }
        
        # Format progress over time data (mock data for demonstration)
        dates = []
        scores = []
        if graded_essays:
            # Sort essays by submission date
            sorted_essays = sorted(graded_essays, key=lambda x: x.submitted_at)
            for essay in sorted_essays:
                dates.append(essay.submitted_at.strftime('%b %d'))
                scores.append(essay.overall_score)
        
        progress_over_time = {
            'labels': dates,
            'datasets': [{
                'label': 'Essay Scores',
                'data': scores,
                'fill': False,
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }]
        }
        
        return render_template('student_dashboard.html', 
                              user=user_obj, 
                              total_essays=total_essays,
                              avg_score=avg_score,
                              pending_feedback=pending_feedback,
                              recent_essays=recent_essays,
                              grammar_score=grammar_avg,
                              content_score=content_avg,
                              structure_score=structure_avg,
                              courses=courses,
                              progress_data=progress_data,
                              progress_over_time=progress_over_time)

@app.route('/essay-scorer')
def essay_scorer():
    """Render the essay scorer page with role-based access control"""
    # Check if user is logged in
    if 'user' not in session:
        flash('Please log in to access this feature', 'warning')
        return redirect(url_for('login'))
    
    user = session.get('user')
    action = request.args.get('action', 'view')  # Default to view mode, can be 'submit' for submission mode
    
    # Role-based access control
    if action == 'grade' and user['role'] != 'teacher':
        flash('Only teachers can access the grading functionality', 'danger')
        return redirect(url_for('dashboard'))
    
    # Students can only view their essays or submit new ones
    if user['role'] == 'student' and action not in ['view', 'submit']:
        action = 'view'  # Default to view mode for students
    
    return render_template('essay_scorer.html', user=user, action=action)

@app.route('/courses')
def courses():
    """Render the courses page"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Get courses for the user from the database
    user_obj = User.query.get(user['id'])
    if not user_obj:
        return redirect(url_for('logout'))
    
    # Get course enrollments
    enrollments = CourseEnrollment.query.filter_by(user_id=user['id']).all()
    courses = [enrollment.course for enrollment in enrollments]
    
    # Render different templates based on user role
    if user['role'] == 'teacher':
        return render_template('teacher_courses.html', user=user, courses=courses)
    else:
        return render_template('student_courses.html', user=user, courses=courses)

@app.route('/progress')
def progress():
    """Render the progress page for students"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Only students can access this page
    if user['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    return render_template('student_progress.html', user=user)

@app.route('/analytics')
def analytics():
    """Render the analytics page for teachers"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Only teachers can access this page
    if user['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    return render_template('teacher_analytics.html', user=user)

@app.route('/students')
def students():
    """Render the students page for teachers"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Only teachers can access this page
    if user['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    # Get all students
    students = User.query.filter_by(role='student').all()
    
    return render_template('teacher_students.html', user=user, students=students)

@app.route('/schedule')
def schedule():
    """Render the schedule page for teachers"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Only teachers can access this page
    if user['role'] != 'teacher':
        return redirect(url_for('dashboard'))
    
    return render_template('teacher_schedule.html', user=user)

@app.route('/resources')
def resources():
    """Render the resources page for students"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Only students can access this page
    if user['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    return render_template('student_resources.html', user=user)

@app.route('/achievements')
def achievements():
    """Render the achievements page for students"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Only students can access this page
    if user['role'] != 'student':
        return redirect(url_for('dashboard'))
    
    # In a real application, we would fetch achievements from the database
    # For now, we'll use placeholder data
    achievements_unlocked = 3
    total_achievements = 15
    total_points = 250
    level = 'Novice'
    next_achievement = 'Essay Master'
    
    return render_template('student_achievements.html', 
                          user=user, 
                          achievements_unlocked=achievements_unlocked,
                          total_achievements=total_achievements,
                          total_points=total_points,
                          level=level,
                          next_achievement=next_achievement)

@app.route('/settings')
def settings():
    """Render the settings page"""
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    # Get user from database
    user_obj = User.query.get(user['id'])
    if not user_obj:
        return redirect(url_for('logout'))
    
    # Pass the user object to our unified settings template
    return render_template('settings.html', user=user_obj)

@app.route('/api/score-essay', methods=['POST'])
def score_essay():
    """Score an essay using the Gemini API"""
    data = request.json
    
    # Validate input
    if not data.get('essay'):
        return jsonify({'error': 'Essay text is required'}), 400
    
    essay = data.get('essay')
    prompt = data.get('prompt', 'Write an essay on the given topic.')
    
    # Use the Google Gen AI SDK
    try:
        print("Using Gemini API with Google Gen AI SDK...")
        
        # Check if API key is valid
        if not GEMINI_API_KEY or len(GEMINI_API_KEY) < 20:
            return jsonify({
                'error': 'Invalid API key format',
                'message': 'The Gemini API key appears to be invalid or missing.'
            }), 500
            
        # Import the Google Gen AI SDK
        from google import genai
        from google.genai import types
        
        # Create a client with the API key
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Create the essay evaluation prompt
        evaluation_prompt = f"""
        You are an expert essay evaluator with years of experience in academic assessment.
        
        Evaluate the following essay based on standard academic criteria including:
        - Content and development
        - Organization and structure
        - Language use and vocabulary
        - Grammar and mechanics
        
        Essay prompt: {prompt}
        
        Essay text: 
        {essay}
        
        Provide your evaluation in the following JSON format:
        {{
            "overall_score": (float between 0-1, representing percentage score),
            "total_points": (integer points awarded out of 100),
            "max_points": 100,
            "strengths": [(list of 2-4 specific strengths)],
            "areas_for_improvement": [(list of 2-4 specific areas to improve)],
            "overall_feedback": (2-3 sentence general feedback summarizing the evaluation)
        }}
        
        Return ONLY the JSON object with no additional text.
        """
        
        # Create content for the model
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=evaluation_prompt),
                ],
            ),
        ]
        
        # Configure generation parameters
        generate_content_config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
            response_mime_type="application/json"
        )
        
        print("Sending request to Gemini API...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Using a faster model for quicker response
            contents=contents,
            config=generate_content_config
        )
        
        print("Received response from Gemini API")
        
        # Extract the text response
        text_response = response.text
        print(f"Response text: {text_response[:100]}...")
        
        # Parse the JSON from the text response
        try:
            # Find the JSON object in the text (it might be surrounded by other text)
            import re
            json_match = re.search(r'\{[\s\S]*\}', text_response)
            if json_match:
                feedback_json = json.loads(json_match.group(0))
                print("Successfully parsed JSON from response")
            else:
                feedback_json = json.loads(text_response)
                print("Successfully parsed JSON directly from response")
                
            return jsonify(feedback_json)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {str(e)}")
            return jsonify({
                'error': 'Failed to parse JSON response from Gemini API',
                'message': 'The API response could not be parsed as JSON. Please try again.'
            }), 500
            
    except Exception as e:
        print(f"Error using Gemini API: {str(e)}")
        
        # Provide a more detailed error message based on the exception type
        error_message = f"An error occurred while communicating with the Gemini API: {str(e)}"
        
        if "API key" in str(e).lower():
            error_message = "Invalid API key. Please check your GEMINI_API_KEY environment variable."
        elif "quota" in str(e).lower():
            error_message = "API quota exceeded. Please try again later or upgrade your API plan."
        elif "timeout" in str(e).lower():
            error_message = "Request timed out. The API server may be experiencing high load."
        elif "model" in str(e).lower() and "not found" in str(e).lower():
            error_message = "The specified model was not found. Please check the model name."
        
        return jsonify({
            'error': 'Gemini API error',
            'message': error_message
        }), 500

# Save teacher grade endpoint
@app.route('/api/save-grade', methods=['POST'])
def save_grade():
    """Save a teacher's grade for an essay"""
    if 'user' not in session or session['user']['role'] != 'teacher':
        return jsonify({'error': 'Only teachers can save grades'}), 403
    
    data = request.json
    
    # Validate input
    if not data.get('essay') or not data.get('score'):
        return jsonify({'error': 'Essay text and score are required'}), 400
    
    # In a real app, we would save to database here
    # For now, we'll just return success
    return jsonify({
        'success': True,
        'message': 'Grade saved successfully',
        'grade': {
            'score': data.get('score'),
            'feedback': data.get('feedback'),
            'graded_by': session['user']['name'],
            'graded_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })

# Note: The simple_score function has been removed as we're now using only the Gemini API for scoring

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8088)
