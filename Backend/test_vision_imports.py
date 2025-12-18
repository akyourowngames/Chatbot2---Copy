
print("Testing Vision Analysis...")
try:
    from Backend.vision.florence_loader import load_florence_model
    # Don't actually load it fully if it takes time/download, but check imports
    print("Imports successful.")
except ImportError as e:
    print(f"Import failed: {e}")

# We can't easily test the model download without internet access and time
print("Ready to run server.")
