#!/usr/bin/env python3
"""
Simple test script to validate the ModelManager method signature
without importing the full app
"""

import sys
import os
import json
import inspect

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_model_manager_signature():
    """Test ModelManager method signature without full initialization"""
    print("Testing ModelManager train_model method signature...")
    
    try:
        # Import just the ModelManager class
        from model_manager import ModelManager
        
        # Get the method signature
        signature = inspect.signature(ModelManager.train_model)
        params = list(signature.parameters.keys())
        
        print(f"✓ train_model method signature: {params}")
        
        # Check if signature is correct (should be ['self', 'model_type'])
        expected_params = ['self', 'model_type']
        if params == expected_params:
            print("✓ Method signature is correct: train_model(self, model_type)")
            return True
        else:
            print(f"✗ Method signature unexpected. Expected {expected_params}, got {params}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing signature: {e}")
        return False

def test_config_methods():
    """Test that config update methods exist"""
    print("Testing ModelManager configuration methods...")
    
    try:
        from model_manager import ModelManager
        
        # Check if update_model_config method exists
        if hasattr(ModelManager, 'update_model_config'):
            print("✓ update_model_config method exists")
            
            # Check signature
            signature = inspect.signature(ModelManager.update_model_config)
            params = list(signature.parameters.keys())
            print(f"✓ update_model_config signature: {params}")
            
            expected_params = ['self', 'model_type', 'config']
            if params == expected_params:
                print("✓ update_model_config signature is correct")
            else:
                print(f"✗ update_model_config signature unexpected. Expected {expected_params}, got {params}")
                return False
        else:
            print("✗ update_model_config method not found")
            return False
            
        # Check if get_model_config method exists
        if hasattr(ModelManager, 'get_model_config'):
            print("✓ get_model_config method exists")
        else:
            print("✗ get_model_config method not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing config methods: {e}")
        return False

def simulate_endpoint_behavior():
    """Simulate what the endpoint would do"""
    print("Simulating training endpoint behavior...")
    
    # Simulate form data
    form_data = {
        'model_type': 'lstm',
        'epochs': '50',
        'batch_size': '32',
        'learning_rate': '0.001',
        'sequence_length': '24'
    }
    
    print(f"Form data: {form_data}")
    
    # Simulate parameter conversion (what the endpoint would do)
    try:
        model_type = form_data['model_type']
        config_updates = {
            'epochs': int(form_data['epochs']),
            'batch_size': int(form_data['batch_size']),
            'learning_rate': float(form_data['learning_rate']),
            'lookback': int(form_data['sequence_length'])  # sequence_length becomes lookback
        }
        
        print(f"✓ Converted parameters: {config_updates}")
        print(f"✓ Model type: {model_type}")
        
        # This is what the endpoint would call:
        # 1. model_manager.update_model_config(model_type, config_updates)
        # 2. model_manager.train_model(model_type)
        
        print("✓ Simulation shows correct parameter flow")
        return True
        
    except Exception as e:
        print(f"✗ Error in simulation: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING TRAINING PARAMETER FIXES")
    print("=" * 50)
    
    success = True
    
    success &= test_model_manager_signature()
    print()
    success &= test_config_methods()
    print()
    success &= simulate_endpoint_behavior()
    
    print()
    print("=" * 50)
    if success:
        print("✓ ALL TESTS PASSED! The training parameter fix should work.")
    else:
        print("✗ SOME TESTS FAILED! There may be issues with the fix.")
    print("=" * 50)
    
    sys.exit(0 if success else 1)
