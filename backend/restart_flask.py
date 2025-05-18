import os
import sys
import subprocess
import signal
import time

def restart_flask():
    """Restart the Flask application"""
    print("Restarting Flask application...")
    
    # Kill current Flask process if any
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if this is a Python process running our Flask app
                if proc.info['name'] == 'python.exe' and any('run.py' in arg for arg in proc.info['cmdline']):
                    print(f"Killing previous Flask process (PID: {proc.info['pid']})")
                    os.kill(proc.info['pid'], signal.SIGTERM)
                    time.sleep(1)  # Give it time to shut down
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        print("psutil not installed, skipping process kill. Please stop the Flask server manually.")
    
    # Start the Flask application in a new process
    try:
        flask_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(flask_dir)
        print(f"Starting Flask from {flask_dir}")
        
        # Start the Flask app
        subprocess.Popen([sys.executable, 'run.py'], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        print("Flask application started.")
    except Exception as e:
        print(f"Error starting Flask: {e}")

if __name__ == "__main__":
    restart_flask()
