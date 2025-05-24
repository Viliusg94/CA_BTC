"""
Strategy factory module - utilities for creating and managing trading strategies
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any, Union

from app.trading.trading_strategies import Strategy, Action
from app.trading.strategies import (
    MovingAverageStrategy, RSIStrategy, BollingerBandsStrategy, 
    MACDStrategy, MLModelStrategy, EnsembleStrategy, create_strategy
)

logger = logging.getLogger(__name__)

class StrategyFactory:
    """Factory class to create and manage trading strategies"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the strategy factory
        
        Args:
            config_dir: Directory for strategy configuration files
        """
        self.config_dir = config_dir
        self.strategy_types = {
            'moving_average': MovingAverageStrategy,
            'ma': MovingAverageStrategy,
            'rsi': RSIStrategy, 
            'bollinger_bands': BollingerBandsStrategy,
            'bb': BollingerBandsStrategy,
            'macd': MACDStrategy,
            'ml_model': MLModelStrategy,
            'ensemble': EnsembleStrategy
        }
    
    def create_strategy(self, strategy_type: str, **kwargs) -> Strategy:
        """
        Create a strategy instance
        
        Args:
            strategy_type: Type of strategy to create
            **kwargs: Strategy parameters
            
        Returns:
            Strategy: Instance of the specified strategy
        """
        strategy_type = strategy_type.lower()
        if strategy_type not in self.strategy_types:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        strategy_class = self.strategy_types[strategy_type]
        return strategy_class(**kwargs)
    
    def create_strategy_from_config(self, config: Dict) -> Strategy:
        """
        Create a strategy instance from a configuration dictionary
        
        Args:
            config: Strategy configuration
            
        Returns:
            Strategy: Instance of the specified strategy
        """
        if 'type' not in config:
            raise ValueError("Strategy configuration must include 'type'")
        
        strategy_type = config['type']
        
        # Handle the ensemble strategy specially
        if strategy_type.lower() in ('ensemble', 'ensemble_strategy'):
            if 'strategies' not in config:
                raise ValueError("Ensemble strategy configuration must include 'strategies'")
                
            # Create sub-strategies
            strategies = []
            for sub_config in config['strategies']:
                sub_strategy = self.create_strategy_from_config(sub_config)
                strategies.append(sub_strategy)
            
            # Create ensemble with the sub-strategies
            weights = config.get('weights')
            
            # Extract other kwargs
            kwargs = {k: v for k, v in config.items() if k not in ('type', 'strategies', 'weights')}
            
            return EnsembleStrategy(
                strategies=strategies,
                weights=weights,
                **kwargs
            )
        
        # Handle other strategy types
        kwargs = {k: v for k, v in config.items() if k != 'type'}
        return self.create_strategy(strategy_type, **kwargs)
    
    def load_strategy_config(self, strategy_name: str) -> Dict:
        """
        Load a strategy configuration from file
        
        Args:
            strategy_name: Name of the strategy configuration file (without extension)
            
        Returns:
            Dict: Strategy configuration
        """
        if not self.config_dir:
            raise ValueError("No configuration directory specified")
            
        config_path = os.path.join(self.config_dir, f"{strategy_name}.json")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Strategy configuration not found: {config_path}")
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading strategy configuration: {str(e)}")
            raise
    
    def save_strategy_config(self, config: Dict, strategy_name: str) -> bool:
        """
        Save a strategy configuration to file
        
        Args:
            config: Strategy configuration
            strategy_name: Name for the strategy configuration file (without extension)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.config_dir:
            raise ValueError("No configuration directory specified")
            
        os.makedirs(self.config_dir, exist_ok=True)
        config_path = os.path.join(self.config_dir, f"{strategy_name}.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy configuration: {str(e)}")
            return False
    
    def get_available_strategies(self) -> List[str]:
        """
        Get a list of available strategy configurations
        
        Returns:
            List[str]: Names of available strategy configurations
        """
        if not self.config_dir or not os.path.exists(self.config_dir):
            return []
            
        config_files = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
        return [os.path.splitext(f)[0] for f in config_files]
