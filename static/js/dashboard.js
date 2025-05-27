// Dashboard and Course Management

// Open dashboard modal
function openDashboard() {
    // Reset selected course
    selectedCourseId = null;
    
    // Load courses
    loadCourses();
    
    // Show dashboard modal
    $('#dashboardModal').modal('show');
}

// Load courses for the current user
function loadCourses() {
    fetch('/courses')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load courses');
            }
            return response.json();
        })
        .then(data => {
            displayCourses(data.courses);
            
            // Show teacher controls if user is a teacher
            if (currentUser && currentUser.role === 'teacher') {
                document.getElementById('teacher-courses-controls').style.display = 'block';
            } else {
                document.getElementById('teacher-courses-controls').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error loading courses:', error);
            document.getElementById('courses-container').innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Failed to load courses. Please try again later.
                    </div>
                </div>
            `;
        });
}

// Display courses in the dashboard
function displayCourses(courses) {
    const container = document.getElementById('courses-container');
    
    if (courses.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    ${currentUser.role === 'teacher' ? 
                        'You haven\'t created any courses yet. Click "Add New Course" to get started.' : 
                        'You aren\'t enrolled in any courses yet. Contact your teacher to enroll.'}
                </div>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    courses.forEach(course => {
        html += `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0">${course.code}</h5>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">${course.title}</h6>
                        <p class="card-text text-muted small">${course.description || 'No description available'}</p>
                        <div class="d-flex align-items-center mb-3">
                            <span class="badge bg-primary me-2">${course.units} Units</span>
                        </div>
                    </div>
                    <div class="card-footer bg-white">
                        <div class="d-flex justify-content-between">
                            <button class="btn btn-sm btn-outline-primary view-questions-btn" data-course-id="${course.id}">
                                <i class="fas fa-question-circle me-1"></i> Questions
                            </button>
                            <button class="btn btn-sm btn-outline-primary view-exams-btn" data-course-id="${course.id}">
                                <i class="fas fa-file-alt me-1"></i> Exams
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Add event listeners to buttons
    document.querySelectorAll('.view-questions-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            selectedCourseId = courseId;
            loadQuestions(courseId);
            document.getElementById('questions-tab').click();
        });
    });
    
    document.querySelectorAll('.view-exams-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            selectedCourseId = courseId;
            loadExams(courseId);
            document.getElementById('exams-tab').click();
        });
    });
}

// Handle adding a new course
function handleAddCourse(e) {
    e.preventDefault();
    
    const code = document.getElementById('course-code').value;
    const title = document.getElementById('course-title').value;
    const description = document.getElementById('course-description').value;
    const units = parseInt(document.getElementById('course-units').value);
    
    fetch('/courses', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code, title, description, units })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            // Show error message
            const errorElement = document.getElementById('add-course-error');
            errorElement.textContent = data.error;
            errorElement.style.display = 'block';
        } else {
            // Course added successfully
            $('#addCourseModal').modal('hide');
            
            // Reset form
            document.getElementById('add-course-form').reset();
            document.getElementById('add-course-error').style.display = 'none';
            
            // Reload courses
            loadCourses();
        }
    })
    .catch(error => {
        console.error('Error adding course:', error);
    });
}

// Load questions for a course
function loadQuestions(courseId) {
    // Show questions tab
    document.getElementById('questions-tab-item').style.display = 'block';
    
    // Show teacher controls if user is a teacher
    if (currentUser && currentUser.role === 'teacher') {
        document.getElementById('teacher-questions-controls').style.display = 'block';
    } else {
        document.getElementById('teacher-questions-controls').style.display = 'none';
    }
    
    fetch(`/courses/${courseId}/questions`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load questions');
            }
            return response.json();
        })
        .then(data => {
            displayQuestions(data.questions);
        })
        .catch(error => {
            console.error('Error loading questions:', error);
            document.getElementById('questions-container').innerHTML = `
                <div class="alert alert-danger">
                    Failed to load questions. Please try again later.
                </div>
            `;
        });
}

// Display questions for a course
function displayQuestions(questions) {
    const container = document.getElementById('questions-container');
    
    if (questions.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                ${currentUser.role === 'teacher' ? 
                    'No questions have been added yet. Click "Add New Question" to get started.' : 
                    'No questions are available for this course yet.'}
            </div>
        `;
        return;
    }
    
    let html = '';
    
    questions.forEach((question, index) => {
        html += `
            <div class="card mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Question ${index + 1}</h6>
                    ${currentUser.role === 'teacher' ? `
                        <button class="btn btn-sm btn-outline-primary add-subquestion-btn" data-question-id="${question.id}">
                            <i class="fas fa-plus me-1"></i> Add Sub-question
                        </button>
                    ` : ''}
                </div>
                <div class="card-body">
                    <p>${question.text}</p>
                    ${currentUser.role === 'teacher' ? `
                        <div class="card mb-3">
                            <div class="card-header bg-light">
                                <h6 class="mb-0 small">Marking Guide</h6>
                            </div>
                            <div class="card-body">
                                <p class="small">${question.marking_guide}</p>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${question.sub_questions.length > 0 ? `
                        <div class="mt-3">
                            <h6>Sub-questions:</h6>
                            <div class="ps-4">
                                ${question.sub_questions.map((subQ, subIndex) => `
                                    <div class="card mb-2">
                                        <div class="card-header bg-light">
                                            <h6 class="mb-0 small">Sub-question ${subIndex + 1}</h6>
                                        </div>
                                        <div class="card-body">
                                            <p>${subQ.text}</p>
                                            ${currentUser.role === 'teacher' ? `
                                                <div class="card">
                                                    <div class="card-header bg-light">
                                                        <h6 class="mb-0 small">Marking Guide</h6>
                                                    </div>
                                                    <div class="card-body">
                                                        <p class="small">${subQ.marking_guide}</p>
                                                    </div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Add event listeners for sub-question buttons
    if (currentUser.role === 'teacher') {
        document.querySelectorAll('.add-subquestion-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const questionId = this.getAttribute('data-question-id');
                document.getElementById('question-course-id').value = selectedCourseId;
                document.getElementById('question-parent-id').value = questionId;
                $('#addQuestionModal').modal('show');
            });
        });
    }
}

// Handle adding a new question
function handleAddQuestion(e) {
    e.preventDefault();
    
    const courseId = document.getElementById('question-course-id').value;
    const parentId = document.getElementById('question-parent-id').value || null;
    const text = document.getElementById('question-text').value;
    const markingGuide = document.getElementById('question-marking-guide').value;
    
    fetch(`/courses/${courseId}/questions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            text, 
            marking_guide: markingGuide,
            parent_id: parentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            // Show error message
            const errorElement = document.getElementById('add-question-error');
            errorElement.textContent = data.error;
            errorElement.style.display = 'block';
        } else {
            // Question added successfully
            $('#addQuestionModal').modal('hide');
            
            // Reset form
            document.getElementById('add-question-form').reset();
            document.getElementById('add-question-error').style.display = 'none';
            
            // Reload questions
            loadQuestions(courseId);
        }
    })
    .catch(error => {
        console.error('Error adding question:', error);
    });
}
