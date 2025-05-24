"""
Model Signal Interface for Trading System
Connects prediction models with trading strategies
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class SignalType:
    """Signal types for trading decisions"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class ModelSignal:
    """Container for model-generated trading signals"""
    
    def __init__(self, signal_type: str, confidence: float, 
                 predicted_price: float, current_price: float,
                 model_name: str, timestamp: datetime = None):
        self.signal_type = signal_type
        self.confidence = confidence  # 0.0 to 1.0
        self.predicted_price = predicted_price
        self.current_price = current_price
        self.model_name = model_name
        self.timestamp = timestamp or datetime.now()
        
        # Calculate price change percentage
        self.price_change_percent = ((predicted_price - current_price) / current_price) * 100
        
    def __repr__(self):
        return (f"ModelSignal({self.signal_type}, confidence={self.confidence:.2f}, "
                f"price_change={self.price_change_percent:.2f}%, model={self.model_name})")

class BaseModelSignalGenerator(ABC):
    """Base class for generating trading signals from model predictions"""
    
    def __init__(self, model_name: str, 
                 buy_threshold: float = 2.0,
                 sell_threshold: float = -2.0,
                 strong_threshold: float = 5.0):
        self.model_name = model_name
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.strong_threshold = strong_threshold
        
    @abstractmethod
    def generate_signal(self, prediction: float, current_price: float, 
                       confidence: float = 1.0) -> ModelSignal:
        """Generate trading signal from model prediction"""
        pass
    
    def _determine_signal_type(self, price_change_percent: float) -> str:
        """Determine signal type based on price change percentage"""
        if price_change_percent >= self.strong_threshold:
            return SignalType.STRONG_BUY
        elif price_change_percent >= self.buy_threshold:
            return SignalType.BUY
        elif price_change_percent <= -self.strong_threshold:
            return SignalType.STRONG_SELL
        elif price_change_percent <= self.sell_threshold:
            return SignalType.SELL
        else:
            return SignalType.HOLD

class LSTMSignalGenerator(BaseModelSignalGenerator):
    """Signal generator for LSTM model predictions"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__("LSTM", buy_threshold=1.5, sell_threshold=-1.5, strong_threshold=4.0)
        self.confidence_threshold = confidence_threshold
        
    def generate_signal(self, prediction: float, current_price: float, 
                       confidence: float = 1.0) -> ModelSignal:
        price_change_percent = ((prediction - current_price) / current_price) * 100
        
        # Adjust confidence based on model characteristics
        adjusted_confidence = confidence * 0.9  # LSTM typically has good accuracy
        
        signal_type = self._determine_signal_type(price_change_percent)
        
        # Lower confidence for weak signals
        if signal_type == SignalType.HOLD:
            adjusted_confidence *= 0.5
            
        return ModelSignal(
            signal_type=signal_type,
            confidence=adjusted_confidence,
            predicted_price=prediction,
            current_price=current_price,
            model_name=self.model_name
        )

class TransformerSignalGenerator(BaseModelSignalGenerator):
    """Signal generator for Transformer model predictions"""
    
    def __init__(self):
        super().__init__("Transformer", buy_threshold=2.5, sell_threshold=-2.5, strong_threshold=6.0)
        
    def generate_signal(self, prediction: float, current_price: float, 
                       confidence: float = 1.0) -> ModelSignal:
        price_change_percent = ((prediction - current_price) / current_price) * 100
        
        # Transformer models can be more volatile
        adjusted_confidence = confidence * 0.8
        
        signal_type = self._determine_signal_type(price_change_percent)
        
        return ModelSignal(
            signal_type=signal_type,
            confidence=adjusted_confidence,
            predicted_price=prediction,
            current_price=current_price,
            model_name=self.model_name
        )

class CNNSignalGenerator(BaseModelSignalGenerator):
    """Signal generator for CNN model predictions"""
    
    def __init__(self):
        super().__init__("CNN", buy_threshold=2.0, sell_threshold=-2.0, strong_threshold=5.0)
        
    def generate_signal(self, prediction: float, current_price: float, 
                       confidence: float = 1.0) -> ModelSignal:
        price_change_percent = ((prediction - current_price) / current_price) * 100
        
        # CNN models good for pattern recognition
        adjusted_confidence = confidence * 0.85
        
        signal_type = self._determine_signal_type(price_change_percent)
        
        return ModelSignal(
            signal_type=signal_type,
            confidence=adjusted_confidence,
            predicted_price=prediction,
            current_price=current_price,
            model_name=self.model_name
        )

class ModelSignalManager:
    """Manages multiple model signal generators"""
    
    def __init__(self):
        self.generators = {
            'LSTM': LSTMSignalGenerator(),
            'Transformer': TransformerSignalGenerator(),
            'CNN': CNNSignalGenerator(),
            'GRU': LSTMSignalGenerator(),  # Use LSTM generator for GRU (similar characteristics)
        }
        self.signal_history = []
        
    def add_generator(self, model_name: str, generator: BaseModelSignalGenerator):
        """Add custom signal generator"""
        self.generators[model_name] = generator
        
    def generate_signal(self, model_name: str, prediction: float, 
                       current_price: float, confidence: float = 1.0) -> Optional[ModelSignal]:
        """Generate signal from specific model"""
        if model_name not in self.generators:
            logger.warning(f"No signal generator found for model: {model_name}")
            return None
            
        try:
            signal = self.generators[model_name].generate_signal(
                prediction, current_price, confidence
            )
            
            # Store signal in history
            self.signal_history.append(signal)
            
            # Keep only last 100 signals
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
                
            logger.info(f"Generated signal: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {model_name}: {e}")
            return None
    
    def generate_ensemble_signal(self, predictions: Dict[str, Tuple[float, float]], 
                                current_price: float) -> Optional[ModelSignal]:
        """Generate ensemble signal from multiple model predictions"""
        if not predictions:
            return None
            
        signals = []
        total_confidence = 0
        
        for model_name, (prediction, confidence) in predictions.items():
            signal = self.generate_signal(model_name, prediction, current_price, confidence)
            if signal:
                signals.append(signal)
                total_confidence += confidence
        
        if not signals:
            return None
            
        # Calculate weighted average prediction
        weighted_prediction = sum(s.predicted_price * s.confidence for s in signals) / sum(s.confidence for s in signals)
        
        # Calculate ensemble confidence
        ensemble_confidence = total_confidence / len(signals)
        
        # Determine ensemble signal type
        price_change_percent = ((weighted_prediction - current_price) / current_price) * 100
        
        if price_change_percent >= 5.0:
            signal_type = SignalType.STRONG_BUY
        elif price_change_percent >= 2.0:
            signal_type = SignalType.BUY
        elif price_change_percent <= -5.0:
            signal_type = SignalType.STRONG_SELL
        elif price_change_percent <= -2.0:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
            
        # Boost ensemble confidence
        ensemble_confidence *= 1.1  # Ensemble typically more reliable
        ensemble_confidence = min(ensemble_confidence, 1.0)
        
        ensemble_signal = ModelSignal(
            signal_type=signal_type,
            confidence=ensemble_confidence,
            predicted_price=weighted_prediction,
            current_price=current_price,
            model_name="Ensemble"
        )
        
        logger.info(f"Generated ensemble signal: {ensemble_signal}")
        return ensemble_signal
    
    def get_recent_signals(self, model_name: str = None, limit: int = 10) -> List[ModelSignal]:
        """Get recent signals, optionally filtered by model"""
        signals = self.signal_history
        
        if model_name:
            signals = [s for s in signals if s.model_name == model_name]
            
        return signals[-limit:]
    
    def get_signal_statistics(self, model_name: str = None) -> Dict[str, Any]:
        """Get statistics about generated signals"""
        signals = self.signal_history
        
        if model_name:
            signals = [s for s in signals if s.model_name == model_name]
            
        if not signals:
            return {}
            
        signal_counts = {}
        total_confidence = 0
        
        for signal in signals:
            signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
            total_confidence += signal.confidence
            
        return {
            'total_signals': len(signals),
            'signal_distribution': signal_counts,
            'average_confidence': total_confidence / len(signals),
            'latest_signal': signals[-1].signal_type if signals else None
        }

# Global signal manager instance
signal_manager = ModelSignalManager()
