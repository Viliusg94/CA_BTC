"""
Advanced ensemble trading strategies
"""

from app.trading.trading_strategies import Strategy, Action
from app.trading.model_signals import signal_manager, SignalType
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VotingEnsembleStrategy(Strategy):
    """Ensemble strategy using voting mechanism"""
    
    def __init__(self, name: str = "Voting Ensemble", initial_balance: float = 10000,
                 models: List[str] = None, voting_type: str = "majority"):
        super().__init__(name=name, initial_balance=initial_balance)
        
        self.models = models or ['LSTM', 'GRU', 'CNN', 'Transformer']
        self.voting_type = voting_type  # "majority", "unanimous", "weighted"
        
        # Risk management
        self.entry_price = None
        self.stop_loss_pct = 0.03
        self.take_profit_pct = 0.06
        self.max_position_size = 0.8
        
        # Model weights for weighted voting
        self.model_weights = {
            'LSTM': 0.3,
            'GRU': 0.25,
            'CNN': 0.2,
            'Transformer': 0.25
        }
        
    def decide_action(self, current_data):
        """Make decision based on voting ensemble"""
        current_price = current_data.get('close', 0)
        
        # Risk management first
        if self.position and self.entry_price:
            if self._should_exit_position(current_price):
                self.entry_price = None
                return Action.SELL
        
        # Get votes from all models
        votes = self._get_model_votes(current_data)
        
        if not votes:
            return Action.HOLD
            
        # Calculate final decision based on voting type
        decision = self._calculate_vote_result(votes)
        
        # Execute decision
        if decision == "BUY" and not self.position:
            self.entry_price = current_price
            return Action.BUY
        elif decision == "SELL" and self.position:
            self.entry_price = None
            return Action.SELL
            
        return Action.HOLD
    
    def _get_model_votes(self, current_data) -> Dict[str, str]:
        """Get votes from all models"""
        votes = {}
        current_price = current_data.get('close', 0)
        
        for model_name in self.models:
            prediction = self._get_model_prediction(current_data, model_name)
            if prediction is not None:
                signal = signal_manager.generate_signal(model_name, prediction, current_price)
                if signal and signal.confidence > 0.6:
                    if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                        votes[model_name] = "BUY"
                    elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                        votes[model_name] = "SELL"
                    else:
                        votes[model_name] = "HOLD"
        
        return votes
    
    def _calculate_vote_result(self, votes: Dict[str, str]) -> str:
        """Calculate final decision based on votes"""
        if not votes:
            return "HOLD"
            
        if self.voting_type == "majority":
            return self._majority_vote(votes)
        elif self.voting_type == "unanimous":
            return self._unanimous_vote(votes)
        elif self.voting_type == "weighted":
            return self._weighted_vote(votes)
        else:
            return self._majority_vote(votes)
    
    def _majority_vote(self, votes: Dict[str, str]) -> str:
        """Simple majority voting"""
        buy_count = sum(1 for vote in votes.values() if vote == "BUY")
        sell_count = sum(1 for vote in votes.values() if vote == "SELL")
        hold_count = sum(1 for vote in votes.values() if vote == "HOLD")
        
        total_votes = len(votes)
        
        if buy_count > total_votes / 2:
            return "BUY"
        elif sell_count > total_votes / 2:
            return "SELL"
        else:
            return "HOLD"
    
    def _unanimous_vote(self, votes: Dict[str, str]) -> str:
        """Require unanimous decision for action"""
        unique_votes = set(votes.values())
        
        if len(unique_votes) == 1:
            return list(unique_votes)[0]
        else:
            return "HOLD"
    
    def _weighted_vote(self, votes: Dict[str, str]) -> str:
        """Weighted voting based on model weights"""
        weighted_scores = {"BUY": 0, "SELL": 0, "HOLD": 0}
        
        for model_name, vote in votes.items():
            weight = self.model_weights.get(model_name, 0.25)
            weighted_scores[vote] += weight
        
        max_score = max(weighted_scores.values())
        winning_vote = [vote for vote, score in weighted_scores.items() if score == max_score][0]
        
        # Require minimum threshold for action
        if winning_vote in ["BUY", "SELL"] and max_score >= 0.5:
            return winning_vote
        else:
            return "HOLD"
    
    def _get_model_prediction(self, current_data, model_name: str) -> Optional[float]:
        """Get prediction from model (placeholder)"""
        current_price = current_data.get('close', 0)
        import random
        
        # Simulate different model behaviors
        volatility = {
            'LSTM': 0.015,
            'GRU': 0.012,
            'CNN': 0.018,
            'Transformer': 0.022
        }
        
        vol = volatility.get(model_name, 0.015)
        change = random.uniform(-vol, vol)
        return current_price * (1 + change)
    
    def _should_exit_position(self, current_price: float) -> bool:
        """Check if position should be exited"""
        if not self.entry_price:
            return False
            
        price_change = (current_price - self.entry_price) / self.entry_price
        
        return (price_change <= -self.stop_loss_pct or 
                price_change >= self.take_profit_pct)

class ConfidenceWeightedEnsemble(Strategy):
    """Ensemble that weights models by their confidence levels"""
    
    def __init__(self, name: str = "Confidence Weighted Ensemble", 
                 initial_balance: float = 10000):
        super().__init__(name=name, initial_balance=initial_balance)
        
        self.models = ['LSTM', 'GRU', 'CNN', 'Transformer']
        self.min_total_confidence = 2.0  # Minimum total confidence to take action
        self.entry_price = None
        
    def decide_action(self, current_data):
        """Make decision based on confidence-weighted ensemble"""
        current_price = current_data.get('close', 0)
        
        # Get predictions and confidences
        predictions = []
        confidences = []
        signals = []
        
        for model_name in self.models:
            prediction = self._get_model_prediction(current_data, model_name)
            if prediction is not None:
                import random
                confidence = random.uniform(0.5, 0.95)
                signal = signal_manager.generate_signal(model_name, prediction, current_price, confidence)
                
                if signal:
                    predictions.append(prediction)
                    confidences.append(confidence)
                    signals.append(signal)
        
        if not signals:
            return Action.HOLD
            
        # Calculate confidence-weighted average
        total_confidence = sum(confidences)
        
        if total_confidence < self.min_total_confidence:
            return Action.HOLD
            
        # Weight signals by confidence
        buy_weight = 0
        sell_weight = 0
        
        for signal, confidence in zip(signals, confidences):
            weight = confidence / total_confidence
            
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                buy_weight += weight
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                sell_weight += weight
        
        # Make decision
        if buy_weight > 0.6 and not self.position:
            self.entry_price = current_price
            return Action.BUY
        elif sell_weight > 0.6 and self.position:
            self.entry_price = None
            return Action.SELL
            
        return Action.HOLD
    
    def _get_model_prediction(self, current_data, model_name: str) -> Optional[float]:
        """Get model prediction (placeholder)"""
        current_price = current_data.get('close', 0)
        import random
        change = random.uniform(-0.02, 0.02)
        return current_price * (1 + change)

class MetaEnsembleStrategy(Strategy):
    """Meta-strategy that combines multiple ensemble approaches"""
    
    def __init__(self, name: str = "Meta Ensemble", initial_balance: float = 10000):
        super().__init__(name=name, initial_balance=initial_balance)
        
        # Create sub-strategies
        self.sub_strategies = [
            VotingEnsembleStrategy(name="Voting Sub", voting_type="majority"),
            ConfidenceWeightedEnsemble(name="Confidence Sub"),
            VotingEnsembleStrategy(name="Weighted Sub", voting_type="weighted")
        ]
        
        self.entry_price = None
        
    def decide_action(self, current_data):
        """Combine decisions from multiple ensemble strategies"""
        decisions = []
        
        for strategy in self.sub_strategies:
            decision = strategy.decide_action(current_data)
            decisions.append(decision)
        
        # Count decisions
        buy_count = decisions.count(Action.BUY)
        sell_count = decisions.count(Action.SELL)
        hold_count = decisions.count(Action.HOLD)
        
        total_decisions = len(decisions)
        
        # Meta decision logic
        if buy_count >= total_decisions * 0.6 and not self.position:
            self.entry_price = current_data.get('close', 0)
            return Action.BUY
        elif sell_count >= total_decisions * 0.6 and self.position:
            self.entry_price = None
            return Action.SELL
        else:
            return Action.HOLD
