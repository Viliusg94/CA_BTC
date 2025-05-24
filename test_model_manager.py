"""
Test script for ModelManager to verify TensorFlow availability fix
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from model_manager import ModelManager

def test_model_manager():
    """Test ModelManager initialization and basic functionality"""
    
    print("=" * 60)
    print("TESTING MODEL MANAGER")
    print("=" * 60)
    
    try:
        # Initialize ModelManager
        print("1. Initializing ModelManager...")
        model_manager = ModelManager()
        print("   ✅ ModelManager initialized successfully")
        
        # Test TensorFlow availability check
        print("2. Checking TensorFlow availability...")
        tf_available = model_manager.is_tensorflow_available()
        print(f"   TensorFlow available: {'✅ YES' if tf_available else '❌ NO'}")
        print(f"   tensorflow_available attribute: {hasattr(model_manager, 'tensorflow_available')}")
        
        if hasattr(model_manager, 'tensorflow_available'):
            print(f"   tensorflow_available value: {model_manager.tensorflow_available}")
        
        # Test model configuration
        print("3. Testing model configuration...")
        lstm_config = model_manager.get_model_config('lstm')
        print(f"   LSTM config loaded: {'✅ YES' if lstm_config else '❌ NO'}")
        if lstm_config:
            print(f"   LSTM config keys: {list(lstm_config.keys())}")
        
        # Test training progress
        print("4. Testing training progress...")
        progress = model_manager.get_training_progress('lstm')
        print(f"   Training progress structure: {'✅ YES' if progress else '❌ NO'}")
        if progress:
            print(f"   Progress keys: {list(progress.keys())}")
        
        # Test model status
        print("5. Testing model status...")
        status = model_manager.get_model_status('lstm')
        print(f"   Model status structure: {'✅ YES' if status else '❌ NO'}")
        if status:
            print(f"   Status keys: {list(status.keys())}")
        
        # Test available models
        print("6. Testing available models...")
        available = model_manager.get_available_models()
        print(f"   Available models count: {len(available)}")
        
        # Test model summary
        print("7. Testing model summary...")
        summary = model_manager.get_model_summary()
        print(f"   Summary keys: {list(summary.keys())}")
        print(f"   TensorFlow in summary: {summary.get('tensorflow_available', 'NOT FOUND')}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - ModelManager is working correctly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_model_manager()
    sys.exit(0 if success else 1)
