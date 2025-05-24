import os
import sys
import traceback
import time
from datetime import datetime
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== ModelManager Fix Tool ===")
print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Determine model_manager.py location
model_manager_path = None
possible_paths = [
    os.path.join('app', 'model_manager.py'),
    'model_manager.py'
]

for path in possible_paths:
    if os.path.exists(path):
        model_manager_path = path
        print(f"✅ Found model_manager.py at {path}")
        break

if not model_manager_path:
    print("❌ Could not find model_manager.py")
    sys.exit(1)

# Check models directory
models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
if not os.path.exists(models_dir):
    os.makedirs(models_dir)
    print(f"Created models directory at {models_dir}")
else:
    print(f"✅ Models directory exists at {models_dir}")

# Create or update training status files
for model_type in ['lstm', 'gru', 'cnn', 'transformer']:
    status_file = os.path.join(models_dir, f"{model_type}_training_status.json")
    config_file = os.path.join(models_dir, f"{model_type}_config.json")
    
    # Check if files exist
    if not os.path.exists(status_file):
        # Create default status
        status = {
            "status": "Not trained",
            "last_trained": None,
            "performance": "Unknown"
        }
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        print(f"Created default status for {model_type}")
    
    if not os.path.exists(config_file):
        # Create default config
        config = {
            "epochs": 50,
            "batch_size": 32,
            "learning_rate": 0.001,
            "lookback": 24,
            "validation_split": 0.2
        }
        # Add model-specific params
        if model_type == 'lstm' or model_type == 'gru':
            config["lstm_units"] = 50
            config["dropout"] = 0.2
        elif model_type == 'transformer':
            config["num_heads"] = 4
            config["d_model"] = 64
        elif model_type == 'cnn':
            config["filters"] = [32, 64, 128]
            config["kernel_size"] = 3
            
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created default config for {model_type}")

# Create or update progress files
for model_type in ['lstm', 'gru', 'cnn', 'transformer']:
    progress_file = os.path.join(models_dir, f"{model_type}_progress.json")
    
    # Check if file exists
    if not os.path.exists(progress_file):
        # Create default progress
        progress = {
            "status": "idle",
            "progress": 0,
            "current_epoch": 0,
            "total_epochs": 0,
            "loss": 0,
            "val_loss": 0,
            "message": "Not started"
        }
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        print(f"Created default progress for {model_type}")

print("\n✅ All model files initialized")
print("\nYou can now start your Flask application and training should work properly!")
