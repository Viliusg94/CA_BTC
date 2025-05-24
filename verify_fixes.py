"""
Verification script to check that the syntax issues are fixed
"""
import sys
import os
import importlib.util

def check_file_syntax(file_path):
    """Check if a Python file has syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            compile(content, file_path, 'exec')
        print(f"✅ {file_path} - No syntax errors")
        return True
    except SyntaxError as e:
        print(f"❌ {file_path} - Syntax error: {e}")
        return False

def import_module(file_path):
    """Try to import a module from file path"""
    try:
        module_name = os.path.basename(file_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {file_path} - Successfully imported")
        return True
    except Exception as e:
        print(f"❌ {file_path} - Import error: {e}")
        return False

def main():
    print("Checking fixed files for syntax errors...")
    
    # List of files to check
    files_to_check = [
        os.path.join('app', 'model_manager.py'),
        os.path.join('app', 'fixed_endpoints.py'),
        os.path.join('app', 'api', 'model_api.py'),
        os.path.join('app', 'api', 'training_api.py')
    ]
    
    # Base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    all_passed = True
    
    # Check each file
    for rel_path in files_to_check:
        file_path = os.path.join(base_dir, rel_path)
        if os.path.exists(file_path):
            if not check_file_syntax(file_path):
                all_passed = False
        else:
            print(f"⚠️ {file_path} - File not found")
    
    if all_passed:
        print("\nAll files checked successfully! The syntax errors have been fixed.")
        print("You can now try starting the application again.")
    else:
        print("\nSome issues were detected. Please review the errors above.")

if __name__ == "__main__":
    main()
