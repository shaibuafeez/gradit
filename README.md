# Gradit - AI-Powered Essay Grading Platform

Gradit is a comprehensive educational platform that leverages AI to automate essay grading while providing valuable feedback to students and powerful analytics for teachers.
## Key Improvements

1. **Multiple Scoring Approaches**
   - Custom transformer-based model (RoBERTa, BERT, etc.)
   - Google Gemini API integration for advanced scoring
   - Fallback simple scoring system

2. **Advanced Text Preprocessing**
   - Lemmatization using spaCy
   - Stopword removal
   - Special character and number handling
   - Optional spelling correction

3. **Enhanced Feature Engineering**
   - Multiple embedding strategies (mean, CLS token, pooled)
   - Attention-based token weighting
   - Better handling of long essays

4. **Improved Model Architecture**
   - Deeper MLP with configurable hidden layers
   - Batch normalization for better training stability
   - Dropout for regularization
   - Learning rate scheduling

5. **Better Evaluation and Metrics**
   - Cross-validation support
   - Multiple evaluation metrics (QWK, MSE)
   - Per-essay set analysis

6. **User-Friendly Interface**
   - Web application with authentication
   - Course and exam management
   - Detailed feedback visualization
   - API endpoints for integration

## Requirements

- Python 3.7+
- PyTorch
- Transformers (Hugging Face)
- Google Generative AI (for Gemini API)
- Flask and extensions (for web application)
- scikit-learn
- pandas
- numpy
- spaCy
- NLTK
- tqdm
- matplotlib

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/improved-aes.git
cd improved-aes

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Edit .env file to add your Gemini API key
```

## Usage

### Running the Web Application

```bash
# Run the Gemini-powered web application
python gemini_app.py
```

Then visit http://localhost:8088 in your browser.

### Using the Custom ML Model

#### Training a New Model

```bash
python run_aes.py train --data_path data/training_set_rel3.tsv --model_name roberta-base --preprocessing --cv --save_path models/aes_model.pt
```

#### Evaluating an Existing Model

```bash
python run_aes.py evaluate --model_path models/aes_model.pt --data_path data/test_set.csv
```

#### Scoring New Essays

```bash
python run_aes.py predict --model_path models/aes_model.pt --essay_path new_essays.csv --essay_set 1 --output_path predictions.csv
```

### Using the Gemini API Directly

```python
from gemini_service import GeminiService

# Initialize the service with your API key
gemini = GeminiService(api_key="your_api_key_here")

# Score an essay
result = gemini.score_essay(
    essay_text="Your essay text here...",
    prompt="The original essay prompt...",
    rubric=gemini.get_default_rubric()
)

# Get detailed feedback
feedback = gemini.generate_detailed_feedback(essay_text, result)
```

## Dataset

This system uses the Automated Student Assessment Prize (ASAP) dataset, which contains approximately 13,000 essays written by students in grades 7-10. The essays are divided into 8 different sets, each with its own prompt and scoring criteria.

The dataset can be obtained from the [original Kaggle competition](https://www.kaggle.com/c/asap-aes/data).

## Architecture

The system offers two main approaches for essay scoring:

### 1. Custom ML Model

The custom ML pipeline consists of three main components:

- **Text Preprocessor**: Cleans and normalizes the essay text
- **Feature Extractor**: Uses a transformer model to extract embeddings from essays
- **Regressor**: A multi-layer perceptron that predicts essay scores

The default configuration uses RoBERTa as the transformer model, as it has been shown to outperform BERT and DistilBERT for this task.

### 2. Gemini API Integration

The Gemini-powered scoring system:

- Uses Google's advanced LLM capabilities for more nuanced essay evaluation
- Provides detailed, contextual feedback with specific improvement suggestions
- Offers highlighted text analysis pointing out strengths and weaknesses
- Generates example revisions to help students improve their writing

### Web Application

The web application provides:

- User authentication (student and teacher roles)
- Course management
- Exam creation and submission
- Essay scoring and feedback visualization
- Progress tracking and analytics

## Performance

On the ASAP dataset, this improved system achieves:

- **Quadratic Weighted Kappa (QWK)**: ~0.77-0.80 (compared to ~0.75 for the original implementation)
- **Mean Squared Error (MSE)**: Lower by approximately 10-15%

The performance varies by essay set, with some sets showing more significant improvements than others.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The original [aes-bert](https://github.com/leobertolazzi/aes-bert) implementation
- The Hewlett Foundation for providing the ASAP dataset
- The Hugging Face team for their Transformers library
- Google for the Gemini API

## API Keys

To use the Gemini API features, you'll need to:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add your API key to the `.env` file
3. Restart the application
