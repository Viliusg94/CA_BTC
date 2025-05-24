# How to Fix Training Status Not Appearing

This guide will help you fix the issue where model training doesn't appear on the training status page.

## 1. Run the Debug Script

First, run the debug script to check for common issues:

```bash
python debug_training.py
```

This will:
- Check your models directory and permissions
- Examine the training status files
- Verify database connections
- Add debugging features to help identify issues

## 2. Add the Debug Page

After running the debug script, add the debug page route to your `new_endpoints.py` file:

```python
@app.route('/training_debug')
def training_debug_page():
    """Debug page for training status"""
    try:
        return render_template('training_status_debug.html')
    except Exception as e:
        logger.error(f"Error in training debug page: {str(e)}")
        return f"Error loading debug page: {str(e)}"
```

And add the reset endpoint:

```python
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
```

## 3. Restart the Application

After making these changes, restart your Flask application:

```bash
python app/app.py
```

## 4. Test Training with Debug Mode

1. Go to the debug page at `/training_debug`
2. Click "Test Training API" to start a test training job
3. The debug information will show if the training is being registered correctly
4. Check the console output for any error messages

## 5. Common Issues and Solutions

### Missing Training Status File

If the training status file doesn't exist or has invalid JSON:

```bash
python -c "import json, os; os.makedirs('models', exist_ok=True); json.dump({}, open('models/training_status.json', 'w'))"
```

### Stuck Training Jobs

If a training job is stuck in "Training" state, use the "Reset Training Status" button on the debug page.

### Thread Issues

If training threads aren't running properly:
- Check if the main Flask application is running in debug mode
- Ensure threading is properly implemented in `model_manager.py`
- Verify the daemon flag is set to True in the training thread

## 6. Verifying the Fix

After applying these fixes:
1. Try training a model again from the models page
2. Go to the training status page to see if the model appears
3. Check the debug page to confirm the training thread is running

## 7. Additional Debugging

If issues persist, run the test_model_training.py script:

```bash
python test_model_training.py
```

This will test the training API directly and provide detailed error information.
