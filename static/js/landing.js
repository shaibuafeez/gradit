/**
 * Landing page JavaScript for the AES System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in (by looking for user data in the page)
    const userDropdown = document.getElementById('user-dropdown');
    const loginNavItem = document.getElementById('login-nav-item');
    const registerNavItem = document.getElementById('register-nav-item');
    const usernameDisplay = document.getElementById('username-display');
    
    // Handle login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            
            // Create form data
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
            
            // Submit login request
            fetch('/login', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    return response.text();
                }
            })
            .then(data => {
                if (data) {
                    // Show error message
                    const loginErrorElement = document.getElementById('login-error');
                    if (loginErrorElement) {
                        loginErrorElement.textContent = 'Invalid email or password';
                        loginErrorElement.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('Login error:', error);
            });
        });
    }
    
    // Handle registration form submission
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('register-name').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const role = document.querySelector('input[name="register-role"]:checked').value;
            
            // Create form data
            const formData = new FormData();
            formData.append('name', name);
            formData.append('email', email);
            formData.append('password', password);
            formData.append('role', role);
            
            // Submit registration request
            fetch('/register', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to dashboard
                    window.location.href = data.redirect;
                } else {
                    // Show error message
                    const registerErrorElement = document.getElementById('register-error');
                    if (registerErrorElement) {
                        registerErrorElement.textContent = data.message;
                        registerErrorElement.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('Registration error:', error);
            });
        });
    }
    
    // Handle logout
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Submit logout request
            fetch('/logout')
            .then(response => {
                window.location.href = '/';
            })
            .catch(error => {
                console.error('Logout error:', error);
            });
        });
    }
    
    // Handle "Score Essay" button click
    const scoreEssayButtons = document.querySelectorAll('.score-essay-btn');
    scoreEssayButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            window.location.href = '/essay-scorer';
        });
    });
    
    // Handle "Dashboard" link click
    const dashboardLink = document.getElementById('dashboard-link');
    if (dashboardLink) {
        dashboardLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/dashboard';
        });
    }
});
