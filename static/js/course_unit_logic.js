/**
 * Course-Unit Logic for Gradit
 * Handles the mapping rule:
 * - 2-unit course → 3 questions total
 * - 3-unit course → 6 questions total
 */

class CourseUnitLogic {
    constructor() {
        this.unitQuestionMap = {
            2: 3, // 2-unit course has 3 questions
            3: 6  // 3-unit course has 6 questions
        };
    }

    /**
     * Get the required number of questions for a course based on its unit load
     * @param {number} units - The number of units for the course
     * @returns {number} The required number of questions
     */
    getRequiredQuestions(units) {
        return this.unitQuestionMap[units] || 0;
    }

    /**
     * Validate if the number of questions matches the course unit requirement
     * @param {number} units - The number of units for the course
     * @param {number} questionCount - The current number of questions
     * @returns {boolean} Whether the question count is valid
     */
    validateQuestionCount(units, questionCount) {
        const requiredQuestions = this.getRequiredQuestions(units);
        return questionCount === requiredQuestions;
    }

    /**
     * Get validation message based on question count and course units
     * @param {number} units - The number of units for the course
     * @param {number} questionCount - The current number of questions
     * @returns {string} Validation message
     */
    getValidationMessage(units, questionCount) {
        const requiredQuestions = this.getRequiredQuestions(units);
        
        if (questionCount < requiredQuestions) {
            return `You need to add ${requiredQuestions - questionCount} more question(s). A ${units}-unit course requires ${requiredQuestions} questions.`;
        } else if (questionCount > requiredQuestions) {
            return `You have ${questionCount - requiredQuestions} too many questions. A ${units}-unit course requires exactly ${requiredQuestions} questions.`;
        }
        
        return `Valid: ${requiredQuestions} questions for a ${units}-unit course.`;
    }
}

// Initialize the course unit logic when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    window.courseUnitLogic = new CourseUnitLogic();
    
    // Add event listeners to course selection dropdown if it exists
    const courseSelect = document.getElementById('course-select');
    if (courseSelect) {
        courseSelect.addEventListener('change', updateQuestionRequirements);
    }
    
    // Initial update of question requirements
    updateQuestionRequirements();
});

/**
 * Update the question requirements based on selected course
 */
function updateQuestionRequirements() {
    const courseSelect = document.getElementById('course-select');
    const questionContainer = document.getElementById('question-container');
    const validationMessage = document.getElementById('validation-message');
    
    if (!courseSelect || !questionContainer || !validationMessage) return;
    
    // Get the selected course's unit value from data attribute
    const selectedOption = courseSelect.options[courseSelect.selectedIndex];
    const units = parseInt(selectedOption.getAttribute('data-units') || '0');
    
    // Get the current question count
    const questionCount = document.querySelectorAll('.question-item').length;
    
    // Update validation message
    const message = window.courseUnitLogic.getValidationMessage(units, questionCount);
    validationMessage.textContent = message;
    
    // Update UI based on validation
    const isValid = window.courseUnitLogic.validateQuestionCount(units, questionCount);
    validationMessage.className = isValid ? 'text-success' : 'text-danger';
    
    // Enable/disable submit button based on validation
    const submitButton = document.getElementById('submit-exam-btn');
    if (submitButton) {
        submitButton.disabled = !isValid;
    }
}

/**
 * Add a new question to the form
 */
function addQuestion() {
    const courseSelect = document.getElementById('course-select');
    const questionContainer = document.getElementById('question-container');
    
    if (!courseSelect || !questionContainer) return;
    
    // Get the selected course's unit value
    const selectedOption = courseSelect.options[courseSelect.selectedIndex];
    const units = parseInt(selectedOption.getAttribute('data-units') || '0');
    
    // Get the current question count
    const questionCount = document.querySelectorAll('.question-item').length;
    
    // Check if we can add more questions
    const requiredQuestions = window.courseUnitLogic.getRequiredQuestions(units);
    if (questionCount >= requiredQuestions) {
        alert(`You cannot add more than ${requiredQuestions} questions for a ${units}-unit course.`);
        return;
    }
    
    // Create a new question item
    const questionNumber = questionCount + 1;
    const questionItem = document.createElement('div');
    questionItem.className = 'question-item card mb-3';
    questionItem.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Question ${questionNumber}</h5>
            <button type="button" class="btn btn-sm btn-danger remove-question-btn">
                <i class="fas fa-trash"></i> Remove
            </button>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <label for="question-text-${questionNumber}" class="form-label">Question Text</label>
                <textarea class="form-control" id="question-text-${questionNumber}" name="questions[${questionNumber}][text]" rows="3" required></textarea>
            </div>
            <div class="mb-3">
                <label for="marking-guide-${questionNumber}" class="form-label">Marking Guide</label>
                <textarea class="form-control" id="marking-guide-${questionNumber}" name="questions[${questionNumber}][marking_guide]" rows="3" required></textarea>
            </div>
            <div class="mb-3">
                <label for="keywords-${questionNumber}" class="form-label">Keywords/Phrases (comma separated)</label>
                <input type="text" class="form-control" id="keywords-${questionNumber}" name="questions[${questionNumber}][keywords]" placeholder="key concept, important term, critical point">
            </div>
        </div>
    `;
    
    // Add event listener to remove button
    const removeButton = questionItem.querySelector('.remove-question-btn');
    removeButton.addEventListener('click', function() {
        questionContainer.removeChild(questionItem);
        renumberQuestions();
        updateQuestionRequirements();
    });
    
    // Add the question to the container
    questionContainer.appendChild(questionItem);
    
    // Update validation
    updateQuestionRequirements();
}

/**
 * Renumber all questions after adding/removing
 */
function renumberQuestions() {
    const questionItems = document.querySelectorAll('.question-item');
    questionItems.forEach((item, index) => {
        const questionNumber = index + 1;
        
        // Update the heading
        const heading = item.querySelector('.card-header h5');
        if (heading) heading.textContent = `Question ${questionNumber}`;
        
        // Update the input IDs and names
        const textArea = item.querySelector('[id^="question-text-"]');
        const markingGuide = item.querySelector('[id^="marking-guide-"]');
        const keywords = item.querySelector('[id^="keywords-"]');
        
        if (textArea) {
            textArea.id = `question-text-${questionNumber}`;
            textArea.name = `questions[${questionNumber}][text]`;
        }
        
        if (markingGuide) {
            markingGuide.id = `marking-guide-${questionNumber}`;
            markingGuide.name = `questions[${questionNumber}][marking_guide]`;
        }
        
        if (keywords) {
            keywords.id = `keywords-${questionNumber}`;
            keywords.name = `questions[${questionNumber}][keywords]`;
        }
    });
}
