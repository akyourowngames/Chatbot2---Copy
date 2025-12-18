import sys
import os
import threading
import time
import logging

# Ensure we can import from the current directory (important for PyInstaller)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the core components
# Note: api_server.py is huge and does its own setup
from api_server import start_api_server

def run_backend():
    try:
        print("[LAUNCHER] Starting Backend API Server...")
        # Run on port 5000, no debug, no reloader
        start_api_server(port=5000, debug=False)
    except Exception as e:
        print(f"[LAUNCHER] Backend failed to start: {e}")
        logging.error(f"Backend failure: {e}")

if __name__ == "__main__":
    # Handle multiprocessing freeze for PyInstaller
    import multiprocessing
    multiprocessing.freeze_support()

    print("========================================")
    print("   KAI OS - Beast Mode AI Assistant")
    print("========================================")
    
    # 1. Start backend thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # 2. Wait for backend to initialize (integrations take time)
    print("[LAUNCHER] Initializing systems, please wait...")
    time.sleep(4)
    
    # 3. Start Frontend
    try:
        from Frontend.GUI_Futuristic import Dashboard
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFont, QIcon
        
        print("[LAUNCHER] Launching GUI...")
        qt_app = QApplication(sys.argv)
        qt_app.setStyle('Fusion')
        qt_app.setFont(QFont("Segoe UI", 10))
        
        # Set app icon if available
        if os.path.exists("app_icon.ico"):
            qt_app.setWindowIcon(QIcon("app_icon.ico"))
            
        window = Dashboard()
        window.show()
        
        print("[LAUNCHER] KAI OS is active.")
        sys.exit(qt_app.exec_())
        
    except Exception as e:
        print(f"[LAUNCHER] GUI Launch Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
