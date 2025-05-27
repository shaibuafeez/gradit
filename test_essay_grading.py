#!/usr/bin/env python3
"""
Test script for the essay grading functionality
"""
import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8088"
TEST_PROMPT = "Discuss the impact of artificial intelligence on education."
TEST_ESSAYS = [
    # Short essay with minimal content
    {
        "name": "Short essay",
        "content": "AI is changing education. It helps students learn better."
    },
    # Medium essay with some structure
    {
        "name": "Medium essay with structure",
        "content": """
        Introduction:
        Artificial intelligence has become increasingly prevalent in education.
        
        Body:
        AI tools can personalize learning experiences for students. For example, adaptive learning platforms
        can adjust content based on student performance. Additionally, AI can automate grading for certain
        types of assessments, freeing up teacher time.
        
        Conclusion:
        While AI offers many benefits to education, we must ensure it supplements rather than replaces
        human teachers.
        """
    },
    # Longer, well-structured essay
    {
        "name": "Comprehensive essay",
        "content": """
        Introduction:
        The integration of artificial intelligence (AI) into educational systems represents one of the most significant
        technological shifts in modern pedagogy. As AI technologies continue to evolve, their impact on how we teach
        and learn is becoming increasingly profound and multifaceted.
        
        Body:
        Personalized Learning:
        One of the most promising applications of AI in education is the ability to create truly personalized learning
        experiences. Traditional classroom settings often struggle to accommodate diverse learning styles and paces.
        AI-powered adaptive learning platforms can analyze individual student performance data in real-time, identifying
        strengths, weaknesses, and learning patterns. This enables the creation of customized learning pathways that
        adapt to each student's needs, providing additional support in challenging areas while accelerating through
        content they grasp quickly.
        
        For instance, platforms like Carnegie Learning's MATHia use AI to adjust mathematics instruction based on
        student interactions, providing targeted interventions precisely when needed. Similarly, language learning
        applications like Duolingo employ sophisticated algorithms to tailor vocabulary and grammar exercises to
        individual proficiency levels.
        
        Automated Assessment:
        AI has revolutionized assessment practices through automated grading systems. While initially limited to
        multiple-choice questions, modern AI can evaluate complex assignments including essays, programming
        assignments, and even artistic works. These systems not only reduce teacher workload but can provide
        immediate feedback to students, accelerating the learning cycle.
        
        Intelligent Tutoring Systems:
        AI-powered tutoring systems serve as virtual teaching assistants, available 24/7 to answer questions and
        provide guidance. These systems can simulate one-on-one tutoring experiences, offering explanations,
        hints, and feedback tailored to individual learning needs.
        
        Challenges and Concerns:
        Despite these advantages, the integration of AI in education raises important concerns. Privacy issues
        surrounding student data collection and analysis require careful consideration. Additionally, there's
        the risk of over-reliance on technology, potentially diminishing crucial human elements of education
        such as mentorship, empathy, and moral guidance.
        
        The digital divide presents another significant challenge, as unequal access to AI educational tools
        could exacerbate existing educational inequalities. Ensuring equitable access to these technologies
        must be a priority for educational policymakers.
        
        Conclusion:
        Artificial intelligence is transforming education in profound ways, offering unprecedented opportunities
        for personalization, efficiency, and accessibility. However, successful integration requires balancing
        technological innovation with human values and ensuring equitable access. The future of education likely
        lies not in choosing between human teachers and AI systems, but in thoughtfully combining their respective
        strengths to create more effective and inclusive learning environments.
        """
    }
]

def login_to_system():
    """Log in to the system to get a session cookie"""
    login_data = {
        "email": "teacher@example.com",
        "password": "password123"
    }
    session = requests.Session()
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200 or response.status_code == 302:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed with status code {response.status_code}")
        return None

def test_essay_scoring(session, essay):
    """Test the essay scoring functionality"""
    print(f"\n🔍 Testing essay: {essay['name']}")
    
    data = {
        "prompt": TEST_PROMPT,
        "essay": essay['content']
    }
    
    # Test the main scoring endpoint
    try:
        start_time = time.time()
        response = session.post(f"{BASE_URL}/api/score-essay", json=data)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Essay scored successfully in {end_time - start_time:.2f} seconds")
            print(f"   Score: {result.get('total_points', 'N/A')}/100")
            print(f"   Strengths: {len(result.get('strengths', []))} items")
            print(f"   Areas for improvement: {len(result.get('areas_for_improvement', []))} items")
            return True
        else:
            print(f"❌ Essay scoring failed with status code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during essay scoring: {str(e)}")
        return False

# Note: Fallback scoring function has been removed as we're now using only the Gemini API

def test_teacher_grading(session, essay):
    """Test the teacher grading functionality"""
    print(f"\n🔍 Testing teacher grading for: {essay['name']}")
    
    data = {
        "essay": essay['content'],
        "prompt": TEST_PROMPT,
        "score": 85,
        "feedback": "This is custom feedback from a teacher."
    }
    
    # Test the teacher grading endpoint
    try:
        response = session.post(f"{BASE_URL}/api/save-grade", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Teacher grading successful")
            print(f"   Response: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ Teacher grading failed with status code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during teacher grading: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting essay grading tests...")
    
    # Login to the system
    session = login_to_system()
    if not session:
        return
    
    # Test each essay with Gemini API scoring
    for essay in TEST_ESSAYS:
        test_essay_scoring(session, essay)
        test_teacher_grading(session, essay)
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    run_all_tests()
