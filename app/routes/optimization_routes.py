from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import os
import logging
from datetime import datetime
import threading
import time

from app.services.hyperparameter_optimizer import HyperparameterOptimizer
from app.services.model_comparison_service import ModelComparisonService
from app.utils.json_util import serialize_for_template

logger = logging.getLogger(__name__)

optimization_routes = Blueprint('optimization', __name__, url_prefix='/optimization')

# Global optimizer instance
optimizer = HyperparameterOptimizer()
comparison_service = ModelComparisonService()

@optimization_routes.route('/')
def index():
    """Main optimization dashboard"""
    try:
        # Get current optimization status
        status = optimizer.get_optimization_status()
        
        # Get available optimization results
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        
        # Load recent optimization results
        recent_results = []
        results_file = os.path.join(results_dir, 'hyperparameter_optimization_results.csv')
        if os.path.exists(results_file):
            import pandas as pd
            df = pd.read_csv(results_file)
            recent_results = df.head(10).to_dict('records')
        
        # Load comprehensive results
        comprehensive_file = os.path.join(results_dir, 'comprehensive_optimization_results.json')
        comprehensive_results = {}
        if os.path.exists(comprehensive_file):
            with open(comprehensive_file, 'r') as f:
                comprehensive_results = json.load(f)
        
        return render_template('optimization/index.html',
                             status=status,
                             recent_results=recent_results,
                             comprehensive_results=comprehensive_results,
                             recent_results_json=serialize_for_template(recent_results))
    except Exception as e:
        logger.error(f"Error in optimization index: {e}")
        flash(f"Error loading optimization dashboard: {str(e)}", "error")
        return render_template('optimization/index.html',
                             status={},
                             recent_results=[],
                             comprehensive_results={},
                             recent_results_json="[]")

@optimization_routes.route('/hyperparameter')
def hyperparameter_optimization():
    """Hyperparameter optimization interface"""
    try:
        # Get available models
        available_models = ['LSTM', 'GRU', 'CNN', 'Transformer', 'CNN-LSTM']
        
        # Get current optimization status
        status = optimizer.get_optimization_status()
        
        # Get optimization history
        history = optimizer.get_optimization_history()
        
        return render_template('optimization/hyperparameter.html',
                             available_models=available_models,
                             status=status,
                             history=history,
                             history_json=serialize_for_template(history))
    except Exception as e:
        logger.error(f"Error in hyperparameter optimization page: {e}")
        flash(f"Error loading hyperparameter optimization: {str(e)}", "error")
        return redirect(url_for('optimization.index'))

@optimization_routes.route('/comparison')
def model_comparison():
    """Model comparison interface"""
    try:
        # Get model comparison data
        comparison_data = comparison_service.get_comprehensive_comparison()
        
        # Get available models
        available_models = comparison_service.get_available_models()
        
        return render_template('optimization/comparison.html',
                             comparison_data=comparison_data,
                             available_models=available_models,
                             comparison_json=serialize_for_template(comparison_data))
    except Exception as e:
        logger.error(f"Error in model comparison page: {e}")
        flash(f"Error loading model comparison: {str(e)}", "error")
        return redirect(url_for('optimization.index'))

@optimization_routes.route('/start_optimization', methods=['POST'])
def start_optimization():
    """Start hyperparameter optimization"""
    try:
        data = request.get_json()
        
        # Get optimization parameters
        optimization_type = data.get('optimization_type', 'grid_search')
        model_types = data.get('model_types', ['LSTM'])
        n_trials = data.get('n_trials', 50)
        timeout = data.get('timeout', 3600)
        
        # Validate parameters
        if optimization_type not in ['grid_search', 'bayesian', 'random_search']:
            return jsonify({'success': False, 'error': 'Invalid optimization type'})
        
        if not model_types:
            return jsonify({'success': False, 'error': 'No model types selected'})
        
        # Start optimization in background
        def run_optimization():
            try:
                if optimization_type == 'bayesian':
                    optimizer.bayesian_optimization(model_types, n_trials, timeout)
                elif optimization_type == 'random_search':
                    optimizer.random_search_optimization(model_types, n_trials)
                else:
                    optimizer.grid_search_optimization(model_types)
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                optimizer.set_error_status(str(e))
        
        # Check if optimization is already running
        if optimizer.is_running():
            return jsonify({'success': False, 'error': 'Optimization is already running'})
        
        # Start optimization thread
        thread = threading.Thread(target=run_optimization)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Optimization started successfully'})
        
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        return jsonify({'success': False, 'error': str(e)})

@optimization_routes.route('/stop_optimization', methods=['POST'])
def stop_optimization():
    """Stop current optimization"""
    try:
        optimizer.stop_optimization()
        return jsonify({'success': True, 'message': 'Optimization stopped'})
    except Exception as e:
        logger.error(f"Error stopping optimization: {e}")
        return jsonify({'success': False, 'error': str(e)})

@optimization_routes.route('/api/status')
def api_optimization_status():
    """Get current optimization status"""
    try:
        status = optimizer.get_optimization_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@optimization_routes.route('/api/results')
def api_optimization_results():
    """Get optimization results"""
    try:
        results = optimizer.get_optimization_results()
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"Error getting optimization results: {e}")
        return jsonify({'success': False, 'error': str(e)})

@optimization_routes.route('/api/comparison')
def api_model_comparison():
    """Get model comparison data"""
    try:
        comparison_data = comparison_service.get_comprehensive_comparison()
        return jsonify({'success': True, 'data': comparison_data})
    except Exception as e:
        logger.error(f"Error getting comparison data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@optimization_routes.route('/export_results')
def export_results():
    """Export optimization results"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'json':
            results = optimizer.get_optimization_results()
            return jsonify(results)
        elif format_type == 'csv':
            # Convert results to CSV
            import pandas as pd
            results = optimizer.get_optimization_results()
            df = pd.DataFrame(results.get('grid_search_results', []))
            csv_data = df.to_csv(index=False)
            
            from flask import Response
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=optimization_results.csv'}
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid format'})
            
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        return jsonify({'success': False, 'error': str(e)})
