/**
 * JavaScript for the Marking Guide functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    setupMarkingGuide();
});

/**
 * Set up event listeners for the marking guide
 */
function setupMarkingGuide() {
    // Add criteria button
    const addCriteriaBtn = document.getElementById('add-criteria-btn');
    if (addCriteriaBtn) {
        addCriteriaBtn.addEventListener('click', addCriteria);
    }
    
    // Preview button
    const previewBtn = document.getElementById('preview-guide-btn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewMarkingGuide);
    }
    
    // Save button
    const saveBtn = document.getElementById('save-guide-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveMarkingGuide);
    }
    
    // Add initial criteria
    addCriteria();
}

/**
 * Add a new criteria field to the form
 */
function addCriteria() {
    const criteriaContainer = document.getElementById('criteria-container');
    const criteriaCount = criteriaContainer.children.length + 1;
    
    const criteriaDiv = document.createElement('div');
    criteriaDiv.className = 'criteria-item p-3 mb-3';
    criteriaDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Criteria ${criteriaCount}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger criteria-remove" onclick="removeCriteria(this)">
                <i class="fas fa-times"></i> Remove
            </button>
        </div>
        <div class="mb-3">
            <label for="criteria-name-${criteriaCount}" class="form-label">Name</label>
            <input type="text" class="form-control criteria-name" id="criteria-name-${criteriaCount}" placeholder="e.g., Grammar and Spelling">
        </div>
        <div class="mb-3">
            <label for="criteria-description-${criteriaCount}" class="form-label">Description</label>
            <textarea class="form-control criteria-description" id="criteria-description-${criteriaCount}" rows="2" placeholder="Describe what you're looking for in this criteria"></textarea>
        </div>
        <div class="row">
            <div class="col-md-6 mb-3">
                <label for="criteria-weight-${criteriaCount}" class="form-label">Weight (%)</label>
                <input type="number" class="form-control criteria-weight" id="criteria-weight-${criteriaCount}" min="5" max="100" value="20">
            </div>
            <div class="col-md-6 mb-3">
                <label for="criteria-max-score-${criteriaCount}" class="form-label">Max Score</label>
                <input type="number" class="form-control criteria-max-score" id="criteria-max-score-${criteriaCount}" min="1" max="100" value="10">
            </div>
        </div>
    `;
    
    criteriaContainer.appendChild(criteriaDiv);
    
    // Update total weight display
    updateTotalWeight();
}

/**
 * Remove a criteria field from the form
 */
function removeCriteria(button) {
    const criteriaItem = button.closest('.criteria-item');
    criteriaItem.remove();
    
    // Update criteria numbering
    const criteriaItems = document.querySelectorAll('.criteria-item');
    criteriaItems.forEach((item, index) => {
        const heading = item.querySelector('h6');
        heading.textContent = `Criteria ${index + 1}`;
    });
    
    // Update total weight display
    updateTotalWeight();
}

/**
 * Update the total weight display
 */
function updateTotalWeight() {
    const weightInputs = document.querySelectorAll('.criteria-weight');
    let totalWeight = 0;
    
    weightInputs.forEach(input => {
        totalWeight += parseInt(input.value) || 0;
    });
    
    const totalWeightDisplay = document.getElementById('total-weight');
    if (totalWeightDisplay) {
        totalWeightDisplay.textContent = totalWeight;
        
        // Highlight if not 100%
        if (totalWeight === 100) {
            totalWeightDisplay.className = 'text-success';
        } else if (totalWeight < 100) {
            totalWeightDisplay.className = 'text-warning';
        } else {
            totalWeightDisplay.className = 'text-danger';
        }
    }
}

/**
 * Preview the marking guide
 */
function previewMarkingGuide() {
    // Get form values
    const assignmentName = document.getElementById('assignment-name').value;
    const gradeLevel = document.getElementById('grade-level').value;
    const essayPrompt = document.getElementById('essay-prompt').value;
    const exemplarEssay = document.getElementById('exemplar-essay').value;
    
    // Get criteria
    const criteria = [];
    const criteriaItems = document.querySelectorAll('.criteria-item');
    
    criteriaItems.forEach((item, index) => {
        const name = item.querySelector('.criteria-name').value;
        const description = item.querySelector('.criteria-description').value;
        const weight = parseInt(item.querySelector('.criteria-weight').value) || 0;
        const maxScore = parseInt(item.querySelector('.criteria-max-score').value) || 0;
        
        criteria.push({
            name: name || `Criteria ${index + 1}`,
            description: description || 'No description provided',
            weight: weight,
            maxScore: maxScore
        });
    });
    
    // Validate form
    if (!assignmentName) {
        alert('Please enter an assignment name.');
        return;
    }
    
    if (criteria.length === 0) {
        alert('Please add at least one criteria.');
        return;
    }
    
    // Calculate total weight
    const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);
    if (totalWeight !== 100) {
        alert(`Total weight should be 100%. Current total: ${totalWeight}%`);
        return;
    }
    
    // Display preview
    const previewSection = document.getElementById('marking-preview');
    
    // Assignment details
    document.getElementById('preview-assignment-name').textContent = assignmentName;
    document.getElementById('preview-grade-level').textContent = gradeLevel || 'Not specified';
    document.getElementById('preview-essay-prompt').textContent = essayPrompt || 'No prompt provided';
    
    // Exemplar essay
    const exemplarSection = document.getElementById('exemplar-section');
    if (exemplarEssay) {
        document.getElementById('preview-exemplar-essay').textContent = exemplarEssay;
        exemplarSection.classList.remove('d-none');
    } else {
        exemplarSection.classList.add('d-none');
    }
    
    // Criteria
    const criteriaList = document.getElementById('preview-criteria-list');
    criteriaList.innerHTML = '';
    
    let totalMaxPoints = 0;
    
    criteria.forEach(c => {
        totalMaxPoints += c.maxScore;
        
        const criteriaDiv = document.createElement('div');
        criteriaDiv.className = 'criteria-preview-item mb-3';
        criteriaDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h5 class="mb-0">${c.name}</h5>
                <div>
                    <span class="badge bg-primary me-2">${c.weight}%</span>
                    <span class="badge bg-secondary">${c.maxScore} points</span>
                </div>
            </div>
            <p class="mb-0">${c.description}</p>
        `;
        
        criteriaList.appendChild(criteriaDiv);
    });
    
    // Total score
    document.getElementById('preview-total-points').textContent = totalMaxPoints;
    
    // Show preview
    previewSection.classList.remove('d-none');
    previewSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Save the marking guide
 */
function saveMarkingGuide() {
    // Get form values
    const assignmentName = document.getElementById('assignment-name').value;
    const gradeLevel = document.getElementById('grade-level').value;
    const essayPrompt = document.getElementById('essay-prompt').value;
    const exemplarEssay = document.getElementById('exemplar-essay').value;
    
    // Get criteria
    const criteria = [];
    const criteriaItems = document.querySelectorAll('.criteria-item');
    
    criteriaItems.forEach((item, index) => {
        const name = item.querySelector('.criteria-name').value;
        const description = item.querySelector('.criteria-description').value;
        const weight = parseInt(item.querySelector('.criteria-weight').value) || 0;
        const maxScore = parseInt(item.querySelector('.criteria-max-score').value) || 0;
        
        criteria.push({
            name: name || `Criteria ${index + 1}`,
            description: description || 'No description provided',
            weight: weight,
            maxScore: maxScore
        });
    });
    
    // Validate form
    if (!assignmentName) {
        alert('Please enter an assignment name.');
        return;
    }
    
    if (criteria.length === 0) {
        alert('Please add at least one criteria.');
        return;
    }
    
    // Calculate total weight
    const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);
    if (totalWeight !== 100) {
        alert(`Total weight should be 100%. Current total: ${totalWeight}%`);
        return;
    }
    
    // Prepare data for saving
    const markingGuide = {
        assignment_name: assignmentName,
        grade_level: gradeLevel,
        essay_prompt: essayPrompt,
        exemplar_essay: exemplarEssay,
        criteria: criteria,
        created_at: new Date().toISOString()
    };
    
    // Send to server
    fetch('/save_marking_guide', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(markingGuide)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Error saving marking guide');
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        const successDiv = document.createElement('div');
        successDiv.className = 'text-center my-4';
        successDiv.innerHTML = `
            <div class="success-icon mb-3">
                <i class="fas fa-check"></i>
            </div>
            <h4 class="mb-3">Marking Guide Saved!</h4>
            <p class="mb-4">Your marking guide "${assignmentName}" has been saved successfully.</p>
            <button type="button" class="btn btn-primary" onclick="resetMarkingForm()">
                Create Another Guide
            </button>
        `;
        
        const formContainer = document.getElementById('marking-form-container');
        formContainer.innerHTML = '';
        formContainer.appendChild(successDiv);
        
        // Hide preview
        document.getElementById('marking-preview').classList.add('d-none');
    })
    .catch(error => {
        alert(`Error saving marking guide: ${error.message}`);
        console.error('Error saving marking guide:', error);
    });
}

/**
 * Reset the marking guide form
 */
function resetMarkingForm() {
    // Reload the page to reset the form
    window.location.reload();
}

// Make removeCriteria available globally
window.removeCriteria = removeCriteria;
