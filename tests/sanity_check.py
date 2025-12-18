import sys
import os

# Ensure backend matches path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Importing Dispatcher...")
try:
    from Backend.Dispatcher import dispatcher
    print("Dispatcher imported successfully.")
except Exception as e:
    print(f"Error importing Dispatcher: {e}")

print("Importing IntentClassifier...")
try:
    from Backend.IntentClassifier import IntentClassifier
    ic = IntentClassifier()
    print("IntentClassifier initialized.")
except Exception as e:
    print(f"Error importing IntentClassifier: {e}")
    
print("Sanity Check Complete.")
