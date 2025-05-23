"""
Main application startup script with diagnostics
"""

import os
import sys
import subprocess
import time

def run_diagnostics():
    """Run startup diagnostics"""
    print("Running startup diagnostics...")
    
    try:
        result = subprocess.run([
            sys.executable, 
            os.path.join('app', 'startup_check.py')
        ], capture_output=True, text=True, timeout=30)
        
        print("=== DIAGNOSTIC OUTPUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== DIAGNOSTIC ERRORS ===")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Diagnostics timed out - continuing anyway...")
        return True
    except Exception as e:
        print(f"Diagnostic error: {e}")
        return True

def main():
    """Main startup function"""
    print("=== BITCOIN PRICE PREDICTION APP STARTUP ===")
    
    # Change to app directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run diagnostics (optional)
    diagnostics_ok = run_diagnostics()
    
    if not diagnostics_ok:
        print("Diagnostics failed, but attempting to start anyway...")
        time.sleep(2)
    
    # Start the application
    print("Starting application...")
    try:
        # Import and run the app
        sys.path.insert(0, 'app')
        from app import app
        
        print("Flask app imported successfully")
        print("Starting server on http://localhost:5000")
        print("Press Ctrl+C to stop")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Set to False for production
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
