"""
Exam Routes for Gradit
Handles all routes related to exam creation, management, and submission
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from models import db, User, Course, Exam, Question, ExamSubmission, Answer
from utils.encryption import encrypt_data, decrypt_data
import json
from datetime import datetime
import uuid

exam_bp = Blueprint('exam_bp', __name__)

# Teacher routes for exam management
@exam_bp.route('/teacher/exams')
def teacher_exams():
    """Display all exams for a teacher"""
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('index'))
    
    teacher_id = session['user']['id']
    # Get all courses taught by this teacher
    courses = Course.query.filter_by(teacher_id=teacher_id).all()
    
    # Get all exams for these courses
    exams = []
    for course in courses:
        course_exams = Exam.query.filter_by(course_id=course.id).all()
        for exam in course_exams:
            exam.course = course  # Add course info to each exam
            exam.exam_questions = Question.query.filter_by(exam_id=exam.id).all()
            exams.append(exam)
    
    return render_template('teacher_exams.html', exams=exams, courses=courses, user=session['user'])

@exam_bp.route('/teacher/exams/create', methods=['GET', 'POST'])
def create_exam():
    """Create a new exam"""
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('index'))
    
    teacher_id = session['user']['id']
    
    if request.method == 'GET':
        # Get all courses taught by this teacher
        courses = Course.query.filter_by(teacher_id=teacher_id).all()
        return render_template('create_exam.html', courses=courses, user=session['user'])
    
    elif request.method == 'POST':
        # Process form submission
        title = request.form.get('title')
        course_id = request.form.get('course_id')
        duration_minutes = request.form.get('duration_minutes')
        exam_date = request.form.get('exam_date')
        description = request.form.get('description')
        instructions = request.form.get('instructions')
        is_active = True if request.form.get('is_active') else False
        save_draft = True if request.form.get('save_draft') else False
        
        # If saving as draft, mark as inactive
        if save_draft:
            is_active = False
        
        # Create new exam
        new_exam = Exam(
            title=title,
            course_id=course_id,
            duration_minutes=duration_minutes,
            exam_date=datetime.strptime(exam_date, '%Y-%m-%d'),
            description=description,
            instructions=instructions,
            is_active=is_active,
            created_by=teacher_id
        )
        
        db.session.add(new_exam)
        db.session.flush()  # Get the exam ID without committing
        
        # Process questions
        questions_data = {}
        for key, value in request.form.items():
            if key.startswith('questions[') and key.endswith('][text]'):
                # Extract question ID from the key
                question_id = key.split('[')[1].split(']')[0]
                
                if question_id not in questions_data:
                    questions_data[question_id] = {}
                
                questions_data[question_id]['text'] = value
            
            elif key.startswith('questions[') and key.endswith('][type]'):
                question_id = key.split('[')[1].split(']')[0]
                
                if question_id not in questions_data:
                    questions_data[question_id] = {}
                
                questions_data[question_id]['type'] = value
            
            elif key.startswith('questions[') and key.endswith('][options]'):
                question_id = key.split('[')[1].split(']')[0]
                
                if question_id not in questions_data:
                    questions_data[question_id] = {}
                
                # Split options by newline
                options = value.strip().split('\n')
                questions_data[question_id]['options'] = options
            
            elif key.startswith('questions[') and key.endswith('][marking_guide]'):
                question_id = key.split('[')[1].split(']')[0]
                
                if question_id not in questions_data:
                    questions_data[question_id] = {}
                
                # Parse the marking guide JSON
                marking_guide = json.loads(value)
                questions_data[question_id]['marking_guide'] = marking_guide
        
        # Create questions
        for question_id, question_data in questions_data.items():
            # Encrypt sensitive data
            encrypted_text = encrypt_data(question_data['text'])
            encrypted_marking_guide = encrypt_data(json.dumps(question_data['marking_guide']))
            
            # Create question
            new_question = Question(
                exam_id=new_exam.id,
                text=encrypted_text,
                question_type=question_data['type'],
                marking_guide=encrypted_marking_guide
            )
            
            # Add options for multiple choice questions
            if question_data['type'] == 'multiple_choice' and 'options' in question_data:
                new_question.options = encrypt_data(json.dumps(question_data['options']))
            
            db.session.add(new_question)
        
        # Commit all changes
        db.session.commit()
        
        flash('Exam created successfully!', 'success')
        return redirect(url_for('exam_bp.teacher_exams'))

@exam_bp.route('/teacher/exams/<int:exam_id>')
def view_exam(exam_id):
    """View details of a specific exam"""
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('index'))
    
    teacher_id = session['user']['id']
    
    # Get the exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if this teacher has access to this exam
    course = Course.query.get(exam.course_id)
    if course.teacher_id != teacher_id:
        flash('You do not have permission to view this exam.', 'danger')
        return redirect(url_for('exam_bp.teacher_exams'))
    
    # Get questions for this exam
    questions = Question.query.filter_by(exam_id=exam_id).all()
    
    # Decrypt question data
    for question in questions:
        question.text = decrypt_data(question.text)
        question.marking_guide = json.loads(decrypt_data(question.marking_guide))
        
        if question.options:
            question.options_list = json.loads(decrypt_data(question.options))
    
    # Get submissions for this exam
    submissions = ExamSubmission.query.filter_by(exam_id=exam_id).all()
    
    # Get student info for each submission
    for submission in submissions:
        submission.student = User.query.get(submission.student_id)
    
    return render_template('view_exam.html', 
                          exam=exam, 
                          questions=questions, 
                          submissions=submissions, 
                          course=course,
                          user=session['user'])

@exam_bp.route('/teacher/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
def edit_exam(exam_id):
    """Edit an existing exam"""
    if 'user' not in session or session['user']['role'] != 'teacher':
        return redirect(url_for('index'))
    
    teacher_id = session['user']['id']
    
    # Get the exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if this teacher has access to this exam
    course = Course.query.get(exam.course_id)
    if course.teacher_id != teacher_id:
        flash('You do not have permission to edit this exam.', 'danger')
        return redirect(url_for('exam_bp.teacher_exams'))
    
    if request.method == 'GET':
        # Get all courses taught by this teacher
        courses = Course.query.filter_by(teacher_id=teacher_id).all()
        
        # Get questions for this exam
        questions = Question.query.filter_by(exam_id=exam_id).all()
        
        # Decrypt question data
        for question in questions:
            question.text = decrypt_data(question.text)
            question.marking_guide = json.loads(decrypt_data(question.marking_guide))
            
            if question.options:
                question.options_list = json.loads(decrypt_data(question.options))
        
        return render_template('edit_exam.html', 
                              exam=exam, 
                              questions=questions, 
                              courses=courses,
                              course=course,
                              user=session['user'])
    
    elif request.method == 'POST':
        # Process form submission (similar to create_exam)
        # This would be implemented similarly to the create_exam POST handler
        # but with updates to existing records instead of creating new ones
        pass

@exam_bp.route('/teacher/exams/<int:exam_id>/toggle-status', methods=['POST'])
def toggle_exam_status(exam_id):
    """Toggle the active status of an exam"""
    if 'user' not in session or session['user']['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    teacher_id = session['user']['id']
    
    # Get the exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if this teacher has access to this exam
    course = Course.query.get(exam.course_id)
    if course.teacher_id != teacher_id:
        return jsonify({'success': False, 'message': 'You do not have permission to modify this exam.'})
    
    # Toggle status
    exam.is_active = not exam.is_active
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'is_active': exam.is_active,
        'message': f'Exam is now {"active" if exam.is_active else "inactive"}'
    })

# Student routes for taking exams
@exam_bp.route('/student/exams')
def student_exams():
    """Display available exams for a student"""
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('index'))
    
    student_id = session['user']['id']
    
    # Get all courses this student is enrolled in
    # This would require a student_courses table in a real implementation
    # For now, we'll assume students can see all active exams
    
    # Get all active exams
    exams = Exam.query.filter_by(is_active=True).all()
    
    # Add course info to each exam
    for exam in exams:
        exam.course = Course.query.get(exam.course_id)
        
        # Check if student has already submitted this exam
        submission = ExamSubmission.query.filter_by(
            exam_id=exam.id,
            student_id=student_id
        ).first()
        
        exam.submitted = submission is not None
        if exam.submitted:
            exam.submission_id = submission.id
    
    return render_template('student_exams.html', exams=exams, user=session['user'])

@exam_bp.route('/student/exams/<int:exam_id>/take')
def take_exam(exam_id):
    """Take an exam"""
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('index'))
    
    student_id = session['user']['id']
    
    # Get the exam
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if exam is active
    if not exam.is_active:
        flash('This exam is not currently available.', 'danger')
        return redirect(url_for('exam_bp.student_exams'))
    
    # Check if student has already submitted this exam
    submission = ExamSubmission.query.filter_by(
        exam_id=exam_id,
        student_id=student_id
    ).first()
    
    if submission:
        flash('You have already submitted this exam.', 'info')
        return redirect(url_for('exam_bp.exam_results', submission_id=submission.id))
    
    # Get course info
    exam.course = Course.query.get(exam.course_id)
    
    # Get questions for this exam
    questions = Question.query.filter_by(exam_id=exam_id).all()
    
    # Decrypt question data
    for question in questions:
        question.text = decrypt_data(question.text)
        
        if question.options:
            question.options = json.loads(decrypt_data(question.options))
    
    # Add questions to exam object for template access
    exam.questions = questions
    
    return render_template('student_exam.html', exam=exam, user=session['user'])

@exam_bp.route('/student/exams/submit', methods=['POST'])
def submit_exam():
    """Submit an exam"""
    if 'user' not in session or session['user']['role'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student_id = session['user']['id']
    
    # Get submission data
    data = request.json
    exam_id = data.get('exam_id')
    answers = data.get('answers')
    time_taken = data.get('time_taken')
    
    # Validate data
    if not exam_id or not answers:
        return jsonify({'success': False, 'message': 'Missing required data'})
    
    # Check if student has already submitted this exam
    existing_submission = ExamSubmission.query.filter_by(
        exam_id=exam_id,
        student_id=student_id
    ).first()
    
    if existing_submission:
        return jsonify({
            'success': False, 
            'message': 'You have already submitted this exam',
            'submission_id': existing_submission.id
        })
    
    # Create new submission
    submission = ExamSubmission(
        exam_id=exam_id,
        student_id=student_id,
        time_taken=time_taken,
        start_time=datetime.now()
    )
    
    db.session.add(submission)
    db.session.flush()  # Get the submission ID without committing
    
    # Get questions for this exam
    questions = Question.query.filter_by(exam_id=exam_id).all()
    
    # Process each answer
    is_graded = 0
    overall_grade = 0
    
    for question in questions:
        question_id = str(question.id)
        
        # Skip if no answer provided for this question
        if question_id not in answers:
            continue
        
        # Encrypt the answer
        encrypted_answer = encrypt_data(answers[question_id])
        
        # Create answer submission
        answer_submission = Answer(
            submission_id=submission.id,
            question_id=question.id,
            text=encrypted_answer
        )
        
        db.session.add(answer_submission)
        
        # Grade the answer
        marking_guide = json.loads(decrypt_data(question.marking_guide))
        
        # Calculate points based on marking guide
        question_is_graded = marking_guide.get('totalPoints', 0)
        is_graded += question_is_graded
        
        # In a real implementation, this would use more sophisticated grading
        # For now, we'll use a simple keyword matching approach
        keywords = marking_guide.get('keywords', [])
        criteria = marking_guide.get('criteria', [])
        
        # Calculate a simple score based on keywords
        text = answers[question_id].lower()
        keywords_found = []
        keywords_missing = []
        
        for keyword in keywords:
            if keyword.lower() in text:
                keywords_found.append(keyword)
            else:
                keywords_missing.append(keyword)
        
        keyword_score = len(keywords_found) / len(keywords) if keywords else 0.5
        
        # Process each criterion
        criteria_results = []
        question_overall_grade = 0
        
        for criterion in criteria:
            criterion_points = criterion.get('points', 0)
            criterion_earned = criterion_points * keyword_score  # Simplified scoring
            
            question_overall_grade += criterion_earned
            
            # Generate feedback for this criterion
            if keyword_score >= 0.8:
                feedback = "Excellent understanding demonstrated."
            elif keyword_score >= 0.5:
                feedback = "Good understanding, but some key points missing."
            elif keyword_score >= 0.3:
                feedback = "Basic understanding shown, but significant improvement needed."
            else:
                feedback = "Limited understanding of this criterion."
            
            criteria_results.append({
                'description': criterion.get('description', ''),
                'possible_points': criterion_points,
                'overall_grade': criterion_earned,
                'feedback': feedback
            })
        
        overall_grade += question_overall_grade
        
        # Generate overall feedback
        percentage = (question_overall_grade / question_is_graded) * 100 if question_is_graded > 0 else 0
        
        if percentage >= 90:
            feedback = 'Outstanding work! Your answer demonstrates excellent understanding of the topic.'
        elif percentage >= 80:
            feedback = 'Great job! Your answer shows strong understanding of the key concepts.'
        elif percentage >= 70:
            feedback = 'Good work! You have a solid understanding of most concepts.'
        elif percentage >= 60:
            feedback = 'Satisfactory work. You understand the basics, but there\'s room for improvement.'
        elif percentage >= 50:
            feedback = 'You\'ve shown basic understanding, but need to develop your knowledge further.'
        else:
            feedback = 'Your answer needs significant improvement. Please review the course materials.'
        
        # Add keyword feedback
        if keywords_missing:
            feedback += ' Consider including these important concepts: ' + ', '.join(keywords_missing) + '.'
        
        if keywords_found:
            feedback += ' You effectively incorporated these key concepts: ' + ', '.join(keywords_found) + '.'
        
        # Store grading results
        result = {
            'questionId': question.id,
            'totalPossiblePoints': question_is_graded,
            'earnedPoints': question_overall_grade,
            'percentage': percentage,
            'criteriaResults': criteria_results,
            'keywordsFound': keywords_found,
            'keywordsMissing': keywords_missing,
            'feedback': feedback
        }
        
        # Encrypt and store the results
        answer_submission.feedback = encrypt_data(json.dumps(result))
    
    # Update submission with total scores
    submission.is_graded = is_graded
    submission.overall_grade = overall_grade
    submission.percentage = (overall_grade / is_graded) * 100 if is_graded > 0 else 0
    
    # Commit all changes
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Exam submitted successfully',
        'submission_id': submission.id
    })

@exam_bp.route('/student/exams/<int:submission_id>/results')
def exam_results(submission_id):
    """View exam results"""
    if 'user' not in session or session['user']['role'] != 'student':
        return redirect(url_for('index'))
    
    student_id = session['user']['id']
    
    # Get the submission
    submission = ExamSubmission.query.get_or_404(submission_id)
    
    # Check if this student has access to this submission
    if submission.student_id != student_id:
        flash('You do not have permission to view these results.', 'danger')
        return redirect(url_for('exam_bp.student_exams'))
    
    # Get the exam
    exam = Exam.query.get(submission.exam_id)
    
    # Get course info
    exam.course = Course.query.get(exam.course_id)
    
    # Get questions for this exam
    questions = Question.query.filter_by(exam_id=exam.id).all()
    
    # Decrypt question data
    for question in questions:
        question.text = decrypt_data(question.text)
        question.id = question.id  # Ensure ID is accessible in template
        
        if question.options:
            question.options = json.loads(decrypt_data(question.options))
    
    # Add questions to exam object for template access
    exam.questions = questions
    
    # Get answer submissions
    answer_submissions = Answer.query.filter_by(submission_id=submission_id).all()
    
    # Process answers and results
    submission.answers = {}
    submission.results = {}
    
    for answer in answer_submissions:
        # Decrypt answer
        decrypted_answer = decrypt_data(answer.text)
        submission.answers[str(answer.question_id)] = decrypted_answer
        
        # Decrypt results if available
        if answer.feedback:
            results = json.loads(decrypt_data(answer.feedback))
            submission.results[str(answer.question_id)] = results
    
    # Check if review can be requested (e.g., within 7 days of submission)
    start_time = submission.start_time
    current_date = datetime.now()
    days_since_submission = (current_date - start_time).days
    
    submission.can_request_review = days_since_submission <= 7
    
    return render_template('student_exam_results.html', 
                          submission=submission, 
                          exam=exam, 
                          user=session['user'])

@exam_bp.route('/student/exams/<int:submission_id>/request-review', methods=['POST'])
def request_review(submission_id):
    """Request a manual review of an exam submission"""
    if 'user' not in session or session['user']['role'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student_id = session['user']['id']
    
    # Get the submission
    submission = ExamSubmission.query.get_or_404(submission_id)
    
    # Check if this student has access to this submission
    if submission.student_id != student_id:
        return jsonify({'success': False, 'message': 'You do not have permission to request a review for this submission.'})
    
    # Check if review can be requested (e.g., within 7 days of submission)
    start_time = submission.start_time
    current_date = datetime.now()
    days_since_submission = (current_date - start_time).days
    
    if days_since_submission > 7:
        return jsonify({'success': False, 'message': 'Review requests must be submitted within 7 days of the exam.'})
    
    # Get request data
    data = request.json
    reason = data.get('reason')
    questions = data.get('questions')
    
    if not reason or not questions:
        return jsonify({'success': False, 'message': 'Missing required data'})
    
    # In a real implementation, this would create a review request record
    # For now, we'll just mark the submission as under review
    submission.review_requested = True
    submission.review_reason = reason
    submission.review_questions = ','.join(questions)
    submission.review_date = current_date
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Review request submitted successfully'
    })
