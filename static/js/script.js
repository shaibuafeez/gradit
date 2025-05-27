/**
 * JavaScript for the AES web interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if model is available
    checkModelAvailability();
    
    // Set up event listeners
    setupEssayScoring();
    setupModelTraining();
});

/**
 * Check if a trained model is available
 */
function checkModelAvailability() {
    fetch('/model_info')
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                // Enable scoring button
                document.getElementById('score-button').disabled = false;
                
                // Update essay set dropdown with available sets
                const essaySetSelect = document.getElementById('essay-set');
                essaySetSelect.innerHTML = '<option value="" selected disabled>Select an essay set</option>';
                
                data.essay_sets.forEach(setId => {
                    const option = document.createElement('option');
                    option.value = setId;
                    option.textContent = `Set ${setId}`;
                    essaySetSelect.appendChild(option);
                });
                
                // Show model info
                console.log('Model available:', data);
            } else {
                // Disable scoring button
                document.getElementById('score-button').disabled = true;
                
                // Show warning
                const warningDiv = document.createElement('div');
                warningDiv.className = 'alert alert-warning';
                warningDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>No model is currently available. Please train a model first.';
                
                const formElement = document.getElementById('essay-form');
                formElement.parentNode.insertBefore(warningDiv, formElement);
            }
        })
        .catch(error => {
            console.error('Error checking model availability:', error);
        });
}

/**
 * Set up event listeners for essay scoring
 */
function setupEssayScoring() {
    const essayForm = document.getElementById('essay-form');
    
    essayForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Get form values
        const essaySet = document.getElementById('essay-set').value;
        const essayText = document.getElementById('essay-text').value;
        
        // Validate form
        if (!essaySet || !essayText) {
            alert('Please select an essay set and enter essay text.');
            return;
        }
        
        // Show loading indicator
        document.getElementById('scoring-results').classList.add('d-none');
        document.getElementById('scoring-error').classList.add('d-none');
        document.getElementById('scoring-loading').classList.remove('d-none');
        
        // Send request to score essay
        fetch('/score', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                essay: essayText,
                essay_set: parseInt(essaySet)
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error scoring essay');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            document.getElementById('scoring-loading').classList.add('d-none');
            
            // Display results
            displayScoringResults(data);
        })
        .catch(error => {
            // Hide loading indicator
            document.getElementById('scoring-loading').classList.add('d-none');
            
            // Show error
            document.getElementById('error-message').textContent = error.message;
            document.getElementById('scoring-error').classList.remove('d-none');
            
            console.error('Error scoring essay:', error);
        });
    });
}

/**
 * Display essay scoring results
 */
function displayScoringResults(data) {
    // Update score
    document.getElementById('essay-score').textContent = data.score.toFixed(1);
    
    // Update percentage
    const percentage = data.percentage.toFixed(1);
    document.getElementById('score-percentage').textContent = `${percentage}%`;
    
    // Update progress bar
    const progressBar = document.getElementById('score-progress');
    progressBar.style.width = `${percentage}%`;
    
    // Set progress bar color based on feedback level
    progressBar.className = 'progress-bar';
    progressBar.classList.add(data.feedback.level);
    
    // Update feedback
    document.getElementById('feedback-level').textContent = formatFeedbackLevel(data.feedback.level);
    document.getElementById('feedback-level').className = 'card-title';
    document.getElementById('feedback-level').classList.add(`feedback-${data.feedback.level}`);
    
    document.getElementById('feedback-message').textContent = data.feedback.message;
    
    // Update suggestions
    const suggestionsList = document.getElementById('feedback-suggestions');
    suggestionsList.innerHTML = '';
    
    data.feedback.suggestions.forEach(suggestion => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.innerHTML = `<i class="fas fa-lightbulb suggestion-icon"></i> ${suggestion}`;
        suggestionsList.appendChild(li);
    });
    
    // Show results
    document.getElementById('scoring-results').classList.remove('d-none');
    
    // Scroll to results
    document.getElementById('scoring-results').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Format feedback level for display
 */
function formatFeedbackLevel(level) {
    switch (level) {
        case 'excellent':
            return 'Excellent';
        case 'good':
            return 'Good';
        case 'satisfactory':
            return 'Satisfactory';
        case 'needs_improvement':
            return 'Needs Improvement';
        case 'unsatisfactory':
            return 'Unsatisfactory';
        default:
            return 'Feedback';
    }
}

/**
 * Set up event listeners for model training
 */
function setupModelTraining() {
    const trainForm = document.getElementById('train-form');
    
    // Check if the form exists before adding event listener
    if (trainForm) {
        trainForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get form values
            const dataPath = document.getElementById('data-path').value;
            const modelName = document.getElementById('model-name').value;
            const essaySet = document.getElementById('train-essay-set').value;
            const epochs = document.getElementById('epochs').value;
            const preprocessing = document.getElementById('preprocessing').checked;
            
            // Validate form
            if (!dataPath) {
                alert('Please enter a data path.');
                return;
            }
            
            // Disable form
            document.getElementById('train-button').disabled = true;
            
            // Show progress container
            document.getElementById('training-progress-container').classList.remove('d-none');
            document.getElementById('training-error').classList.add('d-none');
            
            // Update status
            document.getElementById('training-status').textContent = 'Initializing...';
            document.getElementById('training-message').textContent = 'Starting the training process...';
            document.getElementById('training-progress').style.width = '0%';
            
            // Send request to train model
            fetch('/train', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    data_path: dataPath,
                    model_name: modelName,
                    essay_set: essaySet ? parseInt(essaySet) : null,
                    preprocessing: preprocessing,
                    epochs: parseInt(epochs)
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Error starting training');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Training started:', data);
                
                // Poll for training status
                pollTrainingStatus();
            })
            .catch(error => {
                // Show error
                document.getElementById('training-error-message').textContent = error.message;
                document.getElementById('training-error').classList.remove('d-none');
                
                // Re-enable form
                document.getElementById('train-button').disabled = false;
                
                console.error('Error starting training:', error);
            });
        });
    }
}

/**
 * Poll for training status
 */
function pollTrainingStatus() {
    const statusInterval = setInterval(function() {
        fetch('/training_status')
            .then(response => response.json())
            .then(data => {
                // Update progress
                document.getElementById('training-progress').style.width = `${data.progress}%`;
                document.getElementById('training-status').textContent = formatTrainingStatus(data.status);
                document.getElementById('training-message').textContent = data.message;
                
                // Check if training is complete or failed
                if (data.status === 'completed') {
                    clearInterval(statusInterval);
                    
                    // Re-enable form
                    document.getElementById('train-button').disabled = false;
                    
                    // Update model availability
                    setTimeout(checkModelAvailability, 1000);
                    
                    // Show success message
                    alert('Training completed successfully!');
                } else if (data.status === 'error') {
                    clearInterval(statusInterval);
                    
                    // Show error
                    document.getElementById('training-error-message').textContent = data.message;
                    document.getElementById('training-error').classList.remove('d-none');
                    
                    // Re-enable form
                    document.getElementById('train-button').disabled = false;
                }
            })
            .catch(error => {
                console.error('Error polling training status:', error);
            });
    }, 2000); // Poll every 2 seconds
}

/**
 * Format training status for display
 */
function formatTrainingStatus(status) {
    switch (status) {
        case 'starting':
            return 'Starting Training';
        case 'preprocessing':
            return 'Preprocessing Data';
        case 'extracting_features':
            return 'Extracting Features';
        case 'training':
            return 'Training Model';
        case 'evaluating':
            return 'Evaluating Model';
        case 'saving':
            return 'Saving Model';
        case 'completed':
            return 'Training Completed';
        case 'error':
            return 'Training Error';
        default:
            return 'Processing';
    }
}
