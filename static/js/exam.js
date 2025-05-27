// Exam Management and Grading

// Load exams for a course
function loadExams(courseId) {
    // Show exams tab
    document.getElementById('exams-tab-item').style.display = 'block';
    
    // Show teacher controls if user is a teacher
    if (currentUser && currentUser.role === 'teacher') {
        document.getElementById('teacher-exams-controls').style.display = 'block';
    } else {
        document.getElementById('teacher-exams-controls').style.display = 'none';
    }
    
    fetch(`/courses/${courseId}/exams`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load exams');
            }
            return response.json();
        })
        .then(data => {
            displayExams(data.exams, courseId);
        })
        .catch(error => {
            console.error('Error loading exams:', error);
            document.getElementById('exams-container').innerHTML = `
                <div class="alert alert-danger">
                    Failed to load exams. Please try again later.
                </div>
            `;
        });
}

// Display exams for a course
function displayExams(exams, courseId) {
    const container = document.getElementById('exams-container');
    
    if (exams.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                ${currentUser.role === 'teacher' ? 
                    'No exams have been created yet. Click "Create New Exam" to get started.' : 
                    'No exams are available for this course yet.'}
            </div>
        `;
        return;
    }
    
    let html = '';
    
    if (currentUser.role === 'teacher') {
        // Teacher view
        html = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Submissions</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${exams.map(exam => `
                        <tr>
                            <td>${exam.title}</td>
                            <td>${exam.duration_minutes} minutes</td>
                            <td>
                                <span class="badge ${exam.is_active ? 'bg-success' : 'bg-secondary'}">
                                    ${exam.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                            <td>${exam.submission_count || 0}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary toggle-exam-btn" data-exam-id="${exam.id}" data-active="${exam.is_active}">
                                    ${exam.is_active ? 'Deactivate' : 'Activate'}
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else {
        // Student view
        html = `
            <div class="row">
                ${exams.map(exam => `
                    <div class="col-md-6 col-lg-4 mb-4">
                        <div class="card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">${exam.title}</h5>
                                <span class="badge bg-success">Active</span>
                            </div>
                            <div class="card-body">
                                <p class="card-text">${exam.description || 'No description available'}</p>
                                <div class="d-flex align-items-center mb-3">
                                    <i class="fas fa-clock me-2 text-muted"></i>
                                    <span>${exam.duration_minutes} minutes</span>
                                </div>
                            </div>
                            <div class="card-footer bg-white">
                                <div class="d-grid">
                                    <button class="btn btn-primary start-exam-btn" data-exam-id="${exam.id}">
                                        <i class="fas fa-play me-1"></i> Start Exam
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    container.innerHTML = html;
    
    // Add event listeners
    if (currentUser.role === 'teacher') {
        document.querySelectorAll('.toggle-exam-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const examId = this.getAttribute('data-exam-id');
                const isActive = this.getAttribute('data-active') === 'true';
                toggleExamStatus(examId, !isActive, courseId);
            });
        });
    } else {
        document.querySelectorAll('.start-exam-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const examId = this.getAttribute('data-exam-id');
                startExam(examId);
            });
        });
    }
}

// Load questions for creating an exam
function loadQuestionsForExam(courseId) {
    const container = document.getElementById('exam-questions-container');
    
    fetch(`/courses/${courseId}/questions`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load questions');
            }
            return response.json();
        })
        .then(data => {
            if (data.questions.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        No questions available. Please add questions to this course first.
                    </div>
                `;
                return;
            }
            
            let html = '';
            
            data.questions.forEach((question, index) => {
                html += `
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" value="${question.id}" id="question-${question.id}" name="exam-questions">
                        <label class="form-check-label" for="question-${question.id}">
                            ${question.text.substring(0, 100)}${question.text.length > 100 ? '...' : ''}
                        </label>
                    </div>
                `;
                
                // Add sub-questions if any
                if (question.sub_questions && question.sub_questions.length > 0) {
                    html += '<div class="ms-4">';
                    question.sub_questions.forEach((subQ, subIndex) => {
                        html += `
                            <div class="form-check mb-2">
                                <input class="form-check-input" type="checkbox" value="${subQ.id}" id="question-${subQ.id}" name="exam-questions">
                                <label class="form-check-label" for="question-${subQ.id}">
                                    <small class="text-muted">Sub-question:</small> ${subQ.text.substring(0, 100)}${subQ.text.length > 100 ? '...' : ''}
                                </label>
                            </div>
                        `;
                    });
                    html += '</div>';
                }
            });
            
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading questions for exam:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load questions. Please try again later.
                </div>
            `;
        });
}

// Handle creating a new exam
function handleCreateExam(e) {
    e.preventDefault();
    
    const courseId = document.getElementById('exam-course-id').value;
    const title = document.getElementById('exam-title').value;
    const description = document.getElementById('exam-description').value;
    const durationMinutes = parseInt(document.getElementById('exam-duration').value);
    const isActive = document.getElementById('exam-active').checked;
    
    // Get selected questions
    const selectedQuestions = Array.from(
        document.querySelectorAll('input[name="exam-questions"]:checked')
    ).map(input => parseInt(input.value));
    
    if (selectedQuestions.length === 0) {
        const errorElement = document.getElementById('create-exam-error');
        errorElement.textContent = 'Please select at least one question';
        errorElement.style.display = 'block';
        return;
    }
    
    fetch(`/courses/${courseId}/exams`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title,
            description,
            duration_minutes: durationMinutes,
            is_active: isActive,
            question_ids: selectedQuestions
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            // Show error message
            const errorElement = document.getElementById('create-exam-error');
            errorElement.textContent = data.error;
            errorElement.style.display = 'block';
        } else {
            // Exam created successfully
            $('#createExamModal').modal('hide');
            
            // Reset form
            document.getElementById('create-exam-form').reset();
            document.getElementById('create-exam-error').style.display = 'none';
            
            // Reload exams
            loadExams(courseId);
        }
    })
    .catch(error => {
        console.error('Error creating exam:', error);
    });
}

// Toggle exam active status
function toggleExamStatus(examId, active, courseId) {
    // This would be implemented in a real application
    // For this demo, we'll just reload the exams
    loadExams(courseId);
}

// Start an exam
function startExam(examId) {
    fetch(`/exams/${examId}/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Store submission ID
        document.getElementById('exam-submission-id').value = data.submission_id;
        
        // Set exam title
        document.getElementById('takeExamModalLabel').textContent = 'Exam';
        
        // Set instructions based on number of questions to answer
        const instructionText = document.getElementById('exam-instruction-text');
        instructionText.textContent = `Please answer at least ${data.num_to_answer} out of ${data.questions.length} questions within the time limit.`;
        
        // Display questions
        displayExamQuestions(data.questions, data.num_to_answer);
        
        // Start timer
        startExamTimer(data.duration_minutes, data.start_time);
        
        // Show exam modal
        $('#takeExamModal').modal('show');
    })
    .catch(error => {
        console.error('Error starting exam:', error);
        alert('Failed to start exam. Please try again later.');
    });
}

// Display exam questions
function displayExamQuestions(questions, numToAnswer) {
    const container = document.getElementById('exam-questions');
    
    let html = `
        <div class="alert alert-warning mb-4">
            <i class="fas fa-exclamation-triangle me-2"></i>
            You must answer at least <strong>${numToAnswer}</strong> questions.
        </div>
    `;
    
    questions.forEach((question, index) => {
        html += `
            <div class="card mb-4 question-card">
                <div class="card-header">
                    <h5 class="mb-0">Question ${index + 1}</h5>
                </div>
                <div class="card-body">
                    <p class="mb-3">${question.text}</p>
                    <div class="mb-3">
                        <label for="answer-${question.id}" class="form-label">Your Answer:</label>
                        <textarea class="form-control answer-textarea" id="answer-${question.id}" 
                            data-question-id="${question.id}" rows="5" placeholder="Type your answer here..."></textarea>
                    </div>
                    
                    ${question.sub_questions.length > 0 ? `
                        <div class="mt-4">
                            <h6>Sub-questions:</h6>
                            ${question.sub_questions.map((subQ, subIndex) => `
                                <div class="card mb-3">
                                    <div class="card-header bg-light">
                                        <h6 class="mb-0">Sub-question ${subIndex + 1}</h6>
                                    </div>
                                    <div class="card-body">
                                        <p class="mb-3">${subQ.text}</p>
                                        <div class="mb-3">
                                            <label for="answer-${subQ.id}" class="form-label">Your Answer:</label>
                                            <textarea class="form-control answer-textarea" id="answer-${subQ.id}" 
                                                data-question-id="${subQ.id}" rows="3" placeholder="Type your answer here..."></textarea>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Start exam timer
function startExamTimer(durationMinutes, startTime) {
    const timerDisplay = document.getElementById('exam-timer');
    const startTimeMs = new Date(startTime).getTime();
    const endTimeMs = startTimeMs + (durationMinutes * 60 * 1000);
    
    // Update timer every second
    const timerInterval = setInterval(() => {
        const now = new Date().getTime();
        const timeLeftMs = endTimeMs - now;
        
        if (timeLeftMs <= 0) {
            // Time's up
            clearInterval(timerInterval);
            timerDisplay.textContent = '00:00:00';
            timerDisplay.classList.add('text-danger');
            
            // Auto-submit exam
            alert('Time is up! Your exam will be submitted automatically.');
            document.getElementById('take-exam-form').dispatchEvent(new Event('submit'));
            return;
        }
        
        // Calculate hours, minutes, seconds
        const hours = Math.floor(timeLeftMs / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeftMs % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeftMs % (1000 * 60)) / 1000);
        
        // Display time
        timerDisplay.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Change color when less than 5 minutes left
        if (timeLeftMs < 5 * 60 * 1000) {
            timerDisplay.classList.add('text-danger');
        }
    }, 1000);
    
    // Store interval ID to clear when modal is closed
    $('#takeExamModal').on('hidden.bs.modal', function() {
        clearInterval(timerInterval);
    });
}

// Handle exam submission
function handleSubmitExam(e) {
    e.preventDefault();
    
    const submissionId = document.getElementById('exam-submission-id').value;
    
    // Collect answers
    const answerTextareas = document.querySelectorAll('.answer-textarea');
    const answers = [];
    
    answerTextareas.forEach(textarea => {
        const questionId = textarea.getAttribute('data-question-id');
        const text = textarea.value.trim();
        
        if (text) {
            answers.push({
                question_id: parseInt(questionId),
                text: text
            });
        }
    });
    
    // Submit answers
    fetch(`/exams/submissions/${submissionId}/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ answers })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Hide exam modal
        $('#takeExamModal').modal('hide');
        
        // Show results
        displayExamResults(data);
    })
    .catch(error => {
        console.error('Error submitting exam:', error);
        alert('Failed to submit exam. Please try again.');
    });
}

// Display exam results
function displayExamResults(data) {
    // Set overall grade
    document.getElementById('overall-grade').textContent = `${data.overall_grade.toFixed(1)}%`;
    
    // Display individual question scores
    const scoresContainer = document.getElementById('question-scores-container');
    let html = '';
    
    data.answers.forEach((answer, index) => {
        html += `
            <div class="mb-3 p-3 border rounded ${answer.grade >= 70 ? 'border-success' : answer.grade >= 50 ? 'border-warning' : 'border-danger'}">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">Question ${index + 1}</h6>
                    <span class="badge ${answer.grade >= 70 ? 'bg-success' : answer.grade >= 50 ? 'bg-warning' : 'bg-danger'}">
                        ${answer.grade.toFixed(1)}%
                    </span>
                </div>
                <div class="progress mb-2" style="height: 10px;">
                    <div class="progress-bar ${answer.grade >= 70 ? 'bg-success' : answer.grade >= 50 ? 'bg-warning' : 'bg-danger'}" 
                        role="progressbar" style="width: ${answer.grade}%"></div>
                </div>
                <div class="small text-muted">
                    Similarity score: ${(answer.similarity * 100).toFixed(1)}%
                </div>
            </div>
        `;
    });
    
    scoresContainer.innerHTML = html;
    
    // Show results modal
    $('#examResultsModal').modal('show');
}
