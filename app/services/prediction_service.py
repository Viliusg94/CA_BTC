"""
Service for making predictions with trained models
"""

import os
import logging
import json
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import pickle
import random

# Set up logging
logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self):
        self.app = None
        self.db = None
        self.thread = None
        self.running = False
        self.models = {}
        self.scalers = {}
        self.last_updated = {}
        
    def init_app(self, app, db=None):
        """Initialize with Flask app and database"""
        self.app = app
        self.db = db
        self.models_dir = os.path.join(os.path.dirname(app.instance_path), 'models')
        
        # Load models and scalers
        self._load_resources()
        
    def start(self):
        """Start the background thread for periodic model loading"""
        if not self.running:
            self.running = True
            # Load the actual model file
            model_path = os.path.join(self.models_dir, f"{model.model_type.lower()}_model.h5")
            scaler_path = os.path.join(self.models_dir, f"{model.model_type.lower()}_scaler.pkl")
            
            if not os.path.exists(model_path):
                # Generate mock predictions based on model performance
                return self._generate_mock_predictions(model, days)
            
            # Load the trained model and scaler
            try:
                import tensorflow as tf
                trained_model = tf.keras.models.load_model(model_path)
                
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                
                # Get recent data for prediction
                recent_data = self._get_recent_data()
                
                # Generate actual predictions
                predictions = self._predict_with_model(trained_model, scaler, recent_data, days)
                
                return predictions
                
            except Exception as e:
                logger.warning(f"Could not load model files: {e}. Using mock predictions.")
                return self._generate_mock_predictions(model, days)
                
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}", exc_info=True)
            raise
    
    def _generate_mock_predictions(self, model, days):
        """Generate mock predictions based on model performance"""
        # Get current Bitcoin price
        current_price = self._get_current_price()
        
        # Use model performance to influence prediction quality
        accuracy = model.r2 if model.r2 else 0.75
        volatility = 0.02 * (1 - accuracy)  # Lower accuracy = higher volatility
        
        predictions = []
        dates = []
        
        for i in range(days):
            # Generate prediction with some randomness
            if i == 0:
                # First prediction based on current price
                change = np.random.normal(0, volatility)
                pred_price = current_price * (1 + change)
            else:
                # Subsequent predictions based on previous prediction
                change = np.random.normal(0.001, volatility)  # Slight upward bias
                pred_price = predictions[i-1] * (1 + change)
            
            predictions.append(round(pred_price, 2))
            dates.append((datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'))
        
        return {
            'dates': dates,
            'values': predictions,
            'model_info': {
                'id': model.id,
                'type': model.model_type,
                'accuracy': accuracy
            }
        }
    
    def _get_current_price(self):
        """Get current Bitcoin price"""
        try:
            import requests
            response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
            if response.status_code == 200:
                return float(response.json()['price'])
        except:
            pass
        return 45000.0  # Fallback price
    
    def _get_recent_data(self):
        """Get recent Bitcoin data for predictions"""
        # This would typically fetch recent price data
        # For now, return mock data structure
        return np.random.random((30, 5))  # 30 time steps, 5 features
    
    def _predict_with_model(self, model, scaler, data, days):
        """Generate predictions using the actual trained model"""
        try:
            # Prepare input data
            if len(data.shape) == 2:
                # Add batch dimension
                input_data = data[-1:].reshape(1, -1, data.shape[1])
            else:
                input_data = data[-1:]
            
            predictions = []
            current_input = input_data
            
            for _ in range(days):
                # Predict next value
                pred = model.predict(current_input, verbose=0)
                predictions.append(pred[0, 0])
                
                # Update input for next prediction (sliding window)
                # This is simplified - in practice you'd need proper feature engineering
                if len(current_input.shape) == 3:
                    new_input = np.roll(current_input, -1, axis=1)
                    new_input[0, -1, 3] = pred[0, 0]  # Assuming close price is feature 3
                    current_input = new_input
            
            # Inverse transform predictions
            dummy = np.zeros((len(predictions), 5))
            dummy[:, 3] = predictions  # Close price column
            predictions_scaled = scaler.inverse_transform(dummy)[:, 3]
            
            dates = [(datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(days)]
            
            return {
                'dates': dates,
                'values': predictions_scaled.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in model prediction: {str(e)}")
            # Fall back to mock predictions
            return self._generate_mock_predictions_simple(days)
    
    def _generate_mock_predictions_simple(self, days):
        """Simple mock predictions as fallback"""
        current_price = self._get_current_price()
        predictions = []
        dates = []
        
        for i in range(days):
            # Simple random walk
            change = np.random.normal(0.001, 0.02)
            if i == 0:
                pred_price = current_price * (1 + change)
            else:
                pred_price = predictions[i-1] * (1 + change)
            
            predictions.append(round(pred_price, 2))
            dates.append((datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'))
        
        return {
            'dates': dates,
            'values': predictions
        }

# Global instance
prediction_service = PredictionService()
