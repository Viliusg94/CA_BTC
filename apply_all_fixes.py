#!/usr/bin/env python3
"""
Apply all fixes to the Bitcoin LSTM application
"""

import os
import shutil
import subprocess
import sys

def run_fix_script(script_name):
    """Run a fix script and return success status"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            return True
        else:
            print(f"❌ {script_name} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    """Apply all fixes"""
    print("🚀 APPLYING ALL FIXES TO BITCOIN LSTM APPLICATION")
    print("=" * 60)
    
    # 1. Create templates
    print("\n1. Creating template files...")
    try:
        exec(open('create_templates.py').read())
    except Exception as e:
        print(f"❌ Error creating templates: {e}")
    
    # 2. Create fixed app.py
    print("\n2. Creating fixed app.py...")
    try:
        exec(open('create_fixed_app.py').read())
    except Exception as e:
        print(f"❌ Error creating fixed app: {e}")
    
    # 3. Create directories
    print("\n3. Creating required directories...")
    directories = [
        'app/models',
        'app/static/js',
        'app/static/css',
        'models'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ {directory}")
    
    # 4. Run diagnostic
    print("\n4. Running diagnostic...")
    try:
        exec(open('diagnostic.py').read())
    except Exception as e:
        print(f"❌ Error running diagnostic: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 ALL FIXES APPLIED!")
    print("\n📋 NEXT STEPS:")
    print("1. cd app")
    print("2. python app.py")
    print("3. Open http://localhost:5000 in your browser")
    print("4. Test the following pages:")
    print("   - http://localhost:5000/models")
    print("   - http://localhost:5000/training_status")
    print("   - http://localhost:5000/predict")

if __name__ == '__main__':
    main()
