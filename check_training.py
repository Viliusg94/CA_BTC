import os
import sys
import json
import time
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== Training System Diagnostic Tool ===")
print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Working directory:", os.getcwd())

# Check if model_manager.py exists
model_manager_path = os.path.join('app', 'model_manager.py')
if os.path.exists(model_manager_path):
    print(f"✅ model_manager.py found at {model_manager_path}")
else:
    print(f"❌ model_manager.py NOT found at {model_manager_path}")
    # Check in project root
    if os.path.exists('model_manager.py'):
        print(f"✅ model_manager.py found in project root")
        model_manager_path = 'model_manager.py'
    else:
        print(f"❌ model_manager.py NOT found in project root either")

# Try to import and check model manager
try:
    # Try importing from both possible locations
    try:
        sys.path.append('app')
        from model_manager import ModelManager
    except ImportError:
        from app.model_manager import ModelManager
    
    print("✅ Successfully imported ModelManager class")
    
    # Check models directory
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Created models directory at {models_dir}")
    else:
        print(f"✅ Models directory exists at {models_dir}")
    
    # Initialize model manager
    model_manager = ModelManager(models_dir=models_dir)
    print("✅ Successfully created ModelManager instance")
    
    # Check tensorflow availability
    if hasattr(model_manager, 'tensorflow_available'):
        tf_status = "✅ available" if model_manager.tensorflow_available else "❌ NOT available"
        print(f"TensorFlow is {tf_status}")
    else:
        print("❌ ModelManager missing tensorflow_available attribute")
    
    # Check model status for various model types
    model_types = ['lstm', 'gru', 'cnn', 'transformer']
    for model_type in model_types:
        print(f"\nChecking {model_type.upper()} model status:")
        try:
            status = model_manager.get_model_status(model_type)
            progress = model_manager.get_training_progress(model_type)
            
            print(f"  Status: {status}")
            print(f"  Progress: {progress}")
            
            config = model_manager.get_model_config(model_type)
            print(f"  Config: {json.dumps(config, indent=2)}")
            
            # Check if model is currently training
            is_training = (
                progress.get('status', '').lower() in ['training', 'treniruojama'] or
                (progress.get('progress', 0) > 0 and progress.get('progress', 0) < 100)
            )
            if is_training:
                print(f"  ✅ {model_type.upper()} IS CURRENTLY TRAINING")
            else:
                print(f"  ℹ️ {model_type.upper()} is not currently training")
                
        except Exception as e:
            print(f"  ❌ Error checking {model_type} status: {str(e)}")
    
    # Check if training can be started
    print("\nTesting start_training functionality:")
    model_type_to_test = 'lstm'
    try:
        # Don't actually start training, just check if method exists
        if hasattr(model_manager, 'start_training'):
            print(f"✅ start_training method exists")
            
            # Check method signature
            import inspect
            sig = inspect.signature(model_manager.start_training)
            print(f"  Method signature: {sig}")
            
            print("  Method exists and appears valid")
        else:
            print("❌ start_training method does NOT exist")
    except Exception as e:
        print(f"❌ Error checking start_training method: {str(e)}")
    
except ImportError as e:
    print(f"❌ Failed to import ModelManager: {e}")
except Exception as e:
    print(f"❌ Error initializing model manager: {e}")

# Check training_api.py
training_api_path = os.path.join('app', 'api', 'training_api.py')
if os.path.exists(training_api_path):
    print(f"\n✅ training_api.py found at {training_api_path}")
    # Show stats
    size = os.path.getsize(training_api_path)
    modified = datetime.fromtimestamp(os.path.getmtime(training_api_path))
    print(f"  Size: {size} bytes")
    print(f"  Last modified: {modified}")
else:
    print(f"\n❌ training_api.py NOT found at {training_api_path}")

print("\n=== Diagnostic complete ===")
