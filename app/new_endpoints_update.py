"""
Additional debugging endpoints to add to new_endpoints.py
"""

# Add these routes to your new_endpoints.py file
@app.route('/training_debug')
def training_debug_page():
    """Debug page for training status"""
    try:
        return render_template('training_status_debug.html')
    except Exception as e:
        logger.error(f"Error in training debug page: {str(e)}")
        return f"Error loading debug page: {str(e)}"

@app.route('/api/reset_training_status', methods=['POST'])
def reset_training_status():
    """Reset all training status"""
    try:
        if not model_manager:
            return jsonify({'success': False, 'error': 'Model manager not available'}), 500
        
        # Get training status
        training_status = getattr(model_manager, 'training_status', {})
        
        # Reset status for all models
        for model_type in training_status:
            training_status[model_type] = {
                'status': 'Idle',
                'progress': 0,
                'current_epoch': 0,
                'total_epochs': 0,
                'loss': None,
                'val_loss': None
            }
        
        # Save to file
        try:
            models_dir = model_manager.models_dir
            status_file = os.path.join(models_dir, 'training_status.json')
            with open(status_file, 'w') as f:
                json.dump(training_status, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving training status: {str(e)}")
        
        return jsonify({'success': True, 'message': 'Training status reset successfully'})
    except Exception as e:
        logger.error(f"Error resetting training status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
