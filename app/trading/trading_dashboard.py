"""
Trading dashboard endpoints for visualizing strategies and backtests
"""
import os
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, request, jsonify
from flask import current_app

from app.trading.trading_strategies import STRATEGY_REGISTRY, Strategy, Action
from app.trading.backtester import Backtester

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
trading_dashboard = Blueprint('trading_dashboard', __name__, url_prefix='/trading')

@trading_dashboard.route('/dashboard')
def dashboard():
    """Render the trading dashboard page"""
    try:
        # Get list of available strategies
        strategies = list(STRATEGY_REGISTRY.keys())
        
        # Get any active strategy
        from app.trading.trading_routes import active_strategy, active_config
        
        # Prepare template data
        data = {
            'strategies': strategies,
            'active_strategy': active_strategy.name if active_strategy else None,
            'active_config': active_config
        }
        
        # Render the dashboard template
        return render_template('trading/dashboard.html', **data)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return render_template('error.html', error=str(e))

@trading_dashboard.route('/backtest_view')
def backtest_view():
    """Render the backtest view page"""
    try:
        # Get list of available strategies
        strategies = list(STRATEGY_REGISTRY.keys())
        
        # Prepare template data
        data = {
            'strategies': strategies
        }
        
        # Render the backtest template
        return render_template('trading/backtest.html', **data)
    except Exception as e:
        logger.error(f"Error rendering backtest view: {e}")
        return render_template('error.html', error=str(e))

@trading_dashboard.route('/strategy/<strategy_type>')
def strategy_details(strategy_type):
    """Render the strategy details page"""
    try:
        if strategy_type not in STRATEGY_REGISTRY:
            return render_template('error.html', error=f"Unknown strategy type: {strategy_type}")
            
        # Get strategy class and create instance with default params
        strategy_class = STRATEGY_REGISTRY[strategy_type]
        
        # Get default parameter values
        default_params = {
            'name': strategy_type,
            'initial_balance': 10000,
            'fee_rate': 0.001
        }
        
        # Get parameter descriptions
        param_descriptions = {
            'name': 'Name of the strategy instance',
            'initial_balance': 'Initial USD balance',
            'fee_rate': 'Trading fee rate (decimal)',
            'stop_loss': 'Stop loss percentage (decimal)',
            'take_profit': 'Take profit percentage (decimal)',
            'short_period': 'Short period for Moving Average',
            'long_period': 'Long period for Moving Average',
            'threshold_percent': 'Price change threshold for prediction-based strategies',
            'max_holding_days': 'Maximum holding period in days',
            'lstm_units': 'Number of units in LSTM layer',
            'dropout': 'Dropout rate for regularization',
            'num_heads': 'Number of attention heads in Transformer',
            'd_model': 'Dimension of model in Transformer',
            'filters': 'Number of filters in CNN layers',
            'kernel_size': 'Kernel size in CNN layers'
        }
        
        # Create template data
        data = {
            'strategy_type': strategy_type,
            'strategy_class': strategy_class.__name__,
            'default_params': default_params,
            'param_descriptions': param_descriptions
        }
        
        return render_template('trading/strategy_details.html', **data)
    except Exception as e:
        logger.error(f"Error rendering strategy details: {e}")
        return render_template('error.html', error=str(e))

@trading_dashboard.route('/visualize_backtest/<backtest_id>')
def visualize_backtest(backtest_id):
    """Visualize a specific backtest result"""
    try:
        # In a real app, we would load the backtest result from a database
        # For now, we'll assume the backtest_id points to a JSON file
        backtest_dir = os.path.join(current_app.root_path, 'data', 'backtests')
        backtest_file = os.path.join(backtest_dir, f'{backtest_id}.json')
        
        if not os.path.exists(backtest_file):
            return render_template('error.html', error=f"Backtest result not found: {backtest_id}")
            
        # Load backtest result
        with open(backtest_file, 'r') as f:
            backtest_result = json.load(f)
            
        # Prepare template data
        data = {
            'backtest_id': backtest_id,
            'backtest_result': backtest_result
        }
        
        return render_template('trading/visualize_backtest.html', **data)
    except Exception as e:
        logger.error(f"Error visualizing backtest: {e}")
        return render_template('error.html', error=str(e))

@trading_dashboard.route('/save_backtest', methods=['POST'])
def save_backtest():
    """Save a backtest result for future reference"""
    try:
        # Get backtest data from request
        backtest_data = request.json
        
        if not backtest_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        # Generate unique ID for the backtest
        backtest_id = f"backtest_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(backtest_data))}"
        
        # Create backtest directory if it doesn't exist
        backtest_dir = os.path.join(current_app.root_path, 'data', 'backtests')
        os.makedirs(backtest_dir, exist_ok=True)
        
        # Save backtest result to JSON file
        backtest_file = os.path.join(backtest_dir, f'{backtest_id}.json')
        with open(backtest_file, 'w') as f:
            json.dump(backtest_data, f, indent=2)
            
        return jsonify({
            'success': True,
            'backtest_id': backtest_id,
            'message': 'Backtest saved successfully'
        })
    except Exception as e:
        logger.error(f"Error saving backtest: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@trading_dashboard.route('/list_backtests')
def list_backtests():
    """List all saved backtests"""
    try:
        # Get backtest directory
        backtest_dir = os.path.join(current_app.root_path, 'data', 'backtests')
        
        if not os.path.exists(backtest_dir):
            return jsonify({'success': True, 'backtests': []})
            
        # Get all backtest files
        backtest_files = [f for f in os.listdir(backtest_dir) if f.endswith('.json')]
        
        # Load summary information for each backtest
        backtests = []
        for filename in backtest_files:
            try:
                backtest_id = filename[:-5]  # Remove .json extension
                backtest_file = os.path.join(backtest_dir, filename)
                
                with open(backtest_file, 'r') as f:
                    data = json.load(f)
                    
                # Extract summary information
                backtest_info = {
                    'id': backtest_id,
                    'strategy_type': data.get('strategy_type', 'Unknown'),
                    'date': data.get('date', 'Unknown'),
                    'initial_balance': data.get('initial_balance', 0),
                    'final_balance': data.get('final_balance', 0),
                    'profit_percentage': data.get('profit_percentage', 0),
                    'total_trades': data.get('total_trades', 0)
                }
                
                backtests.append(backtest_info)
            except Exception as e:
                logger.error(f"Error loading backtest {filename}: {e}")
                
        return jsonify({'success': True, 'backtests': backtests})
    except Exception as e:
        logger.error(f"Error listing backtests: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
