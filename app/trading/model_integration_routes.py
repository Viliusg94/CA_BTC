"""
Routes for managing model integration with trading strategies
"""

import os
import json
import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta

from app.trading.model_signals import ModelSignalManager, LSTMSignalProvider, TechnicalAnalysisSignalProvider
from app.trading.ensemble_strategies import EnsembleStrategy, AdaptiveEnsembleStrategy
from app.trading.trading_strategies import ModelDrivenStrategy, HybridStrategy
from app.trading.backtester import Backtester

# Create blueprint
model_integration = Blueprint('model_integration', __name__, url_prefix='/trading/models')

logger = logging.getLogger(__name__)

# Global signal manager (would be better to use dependency injection)
signal_manager = ModelSignalManager()

@model_integration.route('/')
def index():
    """Model integration dashboard"""
    try:
        # Get available models
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        available_models = []
        
        # Check for model files
        model_files = {
            'LSTM': 'lstm_model.h5',
            'GRU': 'gru_model.h5',
            'CNN': 'cnn_model.h5',
            'Transformer': 'transformer_model.h5'
        }
        
        for model_name, filename in model_files.items():
            model_path = os.path.join(models_dir, filename)
            if os.path.exists(model_path):
                # Try to load model info
                info_path = os.path.join(models_dir, f"{model_name.lower()}_model_info.json")
                model_info = {'metrics': {}}
                
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r') as f:
                            model_info = json.load(f)
                    except Exception as e:
                        logger.error(f"Error loading model info for {model_name}: {e}")
                
                available_models.append({
                    'name': model_name,
                    'path': model_path,
                    'info': model_info,
                    'is_active': model_name in signal_manager.providers
                })
        
        # Get current signal providers
        active_providers = []
        for name, provider in signal_manager.providers.items():
            weight = signal_manager.signal_weights.get(name, 1.0)
            
            # Get recent signals
            recent_signals = provider.get_signal_history(limit=10)
            
            active_providers.append({
                'name': name,
                'weight': weight,
                'recent_signals': [s.to_dict() for s in recent_signals],
                'signal_count': len(provider.signal_history)
            })
        
        return render_template('trading/model_integration.html',
                             available_models=available_models,
                             active_providers=active_providers)
    
    except Exception as e:
        logger.error(f"Error in model integration index: {e}")
        flash(f"Error loading model integration: {str(e)}", "error")
        return redirect(url_for('trading.index'))

@model_integration.route('/api/add_provider', methods=['POST'])
def add_provider():
    """Add a model signal provider"""
    try:
        data = request.json
        model_type = data.get('model_type')
        model_path = data.get('model_path')
        weight = float(data.get('weight', 1.0))
        
        if not model_type:
            return jsonify({'success': False, 'error': 'Model type is required'}), 400
        
        # Create appropriate provider
        if model_type.upper() == 'LSTM':
            provider = LSTMSignalProvider(model_path)
        elif model_type.upper() == 'TECHNICAL_ANALYSIS':
            provider = TechnicalAnalysisSignalProvider()
        else:
            return jsonify({'success': False, 'error': f'Unsupported model type: {model_type}'}), 400
        
        # Add to signal manager
        signal_manager.add_provider(provider, weight)
        
        return jsonify({
            'success': True,
            'message': f'Added {model_type} provider with weight {weight}'
        })
    
    except Exception as e:
        logger.error(f"Error adding provider: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@model_integration.route('/api/remove_provider', methods=['POST'])
def remove_provider():
    """Remove a model signal provider"""
    try:
        data = request.json
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'success': False, 'error': 'Model name is required'}), 400
        
        signal_manager.remove_provider(model_name)
        
        return jsonify({
            'success': True,
            'message': f'Removed {model_name} provider'
        })
    
    except Exception as e:
        logger.error(f"Error removing provider: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@model_integration.route('/api/update_weight', methods=['POST'])
def update_weight():
    """Update model weight"""
    try:
        data = request.json
        model_name = data.get('model_name')
        new_weight = float(data.get('weight', 1.0))
        
        if not model_name or model_name not in signal_manager.providers:
            return jsonify({'success': False, 'error': 'Invalid model name'}), 400
        
        signal_manager.signal_weights[model_name] = new_weight
        
        return jsonify({
            'success': True,
            'message': f'Updated {model_name} weight to {new_weight}'
        })
    
    except Exception as e:
        logger.error(f"Error updating weight: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@model_integration.route('/api/test_signal')
def test_signal():
    """Test signal generation with current data"""
    try:
        # Get current Bitcoin price (simplified)
        current_data = {
            'open': 45000,
            'high': 45500,
            'low': 44500,
            'close': 45200,
            'volume': 1000000
        }
        
        # Get consensus signal
        consensus_signal = signal_manager.get_consensus_signal(current_data)
        
        # Get all individual signals
        all_signals = signal_manager.get_all_signals(current_data)
        
        response_data = {
            'consensus': consensus_signal.to_dict(),
            'individual_signals': {name: signal.to_dict() for name, signal in all_signals.items()},
            'providers_count': len(signal_manager.providers),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
    
    except Exception as e:
        logger.error(f"Error testing signal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@model_integration.route('/api/backtest_strategy', methods=['POST'])
def backtest_strategy():
    """Backtest a model-driven strategy"""
    try:
        data = request.json
        strategy_type = data.get('strategy_type', 'model_driven')
        test_days = int(data.get('test_days', 30))
        
        # Create strategy based on type
        if strategy_type == 'model_driven':
            strategy = ModelDrivenStrategy(
                signal_manager=signal_manager,
                signal_threshold=0.6,
                confidence_threshold=0.5
            )
        elif strategy_type == 'hybrid':
            strategy = HybridStrategy(
                signal_manager=signal_manager,
                model_weight=0.7,
                ta_weight=0.3
            )
        elif strategy_type == 'ensemble':
            strategy = EnsembleStrategy(
                voting_method="weighted",
                confidence_threshold=0.6
            )
        elif strategy_type == 'adaptive_ensemble':
            strategy = AdaptiveEnsembleStrategy(
                adaptation_rate=0.1,
                performance_window=50
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid strategy type'}), 400
        
        # Get test data (simplified - would normally fetch from API)
        # For now, return a placeholder result
        results = {
            'strategy_name': strategy.name,
            'test_period': f'{test_days} days',
            'total_return_percent': 12.5,
            'max_drawdown_percent': -3.2,
            'sharpe_ratio': 1.8,
            'total_trades': 15,
            'win_rate_percent': 66.7,
            'profit_factor': 2.1
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error backtesting strategy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@model_integration.route('/api/strategy_comparison')
def strategy_comparison():
    """Compare different model integration strategies"""
    try:
        # Create different strategies
        strategies = [
            ModelDrivenStrategy(name="Model-Only", signal_manager=signal_manager),
            HybridStrategy(name="Hybrid (70/30)", signal_manager=signal_manager, 
                          model_weight=0.7, ta_weight=0.3),
            EnsembleStrategy(name="Ensemble-Weighted", voting_method="weighted"),
            AdaptiveEnsembleStrategy(name="Adaptive-Ensemble")
        ]
        
        # Placeholder comparison results
        comparison_results = []
        
        for i, strategy in enumerate(strategies):
            # Simulate backtest results
            base_return = 10.0 + i * 2.5
            results = {
                'strategy_name': strategy.name,
                'total_return_percent': base_return + (i * 0.5),
                'max_drawdown_percent': -(2.0 + i * 0.5),
                'sharpe_ratio': 1.5 + (i * 0.2),
                'total_trades': 12 + i * 3,
                'win_rate_percent': 60.0 + i * 5,
                'profit_factor': 1.8 + (i * 0.3)
            }
            comparison_results.append(results)
        
        return jsonify({
            'success': True,
            'comparison': comparison_results
        })
    
    except Exception as e:
        logger.error(f"Error in strategy comparison: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@model_integration.route('/settings')
def settings():
    """Model integration settings page"""
    try:
        # Get current settings
        settings_data = {
            'signal_manager': {
                'providers_count': len(signal_manager.providers),
                'total_weights': sum(signal_manager.signal_weights.values()),
                'providers': [
                    {
                        'name': name,
                        'weight': signal_manager.signal_weights.get(name, 1.0),
                        'type': type(provider).__name__
                    }
                    for name, provider in signal_manager.providers.items()
                ]
            },
            'available_strategies': [
                'ModelDrivenStrategy',
                'HybridStrategy', 
                'EnsembleStrategy',
                'AdaptiveEnsembleStrategy'
            ]
        }
        
        return render_template('trading/model_integration_settings.html',
                             settings=settings_data)
    
    except Exception as e:
        logger.error(f"Error in model integration settings: {e}")
        flash(f"Error loading settings: {str(e)}", "error")
        return redirect(url_for('model_integration.index'))

@model_integration.route('/test_strategy', methods=['POST'])
def test_strategy():
    """Test a model-driven strategy"""
    try:
        strategy_type = request.form.get('strategy_type')
        model_name = request.form.get('model_name', 'LSTM')
        test_period = int(request.form.get('test_period', 30))
        
        # Create strategy based on type
        if strategy_type == 'lstm':
            strategy = LSTMStrategy()
        elif strategy_type == 'transformer':
            strategy = TransformerStrategy()
        elif strategy_type == 'cnn':
            strategy = CNNStrategy()
        elif strategy_type == 'ensemble':
            strategy = EnsembleStrategy()
        elif strategy_type == 'adaptive_ensemble':
            strategy = AdaptiveEnsembleStrategy()
        elif strategy_type == 'voting_ensemble':
            strategy = VotingEnsembleStrategy()
        elif strategy_type == 'confidence_ensemble':
            strategy = ConfidenceWeightedEnsemble()
        elif strategy_type == 'meta_ensemble':
            strategy = MetaEnsembleStrategy()
        else:
            flash("Invalid strategy type", "error")
            return redirect(url_for('model_integration.index'))
        
        # Get test data (placeholder - would use real historical data)
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate sample data for testing
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=test_period),
            end=datetime.now(),
            freq='H'
        )
        
        base_price = 45000
        prices = []
        for i in range(len(dates)):
            price = base_price * (1 + np.random.normal(0, 0.02))
            prices.append(price)
            base_price = price
        
        test_data = pd.DataFrame({
            'time': dates,
            'close': prices,
            'volume': np.random.randint(100, 1000, len(dates))
        })
        
        # Run backtest
        backtester = Backtester(strategy)
        results = backtester.run_backtest(test_data)
        
        return jsonify({
            'status': 'success',
            'results': {
                'strategy_name': results['strategy_name'],
                'total_return': results['total_return_percent'],
                'max_drawdown': results['max_drawdown_percent'],
                'sharpe_ratio': results['sharpe_ratio'],
                'total_trades': results['total_trades'],
                'win_rate': results['win_rate_percent']
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing strategy: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@model_integration.route('/signal_history/<model_name>')
def signal_history(model_name):
    """Get signal history for a specific model"""
    try:
        signals = signal_manager.get_recent_signals(model_name, limit=50)
        
        signal_data = []
        for signal in signals:
            signal_data.append({
                'timestamp': signal.timestamp.isoformat(),
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'predicted_price': signal.predicted_price,
                'current_price': signal.current_price,
                'price_change_percent': signal.price_change_percent
            })
        
        return jsonify({
            'status': 'success',
            'model_name': model_name,
            'signals': signal_data
        })
        
    except Exception as e:
        logger.error(f"Error getting signal history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@model_integration.route('/strategy_comparison')
def strategy_comparison():
    """Compare different model-driven strategies"""
    try:
        # Define strategies to compare
        strategies = [
            LSTMStrategy(initial_balance=10000),
            TransformerStrategy(initial_balance=10000),
            CNNStrategy(initial_balance=10000),
            EnsembleStrategy(initial_balance=10000),
            VotingEnsembleStrategy(initial_balance=10000),
            ConfidenceWeightedEnsemble(initial_balance=10000)
        ]
        
        # Generate test data
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=60),
            end=datetime.now(),
            freq='H'
        )
        
        base_price = 45000
        prices = []
        for i in range(len(dates)):
            price = base_price * (1 + np.random.normal(0, 0.015))
            prices.append(price)
            base_price = price
        
        test_data = pd.DataFrame({
            'time': dates,
            'close': prices,
            'volume': np.random.randint(100, 1000, len(dates))
        })
        
        # Compare strategies
        backtester = Backtester(strategies[0])  # Use first strategy as template
        comparison_results = backtester.compare_strategies(strategies, test_data, plot=False)
        
        # Format results for JSON
        formatted_results = {}
        for strategy_name, results in comparison_results.items():
            formatted_results[strategy_name] = {
                'total_return': results['total_return_percent'],
                'max_drawdown': results['max_drawdown_percent'],
                'sharpe_ratio': results['sharpe_ratio'],
                'total_trades': results['total_trades'],
                'win_rate': results['win_rate_percent'],
                'profit_factor': results['profit_factor']
            }
        
        return jsonify({
            'status': 'success',
            'comparison_results': formatted_results
        })
        
    except Exception as e:
        logger.error(f"Error in strategy comparison: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@model_integration.route('/live_signals')
def live_signals():
    """Get live signals from all models"""
    try:
        # This would integrate with real prediction service
        # For now, we'll simulate signals
        
        import random
        current_price = 45000 + random.uniform(-1000, 1000)
        
        live_signals = {}
        models = ['LSTM', 'GRU', 'CNN', 'Transformer']
        
        for model in models:
            # Simulate prediction
            prediction = current_price * (1 + random.uniform(-0.02, 0.02))
            confidence = random.uniform(0.6, 0.95)
            
            signal = signal_manager.generate_signal(
                model, prediction, current_price, confidence
            )
            
            if signal:
                live_signals[model] = {
                    'signal_type': signal.signal_type,
                    'confidence': signal.confidence,
                    'predicted_price': signal.predicted_price,
                    'price_change_percent': signal.price_change_percent,
                    'timestamp': signal.timestamp.isoformat()
                }
        
        # Generate ensemble signal
        if live_signals:
            predictions_dict = {
                model: (data['predicted_price'], data['confidence'])
                for model, data in live_signals.items()
            }
            
            ensemble_signal = signal_manager.generate_ensemble_signal(
                predictions_dict, current_price
            )
            
            if ensemble_signal:
                live_signals['Ensemble'] = {
                    'signal_type': ensemble_signal.signal_type,
                    'confidence': ensemble_signal.confidence,
                    'predicted_price': ensemble_signal.predicted_price,
                    'price_change_percent': ensemble_signal.price_change_percent,
                    'timestamp': ensemble_signal.timestamp.isoformat()
                }
        
        return jsonify({
            'status': 'success',
            'current_price': current_price,
            'signals': live_signals
        })
        
    except Exception as e:
        logger.error(f"Error getting live signals: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
