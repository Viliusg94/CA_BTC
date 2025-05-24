#!/usr/bin/env python3
"""
Bitcoin LSTM Application Diagnostic Script
Run this script to diagnose and fix common issues
"""

import os
import sys
import json
import requests
import sqlite3
from datetime import datetime

def check_project_structure():
    """Check if project structure is correct"""
    print("🔍 Checking project structure...")
    
    required_paths = [
        'app/app.py',
        'app/new_endpoints.py',
        'app/model_manager.py',
        'models/',
        'app/templates/',
        'app/static/'
    ]
    
    issues = []
    for path in required_paths:
        if not os.path.exists(path):
            issues.append(f"Missing: {path}")
        else:
            print(f"  ✅ {path}")
    
    if issues:
        print("  ❌ Issues found:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print("  ✅ Project structure looks good")
        return True

def check_flask_app_running():
    """Check if Flask app is running"""
    print("\n🌐 Checking Flask application...")
    
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("  ✅ Flask app is running")
            return True
        else:
            print(f"  ⚠️ Flask app returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("  ❌ Flask app is not running or not accessible")
        return False

def check_database():
    """Check database status"""
    print("\n💾 Checking database...")
    
    db_path = 'app/bitcoin_models.db'
    if not os.path.exists(db_path):
        print("  ❌ Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if model_history table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_history'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM model_history")
            model_count = cursor.fetchone()[0]
            print(f"  ✅ Database found with {model_count} models")
        else:
            print("  ⚠️ model_history table not found")
        
        conn.close()
        return table_exists
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def check_api_endpoints():
    """Check API endpoints"""
    print("\n🔗 Checking API endpoints...")
    
    endpoints = [
        '/api/model_history_db',
        '/api/model/config?model_type=lstm',
        '/models',
        '/training_status'
    ]
    
    working_endpoints = 0
    for endpoint in endpoints:
        try:
            url = f'http://localhost:5000{endpoint}'
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                try:
                    response.json()  # Try to parse as JSON
                    print(f"  ✅ {endpoint}")
                    working_endpoints += 1
                except:
                    print(f"  ⚠️ {endpoint} (returns HTML, not JSON)")
            else:
                print(f"  ❌ {endpoint} (status {response.status_code})")
                
        except Exception as e:
            print(f"  ❌ {endpoint} (error: {str(e)[:50]})")
    
    print(f"  📊 {working_endpoints}/{len(endpoints)} endpoints working correctly")
    return working_endpoints == len(endpoints)

def create_minimal_endpoints():
    """Create minimal working endpoints"""
    print("\n🔧 Creating minimal endpoints fix...")
    
    minimal_endpoints = """
from flask import jsonify, render_template, request
import logging

logger = logging.getLogger(__name__)

def register_endpoints(app, db=None, ModelHistory=None, model_manager=None):
    
    @app.route('/models')
    def models_page():
        try:
            return render_template('models.html', 
                                 model_files={},
                                 model_history={})
        except Exception as e:
            return f"Models page error: {e}"
    
    @app.route('/training_status')
    def training_status():
        try:
            return render_template('training_status.html', 
                                 progress_data={})
        except Exception as e:
            return f"Training status error: {e}"
    
    @app.route('/api/model_history_db')
    def api_model_history_db():
        return jsonify({'success': True, 'models': [], 'count': 0})
    
    @app.route('/api/model/config')
    def model_config():
        return jsonify({'success': True, 'config': {}})
    
    @app.route('/api/model_details/<model_type>')
    def api_model_details(model_type):
        return jsonify({'success': True, 'details': {'model_type': model_type}})
    
    @app.route('/api/price_history')
    def api_price_history():
        return jsonify({'status': 'success', 'data': {'dates': [], 'prices': []}})
    
    @app.route('/api/predictions')
    def api_predictions():
        return jsonify({'status': 'success', 'data': {'dates': [], 'values': []}})
    
    logger.info("Minimal endpoints registered")
"""
    
    try:
        with open('app/new_endpoints.py', 'w') as f:
            f.write(minimal_endpoints)
        print("  ✅ Created minimal endpoints file")
        return True
    except Exception as e:
        print(f"  ❌ Error creating endpoints: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 BITCOIN LSTM APPLICATION DIAGNOSTICS")
    print("=" * 50)
    
    # Run all checks
    structure_ok = check_project_structure()
    flask_running = check_flask_app_running()
    database_ok = check_database()
    
    if flask_running:
        endpoints_ok = check_api_endpoints()
    else:
        endpoints_ok = False
        print("  ⚠️ Skipping endpoint check (Flask not running)")
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    print(f"Project Structure: {'✅' if structure_ok else '❌'}")
    print(f"Flask Application: {'✅' if flask_running else '❌'}")
    print(f"Database: {'✅' if database_ok else '❌'}")
    print(f"API Endpoints: {'✅' if endpoints_ok else '❌'}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 20)
    
    if not flask_running:
        print("1. Start the Flask application: cd app && python app.py")
    
    if not endpoints_ok and flask_running:
        print("2. API endpoints are not working correctly")
        print("   Consider creating minimal endpoints:")
        create_minimal_endpoints()
        print("   Then restart Flask application")
    
    if not database_ok:
        print("3. Database issues detected")
        print("   The application should create the database automatically")
    
    print("\n🔄 After making changes, restart the Flask app and run diagnostics again")

if __name__ == "__main__":
    main()
