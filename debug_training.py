#!/usr/bin/env python3
"""
This script diagnoses and fixes issues with model training status.
"""

import os
import sys
import json
import sqlite3
import time
from datetime import datetime

def check_models_directory():
    """Check if models directory exists and has proper permissions"""
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    print(f"Checking models directory: {models_dir}")
    
    if not os.path.exists(models_dir):
        print(f"  ❌ Models directory does not exist. Creating it...")
        try:
            os.makedirs(models_dir)
            print(f"  ✅ Models directory created successfully")
        except Exception as e:
            print(f"  ❌ Failed to create models directory: {str(e)}")
            return False
    else:
        print(f"  ✅ Models directory exists")
    
    # Check permissions
    try:
        test_file = os.path.join(models_dir, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"  ✅ Models directory is writable")
    except Exception as e:
        print(f"  ❌ Models directory is not writable: {str(e)}")
        return False
    
    return True

def check_training_status_files():
    """Check training status files"""
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    status_file = os.path.join(models_dir, 'training_status.json')
    print(f"Checking training status file: {status_file}")
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            print(f"  ✅ Training status file exists and is valid JSON")
            print(f"  📊 Current status contains: {list(status.keys())}")
            
            # Check if any models are in 'Training' state
            training_models = [model_type for model_type, info in status.items() 
                               if isinstance(info, dict) and info.get('status') == 'Training']
            
            if training_models:
                print(f"  ⚠️ Found models in 'Training' state: {training_models}")
                
                # Reset their status
                for model_type in training_models:
                    status[model_type]['status'] = 'Idle'
                    status[model_type]['progress'] = 0
                
                # Save the fixed status
                with open(status_file, 'w') as f:
                    json.dump(status, f, indent=2)
                print(f"  ✅ Reset training status for these models")
            else:
                print(f"  ✅ No models currently in 'Training' state")
        except json.JSONDecodeError:
            print(f"  ❌ Training status file exists but is not valid JSON")
            print(f"  🔄 Creating new training status file...")
            
            # Create a new empty status file
            with open(status_file, 'w') as f:
                json.dump({}, f)
            print(f"  ✅ Created new empty training status file")
    else:
        print(f"  ⚠️ Training status file does not exist. Creating it...")
        
        # Create a new empty status file
        try:
            with open(status_file, 'w') as f:
                json.dump({}, f)
            print(f"  ✅ Created new training status file")
        except Exception as e:
            print(f"  ❌ Failed to create training status file: {str(e)}")

def check_database():
    """Check the SQLite database"""
    db_path = os.path.join(os.path.dirname(__file__), 'app', 'bitcoin_models.db')
    print(f"Checking database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"  ❌ Database file does not exist")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if model_history table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_history'")
        if cursor.fetchone() is None:
            print(f"  ❌ model_history table does not exist")
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(model_history)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {'id', 'model_type', 'timestamp', 'is_active', 'r2', 'mae', 'rmse'}
        missing_columns = required_columns - columns
        
        if missing_columns:
            print(f"  ❌ Missing columns in model_history table: {missing_columns}")
        else:
            print(f"  ✅ model_history table has all required columns")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM model_history")
        count = cursor.fetchone()[0]
        print(f"  📊 Database has {count} model records")
        
        conn.close()
        return True
    except Exception as e:
        print(f"  ❌ Error checking database: {str(e)}")
        return False

def check_model_manager():
    """Check model_manager.py file"""
    manager_path = os.path.join(os.path.dirname(__file__), 'app', 'model_manager.py')
    print(f"Checking model_manager.py: {manager_path}")
    
    if not os.path.exists(manager_path):
        print(f"  ❌ model_manager.py does not exist")
        return False
    
    # Check if file has expected content
    with open(manager_path, 'r') as f:
        content = f.read()
    
    # Check for critical methods
    checks = [
        ('train_model', 'train_model method'),
        ('get_training_progress', 'get_training_progress method'),
        ('is_training', 'is_training method'),
        ('_train_model_thread', '_train_model_thread method')
    ]
    
    all_checks_passed = True
    for term, description in checks:
        if term not in content:
            print(f"  ❌ Missing {description}")
            all_checks_passed = False
        else:
            print(f"  ✅ Found {description}")
    
    if not all_checks_passed:
        print(f"  ⚠️ model_manager.py is missing critical components")
    
    return all_checks_passed

def fix_training_status_view():
    """Fix the training_status.html to show all models"""
    status_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'training_status.html')
    print(f"Checking training_status.html: {status_path}")
    
    if not os.path.exists(status_path):
        print(f"  ❌ training_status.html does not exist")
        return False
    
    try:
        # Read the file
        with open(status_path, 'r') as f:
            content = f.read()
        
        # Check if the file contains specific debugging sections
        if '<!-- DEBUG INFO -->' not in content:
            print(f"  ⚠️ Adding debug section to training_status.html")
            
            # Find a good place to insert our debug information
            insert_position = content.find('<!-- No models message -->')
            if insert_position > 0:
                debug_html = '''
<!-- DEBUG INFO -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card shadow">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0"><i class="fas fa-bug"></i> Debug Information</h5>
            </div>
            <div class="card-body">
                <div id="debug-info">
                    <p>Training status raw data will appear here</p>
                </div>
            </div>
        </div>
    </div>
</div>
'''
                # Insert the debug section
                new_content = content[:insert_position] + debug_html + content[insert_position:]
                
                # Update the JavaScript to populate debug info
                script_section = '''
// Debug info population
function populateDebugInfo() {
    fetch('/api/training_debug')
        .then(response => response.json())
        .then(data => {
            const debugInfo = document.getElementById('debug-info');
            if (debugInfo) {
                let html = '<h6>Raw Training Status:</h6>';
                html += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                debugInfo.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error fetching debug info:', error);
            const debugInfo = document.getElementById('debug-info');
            if (debugInfo) {
                debugInfo.innerHTML = '<div class="alert alert-danger">Error fetching debug data</div>';
            }
        });
}

// Call on page load
populateDebugInfo();
// Refresh every 10 seconds
setInterval(populateDebugInfo, 10000);
'''
                # Find the scripts section
                scripts_pos = new_content.find('{% block scripts %}')
                if scripts_pos > 0:
                    end_scripts_pos = new_content.find('{% endblock %}', scripts_pos)
                    if end_scripts_pos > 0:
                        new_content = (
                            new_content[:end_scripts_pos] + 
                            script_section + 
                            new_content[end_scripts_pos:]
                        )
                
                # Write the updated content
                with open(status_path, 'w') as f:
                    f.write(new_content)
                
                print(f"  ✅ Updated training_status.html with debug information")
            else:
                print(f"  ❌ Could not find a suitable position to insert debug information")
        else:
            print(f"  ✅ training_status.html already has debug section")
        
        return True
    except Exception as e:
        print(f"  ❌ Error updating training_status.html: {str(e)}")
        return False

def add_debug_endpoint():
    """Add a debug endpoint to new_endpoints.py"""
    endpoints_path = os.path.join(os.path.dirname(__file__), 'app', 'new_endpoints.py')
    print(f"Adding debug endpoint to: {endpoints_path}")
    
    if not os.path.exists(endpoints_path):
        print(f"  ❌ new_endpoints.py does not exist")
        return False
    
    try:
        # Read the file
        with open(endpoints_path, 'r') as f:
            content = f.read()
        
        # Check if debug endpoint already exists
        if '/api/training_debug' not in content:
            print(f"  ⚠️ Adding debug endpoint to new_endpoints.py")
            
            # Find the register_endpoints function
            register_pos = content.find('def register_endpoints(')
            if register_pos > 0:
                # Find a good place to insert our debug endpoint
                register_end = content.find(')', register_pos)
                if register_end > 0:
                    debug_endpoint = '''
    @app.route('/api/training_debug')
    def api_training_debug():
        """Debug endpoint for training status"""
        try:
            if not model_manager:
                return jsonify({'error': 'ModelManager not available'}), 500
            
            # Get raw training status data
            training_status = getattr(model_manager, 'training_status', {})
            training_configs = getattr(model_manager, 'configs', {})
            training_threads = {}
            
            # Check if threads are alive
            threads = threading.enumerate()
            for thread in threads:
                if 'train' in thread.name.lower():
                    training_threads[thread.name] = {
                        'alive': thread.is_alive(),
                        'daemon': thread.daemon,
                        'ident': thread.ident
                    }
            
            return jsonify({
                'success': True,
                'training_status': training_status,
                'training_configs': training_configs,
                'training_threads': training_threads,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
'''
                    # Import threading if not already imported
                    if 'import threading' not in content:
                        import_pos = content.find('import')
                        if import_pos > 0:
                            # Find the end of imports section
                            next_line_pos = content.find('\n\n', import_pos)
                            if next_line_pos > 0:
                                content = content[:next_line_pos] + '\nimport threading' + content[next_line_pos:]
                    
                    # Find a good place to insert our endpoint - near the end before logger.info
                    insert_pos = content.rfind('logger.info')
                    if insert_pos > 0:
                        new_content = content[:insert_pos] + debug_endpoint + content[insert_pos:]
                        
                        # Write the updated content
                        with open(endpoints_path, 'w') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ Added debug endpoint to new_endpoints.py")
                    else:
                        print(f"  ❌ Could not find a suitable position to insert debug endpoint")
                else:
                    print(f"  ❌ Could not find end of register_endpoints function")
            else:
                print(f"  ❌ Could not find register_endpoints function")
        else:
            print(f"  ✅ Debug endpoint already exists in new_endpoints.py")
        
        return True
    except Exception as e:
        print(f"  ❌ Error updating new_endpoints.py: {str(e)}")
        return False

def main():
    """Main function to run all checks"""
    print("=== TRAINING STATUS DEBUGGER ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    models_dir_ok = check_models_directory()
    check_training_status_files()
    db_ok = check_database()
    manager_ok = check_model_manager()
    fix_training_status_view()
    add_debug_endpoint()
    
    # Print summary
    print("\n=== SUMMARY ===")
    if models_dir_ok:
        print("✅ Models directory is OK")
    else:
        print("❌ Models directory has issues")
        
    if db_ok:
        print("✅ Database is OK")
    else:
        print("❌ Database has issues")
        
    if manager_ok:
        print("✅ Model manager is OK")
    else:
        print("❌ Model manager has issues")
        
    print("\n=== NEXT STEPS ===")
    print("1. Restart the Flask application")
    print("2. Try training a model again")
    print("3. Check the debug information in the training status page")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
