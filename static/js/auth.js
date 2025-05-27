// Authentication and User Management

// Global variables
let currentUser = null;
let selectedCourseId = null;

// Check if user is logged in on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Auth form submissions
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('logout-link').addEventListener('click', handleLogout);
    
    // Demo account buttons
    const studentDemoBtn = document.getElementById('student-demo-btn');
    const teacherDemoBtn = document.getElementById('teacher-demo-btn');
    
    if (studentDemoBtn) {
        studentDemoBtn.addEventListener('click', function() {
            console.log('Student demo button clicked');
            document.getElementById('login-email').value = 'student@example.com';
            document.getElementById('login-password').value = 'password123';
            
            // Login directly instead of form submission
            loginWithCredentials('student@example.com', 'password123');
        });
    }
    
    if (teacherDemoBtn) {
        teacherDemoBtn.addEventListener('click', function() {
            console.log('Teacher demo button clicked');
            document.getElementById('login-email').value = 'teacher@example.com';
            document.getElementById('login-password').value = 'password123';
            
            // Login directly instead of form submission
            loginWithCredentials('teacher@example.com', 'password123');
        });
    }
    
    // Helper function for demo logins
    function loginWithCredentials(email, password) {
        console.log('Logging in with demo credentials:', email);
        
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                // Show error message
                const errorElement = document.getElementById('login-error');
                errorElement.textContent = data.error;
                errorElement.style.display = 'block';
            } else {
                // Login successful
                // Hide modal using Bootstrap directly if jQuery is not available
                const loginModal = document.getElementById('loginModal');
                if (loginModal) {
                    const modal = bootstrap.Modal.getInstance(loginModal);
                    if (modal) modal.hide();
                }
                
                // Redirect to dashboard
                window.location.href = data.redirect;
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            // Show generic error message
            const errorElement = document.getElementById('login-error');
            errorElement.textContent = 'An error occurred during login. Please try again.';
            errorElement.style.display = 'block';
        });
    }
    
    // Role selection in registration
    document.getElementById('register-role').addEventListener('change', function() {
        const matricGroup = document.getElementById('matric-number-group');
        if (this.value === 'student') {
            matricGroup.style.display = 'block';
        } else {
            matricGroup.style.display = 'none';
        }
    });
    
    // Dashboard link
    document.getElementById('dashboard-link').addEventListener('click', function(e) {
        e.preventDefault();
        openDashboard();
    });
    
    // Add event listeners only if elements exist
    const addCourseBtn = document.getElementById('add-course-btn');
    if (addCourseBtn) {
        addCourseBtn.addEventListener('click', function() {
            const modal = document.getElementById('addCourseModal');
            if (modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    }
    
    const addCourseForm = document.getElementById('add-course-form');
    if (addCourseForm) {
        addCourseForm.addEventListener('submit', handleAddCourse);
    }
    
    // Question management
    const addQuestionBtn = document.getElementById('add-question-btn');
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', function() {
            const questionCourseId = document.getElementById('question-course-id');
            const questionParentId = document.getElementById('question-parent-id');
            
            if (questionCourseId) questionCourseId.value = selectedCourseId;
            if (questionParentId) questionParentId.value = '';
            
            const modal = document.getElementById('addQuestionModal');
            if (modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    }
    
    const addQuestionForm = document.getElementById('add-question-form');
    if (addQuestionForm) {
        addQuestionForm.addEventListener('submit', handleAddQuestion);
    }
    
    // Exam management
    const createExamBtn = document.getElementById('create-exam-btn');
    if (createExamBtn) {
        createExamBtn.addEventListener('click', function() {
            const examCourseId = document.getElementById('exam-course-id');
            if (examCourseId) examCourseId.value = selectedCourseId;
            
            if (typeof loadQuestionsForExam === 'function') {
                loadQuestionsForExam(selectedCourseId);
            }
            
            const modal = document.getElementById('createExamModal');
            if (modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    }
    
    const createExamForm = document.getElementById('create-exam-form');
    if (createExamForm) {
        createExamForm.addEventListener('submit', handleCreateExam);
    }
    
    const takeExamForm = document.getElementById('take-exam-form');
    if (takeExamForm) {
        takeExamForm.addEventListener('submit', handleSubmitExam);
    }
}

// Check authentication status
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
            currentUser = data.user;
            updateUIForLoggedInUser();
        })
        .catch(error => {
            // User is not logged in
            currentUser = null;
            updateUIForLoggedOutUser();
        });
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    // Hide login/register buttons
    document.getElementById('login-nav-item').style.display = 'none';
    document.getElementById('register-nav-item').style.display = 'none';
    
    // Show user dropdown
    const userDropdown = document.getElementById('user-dropdown');
    userDropdown.style.display = 'block';
    document.getElementById('username-display').textContent = currentUser.name;
}

// Update UI for logged out user
function updateUIForLoggedOutUser() {
    // Show login/register buttons
    document.getElementById('login-nav-item').style.display = 'block';
    document.getElementById('register-nav-item').style.display = 'block';
    
    // Hide user dropdown
    document.getElementById('user-dropdown').style.display = 'none';
}

// Handle login form submission
function handleLogin(e) {
    e.preventDefault();
    
    // Show loading state
    const loginButton = document.querySelector('.login-btn');
    const originalButtonText = loginButton.innerHTML;
    loginButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';
    loginButton.disabled = true;
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    // Clear previous errors
    const errorElement = document.getElementById('login-error');
    errorElement.style.display = 'none';
    
    // Use JSON format for the request
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        loginButton.innerHTML = originalButtonText;
        loginButton.disabled = false;
        
        if (!data.success) {
            // Show error message
            errorElement.textContent = data.error;
            errorElement.style.display = 'block';
        } else {
            // Login successful
            // Hide modal using Bootstrap
            const loginModal = document.getElementById('loginModal');
            if (loginModal) {
                const modal = bootstrap.Modal.getInstance(loginModal);
                if (modal) modal.hide();
            }
            
            // Update user state
            currentUser = data.user;
            updateUIForLoggedInUser();
            
            // Reset form
            document.getElementById('login-form').reset();
            
            // Update username display
            const usernameDisplay = document.getElementById('username-display');
            if (usernameDisplay && data.user && data.user.name) {
                usernameDisplay.textContent = data.user.name;
            }
            
            // Redirect to dashboard
            window.location.href = data.redirect;
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        // Reset button state
        loginButton.innerHTML = originalButtonText;
        loginButton.disabled = false;
        // Show generic error
        errorElement.textContent = 'An error occurred during login. Please try again.';
        errorElement.style.display = 'block';
    });
}

// Handle registration form submission
function handleRegister(e) {
    e.preventDefault();
    
    // Show loading state
    const registerButton = document.querySelector('#register-form button[type="submit"]');
    const originalButtonText = registerButton.innerHTML;
    registerButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...';
    registerButton.disabled = true;
    
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const role = document.getElementById('register-role').value;
    const matric = document.getElementById('register-matric').value;
    
    // Clear previous errors
    const errorElement = document.getElementById('register-error');
    errorElement.style.display = 'none';
    
    // Validate matric number for students
    if (role === 'student' && !matric) {
        errorElement.textContent = 'Matric number is required for students';
        errorElement.style.display = 'block';
        registerButton.innerHTML = originalButtonText;
        registerButton.disabled = false;
        return;
    }
    
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ 
            name, 
            email, 
            password, 
            role, 
            matric
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        registerButton.innerHTML = originalButtonText;
        registerButton.disabled = false;
        
        if (!data.success) {
            // Show error message
            errorElement.textContent = data.error;
            errorElement.style.display = 'block';
        } else {
            // Registration successful
            // If auto-login is enabled, update current user
            if (data.user) {
                currentUser = data.user;
                updateUIForLoggedInUser();
                
                // Update username display
                const usernameDisplay = document.getElementById('username-display');
                if (usernameDisplay && data.user.name) {
                    usernameDisplay.textContent = data.user.name;
                }
                
                // Hide registration modal
                const registerModal = document.getElementById('registerModal');
                if (registerModal) {
                    const modal = bootstrap.Modal.getInstance(registerModal);
                    if (modal) modal.hide();
                }
                
                // Redirect to dashboard
                window.location.href = data.redirect;
            } else {
                // Hide registration modal
                const registerModal = document.getElementById('registerModal');
                if (registerModal) {
                    const modal = bootstrap.Modal.getInstance(registerModal);
                    if (modal) modal.hide();
                }
                
                // Show success message and prompt to login
                alert('Registration successful! Please login with your credentials.');
                
                // Show login modal
                const loginModal = document.getElementById('loginModal');
                if (loginModal) {
                    const modal = new bootstrap.Modal(loginModal);
                    modal.show();
                }
            }
            
            // Reset form
            document.getElementById('register-form').reset();
        }
    })
    .catch(error => {
        console.error('Registration error:', error);
        // Reset button state
        registerButton.innerHTML = originalButtonText;
        registerButton.disabled = false;
        // Show generic error
        errorElement.textContent = 'An error occurred during registration. Please try again.';
        errorElement.style.display = 'block';
    });
}

// Handle logout
function handleLogout(e) {
    e.preventDefault();
    
    // Show loading state on logout link
    const logoutLink = document.getElementById('logout-link');
    const originalText = logoutLink.innerHTML;
    logoutLink.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging out...';
    logoutLink.style.pointerEvents = 'none';
    
    fetch('/logout', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Reset user state
        currentUser = null;
        updateUIForLoggedOutUser();
        
        // Redirect to home page
        if (data.redirect) {
            window.location.href = data.redirect;
        } else {
            window.location.href = '/';
        }
    })
    .catch(error => {
        console.error('Logout error:', error);
        // Reset logout link
        logoutLink.innerHTML = originalText;
        logoutLink.style.pointerEvents = 'auto';
        // Fallback redirect
        window.location.href = '/';
    });
}
