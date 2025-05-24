"""
Model File Organization Script
This script helps organize and link model files with the database entries
"""
import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
APP_MODELS_DIR = os.path.join(BASE_DIR, 'app', 'models')
DB_PATH = os.path.join(BASE_DIR, 'data', 'models.db')

def ensure_directory(directory):
    """Ensure directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    return directory

def get_models_from_db():
    """Get models from database"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return []
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, model_type, timestamp FROM model_history ORDER BY timestamp DESC")
        models = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(models)} models in database")
        return models
    except Exception as e:
        print(f"Error reading from database: {str(e)}")
        return []

def organize_model_files():
    """Organize model files based on database entries"""
    models = get_models_from_db()
    ensure_directory(MODELS_DIR)
    
    model_files_organized = 0
    
    # Process each model from the database
    for model_id, model_type, timestamp in models:
        # Create type-specific directories
        model_type_dir = ensure_directory(os.path.join(APP_MODELS_DIR, model_type.lower()))
        
        # Check if we can find model files
        found_model_files = False
        
        # Search in main models directory
        for filename in os.listdir(MODELS_DIR):
            file_path = os.path.join(MODELS_DIR, filename)
            if os.path.isfile(file_path):
                # Check if this file might be related to the current model
                is_match = False
                
                # Check common naming patterns
                patterns = [
                    f"{model_type.lower()}_model.h5",
                    f"{model_type.lower()}_model_{model_id}.h5",
                    f"{model_type.lower()}_{model_id}.h5",
                    f"{model_type.lower()}_model.pkl",
                    f"{model_type.lower()}_model_{model_id}.pkl",
                    f"{model_type.lower()}_{model_id}.pkl",
                    f"{model_type.lower()}_modelis.pkl",
                    f"{model_type.lower()}_scaler.pkl"
                ]
                
                # Check if filename matches any pattern
                for pattern in patterns:
                    if filename.lower() == pattern or (
                        model_type.lower() in filename.lower() and 
                        (filename.endswith('.h5') or filename.endswith('.pkl'))
                    ):
                        is_match = True
                        break
                
                if is_match:
                    # Copy file to model type directory with standardized name
                    if "scaler" in filename.lower():
                        new_filename = f"{model_id}_scaler.pkl"
                    else:
                        ext = os.path.splitext(filename)[1]
                        new_filename = f"{model_id}{ext}"
                    
                    target_path = os.path.join(model_type_dir, new_filename)
                    if not os.path.exists(target_path):
                        shutil.copy2(file_path, target_path)
                        print(f"Copied {filename} to {target_path}")
                        model_files_organized += 1
                        found_model_files = True
        
        # If no files found, create a stub file with model info
        if not found_model_files:
            info_file = os.path.join(model_type_dir, f"{model_id}_info.json")
            if not os.path.exists(info_file):
                with open(info_file, 'w') as f:
                    f.write(f'{{"id": {model_id}, "model_type": "{model_type}", "timestamp": "{timestamp}"}}')
                print(f"Created stub info file: {info_file}")
    
    print(f"\nSuccessfully organized {model_files_organized} model files")
    return model_files_organized

def main():
    print("\n=== MODEL FILE ORGANIZATION TOOL ===\n")
    print(f"Database path: {DB_PATH}")
    print(f"Models directory: {MODELS_DIR}")
    print(f"App models directory: {APP_MODELS_DIR}\n")
    
    organize_model_files()
    
    print("\nOrganization complete! Your models should now be visible in the web interface.")
    print("Restart your Flask server to see the changes.")

if __name__ == "__main__":
    main()
