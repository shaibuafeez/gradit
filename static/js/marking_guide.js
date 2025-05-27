/**
 * Marking Guide Management for Gradit
 * Handles the creation and management of marking guides for exam questions
 */

class MarkingGuide {
    constructor() {
        this.markingSchemes = {};
    }

    /**
     * Initialize a new marking guide for a question
     * @param {number} questionId - The question identifier
     */
    initializeGuide(questionId) {
        if (!this.markingSchemes[questionId]) {
            this.markingSchemes[questionId] = {
                totalPoints: 0,
                criteria: [],
                keywords: []
            };
        }
    }

    /**
     * Add a criterion to the marking guide
     * @param {number} questionId - The question identifier
     * @param {string} description - Description of the criterion
     * @param {number} points - Points allocated to this criterion
     * @returns {number} The index of the added criterion
     */
    addCriterion(questionId, description, points) {
        this.initializeGuide(questionId);
        
        const criterion = {
            id: Date.now(), // Unique identifier
            description: description,
            points: points
        };
        
        this.markingSchemes[questionId].criteria.push(criterion);
        this.updateTotalPoints(questionId);
        
        return this.markingSchemes[questionId].criteria.length - 1;
    }

    /**
     * Remove a criterion from the marking guide
     * @param {number} questionId - The question identifier
     * @param {number} criterionId - The criterion identifier to remove
     */
    removeCriterion(questionId, criterionId) {
        if (!this.markingSchemes[questionId]) return;
        
        this.markingSchemes[questionId].criteria = this.markingSchemes[questionId].criteria.filter(
            criterion => criterion.id !== criterionId
        );
        
        this.updateTotalPoints(questionId);
    }

    /**
     * Update the total points for a question's marking guide
     * @param {number} questionId - The question identifier
     */
    updateTotalPoints(questionId) {
        if (!this.markingSchemes[questionId]) return;
        
        this.markingSchemes[questionId].totalPoints = this.markingSchemes[questionId].criteria.reduce(
            (total, criterion) => total + parseFloat(criterion.points), 0
        );
    }

    /**
     * Add keywords to the marking guide
     * @param {number} questionId - The question identifier
     * @param {string} keywordsString - Comma-separated keywords
     */
    setKeywords(questionId, keywordsString) {
        this.initializeGuide(questionId);
        
        // Split by comma and trim whitespace
        const keywords = keywordsString.split(',')
            .map(keyword => keyword.trim())
            .filter(keyword => keyword.length > 0);
        
        this.markingSchemes[questionId].keywords = keywords;
    }

    /**
     * Get the complete marking guide for a question
     * @param {number} questionId - The question identifier
     * @returns {Object} The complete marking guide
     */
    getMarkingGuide(questionId) {
        return this.markingSchemes[questionId] || null;
    }

    /**
     * Get all marking guides
     * @returns {Object} All marking guides
     */
    getAllMarkingGuides() {
        return this.markingSchemes;
    }

    /**
     * Validate if a marking guide is complete
     * @param {number} questionId - The question identifier
     * @returns {boolean} Whether the marking guide is valid
     */
    isValid(questionId) {
        if (!this.markingSchemes[questionId]) return false;
        
        // Must have at least one criterion
        if (this.markingSchemes[questionId].criteria.length === 0) return false;
        
        // Total points should be greater than 0
        if (this.markingSchemes[questionId].totalPoints <= 0) return false;
        
        return true;
    }

    /**
     * Serialize the marking guide to JSON for storage
     * @param {number} questionId - The question identifier
     * @returns {string} JSON string of the marking guide
     */
    serializeGuide(questionId) {
        if (!this.markingSchemes[questionId]) return '{}';
        
        return JSON.stringify(this.markingSchemes[questionId]);
    }

    /**
     * Deserialize a JSON marking guide
     * @param {number} questionId - The question identifier
     * @param {string} jsonString - JSON string of the marking guide
     */
    deserializeGuide(questionId, jsonString) {
        try {
            this.markingSchemes[questionId] = JSON.parse(jsonString);
        } catch (e) {
            console.error('Error deserializing marking guide:', e);
            this.initializeGuide(questionId);
        }
    }
}

// Initialize the marking guide manager when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    window.markingGuideManager = new MarkingGuide();
    
    // Add event delegation for marking guide UI
    document.addEventListener('click', function(event) {
        // Add criterion button
        if (event.target.matches('.add-criterion-btn') || event.target.closest('.add-criterion-btn')) {
            const questionItem = event.target.closest('.question-item');
            if (!questionItem) return;
            
            const questionId = parseInt(questionItem.getAttribute('data-question-id'));
            addCriterionUI(questionId);
        }
        
        // Remove criterion button
        if (event.target.matches('.remove-criterion-btn') || event.target.closest('.remove-criterion-btn')) {
            const criterionItem = event.target.closest('.criterion-item');
            if (!criterionItem) return;
            
            const questionItem = criterionItem.closest('.question-item');
            const questionId = parseInt(questionItem.getAttribute('data-question-id'));
            const criterionId = parseInt(criterionItem.getAttribute('data-criterion-id'));
            
            removeCriterionUI(questionId, criterionId);
        }
    });
    
    // Add event delegation for input changes
    document.addEventListener('input', function(event) {
        // Criterion description or points change
        if (event.target.matches('.criterion-description, .criterion-points')) {
            const criterionItem = event.target.closest('.criterion-item');
            if (!criterionItem) return;
            
            const questionItem = criterionItem.closest('.question-item');
            const questionId = parseInt(questionItem.getAttribute('data-question-id'));
            const criterionId = parseInt(criterionItem.getAttribute('data-criterion-id'));
            
            updateCriterionUI(questionId, criterionId);
        }
        
        // Keywords change
        if (event.target.matches('.keywords-input')) {
            const questionItem = event.target.closest('.question-item');
            if (!questionItem) return;
            
            const questionId = parseInt(questionItem.getAttribute('data-question-id'));
            updateKeywordsUI(questionId);
        }
    });
});

/**
 * Add a new criterion UI element
 * @param {number} questionId - The question identifier
 */
function addCriterionUI(questionId) {
    const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
    if (!questionItem) return;
    
    const criteriaContainer = questionItem.querySelector('.criteria-container');
    if (!criteriaContainer) return;
    
    // Create a new criterion with default values
    const criterionIndex = window.markingGuideManager.addCriterion(questionId, '', 0);
    const criterion = window.markingGuideManager.getMarkingGuide(questionId).criteria[criterionIndex];
    
    // Create the UI element
    const criterionItem = document.createElement('div');
    criterionItem.className = 'criterion-item card mb-2';
    criterionItem.setAttribute('data-criterion-id', criterion.id);
    criterionItem.innerHTML = `
        <div class="card-body p-3">
            <div class="row g-2">
                <div class="col-md-8">
                    <input type="text" class="form-control criterion-description" 
                           placeholder="Criterion description" value="${criterion.description}">
                </div>
                <div class="col-md-3">
                    <div class="input-group">
                        <input type="number" class="form-control criterion-points" 
                               placeholder="Points" value="${criterion.points}" min="0" step="0.5">
                        <span class="input-group-text">pts</span>
                    </div>
                </div>
                <div class="col-md-1">
                    <button type="button" class="btn btn-sm btn-danger remove-criterion-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add to the container
    criteriaContainer.appendChild(criterionItem);
    
    // Update the total points display
    updateTotalPointsDisplay(questionId);
}

/**
 * Remove a criterion UI element
 * @param {number} questionId - The question identifier
 * @param {number} criterionId - The criterion identifier
 */
function removeCriterionUI(questionId, criterionId) {
    const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
    if (!questionItem) return;
    
    const criterionItem = questionItem.querySelector(`.criterion-item[data-criterion-id="${criterionId}"]`);
    if (!criterionItem) return;
    
    // Remove from the manager
    window.markingGuideManager.removeCriterion(questionId, criterionId);
    
    // Remove from the UI
    criterionItem.remove();
    
    // Update the total points display
    updateTotalPointsDisplay(questionId);
}

/**
 * Update a criterion in the manager when UI changes
 * @param {number} questionId - The question identifier
 * @param {number} criterionId - The criterion identifier
 */
function updateCriterionUI(questionId, criterionId) {
    const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
    if (!questionItem) return;
    
    const criterionItem = questionItem.querySelector(`.criterion-item[data-criterion-id="${criterionId}"]`);
    if (!criterionItem) return;
    
    const descriptionInput = criterionItem.querySelector('.criterion-description');
    const pointsInput = criterionItem.querySelector('.criterion-points');
    
    if (!descriptionInput || !pointsInput) return;
    
    // Get the current guide
    const guide = window.markingGuideManager.getMarkingGuide(questionId);
    if (!guide) return;
    
    // Find and update the criterion
    const criterionIndex = guide.criteria.findIndex(c => c.id === criterionId);
    if (criterionIndex === -1) return;
    
    guide.criteria[criterionIndex].description = descriptionInput.value;
    guide.criteria[criterionIndex].points = parseFloat(pointsInput.value) || 0;
    
    // Update total points
    window.markingGuideManager.updateTotalPoints(questionId);
    updateTotalPointsDisplay(questionId);
    
    // Update the hidden input for form submission
    updateHiddenInput(questionId);
}

/**
 * Update keywords in the manager when UI changes
 * @param {number} questionId - The question identifier
 */
function updateKeywordsUI(questionId) {
    const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
    if (!questionItem) return;
    
    const keywordsInput = questionItem.querySelector('.keywords-input');
    if (!keywordsInput) return;
    
    // Update keywords in the manager
    window.markingGuideManager.setKeywords(questionId, keywordsInput.value);
    
    // Update the hidden input for form submission
    updateHiddenInput(questionId);
}

/**
 * Update the total points display for a question
 * @param {number} questionId - The question identifier
 */
function updateTotalPointsDisplay(questionId) {
    const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
    if (!questionItem) return;
    
    const totalPointsDisplay = questionItem.querySelector('.total-points');
    if (!totalPointsDisplay) return;
    
    const guide = window.markingGuideManager.getMarkingGuide(questionId);
    if (!guide) return;
    
    totalPointsDisplay.textContent = guide.totalPoints;
    
    // Update the hidden input for form submission
    updateHiddenInput(questionId);
}

/**
 * Update the hidden input with the serialized marking guide
 * @param {number} questionId - The question identifier
 */
function updateHiddenInput(questionId) {
    const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
    if (!questionItem) return;
    
    const hiddenInput = questionItem.querySelector(`input[name="questions[${questionId}][marking_guide]"]`);
    if (!hiddenInput) return;
    
    hiddenInput.value = window.markingGuideManager.serializeGuide(questionId);
}

/**
 * Initialize the marking guide UI for a question
 * @param {number} questionId - The question identifier
 * @param {string} existingGuide - Optional JSON string of an existing guide
 */
function initializeMarkingGuideUI(questionId, existingGuide = null) {
    // Initialize in the manager
    window.markingGuideManager.initializeGuide(questionId);
    
    // If there's an existing guide, deserialize it
    if (existingGuide) {
        window.markingGuideManager.deserializeGuide(questionId, existingGuide);
    }
    
    const guide = window.markingGuideManager.getMarkingGuide(questionId);
    if (!guide) return;
    
    // Create UI for each criterion
    const criteriaContainer = document.querySelector(`.question-item[data-question-id="${questionId}"] .criteria-container`);
    if (!criteriaContainer) return;
    
    // Clear existing criteria
    criteriaContainer.innerHTML = '';
    
    // Add each criterion
    guide.criteria.forEach(criterion => {
        const criterionItem = document.createElement('div');
        criterionItem.className = 'criterion-item card mb-2';
        criterionItem.setAttribute('data-criterion-id', criterion.id);
        criterionItem.innerHTML = `
            <div class="card-body p-3">
                <div class="row g-2">
                    <div class="col-md-8">
                        <input type="text" class="form-control criterion-description" 
                               placeholder="Criterion description" value="${criterion.description}">
                    </div>
                    <div class="col-md-3">
                        <div class="input-group">
                            <input type="number" class="form-control criterion-points" 
                                   placeholder="Points" value="${criterion.points}" min="0" step="0.5">
                            <span class="input-group-text">pts</span>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <button type="button" class="btn btn-sm btn-danger remove-criterion-btn">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        criteriaContainer.appendChild(criterionItem);
    });
    
    // Set keywords
    const keywordsInput = document.querySelector(`.question-item[data-question-id="${questionId}"] .keywords-input`);
    if (keywordsInput) {
        keywordsInput.value = guide.keywords.join(', ');
    }
    
    // Update total points display
    updateTotalPointsDisplay(questionId);
}
