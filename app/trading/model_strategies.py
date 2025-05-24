"""
Model-driven trading strategies
"""

from app.trading.trading_strategies import Strategy, Action
from app.trading.model_signals import signal_manager, SignalType, ModelSignal
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ModelDrivenStrategy(Strategy):
    """Base strategy that uses model predictions for trading decisions"""
    
    def __init__(self, name: str = "Model Driven", initial_balance: float = 10000,
                 model_name: str = "LSTM", confidence_threshold: float = 0.7,
                 position_size: float = 1.0, stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.1):
        super().__init__(name=name, initial_balance=initial_balance)
        
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Track entry prices for stop loss/take profit
        self.entry_price = None
        self.last_signal = None
        
    def decide_action(self, current_data):
        """Make trading decision based on model signal"""
        current_price = current_data.get('close', 0)
        
        # Check stop loss and take profit first
        if self.position and self.entry_price:
            if self._should_stop_loss(current_price) or self._should_take_profit(current_price):
                self.entry_price = None
                return Action.SELL
        
        # Get model prediction (this would come from prediction service)
        prediction = self._get_model_prediction(current_data)
        if prediction is None:
            return Action.HOLD
            
        # Generate signal
        signal = signal_manager.generate_signal(
            self.model_name, prediction, current_price
        )
        
        if signal is None or signal.confidence < self.confidence_threshold:
            return Action.HOLD
            
        self.last_signal = signal
        
        # Make trading decision based on signal
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY] and not self.position:
            self.entry_price = current_price
            return Action.BUY
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL] and self.position:
            self.entry_price = None
            return Action.SELL
            
        return Action.HOLD
    
    def _get_model_prediction(self, current_data) -> Optional[float]:
        """Get prediction from model (placeholder - would integrate with prediction service)"""
        # This is a placeholder - in real implementation, this would call
        # the prediction service to get actual model predictions
        current_price = current_data.get('close', 0)
        
        # Simulate model prediction with some randomness
        import random
        prediction_change = random.uniform(-0.02, 0.02)  # ±2% change
        return current_price * (1 + prediction_change)
    
    def _should_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss should be triggered"""
        if not self.entry_price:
            return False
        
        loss_pct = (self.entry_price - current_price) / self.entry_price
        return loss_pct >= self.stop_loss_pct
    
    def _should_take_profit(self, current_price: float) -> bool:
        """Check if take profit should be triggered"""
        if not self.entry_price:
            return False
        
        profit_pct = (current_price - self.entry_price) / self.entry_price
        return profit_pct >= self.take_profit_pct

class LSTMStrategy(ModelDrivenStrategy):
    """Strategy specifically tuned for LSTM model signals"""
    
    def __init__(self, initial_balance: float = 10000):
        super().__init__(
            name="LSTM Strategy",
            initial_balance=initial_balance,
            model_name="LSTM",
            confidence_threshold=0.75,
            position_size=0.8,
            stop_loss_pct=0.03,
            take_profit_pct=0.06
        )

class TransformerStrategy(ModelDrivenStrategy):
    """Strategy specifically tuned for Transformer model signals"""
    
    def __init__(self, initial_balance: float = 10000):
        super().__init__(
            name="Transformer Strategy",
            initial_balance=initial_balance,
            model_name="Transformer",
            confidence_threshold=0.6,  # Lower threshold due to volatility
            position_size=0.6,  # Smaller position size
            stop_loss_pct=0.04,
            take_profit_pct=0.08
        )

class CNNStrategy(ModelDrivenStrategy):
    """Strategy specifically tuned for CNN model signals"""
    
    def __init__(self, initial_balance: float = 10000):
        super().__init__(
            name="CNN Strategy",
            initial_balance=initial_balance,
            model_name="CNN",
            confidence_threshold=0.7,
            position_size=0.7,
            stop_loss_pct=0.035,
            take_profit_pct=0.07
        )

class EnsembleStrategy(Strategy):
    """Strategy that uses multiple models for trading decisions"""
    
    def __init__(self, name: str = "Ensemble Strategy", initial_balance: float = 10000,
                 models: List[str] = None, confidence_threshold: float = 0.8,
                 consensus_threshold: float = 0.6):
        super().__init__(name=name, initial_balance=initial_balance)
        
        self.models = models or ['LSTM', 'CNN', 'Transformer']
        self.confidence_threshold = confidence_threshold
        self.consensus_threshold = consensus_threshold  # Percentage of models that must agree
        
        self.entry_price = None
        self.stop_loss_pct = 0.04
        self.take_profit_pct = 0.08
        
    def decide_action(self, current_data):
        """Make trading decision based on ensemble of model signals"""
        current_price = current_data.get('close', 0)
        
        # Check stop loss and take profit first
        if self.position and self.entry_price:
            if self._should_stop_loss(current_price) or self._should_take_profit(current_price):
                self.entry_price = None
                return Action.SELL
        
        # Get predictions from all models
        predictions = {}
        for model_name in self.models:
            prediction = self._get_model_prediction(current_data, model_name)
            if prediction is not None:
                # Simulate confidence (in real implementation, this would come from model)
                import random
                confidence = random.uniform(0.6, 0.95)
                predictions[model_name] = (prediction, confidence)
        
        if not predictions:
            return Action.HOLD
            
        # Generate ensemble signal
        ensemble_signal = signal_manager.generate_ensemble_signal(predictions, current_price)
        
        if ensemble_signal is None or ensemble_signal.confidence < self.confidence_threshold:
            return Action.HOLD
        
        # Check consensus among individual signals
        buy_signals = 0
        sell_signals = 0
        total_signals = 0
        
        for model_name, (prediction, confidence) in predictions.items():
            signal = signal_manager.generate_signal(model_name, prediction, current_price, confidence)
            if signal:
                total_signals += 1
                if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                    buy_signals += 1
                elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                    sell_signals += 1
        
        if total_signals == 0:
            return Action.HOLD
            
        buy_consensus = buy_signals / total_signals
        sell_consensus = sell_signals / total_signals
        
        # Make trading decision
        if (ensemble_signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY] and
            buy_consensus >= self.consensus_threshold and not self.position):
            self.entry_price = current_price
            return Action.BUY
        elif (ensemble_signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL] and
              sell_consensus >= self.consensus_threshold and self.position):
            self.entry_price = None
            return Action.SELL
            
        return Action.HOLD
    
    def _get_model_prediction(self, current_data, model_name: str) -> Optional[float]:
        """Get prediction from specific model"""
        # Placeholder implementation
        current_price = current_data.get('close', 0)
        import random
        
        # Different models might have different prediction characteristics
        if model_name == "LSTM":
            change = random.uniform(-0.015, 0.015)
        elif model_name == "Transformer":
            change = random.uniform(-0.025, 0.025)
        elif model_name == "CNN":
            change = random.uniform(-0.02, 0.02)
        else:
            change = random.uniform(-0.02, 0.02)
            
        return current_price * (1 + change)
    
    def _should_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss should be triggered"""
        if not self.entry_price:
            return False
        
        loss_pct = (self.entry_price - current_price) / self.entry_price
        return loss_pct >= self.stop_loss_pct
    
    def _should_take_profit(self, current_price: float) -> bool:
        """Check if take profit should be triggered"""
        if not self.entry_price:
            return False
        
        profit_pct = (current_price - self.entry_price) / self.entry_price
        return profit_pct >= self.take_profit_pct

class AdaptiveEnsembleStrategy(EnsembleStrategy):
    """Ensemble strategy that adapts model weights based on recent performance"""
    
    def __init__(self, initial_balance: float = 10000):
        super().__init__(
            name="Adaptive Ensemble Strategy",
            initial_balance=initial_balance,
            confidence_threshold=0.75,
            consensus_threshold=0.5
        )
        
        # Track model performance
        self.model_performance = {model: {'correct': 0, 'total': 0} for model in self.models}
        self.performance_window = 50  # Number of recent predictions to consider
        
    def update_model_performance(self, model_name: str, was_correct: bool):
        """Update performance tracking for a model"""
        if model_name in self.model_performance:
            self.model_performance[model_name]['total'] += 1
            if was_correct:
                self.model_performance[model_name]['correct'] += 1
                
            # Keep only recent performance
            if self.model_performance[model_name]['total'] > self.performance_window:
                # Reset counters (simple approach)
                self.model_performance[model_name]['total'] = self.performance_window
                self.model_performance[model_name]['correct'] = max(
                    0, self.model_performance[model_name]['correct'] - 5
                )
    
    def get_model_weights(self) -> Dict[str, float]:
        """Calculate adaptive weights based on recent model performance"""
        weights = {}
        
        for model_name in self.models:
            perf = self.model_performance[model_name]
            if perf['total'] > 0:
                accuracy = perf['correct'] / perf['total']
                # Convert accuracy to weight (with minimum weight of 0.1)
                weights[model_name] = max(0.1, accuracy)
            else:
                weights[model_name] = 0.5  # Default weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
