/**
 * Auto Grading System for Gradit
 * Handles the automated grading of student exam submissions
 */

class AutoGradingSystem {
    constructor() {
        this.markingGuides = {};
        this.submissions = {};
        this.results = {};
    }

    /**
     * Load a marking guide for a question
     * @param {number} questionId - The question identifier
     * @param {Object} markingGuide - The marking guide object
     */
    loadMarkingGuide(questionId, markingGuide) {
        this.markingGuides[questionId] = markingGuide;
    }

    /**
     * Record a student submission for a question
     * @param {number} questionId - The question identifier
     * @param {string} studentId - The student identifier
     * @param {string} answer - The student's answer
     */
    recordSubmission(questionId, studentId, answer) {
        if (!this.submissions[questionId]) {
            this.submissions[questionId] = {};
        }
        
        this.submissions[questionId][studentId] = answer;
    }

    /**
     * Grade a student's answer for a question
     * @param {number} questionId - The question identifier
     * @param {string} studentId - The student identifier
     * @returns {Object} Grading result with score and feedback
     */
    gradeSubmission(questionId, studentId) {
        if (!this.markingGuides[questionId]) {
            return { error: 'No marking guide available for this question' };
        }
        
        if (!this.submissions[questionId] || !this.submissions[questionId][studentId]) {
            return { error: 'No submission found for this student' };
        }
        
        const guide = this.markingGuides[questionId];
        const answer = this.submissions[questionId][studentId];
        
        // Initialize result
        const result = {
            questionId: questionId,
            studentId: studentId,
            totalPossiblePoints: guide.totalPoints,
            earnedPoints: 0,
            percentage: 0,
            criteriaResults: [],
            keywordsFound: [],
            keywordsMissing: [],
            feedback: ''
        };
        
        // Check each criterion
        guide.criteria.forEach(criterion => {
            const criterionResult = {
                description: criterion.description,
                possiblePoints: criterion.points,
                earnedPoints: 0,
                feedback: ''
            };
            
            // For now, use a simple algorithm based on keywords
            // This would be replaced with more sophisticated NLP in a real implementation
            const keywordsForCriterion = this.extractKeywordsForCriterion(criterion, guide.keywords);
            const matchScore = this.calculateKeywordMatchScore(answer, keywordsForCriterion);
            
            criterionResult.earnedPoints = criterion.points * matchScore;
            result.earnedPoints += criterionResult.earnedPoints;
            
            // Generate feedback based on match score
            if (matchScore >= 0.8) {
                criterionResult.feedback = 'Excellent understanding demonstrated.';
            } else if (matchScore >= 0.5) {
                criterionResult.feedback = 'Good understanding, but some key points missing.';
            } else if (matchScore >= 0.3) {
                criterionResult.feedback = 'Basic understanding shown, but significant improvement needed.';
            } else {
                criterionResult.feedback = 'Limited understanding of this criterion.';
            }
            
            result.criteriaResults.push(criterionResult);
        });
        
        // Calculate overall percentage
        result.percentage = (result.earnedPoints / result.totalPossiblePoints) * 100;
        
        // Check for keywords in the entire answer
        if (guide.keywords && guide.keywords.length > 0) {
            guide.keywords.forEach(keyword => {
                if (this.containsKeyword(answer, keyword)) {
                    result.keywordsFound.push(keyword);
                } else {
                    result.keywordsMissing.push(keyword);
                }
            });
        }
        
        // Generate overall feedback
        result.feedback = this.generateOverallFeedback(result);
        
        // Store the result
        if (!this.results[questionId]) {
            this.results[questionId] = {};
        }
        this.results[questionId][studentId] = result;
        
        return result;
    }

    /**
     * Extract keywords that are relevant to a specific criterion
     * @param {Object} criterion - The criterion object
     * @param {Array} allKeywords - All keywords for the question
     * @returns {Array} Keywords relevant to this criterion
     */
    extractKeywordsForCriterion(criterion, allKeywords) {
        // In a real implementation, this would use NLP to associate keywords with criteria
        // For this demo, we'll just use all keywords for all criteria
        return allKeywords || [];
    }

    /**
     * Calculate a match score based on keywords present in the answer
     * @param {string} answer - The student's answer
     * @param {Array} keywords - Keywords to look for
     * @returns {number} Match score between 0 and 1
     */
    calculateKeywordMatchScore(answer, keywords) {
        if (!keywords || keywords.length === 0) return 0.5; // Default to 50% if no keywords
        
        let matchCount = 0;
        keywords.forEach(keyword => {
            if (this.containsKeyword(answer, keyword)) {
                matchCount++;
            }
        });
        
        return keywords.length > 0 ? matchCount / keywords.length : 0;
    }

    /**
     * Check if an answer contains a specific keyword
     * @param {string} answer - The student's answer
     * @param {string} keyword - Keyword to look for
     * @returns {boolean} Whether the keyword is present
     */
    containsKeyword(answer, keyword) {
        // Case-insensitive search
        const answerLower = answer.toLowerCase();
        const keywordLower = keyword.toLowerCase();
        
        // Check for exact match or word boundary match
        return answerLower.includes(keywordLower);
    }

    /**
     * Generate overall feedback based on grading results
     * @param {Object} result - The grading result
     * @returns {string} Overall feedback
     */
    generateOverallFeedback(result) {
        let feedback = '';
        
        // Feedback based on overall percentage
        if (result.percentage >= 90) {
            feedback += 'Outstanding work! Your answer demonstrates excellent understanding of the topic. ';
        } else if (result.percentage >= 80) {
            feedback += 'Great job! Your answer shows strong understanding of the key concepts. ';
        } else if (result.percentage >= 70) {
            feedback += 'Good work! You have a solid understanding of most concepts. ';
        } else if (result.percentage >= 60) {
            feedback += 'Satisfactory work. You understand the basics, but there\'s room for improvement. ';
        } else if (result.percentage >= 50) {
            feedback += 'You\'ve shown basic understanding, but need to develop your knowledge further. ';
        } else {
            feedback += 'Your answer needs significant improvement. Please review the course materials. ';
        }
        
        // Add feedback about missing keywords if any
        if (result.keywordsMissing.length > 0) {
            feedback += 'Consider including these important concepts in your answer: ' + 
                        result.keywordsMissing.join(', ') + '. ';
        }
        
        // Add positive reinforcement for found keywords if any
        if (result.keywordsFound.length > 0) {
            feedback += 'You effectively incorporated these key concepts: ' + 
                        result.keywordsFound.join(', ') + '. ';
        }
        
        return feedback;
    }

    /**
     * Get all results for a question
     * @param {number} questionId - The question identifier
     * @returns {Object} All student results for this question
     */
    getQuestionResults(questionId) {
        return this.results[questionId] || {};
    }

    /**
     * Get all results for a student
     * @param {string} studentId - The student identifier
     * @returns {Object} All question results for this student
     */
    getStudentResults(studentId) {
        const studentResults = {};
        
        Object.keys(this.results).forEach(questionId => {
            if (this.results[questionId][studentId]) {
                studentResults[questionId] = this.results[questionId][studentId];
            }
        });
        
        return studentResults;
    }

    /**
     * Calculate overall exam score for a student
     * @param {string} studentId - The student identifier
     * @param {Array} questionIds - Array of question IDs in the exam
     * @returns {Object} Overall exam score and statistics
     */
    calculateExamScore(studentId, questionIds) {
        let totalPossiblePoints = 0;
        let totalEarnedPoints = 0;
        let questionsAttempted = 0;
        
        questionIds.forEach(questionId => {
            if (this.results[questionId] && this.results[questionId][studentId]) {
                const result = this.results[questionId][studentId];
                totalPossiblePoints += result.totalPossiblePoints;
                totalEarnedPoints += result.earnedPoints;
                questionsAttempted++;
            }
        });
        
        return {
            studentId: studentId,
            totalPossiblePoints: totalPossiblePoints,
            totalEarnedPoints: totalEarnedPoints,
            percentage: totalPossiblePoints > 0 ? (totalEarnedPoints / totalPossiblePoints) * 100 : 0,
            questionsAttempted: questionsAttempted,
            totalQuestions: questionIds.length
        };
    }
}

// Initialize the auto grading system when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    window.autoGradingSystem = new AutoGradingSystem();
});
