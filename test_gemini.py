#!/usr/bin/env python3
"""
Test script to verify Gemini API connection
"""
import os
from google import genai
from google.genai import types

def test_gemini_api():
    """Test the Gemini API connection"""
    # Get API key from .env file
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        with open(".env") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.strip().split("=", 1)[1].strip()
                    # Remove quotes if present
                    if api_key.startswith('"') and api_key.endswith('"'):
                        api_key = api_key[1:-1]
                    break
    
    print(f"Using API key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        # Initialize the client
        client = genai.Client(api_key=api_key)
        
        # Create a simple prompt
        prompt = "Write a short paragraph about artificial intelligence."
        
        # Create content for the model
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        # Configure generation parameters
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=100,
        )
        
        print("Sending request to Gemini API...")
        
        # Generate content
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=contents,
            config=generate_content_config,
        )
        
        print("\nResponse from Gemini API:")
        print(response.text)
        
        print("\nAPI connection successful!")
        return True
    except Exception as e:
        print(f"\nError connecting to Gemini API: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_api()
