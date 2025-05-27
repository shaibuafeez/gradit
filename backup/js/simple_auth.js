// Simple Authentication for the AES System

document.addEventListener('DOMContentLoaded', function() {
    // Setup event listeners for authentication
    setupAuthListeners();
});

function setupAuthListeners() {
    // Login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            
            // Show loading indicator
            const loginButton = loginForm.querySelector('button[type="submit"]');
            const originalText = loginButton.innerHTML;
            loginButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';
            loginButton.disabled = true;
            
            // Send login request
            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            })
            .then(response => response.json())
            .then(data => {
                // Reset button
                loginButton.innerHTML = originalText;
                loginButton.disabled = false;
                
                if (data.error) {
                    // Show error message
                    const errorElement = document.getElementById('login-error');
                    errorElement.textContent = data.error;
                    errorElement.style.display = 'block';
                } else {
                    // Login successful
                    console.log('Login successful:', data);
                    
                    // Hide modal
                    const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
                    if (loginModal) {
                        loginModal.hide();
                    }
                    
                    // Update UI for logged in user
                    updateUIForLoggedInUser(data.user);
                    
                    // Reset form
                    loginForm.reset();
                    const errorElement = document.getElementById('login-error');
                    if (errorElement) {
                        errorElement.style.display = 'none';
                    }
                    
                    // Show dashboard
                    setTimeout(() => {
                        const dashboardModal = new bootstrap.Modal(document.getElementById('dashboardModal'));
                        dashboardModal.show();
                        
                        // Load courses for the dashboard
                        loadUserCourses();
                    }, 500);
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                loginButton.innerHTML = originalText;
                loginButton.disabled = false;
                
                const errorElement = document.getElementById('login-error');
                errorElement.textContent = 'An error occurred. Please try again.';
                errorElement.style.display = 'block';
            });
        });
    }
    
    // Register form submission
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('register-name').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const role = document.getElementById('register-role').value;
            const matricNumber = document.getElementById('register-matric').value;
            
            // Validate matric number for students
            if (role === 'student' && !matricNumber) {
                const errorElement = document.getElementById('register-error');
                errorElement.textContent = 'Matric number is required for students';
                errorElement.style.display = 'block';
                return;
            }
            
            // Show loading indicator
            const registerButton = registerForm.querySelector('button[type="submit"]');
            const originalText = registerButton.innerHTML;
            registerButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...';
            registerButton.disabled = true;
            
            // Send registration request
            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    name, 
                    email, 
                    password, 
                    role, 
                    matric_number: matricNumber 
                })
            })
            .then(response => response.json())
            .then(data => {
                // Reset button
                registerButton.innerHTML = originalText;
                registerButton.disabled = false;
                
                if (data.error) {
                    // Show error message
                    const errorElement = document.getElementById('register-error');
                    errorElement.textContent = data.error;
                    errorElement.style.display = 'block';
                } else {
                    // Registration successful
                    const registerModal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
                    if (registerModal) {
                        registerModal.hide();
                    }
                    
                    // Show success message and prompt to login
                    alert('Registration successful! Please login with your credentials.');
                    
                    // Show login modal
                    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
                    loginModal.show();
                    
                    // Reset form
                    registerForm.reset();
                    const errorElement = document.getElementById('register-error');
                    if (errorElement) {
                        errorElement.style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.error('Registration error:', error);
                registerButton.innerHTML = originalText;
                registerButton.disabled = false;
                
                const errorElement = document.getElementById('register-error');
                errorElement.textContent = 'An error occurred. Please try again.';
                errorElement.style.display = 'block';
            });
        });
    }
    
    // Role selection in registration
    const roleSelect = document.getElementById('register-role');
    if (roleSelect) {
        roleSelect.addEventListener('change', function() {
            const matricGroup = document.getElementById('matric-number-group');
            if (this.value === 'student') {
                matricGroup.style.display = 'block';
            } else {
                matricGroup.style.display = 'none';
            }
        });
    }
    
    // Logout link
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/logout', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                // Update UI for logged out user
                updateUIForLoggedOutUser();
                
                // Close any open modals
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modalEl => {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) {
                        modal.hide();
                    }
                });
            })
            .catch(error => {
                console.error('Logout error:', error);
            });
        });
    }
    
    // Dashboard link
    const dashboardLink = document.getElementById('dashboard-link');
    if (dashboardLink) {
        dashboardLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show dashboard modal
            const dashboardModal = new bootstrap.Modal(document.getElementById('dashboardModal'));
            dashboardModal.show();
            
            // Load courses for the dashboard
            loadUserCourses();
        });
    }
    
    // Check auth status on page load
    checkAuthStatus();
}

function updateUIForLoggedInUser(user) {
    // Hide login/register buttons
    const loginNavItem = document.getElementById('login-nav-item');
    const registerNavItem = document.getElementById('register-nav-item');
    if (loginNavItem) loginNavItem.style.display = 'none';
    if (registerNavItem) registerNavItem.style.display = 'none';
    
    // Show user dropdown
    const userDropdown = document.getElementById('user-dropdown');
    const usernameDisplay = document.getElementById('username-display');
    if (userDropdown) userDropdown.style.display = 'block';
    if (usernameDisplay) usernameDisplay.textContent = user.name;
    
    // Store user info
    window.currentUser = user;
}

function updateUIForLoggedOutUser() {
    // Show login/register buttons
    const loginNavItem = document.getElementById('login-nav-item');
    const registerNavItem = document.getElementById('register-nav-item');
    if (loginNavItem) loginNavItem.style.display = 'block';
    if (registerNavItem) registerNavItem.style.display = 'block';
    
    // Hide user dropdown
    const userDropdown = document.getElementById('user-dropdown');
    if (userDropdown) userDropdown.style.display = 'none';
    
    // Clear user info
    window.currentUser = null;
}

function checkAuthStatus() {
    fetch('/user')
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Not authenticated');
            }
        })
        .then(data => {
            // User is logged in
            updateUIForLoggedInUser(data.user);
        })
        .catch(error => {
            // User is not logged in
            updateUIForLoggedOutUser();
        });
}

function loadUserCourses() {
    // Only load courses if user is logged in
    if (!window.currentUser) return;
    
    const coursesList = document.getElementById('courses-list');
    if (!coursesList) return;
    
    // Show loading indicator
    coursesList.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading courses...</p>
        </div>
    `;
    
    // Fetch courses
    fetch('/courses')
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Failed to load courses');
            }
        })
        .then(data => {
            if (data.courses && data.courses.length > 0) {
                // Display courses
                let html = '';
                data.courses.forEach(course => {
                    html += `
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <h5 class="card-title">${course.title}</h5>
                                        <h6 class="card-subtitle mb-2 text-muted">${course.code} (${course.units} units)</h6>
                                        <p class="card-text">${course.description || 'No description available'}</p>
                                    </div>
                                    <div>
                                        <button class="btn btn-primary view-course-btn" data-course-id="${course.id}">
                                            <i class="fas fa-eye me-1"></i> View
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer bg-transparent">
                                <small class="text-muted">
                                    <i class="fas fa-users me-1"></i> ${course.student_count} students
                                    <span class="ms-3 badge ${course.role === 'teacher' ? 'bg-danger' : 'bg-success'}">${course.role}</span>
                                </small>
                            </div>
                        </div>
                    `;
                });
                coursesList.innerHTML = html;
                
                // Add event listeners to view buttons
                document.querySelectorAll('.view-course-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        const courseId = this.getAttribute('data-course-id');
                        viewCourse(courseId);
                    });
                });
            } else {
                // No courses
                coursesList.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        ${window.currentUser.role === 'teacher' ? 
                            'You have not created any courses yet. Click the "Add Course" button to create your first course.' : 
                            'You are not enrolled in any courses yet.'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading courses:', error);
            coursesList.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Failed to load courses. Please try again.
                </div>
            `;
        });
}

function viewCourse(courseId) {
    // Store selected course ID
    window.selectedCourseId = courseId;
    
    // Close dashboard modal
    const dashboardModal = bootstrap.Modal.getInstance(document.getElementById('dashboardModal'));
    if (dashboardModal) {
        dashboardModal.hide();
    }
    
    // Show course modal
    const courseModal = new bootstrap.Modal(document.getElementById('courseModal'));
    courseModal.show();
    
    // Load course details
    loadCourseDetails(courseId);
}

function loadCourseDetails(courseId) {
    // Placeholder function - in a real app, this would load course details from the server
    const courseTitle = document.getElementById('course-title');
    const courseContent = document.getElementById('course-content');
    
    if (courseTitle && courseContent) {
        courseTitle.textContent = 'Loading course...';
        courseContent.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading course details...</p>
            </div>
        `;
        
        // In a real app, this would fetch course details from the server
        // For now, just show a placeholder
        setTimeout(() => {
            courseTitle.textContent = 'Course Details';
            courseContent.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    This is a simplified version of the course view. In the full application, you would see:
                    <ul class="mt-2">
                        <li>Course details and description</li>
                        <li>List of enrolled students (for teachers)</li>
                        <li>Course materials and resources</li>
                        <li>Exams and assignments</li>
                        <li>Discussion forums</li>
                    </ul>
                </div>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">Exams</h5>
                    </div>
                    <div class="card-body">
                        <p>No exams available for this course yet.</p>
                        ${window.currentUser && window.currentUser.role === 'teacher' ? 
                            '<button class="btn btn-primary btn-sm"><i class="fas fa-plus me-1"></i> Create Exam</button>' : 
                            ''}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Questions</h5>
                    </div>
                    <div class="card-body">
                        <p>No questions available for this course yet.</p>
                        ${window.currentUser && window.currentUser.role === 'teacher' ? 
                            '<button class="btn btn-primary btn-sm"><i class="fas fa-plus me-1"></i> Add Question</button>' : 
                            ''}
                    </div>
                </div>
            `;
        }, 1000);
    }
}
