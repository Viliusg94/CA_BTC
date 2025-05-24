"""
Quick script to run the routes fix
"""
import subprocess
import sys
import os

def run_fix():
    """Run the routes fix script"""
    try:
        # Change to project directory
        os.chdir('d:/CA_BTC')
        
        # Run the fix script
        result = subprocess.run([sys.executable, 'fix_routes_issue.py'], 
                              capture_output=True, text=True)
        
        print("Fix script output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        print("\n" + "="*50)
        print("Fix completed. Now restart your Flask application.")
        
    except Exception as e:
        print(f"Error running fix: {e}")

if __name__ == "__main__":
    run_fix()
