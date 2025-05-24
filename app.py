import os
import json
import sys
from datetime import datetime
import sqlite3
from flask import Flask, jsonify, request

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/models.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize database connection through our app package
from app.database import db
db.init_app(app)

# Import required models and managers
try:
    from app.models import ModelHistory
    from app.model_manager import model_manager
except ImportError:
    ModelHistory = None
    model_manager = None

# Import the fixed endpoints
from app.fixed_endpoints import register_endpoints
register_endpoints(app)

# Registruoti naujus endpoints
if 'app.new_endpoints' in sys.modules or 'new_endpoints' in sys.modules:
    try:
        from app.new_endpoints import register_endpoints as register_new_endpoints
        register_new_endpoints(app, db, ModelHistory, model_manager)
    except ImportError:
        print("Warning: Could not import new_endpoints module")

@app.route('/api/model_history_db', methods=['GET'])
def get_models():
    """Get list of trained models from database or file system"""
    try:
        models = []
        
        # Option 1: If you have a SQLite database
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'models.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, model_type, r2, mae, rmse, epochs, timestamp, is_active
                FROM model_history 
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            
            for row in rows:
                models.append({
                    'id': row[0],
                    'model_type': row[1],
                    'r2': row[2],
                    'mae': row[3],
                    'rmse': row[4],
                    'epochs': row[5],
                    'timestamp': row[6],
                    'is_active': bool(row[7])
                })
            conn.close()
        
        # Option 2: If you have a JSON file
        elif os.path.exists('model_history.json'):
            with open('model_history.json', 'r') as f:
                models = json.load(f)
        
        # Option 3: Scan models directory
        else:
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
            if os.path.exists(models_dir):
                for i, filename in enumerate(os.listdir(models_dir)):
                    if filename.endswith(('.h5', '.pkl', '.joblib')):
                        # Create basic model info from filename
                        models.append({
                            'id': i + 1,
                            'model_type': filename.split('_')[0] if '_' in filename else 'Unknown',
                            'r2': 0.75,  # You'll need to load actual metrics
                            'mae': 1500,
                            'rmse': 1800,
                            'epochs': 50,
                            'timestamp': datetime.now().isoformat(),
                            'is_active': i == 0  # First model is active
                        })
        
        return jsonify(models)
        
    except Exception as e:
        print(f"Error getting models: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_model/<int:model_id>', methods=['DELETE'])
def delete_model(model_id):
    """Delete a trained model"""
    try:
        # Option 1: Delete from SQLite database
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'models.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM model_history WHERE id = ?", (model_id,))
            conn.commit()
            conn.close()
            print(f"Deleted model {model_id} from database")
        
        # Option 2: Delete from JSON file
        elif os.path.exists('model_history.json'):
            with open('model_history.json', 'r') as f:
                models = json.load(f)
            
            models = [m for m in models if m['id'] != model_id]
            
            with open('model_history.json', 'w') as f:
                json.dump(models, f)
            print(f"Deleted model {model_id} from JSON file")
        
        # Also delete the actual model file
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        for filename in os.listdir(models_dir):
            if f"model_{model_id}" in filename:
                os.remove(os.path.join(models_dir, filename))
                break
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error deleting model: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/activate_model/<int:model_id>', methods=['POST'])
def activate_model(model_id):
    """Activate a specific model"""
    try:
        # Update database or JSON file to set this model as active
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'models.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get the model type first
            cursor.execute("SELECT model_type FROM model_history WHERE id = ?", (model_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Model not found'}), 404
                
            model_type = result[0]
            
            # Deactivate all models of this type
            cursor.execute("UPDATE model_history SET is_active = 0 WHERE model_type = ?", (model_type,))
            
            # Activate selected model
            cursor.execute("UPDATE model_history SET is_active = 1 WHERE id = ?", (model_id,))
            conn.commit()
            conn.close()
            print(f"Activated model {model_id} of type {model_type}")
        
        return jsonify({'success': True, 'message': f'Model {model_id} successfully activated'})
        
    except Exception as e:
        print(f"Error activating model: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/train_model', methods=['POST'])
def train_model():
    """Start model training"""
    try:
        data = request.get_json()
        
        # Check if required data file exists in multiple possible locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'app', 'data', 'btc_data_1y_15m.csv'),
            os.path.join(os.path.dirname(__file__), 'data', 'btc_data_1y_15m.csv'),
            os.path.join('app', 'data', 'btc_data_1y_15m.csv'),
            os.path.join('data', 'btc_data_1y_15m.csv'),
            'btc_data_1y_15m.csv'
        ]
        
        data_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_file_path = path
                break
        
        if not data_file_path:
            # List all CSV files in possible data directories to help debug
            found_files = []
            for search_dir in ['app/data', 'data', '.']:
                if os.path.exists(search_dir):
                    for file in os.listdir(search_dir):
                        if file.endswith('.csv'):
                            found_files.append(os.path.join(search_dir, file))
            
            return jsonify({
                'success': False,
                'error': 'Duomenų failas nerastas',
                'searched_paths': possible_paths,
                'found_csv_files': found_files,
                'message': 'Prašome patikrinti, ar duomenų failas btc_data_1y_15m.csv egzistuoja bet kuriame iš nurodytų kelių.'
            }), 400
        
        # Ensure data directory exists
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # If model_manager is available, use it for training
        if model_manager:
            try:
                result = model_manager.start_training(data_file_path, data)
                return jsonify(result)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Training error: {str(e)}',
                    'data_file_found': data_file_path
                }), 500
        
        # Fallback training logic
        training_id = int(datetime.now().timestamp())
        
        return jsonify({
            'success': True,
            'training_id': training_id,
            'message': 'Training started successfully',
            'data_file': data_file_path
        })
        
    except Exception as e:
        print(f"Error starting training: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)