"""
Web application for the Automated Essay Scoring (AES) system with authentication and exam features.
"""

import os
import json
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from aes_model import AESSystem
from models import db, User, Course, CourseEnrollment, Question, Exam, ExamQuestion, ExamSubmission, Answer
import torch
import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import threading

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aes_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS', 'your-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER', 'your-email@gmail.com')
mail = Mail(app)

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Global variables
MODEL_PATH = 'models/aes_model.pt'
aes_system = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

def load_model():
    """Load the AES model if available, otherwise return None"""
    global aes_system
    
    if aes_system is not None:
        return aes_system
    
    if os.path.exists(MODEL_PATH):
        try:
            aes_system = AESSystem()
            aes_system.load_model(MODEL_PATH)
            print("Model loaded successfully")
            return aes_system
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    else:
        print(f"Model file not found at {MODEL_PATH}")
        return None

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    # Validate input data
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Validate matric number if role is student
    if data.get('role') == 'student':
        if not data.get('matric_number'):
            return jsonify({'error': 'Matric number is required for students'}), 400
        
        # Check if matric number already exists
        if User.query.filter_by(matric_number=data['matric_number']).first():
            return jsonify({'error': 'Matric number already registered'}), 400
        
        # Validate matric number format (example: alphanumeric, minimum length)
        if not (data['matric_number'].isalnum() and len(data['matric_number']) >= 5):
            return jsonify({'error': 'Invalid matric number format'}), 400
    
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
    
    return jsonify({'message': 'Registration successful', 'user_id': new_user.id}), 201

@app.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    
    # Validate input data
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password is correct
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Log in the user
    login_user(user)
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    })

@app.route('/logout')
@login_required
def logout():
    """Logout a user"""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@app.route('/user')
@login_required
def get_user():
    """Get current user information"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role,
            'matric_number': current_user.matric_number
        }
    })

@app.route('/')
def index():
    """Render the main page"""
    # Check if model is available
    model_available = os.path.exists(MODEL_PATH)
    return render_template('index.html', model_available=model_available)

@app.route('/score', methods=['POST'])
def score_essay():
    """Score an essay"""
    data = request.json
    essay = data.get('essay', '')
    essay_set = data.get('essay_set', 1)
    
    if not essay:
        return jsonify({'error': 'No essay provided'}), 400
    
    # Load model if not already loaded
    model = load_model()
    if model is None:
        return jsonify({'error': 'Model not available'}), 503
    
    try:
        # Score the essay
        predictions = model.predict([essay], essay_set)
        score = float(predictions[0])
        
        # Get score range for this essay set
        min_score, max_score = model.score_range[essay_set]
        
        # Calculate percentage score
        percentage = (score - min_score) / (max_score - min_score) * 100
        
        # Determine feedback based on score percentage
        feedback = get_feedback(percentage)
        
        return jsonify({
            'score': score,
            'max_score': max_score,
            'percentage': percentage,
            'feedback': feedback
        })
    except Exception as e:
        print(f"Error scoring essay: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/train', methods=['POST'])
def train_model():
    """Train a new model"""
    data = request.json
    data_path = data.get('data_path', '')
    model_name = data.get('model_name', 'roberta-base')
    essay_set = data.get('essay_set')
    preprocessing = data.get('preprocessing', True)
    epochs = data.get('epochs', 20)
    
    if not data_path:
        return jsonify({'error': 'No data path provided'}), 400
    
    # Initialize session to track training progress
    session['training'] = {
        'status': 'starting',
        'progress': 0,
        'message': 'Initializing training...'
    }
    
    try:
        # Start training in a separate thread
        import threading
        
        def train_thread():
            global aes_system
            
            try:
                session['training']['status'] = 'preprocessing'
                session['training']['message'] = 'Preprocessing data...'
                
                # Initialize AES system
                aes_system = AESSystem(
                    model_name=model_name,
                    preprocessing=preprocessing
                )
                
                # Prepare data
                dataset = aes_system.prepare_data(data_path, essay_set=essay_set)
                
                session['training']['status'] = 'extracting_features'
                session['training']['message'] = 'Extracting features...'
                session['training']['progress'] = 20
                
                # Extract features
                embeddings, id2emb = aes_system.extract_features(dataset)
                
                session['training']['status'] = 'training'
                session['training']['message'] = 'Training model...'
                session['training']['progress'] = 40
                
                # Split data
                from sklearn.model_selection import train_test_split
                train_df, test_df = train_test_split(dataset, test_size=0.2, random_state=42)
                
                # Create data loaders
                train_loader = aes_system.get_data_loader(train_df, embeddings, id2emb)
                test_loader = aes_system.get_data_loader(test_df, embeddings, id2emb, shuffle=False)
                
                # Train model
                for epoch in range(epochs):
                    progress = 40 + int((epoch + 1) / epochs * 50)
                    session['training']['progress'] = progress
                    session['training']['message'] = f'Training epoch {epoch+1}/{epochs}...'
                    
                    # Train for one epoch
                    aes_system.train(train_loader, epochs=1)
                
                session['training']['status'] = 'evaluating'
                session['training']['message'] = 'Evaluating model...'
                session['training']['progress'] = 90
                
                # Evaluate
                test_loss, predictions, targets = aes_system.evaluate(test_loader, return_predictions=True)
                
                # Save model
                session['training']['status'] = 'saving'
                session['training']['message'] = 'Saving model...'
                session['training']['progress'] = 95
                
                aes_system.save_model(MODEL_PATH)
                
                session['training']['status'] = 'completed'
                session['training']['message'] = 'Training completed successfully!'
                session['training']['progress'] = 100
                
            except Exception as e:
                session['training']['status'] = 'error'
                session['training']['message'] = f'Error during training: {str(e)}'
                print(f"Training error: {e}")
        
        # Start training thread
        training_thread = threading.Thread(target=train_thread)
        training_thread.daemon = True
        training_thread.start()
        
        return jsonify({
            'message': 'Training started',
            'status': 'starting'
        })
        
    except Exception as e:
        print(f"Error starting training: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/training_status', methods=['GET'])
def training_status():
    """Get the current training status"""
    if 'training' not in session:
        return jsonify({
            'status': 'not_started',
            'message': 'Training has not been started'
        })
    
    return jsonify(session['training'])

# Course management routes
@app.route('/courses', methods=['GET'])
@login_required
def get_courses():
    """Get courses based on user role"""
    if current_user.role == 'teacher':
        # For teachers, get courses they teach
        enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id, role='teacher').all()
    else:
        # For students, get courses they're enrolled in
        enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id, role='student').all()
    
    courses = []
    for enrollment in enrollments:
        course = enrollment.course
        courses.append({
            'id': course.id,
            'code': course.code,
            'title': course.title,
            'description': course.description,
            'units': course.units
        })
    
    return jsonify({'courses': courses})

@app.route('/courses', methods=['POST'])
@login_required
def create_course():
    """Create a new course (teachers only)"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can create courses'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('code') or not data.get('title') or not data.get('units'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if course code already exists
    if Course.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Course code already exists'}), 400
    
    # Validate units (must be 2 or 3)
    if data['units'] not in [2, 3]:
        return jsonify({'error': 'Units must be either 2 or 3'}), 400
    
    # Create new course
    new_course = Course(
        code=data['code'],
        title=data['title'],
        description=data.get('description', ''),
        units=data['units']
    )
    
    # Save to database
    db.session.add(new_course)
    db.session.commit()
    
    # Enroll the teacher in the course
    enrollment = CourseEnrollment(
        user_id=current_user.id,
        course_id=new_course.id,
        role='teacher'
    )
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': 'Course created successfully',
        'course': {
            'id': new_course.id,
            'code': new_course.code,
            'title': new_course.title,
            'units': new_course.units
        }
    }), 201

@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_student(course_id):
    """Enroll a student in a course (teachers only)"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can enroll students'}), 403
    
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if teacher is enrolled in this course
    teacher_enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        role='teacher'
    ).first()
    
    if not teacher_enrollment:
        return jsonify({'error': 'You are not a teacher for this course'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('student_email'):
        return jsonify({'error': 'Student email is required'}), 400
    
    # Find student by email
    student = User.query.filter_by(email=data['student_email'], role='student').first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check if student is already enrolled
    existing_enrollment = CourseEnrollment.query.filter_by(
        user_id=student.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        return jsonify({'error': 'Student already enrolled in this course'}), 400
    
    # Create enrollment
    enrollment = CourseEnrollment(
        user_id=student.id,
        course_id=course_id,
        role='student'
    )
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({'message': 'Student enrolled successfully'})

# Question management routes
@app.route('/courses/<int:course_id>/questions', methods=['GET'])
@login_required
def get_questions(course_id):
    """Get questions for a course"""
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if user is enrolled in this course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Get all top-level questions (no parent)
    questions = Question.query.filter_by(course_id=course_id, parent_id=None).all()
    
    result = []
    for question in questions:
        q_data = {
            'id': question.id,
            'text': question.text,
            'sub_questions': []
        }
        
        # Include marking guide only for teachers
        if current_user.role == 'teacher':
            q_data['marking_guide'] = question.marking_guide
        
        # Get sub-questions
        for sub_q in question.sub_questions:
            sub_q_data = {
                'id': sub_q.id,
                'text': sub_q.text
            }
            
            # Include marking guide only for teachers
            if current_user.role == 'teacher':
                sub_q_data['marking_guide'] = sub_q.marking_guide
                
            q_data['sub_questions'].append(sub_q_data)
            
        result.append(q_data)
    
    return jsonify({'questions': result})

@app.route('/courses/<int:course_id>/questions', methods=['POST'])
@login_required
def create_question(course_id):
    """Create a new question for a course (teachers only)"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can create questions'}), 403
    
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if teacher is enrolled in this course
    teacher_enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        role='teacher'
    ).first()
    
    if not teacher_enrollment:
        return jsonify({'error': 'You are not a teacher for this course'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('text') or not data.get('marking_guide'):
        return jsonify({'error': 'Question text and marking guide are required'}), 400
    
    # Create new question
    new_question = Question(
        course_id=course_id,
        text=data['text'],
        marking_guide=data['marking_guide'],
        parent_id=data.get('parent_id')  # Optional, for sub-questions
    )
    
    # Save to database
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({
        'message': 'Question created successfully',
        'question': {
            'id': new_question.id,
            'text': new_question.text
        }
    }), 201

# Exam management routes
@app.route('/courses/<int:course_id>/exams', methods=['GET'])
@login_required
def get_exams(course_id):
    """Get exams for a course"""
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if user is enrolled in this course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Get all exams for this course
    exams = Exam.query.filter_by(course_id=course_id).all()
    
    result = []
    for exam in exams:
        exam_data = {
            'id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'duration_minutes': exam.duration_minutes,
            'is_active': exam.is_active
        }
        
        # For students, only show active exams
        if current_user.role == 'student' and not exam.is_active:
            continue
            
        # For teachers, show additional information
        if current_user.role == 'teacher':
            # Count submissions
            submission_count = ExamSubmission.query.filter_by(exam_id=exam.id).count()
            exam_data['submission_count'] = submission_count
            
        result.append(exam_data)
    
    return jsonify({'exams': result})

@app.route('/courses/<int:course_id>/exams', methods=['POST'])
@login_required
def create_exam(course_id):
    """Create a new exam for a course (teachers only)"""
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can create exams'}), 403
    
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if teacher is enrolled in this course
    teacher_enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        role='teacher'
    ).first()
    
    if not teacher_enrollment:
        return jsonify({'error': 'You are not a teacher for this course'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('title') or not data.get('duration_minutes'):
        return jsonify({'error': 'Exam title and duration are required'}), 400
    
    # Validate question IDs
    question_ids = data.get('question_ids', [])
    if not question_ids:
        return jsonify({'error': 'At least one question is required'}), 400
    
    # Create new exam
    new_exam = Exam(
        course_id=course_id,
        title=data['title'],
        description=data.get('description', ''),
        duration_minutes=data['duration_minutes'],
        is_active=data.get('is_active', False)
    )
    
    # Save to database
    db.session.add(new_exam)
    db.session.commit()
    
    # Add questions to exam
    for question_id in question_ids:
        # Verify question exists and belongs to this course
        question = Question.query.filter_by(id=question_id, course_id=course_id).first()
        if not question:
            continue  # Skip invalid questions
            
        exam_question = ExamQuestion(
            exam_id=new_exam.id,
            question_id=question_id
        )
        db.session.add(exam_question)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Exam created successfully',
        'exam': {
            'id': new_exam.id,
            'title': new_exam.title
        }
    }), 201

@app.route('/exams/<int:exam_id>/start', methods=['POST'])
@login_required
def start_exam(exam_id):
    """Start an exam (students only)"""
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can take exams'}), 403
    
    # Check if exam exists and is active
    exam = Exam.query.filter_by(id=exam_id, is_active=True).first()
    if not exam:
        return jsonify({'error': 'Exam not found or not active'}), 404
    
    # Check if student is enrolled in the course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=exam.course_id,
        role='student'
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Check if student has already started this exam
    existing_submission = ExamSubmission.query.filter_by(
        exam_id=exam_id,
        student_id=current_user.id
    ).first()
    
    if existing_submission:
        # If already submitted, don't allow restart
        if existing_submission.submit_time:
            return jsonify({'error': 'You have already submitted this exam'}), 400
            
        # If started but not submitted, return the existing submission
        return jsonify({
            'message': 'Exam already started',
            'submission_id': existing_submission.id,
            'start_time': existing_submission.start_time.isoformat(),
            'remaining_minutes': exam.duration_minutes - int((datetime.datetime.utcnow() - existing_submission.start_time).total_seconds() / 60)
        })
    
    # Create new submission
    submission = ExamSubmission(
        exam_id=exam_id,
        student_id=current_user.id,
        start_time=datetime.datetime.utcnow()
    )
    db.session.add(submission)
    db.session.commit()
    
    # Get questions for this exam based on course units
    course = exam.course
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
    
    # Get all question IDs for this exam
    question_ids = [eq.question_id for eq in exam_questions]
    
    # Fetch the actual questions
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    # Determine how many questions to show based on course units
    num_questions_to_show = 5 if course.units == 2 else 6
    num_questions_to_answer = 3 if course.units == 2 else 4
    
    # If we have more questions than needed, randomly select
    import random
    if len(questions) > num_questions_to_show:
        questions = random.sample(questions, num_questions_to_show)
    
    # Format questions for response
    formatted_questions = []
    for question in questions:
        q_data = {
            'id': question.id,
            'text': question.text,
            'sub_questions': []
        }
        
        # Get sub-questions
        for sub_q in question.sub_questions:
            sub_q_data = {
                'id': sub_q.id,
                'text': sub_q.text
            }
            q_data['sub_questions'].append(sub_q_data)
            
        formatted_questions.append(q_data)
    
    return jsonify({
        'message': 'Exam started successfully',
        'submission_id': submission.id,
        'questions': formatted_questions,
        'num_to_answer': num_questions_to_answer,
        'duration_minutes': exam.duration_minutes,
        'start_time': submission.start_time.isoformat()
    })

@app.route('/exams/submissions/<int:submission_id>/submit', methods=['POST'])
@login_required
def submit_exam(submission_id):
    """Submit exam answers"""
    # Check if submission exists and belongs to current user
    submission = ExamSubmission.query.filter_by(
        id=submission_id,
        student_id=current_user.id
    ).first()
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    # Check if already submitted
    if submission.submit_time:
        return jsonify({'error': 'Exam already submitted'}), 400
    
    # Get exam details
    exam = Exam.query.get(submission.exam_id)
    if not exam:
        return jsonify({'error': 'Exam not found'}), 404
    
    # Check if time limit exceeded
    current_time = datetime.datetime.utcnow()
    time_limit = submission.start_time + datetime.timedelta(minutes=exam.duration_minutes)
    
    if current_time > time_limit:
        # Time exceeded, but still accept submission
        pass
    
    # Process submitted answers
    data = request.json
    answers = data.get('answers', [])
    
    if not answers:
        return jsonify({'error': 'No answers provided'}), 400
    
    # Get course units to determine required number of answers
    course = Course.query.get(exam.course_id)
    required_answers = 3 if course.units == 2 else 4
    
    # Check if enough questions were answered
    if len(answers) < required_answers:
        return jsonify({'error': f'You must answer at least {required_answers} questions'}), 400
    
    # Process each answer
    processed_answers = []
    for answer_data in answers:
        question_id = answer_data.get('question_id')
        answer_text = answer_data.get('text', '')
        
        if not question_id or not answer_text:
            continue
        
        # Verify question belongs to this exam
        exam_question = ExamQuestion.query.filter_by(
            exam_id=exam.id,
            question_id=question_id
        ).first()
        
        if not exam_question:
            continue
        
        # Get question for grading
        question = Question.query.get(question_id)
        if not question:
            continue
        
        # Create answer record
        answer = Answer(
            submission_id=submission.id,
            question_id=question_id,
            text=answer_text
        )
        
        # Grade the answer using similarity algorithm
        similarity_score = calculate_similarity(answer_text, question.marking_guide)
        answer.similarity_score = similarity_score
        
        # Convert similarity to grade (0-100%)
        answer.auto_grade = similarity_score * 100
        
        db.session.add(answer)
        processed_answers.append({
            'question_id': question_id,
            'similarity': similarity_score,
            'grade': answer.auto_grade
        })
    
    # Update submission
    submission.submit_time = current_time
    submission.is_graded = True
    
    # Calculate overall grade (average of all answer grades)
    if processed_answers:
        submission.overall_grade = sum(a['grade'] for a in processed_answers) / len(processed_answers)
    
    db.session.commit()
    
    # Send email notification to teachers
    send_submission_email(submission)
    
    return jsonify({
        'message': 'Exam submitted successfully',
        'submission_id': submission.id,
        'overall_grade': submission.overall_grade,
        'answers': processed_answers
    })

# Helper function to calculate similarity between student answer and marking guide
def calculate_similarity(student_answer, marking_guide):
    """Calculate similarity between student answer and marking guide using cosine similarity"""
    # Use TF-IDF vectorizer for text comparison
    vectorizer = TfidfVectorizer().fit_transform([student_answer, marking_guide])
    vectors = vectorizer.toarray()
    
    # Calculate cosine similarity
    if len(vectors) < 2:
        return 0.0
        
    cosine_sim = cosine_similarity(vectors[0].reshape(1, -1), vectors[1].reshape(1, -1))[0][0]
    return cosine_sim

# Helper function to send email notification to teachers
def send_submission_email(submission):
    """Send email notification to teachers about a new submission"""
    try:
        # Get exam and course details
        exam = Exam.query.get(submission.exam_id)
        course = Course.query.get(exam.course_id)
        student = User.query.get(submission.student_id)
        
        # Get all teachers for this course
        teacher_enrollments = CourseEnrollment.query.filter_by(
            course_id=course.id,
            role='teacher'
        ).all()
        
        teacher_emails = []
        for enrollment in teacher_enrollments:
            teacher = User.query.get(enrollment.user_id)
            if teacher and teacher.email:
                teacher_emails.append(teacher.email)
        
        if not teacher_emails:
            return
        
        # Get answers for this submission
        answers = Answer.query.filter_by(submission_id=submission.id).all()
        
        # Create email content
        subject = f"New Exam Submission: {course.code} - {exam.title}"
        
        body = f"""
        A new exam submission has been received and auto-graded.
        
        Course: {course.code} - {course.title}
        Exam: {exam.title}
        Student: {student.name} ({student.email})
        Submission Time: {submission.submit_time}
        Overall Grade: {submission.overall_grade:.2f}%
        
        Individual Question Grades:
        """
        
        for answer in answers:
            question = Question.query.get(answer.question_id)
            body += f"\nQuestion: {question.text[:50]}...\n"
            body += f"Auto Grade: {answer.auto_grade:.2f}%\n"
            body += f"Student Answer: {answer.text[:100]}...\n"
            body += f"Marking Guide: {question.marking_guide[:100]}...\n"
            body += "---\n"
        
        body += "\nPlease review and approve or adjust the grades as needed."
        
        # Send email
        msg = Message(
            subject=subject,
            recipients=teacher_emails,
            body=body
        )
        mail.send(msg)
        
    except Exception as e:
        print(f"Error sending email: {e}")

# Routes for marking guide
@app.route('/save_marking_guide', methods=['POST'])
def save_marking_guide():
    """Save a marking guide"""
    # Get marking guide data from request
    data = request.json
    
    # Validate required fields
    if not data.get('assignment_name'):
        return jsonify({'error': 'Assignment name is required'}), 400
    
    if not data.get('criteria') or len(data.get('criteria')) == 0:
        return jsonify({'error': 'At least one criteria is required'}), 400
    
    # Add timestamp if not provided
    if not data.get('created_at'):
        data['created_at'] = datetime.datetime.now().isoformat()
    
    # Create directory for marking guides if it doesn't exist
    guides_dir = os.path.join(os.path.dirname(__file__), 'data', 'marking_guides')
    os.makedirs(guides_dir, exist_ok=True)
    
    # Generate a filename based on assignment name
    safe_name = data['assignment_name'].lower().replace(' ', '_')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{safe_name}_{timestamp}.json"
    file_path = os.path.join(guides_dir, filename)
    
    # Save the marking guide to a JSON file
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Marking guide saved successfully',
            'file_path': file_path
        })
    except Exception as e:
        return jsonify({'error': f'Error saving marking guide: {str(e)}'}), 500

@app.route('/get_marking_guides', methods=['GET'])
def get_marking_guides():
    """Get all marking guides"""
    # Get all marking guides
    guides_dir = os.path.join(os.path.dirname(__file__), 'data', 'marking_guides')
    
    # Create directory if it doesn't exist
    os.makedirs(guides_dir, exist_ok=True)
    
    guides = []
    
    # List all JSON files in the directory
    for filename in os.listdir(guides_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(guides_dir, filename)
            
            try:
                with open(file_path, 'r') as f:
                    guide_data = json.load(f)
                    
                    # Add file info
                    guide_data['filename'] = filename
                    guide_data['file_path'] = file_path
                    
                    guides.append(guide_data)
            except Exception as e:
                print(f"Error loading marking guide {filename}: {str(e)}")
    
    # Sort guides by creation date (newest first)
    guides.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify(guides)

@app.route('/model_info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    model = load_model()
    if model is None:
        return jsonify({'available': False})
    
    return jsonify({
        'available': True,
        'model_name': model.model_name,
        'preprocessing': model.preprocessing,
        'embedding_strategy': model.embedding_strategy,
        'essay_sets': list(model.score_range.keys())
    })

def get_feedback(percentage):
    """Generate feedback based on essay score percentage"""
    if percentage >= 90:
        return {
            'level': 'excellent',
            'message': 'Excellent work! Your essay demonstrates exceptional understanding of the topic, strong organization, and effective use of language.',
            'suggestions': [
                'Consider exploring more complex arguments in future essays',
                'Your writing is strong - continue to develop your unique voice'
            ]
        }
    elif percentage >= 75:
        return {
            'level': 'good',
            'message': 'Good job! Your essay shows solid understanding of the topic with clear organization and appropriate language.',
            'suggestions': [
                'Try to include more specific examples to support your arguments',
                'Work on varying your sentence structure for more engaging writing'
            ]
        }
    elif percentage >= 60:
        return {
            'level': 'satisfactory',
            'message': 'Your essay meets the basic requirements with adequate understanding of the topic.',
            'suggestions': [
                'Focus on developing stronger topic sentences for each paragraph',
                'Try to provide more detailed evidence to support your claims',
                'Work on creating smoother transitions between ideas'
            ]
        }
    elif percentage >= 40:
        return {
            'level': 'needs_improvement',
            'message': 'Your essay needs improvement in organization, development, and/or language use.',
            'suggestions': [
                'Make sure your essay has a clear thesis statement',
                'Develop each paragraph around a single main idea',
                'Check for grammatical errors that may interfere with meaning',
                'Try to use more specific vocabulary related to the topic'
            ]
        }
    else:
        return {
            'level': 'unsatisfactory',
            'message': 'Your essay needs significant improvement to meet the requirements.',
            'suggestions': [
                'Review the basic essay structure (introduction, body, conclusion)',
                'Make sure you understand the prompt and are addressing it directly',
                'Focus on writing complete sentences with proper grammar',
                'Consider seeking additional help with your writing skills'
            ]
        }

if __name__ == '__main__':
    # Load model at startup if available
    load_model()
    app.run(debug=True, host='0.0.0.0', port=8082)
