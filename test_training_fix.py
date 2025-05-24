#!/usr/bin/env python3
"""
Test script to validate the training parameter fix
"""

import sys
import os
import requests
import json
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.model_manager import ModelManager

def test_model_manager_training():
    """Test ModelManager training with updated configuration"""
    print("Testing ModelManager training workflow...")
    
    # Initialize ModelManager
    try:
        model_manager = ModelManager(models_dir='models')
        print("✓ ModelManager initialized successfully")
    except Exception as e:
        print(f"✗ ModelManager initialization failed: {e}")
        return False
    
    # Test configuration update
    model_type = 'lstm'
    test_config = {
        'epochs': 10,
        'batch_size': 32,
        'learning_rate': 0.001,
        'lookback': 24
    }
    
    try:
        result = model_manager.update_model_config(model_type, test_config)
        if result:
            print(f"✓ Configuration updated successfully for {model_type}")
        else:
            print(f"✗ Configuration update failed for {model_type}")
            return False
    except Exception as e:
        print(f"✗ Configuration update error: {e}")
        return False
    
    # Verify configuration was updated
    try:
        config = model_manager.get_model_config(model_type)
        print(f"Updated configuration: {config}")
        
        # Check if our parameters were saved
        for key, value in test_config.items():
            if config.get(key) == value:
                print(f"✓ Parameter {key}: {value} correctly saved")
            else:
                print(f"✗ Parameter {key}: expected {value}, got {config.get(key)}")
                return False
    except Exception as e:
        print(f"✗ Configuration retrieval error: {e}")
        return False
    
    # Test method signature (without actually starting training)
    try:
        # This should not raise a TypeError about argument count
        import inspect
        signature = inspect.signature(model_manager.train_model)
        params = list(signature.parameters.keys())
        print(f"✓ train_model method signature: {params}")
        
        if 'model_type' in params and len(params) == 1:
            print("✓ Method signature matches expected (model_type only)")
        else:
            print(f"✗ Method signature unexpected: {params}")
            return False
            
    except Exception as e:
        print(f"✗ Signature inspection error: {e}")
        return False
    
    print("\n✓ All training parameter tests passed!")
    return True

def test_training_status_page():
    """Test if training status page loads correctly"""
    print("Testing training status page...")
    try:
        response = requests.get('http://localhost:5000/training_status')
        if response.status_code == 200:
            print("✅ Training status page loads successfully")
        else:
            print(f"❌ Training status page returned status code: {response.status_code}")
            if 'text/html' in response.headers.get('Content-Type', ''):
                print("Response contains HTML - likely redirecting to another page")
    except Exception as e:
        print(f"❌ Error accessing training status page: {e}")

def test_training_status_api():
    """Test if training status API works"""
    print("\nTesting training status API...")
    try:
        response = requests.get('http://localhost:5000/api/training_status')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Training status API works correctly")
                print(f"Training models: {data.get('training_summary', {}).get('training_models', 0)}")
            else:
                print(f"❌ Training status API returned error: {data.get('error')}")
        else:
            print(f"❌ Training status API returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing training status API: {e}")

def test_stop_training_api():
    """Test if stop training API works"""
    print("\nTesting stop training API...")
    
    model_types = ['lstm', 'gru', 'cnn', 'transformer']
    for model_type in model_types:
        try:
            print(f"Testing stop training for {model_type}...")
            response = requests.post(f'http://localhost:5000/api/stop_training/{model_type}')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Stop training API works for {model_type}")
                else:
                    print(f"❌ Stop training API returned error for {model_type}: {data.get('error')}")
            else:
                print(f"❌ Stop training API returned status code for {model_type}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error accessing stop training API for {model_type}: {e}")

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get('http://localhost:5000', timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server first.")
        sys.exit(1)
    
    # Run tests
    success = test_model_manager_training()
    test_training_status_page()
    test_training_status_api()
    test_stop_training_api()
    sys.exit(0 if success else 1)
