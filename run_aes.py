#!/usr/bin/env python3
"""
Script to run the improved Automated Essay Scoring (AES) system
"""

import os
import argparse
from aes_model import AESSystem

def main():
    parser = argparse.ArgumentParser(description='Run Automated Essay Scoring System')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train a new AES model')
    train_parser.add_argument('--data_path', type=str, required=True,
                        help='Path to the ASAP dataset')
    train_parser.add_argument('--model_name', type=str, default='roberta-base',
                        choices=['bert-base-uncased', 'roberta-base', 'distilbert-base-uncased'],
                        help='Transformer model to use')
    train_parser.add_argument('--essay_set', type=int, default=None,
                        help='Specific essay set to use (1-8)')
    train_parser.add_argument('--preprocessing', action='store_true',
                        help='Apply advanced text preprocessing')
    train_parser.add_argument('--embedding_strategy', type=str, default='mean',
                        choices=['mean', 'cls', 'pooled'],
                        help='Strategy for combining token embeddings')
    train_parser.add_argument('--epochs', type=int, default=20,
                        help='Number of training epochs')
    train_parser.add_argument('--cv', action='store_true',
                        help='Perform cross-validation')
    train_parser.add_argument('--save_path', type=str, default='models/aes_model.pt',
                        help='Path to save the trained model')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate an existing AES model')
    eval_parser.add_argument('--model_path', type=str, required=True,
                        help='Path to the trained model')
    eval_parser.add_argument('--data_path', type=str, required=True,
                        help='Path to the evaluation dataset')
    eval_parser.add_argument('--essay_set', type=int, default=None,
                        help='Specific essay set to use (1-8)')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Score new essays')
    predict_parser.add_argument('--model_path', type=str, required=True,
                        help='Path to the trained model')
    predict_parser.add_argument('--essay_path', type=str, required=True,
                        help='Path to the file containing essays to score')
    predict_parser.add_argument('--essay_set', type=int, required=True,
                        help='Essay set number (1-8)')
    predict_parser.add_argument('--output_path', type=str, default='predictions.csv',
                        help='Path to save the predictions')
    
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs('models', exist_ok=True)
    
    if args.command == 'train':
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
            from sklearn.metrics import mean_squared_error, cohen_kappa_score
            import numpy as np
            
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
    
    elif args.command == 'evaluate':
        # Load model
        aes = AESSystem()
        aes.load_model(args.model_path)
        
        # Prepare data
        dataset = aes.prepare_data(args.data_path, essay_set=args.essay_set)
        print(f"Dataset shape: {dataset.shape}")
        
        # Extract features
        embeddings, id2emb = aes.extract_features(dataset)
        
        # Create data loader
        data_loader = aes.get_data_loader(dataset, embeddings, id2emb, shuffle=False)
        
        # Evaluate
        loss, predictions, targets = aes.evaluate(data_loader, return_predictions=True)
        
        # Convert scaled predictions back to original scores
        original_predictions = []
        original_targets = []
        
        for i, essay_id in enumerate(dataset['essay_id']):
            essay_set = dataset.loc[dataset['essay_id'] == essay_id, 'essay_set'].values[0]
            scaler = aes.score_scaler[essay_set]
            
            pred = scaler.inverse_transform([[predictions[i]]])[0][0]
            target = scaler.inverse_transform([[targets[i]]])[0][0]
            
            original_predictions.append(pred)
            original_targets.append(target)
        
        # Calculate metrics
        from sklearn.metrics import mean_squared_error, cohen_kappa_score
        import numpy as np
        
        mse = mean_squared_error(original_targets, original_predictions)
        qwk = cohen_kappa_score(
            np.round(original_targets).astype(int),
            np.round(original_predictions).astype(int),
            weights='quadratic'
        )
        
        print(f"Evaluation MSE: {mse:.4f}, QWK: {qwk:.4f}")
    
    elif args.command == 'predict':
        # Load model
        aes = AESSystem()
        aes.load_model(args.model_path)
        
        # Load essays
        import pandas as pd
        
        if args.essay_path.endswith('.csv'):
            essays_df = pd.read_csv(args.essay_path)
            essays = essays_df['essay'].tolist()
        elif args.essay_path.endswith('.txt'):
            with open(args.essay_path, 'r', encoding='utf-8') as f:
                essays = [line.strip() for line in f if line.strip()]
        else:
            raise ValueError("Essay file must be .csv or .txt")
        
        # Predict scores
        predictions = aes.predict(essays, args.essay_set)
        
        # Save predictions
        if args.essay_path.endswith('.csv'):
            essays_df['predicted_score'] = predictions
            essays_df.to_csv(args.output_path, index=False)
        else:
            pd.DataFrame({
                'essay': essays,
                'predicted_score': predictions
            }).to_csv(args.output_path, index=False)
        
        print(f"Predictions saved to {args.output_path}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
