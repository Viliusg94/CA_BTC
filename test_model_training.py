#!/usr/bin/env python3
"""
Simple test to verify model training functionality.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

def test_training_api():
    """Test the training API directly"""
    print("=== TESTING TRAINING API ===")
    
    base_url = "http://localhost:5000"
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code != 200:
            print(f"❌ Server returned status {response.status_code}")
            return False
        print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - make sure it's running on port 5000")
        return False
    
    # Test training endpoint
    print("\n--- Testing /api/train_model endpoint ---")
    
    model_type = "lstm"
    training_data = {
        "model_type": model_type,
        "epochs": 5,
        "batch_size": 32,
        "learning_rate": 0.001,
        "sequence_length": 10
    }
    
    try:
        response = requests.post(f"{base_url}/api/train_model", data=training_data)
        print(f"Status code: {response.status_code}")
        
        try:
            result = response.json()
            print("Response JSON:")
            print(json.dumps(result, indent=2))
            
            if result.get("success", False):
                print("✅ Training started successfully")
            else:
                print(f"❌ Training failed: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing JSON response: {str(e)}")
            print(f"Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending request: {str(e)}")
        return False
    
    # Check training status
    print("\n--- Checking training status ---")
    time.sleep(3)  # Wait a bit for training to start
    
    try:
        response = requests.get(f"{base_url}/api/model/progress?model_type={model_type}")
        print(f"Status code: {response.status_code}")
        
        try:
            result = response.json()
            print("Training progress:")
            print(json.dumps(result, indent=2))
            
            if "progress" in result and result["model_type"] == model_type:
                print(f"✅ Training progress: {result['progress'].get('progress', 0)}%")
                print(f"Status: {result['progress'].get('status', 'Unknown')}")
            else:
                print("❌ Invalid training status response")
                return False
        except Exception as e:
            print(f"❌ Error parsing JSON response: {str(e)}")
            print(f"Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending request: {str(e)}")
        return False
    
    # Check debug endpoint
    print("\n--- Checking debug endpoint ---")
    
    try:
        response = requests.get(f"{base_url}/api/training_debug")
        print(f"Status code: {response.status_code}")
        
        try:
            result = response.json()
            print("Debug info:")
            print(json.dumps(result, indent=2))
            
            if result.get("success", False):
                print("✅ Debug endpoint working correctly")
            else:
                print(f"❌ Debug endpoint error: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing JSON response: {str(e)}")
            print(f"Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending request: {str(e)}")
        return False
    
    print("\n=== TEST SUMMARY ===")
    print("✅ All tests passed")
    print("\nNOTE: Training may continue in the background. Check the web interface at:")
    print(f"{base_url}/training_status")
    
    return True

if __name__ == "__main__":
    test_training_api()
