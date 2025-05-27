from minimal_genai_app import app

# This file is required for Vercel deployment
# It exposes the Flask application as a handler function

def handler(request, context):
    return app(request, context)
