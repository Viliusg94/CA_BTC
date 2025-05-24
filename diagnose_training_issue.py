"""
Diagnostic script to identify training issues
"""

import sys
import os
import traceback

def check_tensorflow():
    """Check TensorFlow installation and functionality"""
    print("🔍 Checking TensorFlow...")
    
    try:
        import tensorflow as tf
        print(f"   ✅ TensorFlow {tf.__version__} imported successfully")
        
        # Test basic functionality
        test_tensor = tf.constant([1, 2, 3])
        result = tf.reduce_sum(test_tensor).numpy()
        print(f"   ✅ Basic TensorFlow operations work (test result: {result})")
        
        # Check GPU availability
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"   🎮 {len(gpus)} GPU(s) detected: {[gpu.name for gpu in gpus]}")
        else:
            print("   💻 No GPUs detected, using CPU")
        
        return True, tf
        
    except ImportError as e:
        print(f"   ❌ TensorFlow import failed: {e}")
        return False, None
    except Exception as e:
        print(f"   ❌ TensorFlow functionality test failed: {e}")
        return False, None

def check_model_manager():
    """Check ModelManager class"""
    print("\n🔍 Checking ModelManager...")
    
    try:
        # Add app directory to path
        app_dir = os.path.join(os.path.dirname(__file__), 'app')
        if app_dir not in sys.path:
            sys.path.append(app_dir)
        
        from model_manager import ModelManager
        print("   ✅ ModelManager imported successfully")
        
        # Initialize ModelManager
        model_manager = ModelManager()
        print("   ✅ ModelManager initialized successfully")
        
        # Check for tensorflow_available attribute
        if hasattr(model_manager, 'tensorflow_available'):
            print(f"   ✅ tensorflow_available attribute exists: {model_manager.tensorflow_available}")
        else:
            print("   ❌ tensorflow_available attribute missing!")
            return False, None
        
        # Check other required methods
        required_methods = [
            'is_tensorflow_available',
            'get_model_config',
            'get_training_progress',
            'get_model_status'
        ]
        
        for method in required_methods:
            if hasattr(model_manager, method):
                print(f"   ✅ Method {method} exists")
            else:
                print(f"   ❌ Method {method} missing!")
                return False, None
        
        return True, model_manager
        
    except ImportError as e:
        print(f"   ❌ ModelManager import failed: {e}")
        return False, None
    except Exception as e:
        print(f"   ❌ ModelManager initialization failed: {e}")
        print(f"   📋 Error details: {traceback.format_exc()}")
        return False, None

def check_training_api():
    """Check training API imports"""
    print("\n🔍 Checking Training API...")
    
    try:
        app_dir = os.path.join(os.path.dirname(__file__), 'app')
        if app_dir not in sys.path:
            sys.path.append(app_dir)
        
        # Check if training API files exist
        api_dir = os.path.join(app_dir, 'api')
        training_files = [
            'training_api.py',
            'real_training_api.py'
        ]
        
        for file in training_files:
            file_path = os.path.join(api_dir, file)
            if os.path.exists(file_path):
                print(f"   ✅ {file} exists")
            else:
                print(f"   ❌ {file} missing!")
        
        # Try to import training APIs
        try:
            from api.training_api import training_api
            print("   ✅ training_api imported successfully")
        except ImportError as e:
            print(f"   ❌ training_api import failed: {e}")
        
        try:
            from api.real_training_api import real_training_api
            print("   ✅ real_training_api imported successfully")
        except ImportError as e:
            print(f"   ❌ real_training_api import failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Training API check failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🔧 BITCOIN LSTM TRAINING DIAGNOSTIC")
    print("=" * 50)
    
    # Check TensorFlow
    tf_ok, tf_module = check_tensorflow()
    
    # Check ModelManager
    mm_ok, model_manager = check_model_manager()
    
    # Check Training API
    api_ok = check_training_api()
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    print(f"TensorFlow: {'✅ OK' if tf_ok else '❌ FAILED'}")
    print(f"ModelManager: {'✅ OK' if mm_ok else '❌ FAILED'}")
    print(f"Training API: {'✅ OK' if api_ok else '❌ FAILED'}")
    
    if tf_ok and mm_ok and api_ok:
        print("\n🎉 ALL CHECKS PASSED - Training should work!")
    else:
        print("\n⚠️  ISSUES DETECTED - Please fix the failed components")
        
        if not tf_ok:
            print("   • Install TensorFlow: pip install tensorflow")
        if not mm_ok:
            print("   • Fix ModelManager tensorflow_available attribute")
        if not api_ok:
            print("   • Check training API files")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
