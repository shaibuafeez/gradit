"""
Modified version of the AES web application with authentication functionality
but without the ML components that require problematic dependencies.
"""

import os
import json
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, CourseEnrollment, Question, Exam, ExamQuestion, ExamSubmission, Answer
import datetime

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

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

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
    
    # Login user
    login_user(user)
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'matric_number': user.matric_number
        }
    })

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout a user"""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@app.route('/user', methods=['GET'])
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

# Course management routes
@app.route('/courses', methods=['GET'])
@login_required
def get_courses():
    """Get courses based on user role"""
    # Get user enrollments
    enrollments = CourseEnrollment.query.filter_by(user_id=current_user.id).all()
    
    courses = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Count students in course
        student_count = CourseEnrollment.query.filter_by(
            course_id=course.id, 
            role='student'
        ).count()
        
        courses.append({
            'id': course.id,
            'code': course.code,
            'title': course.title,
            'description': course.description,
            'units': course.units,
            'role': enrollment.role,
            'student_count': student_count
        })
    
    # If user is a teacher, also include courses they can join
    if current_user.role == 'teacher':
        # Get all courses user is not enrolled in
        enrolled_course_ids = [e.course_id for e in enrollments]
        available_courses = Course.query.filter(
            ~Course.id.in_(enrolled_course_ids) if enrolled_course_ids else True
        ).all()
        
        for course in available_courses:
            courses.append({
                'id': course.id,
                'code': course.code,
                'title': course.title,
                'description': course.description,
                'units': course.units,
                'role': 'available',
                'student_count': CourseEnrollment.query.filter_by(
                    course_id=course.id, 
                    role='student'
                ).count()
            })
    
    return jsonify({'courses': courses})

@app.route('/')
def index():
    """Render the main page"""
    return render_template('simple_index.html')

# Placeholder for essay scoring (without ML functionality)
@app.route('/score', methods=['POST'])
def score_essay():
    """Placeholder for essay scoring (without ML functionality)"""
    data = request.json
    essay = data.get('essay', '')
    essay_set = data.get('essay_set', 1)
    
    if not essay:
        return jsonify({'error': 'No essay provided'}), 400
    
    # Provide a placeholder response
    # In the real app, this would use the ML model
    score = 7.5  # Placeholder score
    max_score = 10.0
    percentage = 75.0
    
    # Generate feedback based on score percentage
    feedback = get_feedback(percentage)
    
    return jsonify({
        'score': score,
        'max_score': max_score,
        'percentage': percentage,
        'feedback': feedback
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

# Question management routes
@app.route('/courses/<int:course_id>/questions', methods=['GET'])
@login_required
def get_questions(course_id):
    """Get questions for a course"""
    # Check if user is enrolled in the course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Get questions for the course
    questions = Question.query.filter_by(course_id=course_id, parent_id=None).all()
    
    result = []
    for question in questions:
        # Get sub-questions if any
        sub_questions = []
        for sq in question.sub_questions:
            sub_questions.append({
                'id': sq.id,
                'text': sq.text,
                'marking_guide': sq.marking_guide if enrollment.role == 'teacher' else None
            })
        
        # Add question to result
        result.append({
            'id': question.id,
            'text': question.text,
            'marking_guide': question.marking_guide if enrollment.role == 'teacher' else None,
            'sub_questions': sub_questions
        })
    
    return jsonify({'questions': result})

@app.route('/courses/<int:course_id>/questions', methods=['POST'])
@login_required
def create_question(course_id):
    """Create a new question for a course (teachers only)"""
    # Check if user is a teacher for this course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        role='teacher'
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Only teachers can create questions for this course'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('text') or not data.get('marking_guide'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create new question
    new_question = Question(
        course_id=course_id,
        text=data['text'],
        marking_guide=data['marking_guide'],
        parent_id=data.get('parent_id')
    )
    
    # Save to database
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({
        'message': 'Question created successfully',
        'question': {
            'id': new_question.id,
            'text': new_question.text,
            'marking_guide': new_question.marking_guide
        }
    }), 201

# Exam management routes
@app.route('/courses/<int:course_id>/exams', methods=['GET'])
@login_required
def get_exams(course_id):
    """Get exams for a course"""
    # Check if user is enrolled in the course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Get exams for the course
    exams = Exam.query.filter_by(course_id=course_id).all()
    
    result = []
    for exam in exams:
        # Get exam questions
        questions = []
        for eq in exam.exam_questions:
            questions.append({
                'id': eq.question.id,
                'text': eq.question.text
            })
        
        # Check if user has submitted this exam
        submission = None
        if current_user.role == 'student':
            submission = ExamSubmission.query.filter_by(
                exam_id=exam.id,
                student_id=current_user.id
            ).first()
        
        # Add exam to result
        result.append({
            'id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'duration_minutes': exam.duration_minutes,
            'is_active': exam.is_active,
            'questions': questions,
            'submission_status': {
                'submitted': submission is not None,
                'grade': submission.overall_grade if submission and submission.is_graded else None,
                'submission_id': submission.id if submission else None
            } if current_user.role == 'student' else None
        })
    
    return jsonify({'exams': result})

@app.route('/courses/<int:course_id>/exams', methods=['POST'])
@login_required
def create_exam(course_id):
    """Create a new exam for a course (teachers only)"""
    # Check if user is a teacher for this course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        role='teacher'
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Only teachers can create exams for this course'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('title') or not data.get('duration_minutes') or not data.get('question_ids'):
        return jsonify({'error': 'Missing required fields'}), 400
    
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
    for question_id in data['question_ids']:
        # Check if question exists and belongs to this course
        question = Question.query.filter_by(id=question_id, course_id=course_id).first()
        if not question:
            continue
        
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
            'title': new_exam.title,
            'description': new_exam.description,
            'duration_minutes': new_exam.duration_minutes,
            'is_active': new_exam.is_active
        }
    }), 201

@app.route('/exams/<int:exam_id>/start', methods=['POST'])
@login_required
def start_exam(exam_id):
    """Start an exam (students only)"""
    # Check if user is a student
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can take exams'}), 403
    
    # Get the exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if exam is active
    if not exam.is_active:
        return jsonify({'error': 'This exam is not currently active'}), 400
    
    # Check if user is enrolled in the course
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=exam.course_id,
        role='student'
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'You are not enrolled in this course'}), 403
    
    # Check if user has already submitted this exam
    existing_submission = ExamSubmission.query.filter_by(
        exam_id=exam_id,
        student_id=current_user.id,
        submit_time=None
    ).first()
    
    if existing_submission:
        # Return existing submission
        return jsonify({
            'message': 'Exam already started',
            'submission_id': existing_submission.id,
            'start_time': existing_submission.start_time.isoformat(),
            'duration_minutes': exam.duration_minutes
        })
    
    # Create new submission
    submission = ExamSubmission(
        exam_id=exam_id,
        student_id=current_user.id
    )
    
    db.session.add(submission)
    db.session.commit()
    
    # Get exam questions
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
    questions = []
    
    for eq in exam_questions:
        question = eq.question
        questions.append({
            'id': question.id,
            'text': question.text
        })
    
    return jsonify({
        'message': 'Exam started successfully',
        'submission_id': submission.id,
        'start_time': submission.start_time.isoformat(),
        'duration_minutes': exam.duration_minutes,
        'questions': questions
    })

@app.route('/submissions/<int:submission_id>', methods=['POST'])
@login_required
def submit_exam(submission_id):
    """Submit exam answers"""
    # Check if user is a student
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can submit exams'}), 403
    
    # Get the submission
    submission = ExamSubmission.query.get_or_404(submission_id)
    
    # Check if this submission belongs to the current user
    if submission.student_id != current_user.id:
        return jsonify({'error': 'This submission does not belong to you'}), 403
    
    # Check if submission has already been submitted
    if submission.submit_time is not None:
        return jsonify({'error': 'This exam has already been submitted'}), 400
    
    data = request.json
    
    # Validate input data
    if not data.get('answers') or not isinstance(data['answers'], list):
        return jsonify({'error': 'Missing or invalid answers'}), 400
    
    # Get the exam
    exam = submission.exam
    
    # Get exam questions
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam.id).all()
    question_ids = [eq.question_id for eq in exam_questions]
    
    # Process answers
    total_score = 0
    total_questions = len(question_ids)
    
    for answer_data in data['answers']:
        question_id = answer_data.get('question_id')
        text = answer_data.get('text')
        
        # Skip if question is not part of this exam
        if question_id not in question_ids:
            continue
        
        # Get the question
        question = Question.query.get(question_id)
        
        # Calculate similarity score
        similarity = calculate_similarity(text, question.marking_guide)
        
        # Create answer
        answer = Answer(
            submission_id=submission_id,
            question_id=question_id,
            text=text,
            auto_grade=similarity * 10,  # Scale to 0-10
            similarity_score=similarity
        )
        
        db.session.add(answer)
        total_score += answer.auto_grade
    
    # Update submission
    submission.submit_time = datetime.datetime.utcnow()
    submission.is_graded = True
    submission.overall_grade = total_score / total_questions if total_questions > 0 else 0
    
    db.session.commit()
    
    return jsonify({
        'message': 'Exam submitted successfully',
        'grade': submission.overall_grade,
        'answers': [{
            'question_id': answer.question_id,
            'auto_grade': answer.auto_grade,
            'similarity_score': answer.similarity_score
        } for answer in submission.answers]
    })

# Helper function to calculate similarity
def calculate_similarity(student_answer, marking_guide):
    """Calculate similarity between student answer and marking guide using cosine similarity"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Handle empty inputs
    if not student_answer or not marking_guide:
        return 0.0
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    
    # Calculate TF-IDF vectors
    try:
        tfidf_matrix = vectorizer.fit_transform([student_answer, marking_guide])
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity
    except:
        return 0.0

# Course creation route
@app.route('/courses', methods=['POST'])
@login_required
def create_course():
    """Create a new course (teachers only)"""
    # Check if user is a teacher
    if current_user.role != 'teacher':
        return jsonify({'error': 'Only teachers can create courses'}), 403
    
    data = request.json
    
    # Validate input data
    if not data.get('code') or not data.get('title') or not data.get('units'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if course code already exists
    if Course.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Course code already exists'}), 400
    
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
            'description': new_course.description,
            'units': new_course.units
        }
    }), 201

# Model info endpoint (placeholder)
@app.route('/model_info', methods=['GET'])
def model_info():
    """Get information about the model (placeholder)"""
    return jsonify({
        'available': True,
        'model_name': 'roberta-base',
        'preprocessing': True,
        'embedding_strategy': 'mean',
        'essay_sets': [1, 2, 3, 4, 5, 6, 7, 8]
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8085)
