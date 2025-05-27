/**
 * JavaScript for the Essay Scorer page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const essayForm = document.getElementById('essay-form');
    const essayText = document.getElementById('essay-text');
    const promptText = document.getElementById('prompt-text');
    const feedbackCard = document.getElementById('feedback-card');
    const scoreDisplay = document.getElementById('score-display');
    const totalPoints = document.getElementById('total-points');
    const strengthsList = document.getElementById('strengths-list');
    const improvementsList = document.getElementById('improvements-list');
    const overallFeedback = document.getElementById('overall-feedback');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorAlert = document.getElementById('error-alert');
    const errorMessage = document.getElementById('error-message');
    const newEssayBtn = document.getElementById('newEssayBtn');
    
    // Teacher grading elements (may not exist if user is not a teacher)
    const teacherGradingForm = document.getElementById('teacher-grading-form');
    const teacherScore = teacherGradingForm ? document.getElementById('teacher-score') : null;
    const teacherFeedback = teacherGradingForm ? document.getElementById('teacher-feedback') : null;
    
    // Handle essay form submission
    if (essayForm) {
        essayForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            loadingSpinner.style.display = 'block';
            feedbackCard.style.display = 'none';
            errorAlert.style.display = 'none';
            
            // Get essay text and prompt
            const essay = essayText.value.trim();
            const prompt = promptText.value.trim();
            
            if (!essay) {
                errorMessage.textContent = 'Please enter your essay text';
                errorAlert.style.display = 'block';
                loadingSpinner.style.display = 'none';
                return;
            }
            
            // Score the essay using the API
            fetch('/api/score-essay', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    essay: essay,
                    prompt: prompt
                })
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                loadingSpinner.style.display = 'none';
                
                // Check if there's an error
                if (data.error) {
                    errorMessage.textContent = data.message || 'An error occurred while scoring the essay';
                    errorAlert.style.display = 'block';
                    return;
                }
                
                // Display the results
                displayResults(data);
                
                // Show teacher grading form if it exists
                if (teacherGradingForm) {
                    teacherGradingForm.parentElement.style.display = 'block';
                    // Pre-fill with AI score
                    teacherScore.value = Math.round(data.total_points);
                }
            })
            .catch(error => {
                // Hide loading spinner
                loadingSpinner.style.display = 'none';
                
                // Show error
                errorMessage.textContent = 'An error occurred while communicating with the server';
                errorAlert.style.display = 'block';
                console.error('Error:', error);
            });
        });
    }
    
    // Handle teacher grading form submission
    if (teacherGradingForm) {
        teacherGradingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const score = teacherScore.value;
            const feedback = teacherFeedback.value;
            const essay = essayText.value;
            const prompt = promptText.value;
            
            // Save the grade
            fetch('/api/save-grade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    essay: essay,
                    prompt: prompt,
                    score: score,
                    feedback: feedback
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Grade saved successfully!');
                } else {
                    alert('Error saving grade: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                alert('Error saving grade. Please try again.');
                console.error('Error:', error);
            });
        });
    }
    
    // Handle "Score Another Essay" button
    if (newEssayBtn) {
        newEssayBtn.addEventListener('click', function() {
            // Reset the form
            essayForm.reset();
            
            // Hide results
            feedbackCard.style.display = 'none';
            errorAlert.style.display = 'none';
            
            // Hide teacher grading form if it exists
            if (teacherGradingForm) {
                teacherGradingForm.parentElement.style.display = 'none';
            }
            
            // Focus on the prompt field
            promptText.focus();
        });
    }
    
    // Function to display the results
    function displayResults(data) {
        // Update score display
        const scorePercent = Math.round(data.overall_score * 100);
        scoreDisplay.textContent = scorePercent + '%';
        totalPoints.textContent = data.total_points + ' / ' + data.max_points;
        
        // Update strengths list
        strengthsList.innerHTML = '';
        data.strengths.forEach(strength => {
            const li = document.createElement('li');
            li.className = 'list-group-item strength-item';
            li.innerHTML = `<i class="fas fa-check-circle text-success me-2"></i>${strength}`;
            strengthsList.appendChild(li);
        });
        
        // Update areas for improvement list
        improvementsList.innerHTML = '';
        data.areas_for_improvement.forEach(improvement => {
            const li = document.createElement('li');
            li.className = 'list-group-item improvement-item';
            li.innerHTML = `<i class="fas fa-exclamation-circle text-warning me-2"></i>${improvement}`;
            improvementsList.appendChild(li);
        });
        
        // Update overall feedback
        overallFeedback.textContent = data.overall_feedback;
        
        // Show the feedback card
        feedbackCard.style.display = 'block';
        
        // Scroll to the feedback card
        feedbackCard.scrollIntoView({ behavior: 'smooth' });
    }
});
