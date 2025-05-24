#!/usr/bin/env python3
"""
Restart Flask server script
This script stops and restarts the Flask server process
"""
import os
import signal
import subprocess
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_flask_pid():
    """Find PID of the Flask server process"""
    try:
        if sys.platform == 'win32':
            # Windows version using wmic
            process = subprocess.Popen(['wmic', 'process', 'where', 
                                     'commandline like "%python%app/app.py%" and name like "%python%"', 
                                     'get', 'processid'], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = process.communicate()
            
            if stdout:
                lines = stdout.decode().strip().split('\n')
                if len(lines) >= 2:  # At least header and one process
                    pid_str = lines[1].strip()
                    if pid_str.isdigit():
                        return int(pid_str)
        else:
            # Unix version using pgrep
            process = subprocess.Popen(['pgrep', '-f', 'python.*app/app.py'], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = process.communicate()
            
            if stdout:
                pids = stdout.decode().strip().split('\n')
                if pids and pids[0]:
                    return int(pids[0])
        
        return None
    except Exception as e:
        logger.error(f"Error finding Flask PID: {e}")
        return None

def stop_flask_server():
    """Stop the Flask server process"""
    pid = find_flask_pid()
    
    if pid:
        logger.info(f"Found Flask server with PID {pid}")
        try:
            if sys.platform == 'win32':
                # Windows
                subprocess.run(['taskkill', '/F', '/PID', str(pid)])
                logger.info(f"Terminated process {pid}")
                return True
            else:
                # Unix
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to PID {pid}")
                
                # Wait for process to terminate
                for _ in range(5):
                    time.sleep(1)
                    try:
                        os.kill(pid, 0)  # Check if process exists
                    except OSError:
                        logger.info(f"Process {pid} terminated")
                        return True
                
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"Sent SIGKILL to PID {pid}")
                    return True
                except OSError:
                    logger.info(f"Process {pid} already terminated")
                    return True
                    
        except Exception as e:
            logger.error(f"Error stopping Flask server: {e}")
            return False
    else:
        logger.info("Flask server not running")
        return True

def start_flask_server():
    """Start the Flask server"""
    try:
        logger.info("Starting Flask server...")
        
        # Start Flask in a new process
        if sys.platform == 'win32':
            # Windows
            subprocess.Popen(['python', 'app/app.py'], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # Unix
            subprocess.Popen(['python', 'app/app.py'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE, 
                           start_new_session=True)
        
        logger.info("Flask server started")
        return True
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Flask Server Restart Script ===")
    
    # First, run the fix script if it exists
    fix_script = 'fix_missing_routes.py'
    if os.path.exists(fix_script):
        logger.info(f"Running fix script: {fix_script}")
        try:
            subprocess.run([sys.executable, fix_script], check=True)
            logger.info("Fix script completed successfully")
        except subprocess.CalledProcessError:
            logger.error("Fix script failed")
    
    # Stop the server if running
    stop_result = stop_flask_server()
    
    if stop_result:
        # Wait a moment before starting
        time.sleep(2)
        
        # Start the server
        start_result = start_flask_server()
        
        if start_result:
            logger.info("Flask server successfully restarted")
            logger.info("\nYou should now be able to access:")
            logger.info("  - http://localhost:5000/models")
            logger.info("  - http://localhost:5000/training_status")
        else:
            logger.error("Failed to start Flask server")
    else:
        logger.error("Failed to stop Flask server")
