"""
Improved Automated Essay Scoring (AES) System

This script implements an improved AES system based on transformer models.
It builds upon the work by leobertolazzi/aes-bert with several enhancements:
- Support for multiple transformer models
- More advanced text preprocessing
- Enhanced feature engineering
- Improved model architecture
- Better evaluation metrics
"""

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import cohen_kappa_score, mean_squared_error
from transformers import (
    AutoTokenizer, 
    AutoModel,
    BertTokenizer, 
    BertModel, 
    RobertaTokenizer, 
    RobertaModel, 
    DistilBertTokenizer, 
    DistilBertModel
)
from tqdm import tqdm
import matplotlib.pyplot as plt
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
import argparse

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Set device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

class TextPreprocessor:
    """Advanced text preprocessing for essays"""
    
    def __init__(self, remove_stopwords=True, correct_spelling=False, lemmatize=True):
        self.remove_stopwords = remove_stopwords
        self.correct_spelling = correct_spelling
        self.lemmatize = lemmatize
        
        if remove_stopwords:
            self.stop_words = set(stopwords.words('english'))
        
        if lemmatize:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                print("Downloading spaCy model...")
                os.system("python -m spacy download en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
    
    def clean_text(self, text):
        """Basic text cleaning"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def preprocess(self, text):
        """Full preprocessing pipeline"""
        # Basic cleaning
        text = self.clean_text(text)
        
        if self.lemmatize:
            # Lemmatization using spaCy
            doc = self.nlp(text)
            text = ' '.join([token.lemma_ for token in doc])
        
        if self.remove_stopwords:
            # Remove stopwords
            word_tokens = word_tokenize(text)
            text = ' '.join([word for word in word_tokens if word not in self.stop_words])
        
        return text

class FeatureExtractor:
    """Extract features from essays using transformer models"""
    
    def __init__(self, model_name='roberta-base', max_length=512):
        self.model_name = model_name
        self.max_length = max_length
        
        # Load tokenizer and model based on model_name
        if 'bert-' in model_name:
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertModel.from_pretrained(model_name)
        elif 'roberta' in model_name:
            self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
            self.model = RobertaModel.from_pretrained(model_name)
        elif 'distilbert' in model_name:
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
            self.model = DistilBertModel.from_pretrained(model_name)
        else:
            # Default to Auto classes for other models
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
        
        self.model.to(device)
        self.model.eval()
    
    def extract_embeddings(self, essays, batch_size=8, strategy='mean'):
        """
        Extract embeddings from essays
        
        Parameters:
        - essays: List of essay texts
        - batch_size: Batch size for processing
        - strategy: How to combine token embeddings ('mean', 'cls', or 'pooled')
        
        Returns:
        - Array of essay embeddings
        """
        all_embeddings = []
        
        for i in tqdm(range(0, len(essays), batch_size), desc="Extracting embeddings"):
            batch_essays = essays[i:i+batch_size]
            
            # Tokenize
            encoded_input = self.tokenizer(
                batch_essays,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors='pt'
            ).to(device)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**encoded_input)
            
            # Process embeddings based on strategy
            if strategy == 'cls':
                # Use [CLS] token embedding
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            elif strategy == 'pooled' and hasattr(outputs, 'pooler_output'):
                # Use pooled output if available
                batch_embeddings = outputs.pooler_output.cpu().numpy()
            else:
                # Default: mean of all token embeddings
                # Create attention mask to ignore padding tokens
                attention_mask = encoded_input['attention_mask'].unsqueeze(-1).cpu().numpy()
                embeddings = outputs.last_hidden_state.cpu().numpy()
                # Calculate mean, ignoring padding tokens
                batch_embeddings = np.sum(embeddings * attention_mask, axis=1) / np.sum(attention_mask, axis=1)
            
            all_embeddings.append(batch_embeddings)
        
        return np.vstack(all_embeddings)

class EnhancedMLPRegressor(torch.nn.Module):
    """Enhanced MLP model for essay scoring"""
    
    def __init__(self, input_size, hidden_sizes=[256, 128, 64], dropout_rates=[0.3, 0.3, 0.2]):
        super(EnhancedMLPRegressor, self).__init__()
        
        # Ensure hidden_sizes and dropout_rates have the same length
        assert len(hidden_sizes) == len(dropout_rates), "hidden_sizes and dropout_rates must have the same length"
        
        layers = []
        prev_size = input_size
        
        # Create hidden layers
        for i, (hidden_size, dropout_rate) in enumerate(zip(hidden_sizes, dropout_rates)):
            layers.append(torch.nn.Linear(prev_size, hidden_size))
            layers.append(torch.nn.ReLU())
            layers.append(torch.nn.BatchNorm1d(hidden_size))  # Add batch normalization
            layers.append(torch.nn.Dropout(dropout_rate))
            prev_size = hidden_size
        
        # Output layer
        layers.append(torch.nn.Linear(prev_size, 1))
        
        self.layers = torch.nn.Sequential(*layers)
    
    def forward(self, x):
        return self.layers(x)

class AESSystem:
    """Complete Automated Essay Scoring System"""
    
    def __init__(self, model_name='roberta-base', preprocessing=True, embedding_strategy='mean'):
        self.model_name = model_name
        self.preprocessing = preprocessing
        self.embedding_strategy = embedding_strategy
        
        # Initialize components
        if preprocessing:
            self.preprocessor = TextPreprocessor(remove_stopwords=True, lemmatize=True)
        self.feature_extractor = FeatureExtractor(model_name=model_name)
        
        # Will be initialized during training
        self.mlp_model = None
        self.score_scaler = None
        self.score_range = None
    
    def prepare_data(self, data_path, essay_set=None):
        """
        Load and prepare data
        
        Parameters:
        - data_path: Path to the ASAP dataset
        - essay_set: Optional, specific essay set to use (1-8)
        
        Returns:
        - Processed DataFrame
        """
        # Load data
        df = pd.read_csv(data_path, sep='\t', encoding="ISO-8859-1")
        
        # Create a smaller DataFrame with only the needed columns
        dataset = pd.DataFrame({
            'essay_id': df['essay_id'],
            'essay_set': df['essay_set'],
            'essay': df['essay'],
            'score': df['domain1_score']
        })
        
        # Filter by essay set if specified
        if essay_set is not None:
            dataset = dataset[dataset['essay_set'] == essay_set]
        
        # Preprocess essays if enabled
        if self.preprocessing:
            print("Preprocessing essays...")
            dataset['processed_essay'] = dataset['essay'].apply(self.preprocessor.preprocess)
        else:
            dataset['processed_essay'] = dataset['essay']
        
        # Get score ranges for each essay set
        score_ranges = {}
        for set_id in dataset['essay_set'].unique():
            set_df = dataset[dataset['essay_set'] == set_id]
            score_ranges[set_id] = (set_df['score'].min(), set_df['score'].max())
        self.score_range = score_ranges
        
        # Scale scores per essay set
        self.score_scaler = {}
        dataset['scaled_score'] = 0.0
        
        for set_id in dataset['essay_set'].unique():
            set_mask = dataset['essay_set'] == set_id
            set_scores = dataset.loc[set_mask, 'score'].values.reshape(-1, 1)
            
            scaler = StandardScaler()
            scaled_scores = scaler.fit_transform(set_scores)
            
            dataset.loc[set_mask, 'scaled_score'] = scaled_scores.flatten()
            self.score_scaler[set_id] = scaler
        
        return dataset
    
    def extract_features(self, dataset):
        """Extract features from essays"""
        print("Extracting features...")
        embeddings = self.feature_extractor.extract_embeddings(
            dataset['processed_essay'].tolist(),
            strategy=self.embedding_strategy
        )
        
        # Create a mapping from essay_id to embedding index
        id2emb = {essay_id: i for i, essay_id in enumerate(dataset['essay_id'])}
        
        return embeddings, id2emb
    
    def get_data_loader(self, df, embeddings, id2emb, batch_size=128, shuffle=True):
        """Create a DataLoader for the given DataFrame"""
        # Get embeddings for each essay_id
        batch_embeddings = np.array([embeddings[id2emb[id]] for id in df['essay_id']])
        
        # Create dataset and dataloader
        data = TensorDataset(
            torch.from_numpy(batch_embeddings).float(),
            torch.from_numpy(np.array(df['scaled_score'])).float()
        )
        loader = DataLoader(data, batch_size=batch_size, shuffle=shuffle)
        
        return loader
    
    def train(self, train_loader, val_loader=None, epochs=20, learning_rate=0.001, hidden_sizes=[256, 128, 64]):
        """Train the MLP model"""
        input_size = next(iter(train_loader))[0].shape[1]
        
        # Initialize model
        self.mlp_model = EnhancedMLPRegressor(
            input_size=input_size,
            hidden_sizes=hidden_sizes,
            dropout_rates=[0.3, 0.3, 0.2]
        ).to(device)
        
        # Loss function and optimizer
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(self.mlp_model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=3, verbose=True
        )
        
        # Training loop
        train_losses = []
        val_losses = []
        
        for epoch in range(epochs):
            # Training
            self.mlp_model.train()
            train_loss = 0.0
            samples = 0
            
            for inputs, targets in train_loader:
                inputs = inputs.to(device)
                targets = targets.reshape(-1, 1).to(device)
                
                # Forward pass
                outputs = self.mlp_model(inputs)
                loss = criterion(outputs, targets)
                
                # Backward pass and optimize
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item() * inputs.size(0)
                samples += inputs.size(0)
            
            train_loss /= samples
            train_losses.append(train_loss)
            
            # Validation
            if val_loader is not None:
                val_loss, _ = self.evaluate(val_loader)
                val_losses.append(val_loss)
                
                # Update learning rate
                scheduler.step(val_loss)
                
                print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            else:
                print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}")
        
        return train_losses, val_losses
    
    def evaluate(self, data_loader, return_predictions=False):
        """Evaluate the model on the given data loader"""
        self.mlp_model.eval()
        total_loss = 0.0
        samples = 0
        predictions = []
        targets_list = []
        
        criterion = torch.nn.MSELoss()
        
        with torch.no_grad():
            for inputs, targets in data_loader:
                inputs = inputs.to(device)
                targets = targets.reshape(-1, 1).to(device)
                
                outputs = self.mlp_model(inputs)
                loss = criterion(outputs, targets)
                
                total_loss += loss.item() * inputs.size(0)
                samples += inputs.size(0)
                
                if return_predictions:
                    predictions.extend(outputs.cpu().numpy().flatten())
                    targets_list.extend(targets.cpu().numpy().flatten())
        
        avg_loss = total_loss / samples
        
        if return_predictions:
            return avg_loss, predictions, targets_list
        else:
            return avg_loss, None
    
    def predict(self, essays, essay_set):
        """
        Predict scores for new essays
        
        Parameters:
        - essays: List of essay texts
        - essay_set: The essay set number (1-8)
        
        Returns:
        - Predicted scores
        """
        # Preprocess essays if enabled
        if self.preprocessing:
            processed_essays = [self.preprocessor.preprocess(essay) for essay in essays]
        else:
            processed_essays = essays
        
        # Extract features
        embeddings = self.feature_extractor.extract_embeddings(
            processed_essays,
            strategy=self.embedding_strategy
        )
        
        # Make predictions
        self.mlp_model.eval()
        with torch.no_grad():
            inputs = torch.from_numpy(embeddings).float().to(device)
            outputs = self.mlp_model(inputs).cpu().numpy().flatten()
        
        # Rescale predictions to original score range
        scaler = self.score_scaler[essay_set]
        predictions = scaler.inverse_transform(outputs.reshape(-1, 1)).flatten()
        
        # Clip to valid score range
        min_score, max_score = self.score_range[essay_set]
        predictions = np.clip(predictions, min_score, max_score)
        
        # Round to nearest valid score (assuming integer scores)
        predictions = np.round(predictions).astype(int)
        
        return predictions
    
    def cross_validate(self, dataset, embeddings, id2emb, n_splits=5, epochs=20):
        """Perform k-fold cross-validation"""
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        fold_results = []
        all_predictions = []
        all_targets = []
        
        for fold, (train_idx, test_idx) in enumerate(kf.split(dataset)):
            print(f"\n{'='*50}\nFold {fold+1}/{n_splits}\n{'='*50}")
            
            # Split data
            train_df = dataset.iloc[train_idx].reset_index(drop=True)
            test_df = dataset.iloc[test_idx].reset_index(drop=True)
            
            # Create data loaders
            train_loader = self.get_data_loader(train_df, embeddings, id2emb)
            test_loader = self.get_data_loader(test_df, embeddings, id2emb, shuffle=False)
            
            # Train model
            self.train(train_loader, epochs=epochs)
            
            # Evaluate
            _, predictions, targets = self.evaluate(test_loader, return_predictions=True)
            
            # Convert scaled predictions back to original scores
            original_predictions = []
            original_targets = []
            
            for i, essay_id in enumerate(test_df['essay_id']):
                essay_set = test_df.loc[test_df['essay_id'] == essay_id, 'essay_set'].values[0]
                scaler = self.score_scaler[essay_set]
                
                pred = scaler.inverse_transform([[predictions[i]]])[0][0]
                target = scaler.inverse_transform([[targets[i]]])[0][0]
                
                original_predictions.append(pred)
                original_targets.append(target)
            
            # Calculate metrics
            mse = mean_squared_error(original_targets, original_predictions)
            qwk = cohen_kappa_score(
                np.round(original_targets).astype(int),
                np.round(original_predictions).astype(int),
                weights='quadratic'
            )
            
            print(f"Fold {fold+1} - MSE: {mse:.4f}, QWK: {qwk:.4f}")
            
            fold_results.append({
                'fold': fold+1,
                'mse': mse,
                'qwk': qwk
            })
            
            all_predictions.extend(original_predictions)
            all_targets.extend(original_targets)
        
        # Overall metrics
        overall_mse = mean_squared_error(all_targets, all_predictions)
        overall_qwk = cohen_kappa_score(
            np.round(all_targets).astype(int),
            np.round(all_predictions).astype(int),
            weights='quadratic'
        )
        
        print(f"\n{'='*50}")
        print(f"Overall - MSE: {overall_mse:.4f}, QWK: {overall_qwk:.4f}")
        
        return fold_results, overall_mse, overall_qwk
    
    def save_model(self, path):
        """Save the trained model"""
        if self.mlp_model is None:
            raise ValueError("Model has not been trained yet")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save model state
        model_state = {
            'model_state_dict': self.mlp_model.state_dict(),
            'model_name': self.model_name,
            'preprocessing': self.preprocessing,
            'embedding_strategy': self.embedding_strategy,
            'score_scaler': self.score_scaler,
            'score_range': self.score_range
        }
        
        torch.save(model_state, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path, hidden_sizes=[256, 128, 64]):
        """Load a trained model"""
        model_state = torch.load(path, map_location=device)
        
        # Set attributes
        self.model_name = model_state['model_name']
        self.preprocessing = model_state['preprocessing']
        self.embedding_strategy = model_state['embedding_strategy']
        self.score_scaler = model_state['score_scaler']
        self.score_range = model_state['score_range']
        
        # Reinitialize feature extractor with the correct model
        self.feature_extractor = FeatureExtractor(model_name=self.model_name)
        
        # Initialize preprocessor if needed
        if self.preprocessing:
            self.preprocessor = TextPreprocessor(remove_stopwords=True, lemmatize=True)
        
        # Get input size from the first layer of the saved model
        first_layer_weight = next(iter(model_state['model_state_dict'].items()))[1]
        input_size = first_layer_weight.shape[1]
        
        # Initialize model architecture
        self.mlp_model = EnhancedMLPRegressor(
            input_size=input_size,
            hidden_sizes=hidden_sizes,
            dropout_rates=[0.3, 0.3, 0.2]
        ).to(device)
        
        # Load weights
        self.mlp_model.load_state_dict(model_state['model_state_dict'])
        self.mlp_model.eval()
        
        print(f"Model loaded from {path}")

def main():
    """Main function to run the AES system"""
    parser = argparse.ArgumentParser(description='Automated Essay Scoring System')
    parser.add_argument('--data_path', type=str, default='data/training_set_rel3.tsv',
                        help='Path to the ASAP dataset')
    parser.add_argument('--model_name', type=str, default='roberta-base',
                        choices=['bert-base-uncased', 'roberta-base', 'distilbert-base-uncased'],
                        help='Transformer model to use')
    parser.add_argument('--essay_set', type=int, default=None,
                        help='Specific essay set to use (1-8)')
    parser.add_argument('--preprocessing', action='store_true',
                        help='Apply advanced text preprocessing')
    parser.add_argument('--embedding_strategy', type=str, default='mean',
                        choices=['mean', 'cls', 'pooled'],
                        help='Strategy for combining token embeddings')
    parser.add_argument('--epochs', type=int, default=20,
                        help='Number of training epochs')
    parser.add_argument('--cv', action='store_true',
                        help='Perform cross-validation')
    parser.add_argument('--save_path', type=str, default='models/aes_model.pt',
                        help='Path to save the trained model')
    
    args = parser.parse_args()
    
    # Initialize AES system
    aes = AESSystem(
        model_name=args.model_name,
        preprocessing=args.preprocessing,
        embedding_strategy=args.embedding_strategy
    )
    
    # Prepare data
    dataset = aes.prepare_data(args.data_path, essay_set=args.essay_set)
    print(f"Dataset shape: {dataset.shape}")
    
    # Extract features
    embeddings, id2emb = aes.extract_features(dataset)
    print(f"Embeddings shape: {embeddings.shape}")
    
    if args.cv:
        # Perform cross-validation
        fold_results, overall_mse, overall_qwk = aes.cross_validate(
            dataset, embeddings, id2emb, epochs=args.epochs
        )
    else:
        # Split data into train and test sets (80/20)
        from sklearn.model_selection import train_test_split
        
        train_df, test_df = train_test_split(dataset, test_size=0.2, random_state=42)
        
        # Create data loaders
        train_loader = aes.get_data_loader(train_df, embeddings, id2emb)
        test_loader = aes.get_data_loader(test_df, embeddings, id2emb, shuffle=False)
        
        # Train model
        train_losses, val_losses = aes.train(train_loader, test_loader, epochs=args.epochs)
        
        # Evaluate
        test_loss, predictions, targets = aes.evaluate(test_loader, return_predictions=True)
        
        # Convert scaled predictions back to original scores
        original_predictions = []
        original_targets = []
        
        for i, essay_id in enumerate(test_df['essay_id']):
            essay_set = test_df.loc[test_df['essay_id'] == essay_id, 'essay_set'].values[0]
            scaler = aes.score_scaler[essay_set]
            
            pred = scaler.inverse_transform([[predictions[i]]])[0][0]
            target = scaler.inverse_transform([[targets[i]]])[0][0]
            
            original_predictions.append(pred)
            original_targets.append(target)
        
        # Calculate metrics
        mse = mean_squared_error(original_targets, original_predictions)
        qwk = cohen_kappa_score(
            np.round(original_targets).astype(int),
            np.round(original_predictions).astype(int),
            weights='quadratic'
        )
        
        print(f"Test MSE: {mse:.4f}, QWK: {qwk:.4f}")
        
        # Save model
        if args.save_path:
            aes.save_model(args.save_path)

if __name__ == "__main__":
    main()
