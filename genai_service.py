"""
Google Gen AI Service for Automated Essay Scoring

This module provides integration with Google's Gen AI API for essay scoring and feedback.
Uses the new google-genai SDK (replacing the deprecated google-generativeai).
"""

import os
import json
from typing import Dict, List, Any, Optional
import google.genai as genai
from google.genai.models import GenerativeModel
from google.genai.types import GenerationConfig
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GenAIService:
    """Service for interacting with Google's Gen AI API for essay scoring"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gen AI service
        
        Args:
            api_key: Gen AI API key (optional, can also be set via GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set it via constructor or GEMINI_API_KEY env var.")
        
        # Configure the Gen AI API
        genai.configure(api_key=self.api_key)
        
        # Get available models
        try:
            self.models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print(f"Available Gen AI models: {[m.name for m in self.models]}")
            
            # Use the most capable model by default
            self.model_name = "gemini-1.5-pro" if any(m.name == "gemini-1.5-pro" for m in self.models) else self.models[0].name
            self.model = GenerativeModel(self.model_name)
            
            print(f"Using Gen AI model: {self.model_name}")
        except Exception as e:
            print(f"Warning: Could not list available models: {str(e)}")
            print("Defaulting to gemini-1.5-pro model")
            self.model_name = "gemini-1.5-pro"
            self.model = GenerativeModel(self.model_name)
    
    def score_essay(self, essay_text: str, prompt: str, rubric: Dict[str, Any], essay_set: int = 1) -> Dict[str, Any]:
        """
        Score an essay using Gen AI API
        
        Args:
            essay_text: The essay text to score
            prompt: The original prompt/question the essay is responding to
            rubric: Scoring rubric with criteria and point values
            essay_set: Essay set identifier (for tracking purposes)
            
        Returns:
            Dictionary containing score, feedback, and detailed breakdown
        """
        # Create a system prompt that explains the task to the model
        system_prompt = f"""
        You are an expert essay evaluator with years of experience in academic assessment.
        
        You will be given an essay written in response to a prompt. Your task is to:
        1. Evaluate the essay based on the provided rubric
        2. Assign scores for each rubric criterion
        3. Provide specific, constructive feedback
        4. Calculate an overall score
        5. Return your evaluation in a structured JSON format
        
        Essay Set: {essay_set}
        
        RUBRIC:
        {json.dumps(rubric, indent=2)}
        
        PROMPT:
        {prompt}
        
        Provide your response in the following JSON format:
        {{
            "overall_score": (float between 0-1, representing percentage of total possible points),
            "total_points": (integer sum of points awarded),
            "max_points": (integer maximum possible points),
            "criteria_scores": {{
                "criterion1": {{
                    "score": (points awarded),
                    "max_score": (maximum possible points),
                    "feedback": (specific feedback for this criterion)
                }},
                ...
            }},
            "strengths": [(list of specific strengths)],
            "areas_for_improvement": [(list of specific areas to improve)],
            "overall_feedback": (general feedback summarizing the evaluation)
        }}
        """
        
        # Configure generation parameters
        generation_config = GenerationConfig(
            temperature=0.2,  # Low temperature for more consistent scoring
            top_p=0.95,
            top_k=40,
            response_mime_type="application/json"
        )
        
        try:
            # Generate the response
            response = self.model.generate_content(
                [system_prompt, essay_text],
                generation_config=generation_config
            )
            
            # Parse the JSON response
            try:
                result = json.loads(response.text)
                
                # Validate the response structure
                required_fields = ["overall_score", "total_points", "max_points", "criteria_scores"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field in response: {field}")
                
                return result
            except json.JSONDecodeError:
                # If we couldn't parse JSON, return a simplified result
                return {
                    "overall_score": 0.5,  # Default to middle score
                    "total_points": 0,
                    "max_points": 0,
                    "criteria_scores": {},
                    "strengths": [],
                    "areas_for_improvement": ["Could not properly evaluate essay"],
                    "overall_feedback": "There was an error processing your essay. Please try again.",
                    "error": "Failed to parse API response"
                }
        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return {
                "overall_score": 0.5,
                "total_points": 0,
                "max_points": 0,
                "criteria_scores": {},
                "strengths": [],
                "areas_for_improvement": ["API error occurred"],
                "overall_feedback": f"There was an error processing your essay: {str(e)}",
                "error": str(e)
            }
    
    def generate_detailed_feedback(self, essay_text: str, score_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate more detailed feedback based on the essay and scoring results
        
        Args:
            essay_text: The original essay text
            score_result: The scoring results from score_essay
            
        Returns:
            Dictionary with detailed feedback including suggested improvements
        """
        # Create a prompt for generating detailed feedback
        prompt = f"""
        You are an expert writing tutor. You've been given an essay and its evaluation scores.
        
        Based on this information, provide detailed, constructive feedback to help the student improve.
        
        Focus on specific examples from their essay and offer concrete suggestions for improvement.
        
        EVALUATION SUMMARY:
        {json.dumps(score_result, indent=2)}
        
        ESSAY:
        {essay_text}
        
        Provide your response in the following JSON format:
        {{
            "detailed_feedback": {{
                "introduction": {{
                    "strengths": [(specific strengths)],
                    "improvements": [(specific suggestions)],
                    "example_revision": (example of how to improve a specific sentence or paragraph)
                }},
                "body": {{
                    "strengths": [(specific strengths)],
                    "improvements": [(specific suggestions)],
                    "example_revision": (example of how to improve a specific sentence or paragraph)
                }},
                "conclusion": {{
                    "strengths": [(specific strengths)],
                    "improvements": [(specific suggestions)],
                    "example_revision": (example of how to improve a specific sentence or paragraph)
                }},
                "language_and_style": {{
                    "strengths": [(specific strengths)],
                    "improvements": [(specific suggestions)],
                    "example_revision": (example of how to improve a specific sentence or paragraph)
                }}
            }},
            "highlighted_text": [
                {{
                    "text": (text excerpt from essay),
                    "type": ("strength" or "improvement"),
                    "comment": (specific comment about this excerpt)
                }},
                ...
            ],
            "summary": (overall summary of feedback)
        }}
        """
        
        # Configure generation parameters
        generation_config = GenerationConfig(
            temperature=0.3,
            top_p=0.95,
            top_k=40,
            response_mime_type="application/json"
        )
        
        try:
            # Generate the response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Parse the JSON response
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # Return a simplified response if parsing fails
                return {
                    "detailed_feedback": {
                        "general": {
                            "strengths": ["Your essay addresses the prompt"],
                            "improvements": ["Consider revising for clarity and organization"],
                            "example_revision": "N/A"
                        }
                    },
                    "highlighted_text": [],
                    "summary": "There was an error generating detailed feedback. Please review the general scoring feedback."
                }
        except Exception as e:
            print(f"Error generating detailed feedback: {str(e)}")
            return {
                "detailed_feedback": {
                    "general": {
                        "strengths": ["Your essay addresses the prompt"],
                        "improvements": ["Consider revising for clarity and organization"],
                        "example_revision": "N/A"
                    }
                },
                "highlighted_text": [],
                "summary": f"Error generating feedback: {str(e)}"
            }
    
    def get_default_rubric(self) -> Dict[str, Any]:
        """
        Get a default essay scoring rubric
        
        Returns:
            Dictionary containing default rubric criteria
        """
        return {
            "content": {
                "description": "Depth of analysis, relevance to prompt, and quality of ideas",
                "max_score": 30
            },
            "organization": {
                "description": "Logical flow, clear structure with intro/body/conclusion, effective transitions",
                "max_score": 20
            },
            "evidence": {
                "description": "Use of specific examples, facts, or details to support claims",
                "max_score": 20
            },
            "language": {
                "description": "Grammar, vocabulary, sentence variety, and word choice",
                "max_score": 20
            },
            "style": {
                "description": "Voice, tone, and audience awareness",
                "max_score": 10
            }
        }


# Example usage
if __name__ == "__main__":
    # For testing purposes
    try:
        service = GenAIService()
        
        # Example essay and prompt
        prompt = "Discuss the impact of social media on modern communication."
        essay = """
        Social media has transformed how people communicate in the modern world. Platforms like Facebook, Twitter, and Instagram allow instant sharing of information across the globe. This has both positive and negative effects on society.
        
        On one hand, social media enables people to stay connected with friends and family regardless of distance. It also provides a platform for marginalized voices to be heard. For example, social movements like Black Lives Matter gained significant momentum through social media campaigns.
        
        However, there are also drawbacks. The rise of misinformation and "fake news" has become a serious concern. Additionally, studies suggest that excessive social media use may contribute to mental health issues like anxiety and depression, particularly among younger users.
        
        In conclusion, while social media has revolutionized communication by making it more accessible and immediate, it also presents challenges that society must address to ensure its benefits outweigh its harms.
        """
        
        # Get default rubric
        rubric = service.get_default_rubric()
        
        # Score the essay
        result = service.score_essay(essay, prompt, rubric)
        print(json.dumps(result, indent=2))
        
        # Generate detailed feedback
        feedback = service.generate_detailed_feedback(essay, result)
        print(json.dumps(feedback, indent=2))
        
    except Exception as e:
        print(f"Error testing Gen AI service: {str(e)}")
