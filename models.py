"""
Database models for the AES system with authentication and exam features.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    matric_number = db.Column(db.String(20), unique=True, nullable=True)  # Only for students
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('CourseEnrollment', back_populates='user')
    submissions = db.relationship('ExamSubmission', back_populates='student')

class Course(db.Model):
    """Course model"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    units = db.Column(db.Integer, nullable=False)  # 2 or 3 units
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('CourseEnrollment', back_populates='course')
    questions = db.relationship('Question', back_populates='course')
    exams = db.relationship('Exam', back_populates='course')

class CourseEnrollment(db.Model):
    """Many-to-many relationship between users and courses"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='courses')
    course = db.relationship('Course', back_populates='enrollments')

class Question(db.Model):
    """Question model"""
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    marking_guide = db.Column(db.Text, nullable=False)  # Correct answer/guide
    parent_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)  # For sub-questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='questions')
    sub_questions = db.relationship('Question', backref=db.backref('parent', remote_side=[id]))
    answers = db.relationship('Answer', back_populates='question')

class Exam(db.Model):
    """Exam model"""
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='exams')
    exam_questions = db.relationship('ExamQuestion', back_populates='exam')
    submissions = db.relationship('ExamSubmission', back_populates='exam')

class ExamQuestion(db.Model):
    """Many-to-many relationship between exams and questions"""
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    
    # Relationships
    exam = db.relationship('Exam', back_populates='exam_questions')
    question = db.relationship('Question')

class ExamSubmission(db.Model):
    """Exam submission model"""
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    submit_time = db.Column(db.DateTime, nullable=True)
    is_graded = db.Column(db.Boolean, default=False)
    overall_grade = db.Column(db.Float, nullable=True)
    teacher_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    exam = db.relationship('Exam', back_populates='submissions')
    student = db.relationship('User', back_populates='submissions')
    answers = db.relationship('Answer', back_populates='submission')

class Answer(db.Model):
    """Student answer model"""
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('exam_submission.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    auto_grade = db.Column(db.Float, nullable=True)
    teacher_grade = db.Column(db.Float, nullable=True)
    similarity_score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    
    # Relationships
    submission = db.relationship('ExamSubmission', back_populates='answers')
    question = db.relationship('Question', back_populates='answers')

class Essay(db.Model):
    """Essay model for student submissions"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    prompt = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_graded = db.Column(db.Boolean, default=False)
    grammar_score = db.Column(db.Float, nullable=True)
    content_score = db.Column(db.Float, nullable=True)
    structure_score = db.Column(db.Float, nullable=True)
    overall_score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    teacher_reviewed = db.Column(db.Boolean, default=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('essays_submitted', lazy='dynamic'))
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref=db.backref('essays_reviewed', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('essays', lazy='dynamic'))
