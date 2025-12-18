import os
import shutil
import py_compile
import sys

# Configuration
BUILD_DIR = 'dist/backend_build'
SOURCE_DIRS = ['Backend', 'Config', 'Data', 'models']
ROOT_FILES_TO_COMPILE = ['api_server.py']
ROOT_FILES_TO_COPY = ['Requirements.txt', '.env']

def clean_build_dir():
    if os.path.exists(BUILD_DIR):
        print(f"Cleaning build directory: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

def compile_and_copy(src_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    print(f"Processing directory: {src_dir}")
    
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dest_dir, item)
        
        if os.path.isdir(s):
            if item == '__pycache__':
                continue
            compile_and_copy(s, d)
        else:
            if item.endswith('.py'):
                # Compile to .pyc
                d_pyc = d + 'c' # .py -> .pyc
                print(f"  Compiling {item} -> {item}c")
                try:
                    py_compile.compile(s, cfile=d_pyc, doraise=True)
                except Exception as e:
                    print(f"  ERROR compiling {item}: {e}")
            else:
                # Copy other files directly
                print(f"  Copying {item}")
                shutil.copy2(s, d)

def process_root_files():
    print("Processing root files...")
    # Compile root python files
    for f in ROOT_FILES_TO_COMPILE:
        if os.path.exists(f):
            print(f"  Compiling root: {f}")
            d_pyc = os.path.join(BUILD_DIR, f + 'c')
            py_compile.compile(f, cfile=d_pyc, doraise=True)
            
    # Copy other root files
    for f in ROOT_FILES_TO_COPY:
        if os.path.exists(f):
            print(f"  Copying root: {f}")
            shutil.copy2(f, os.path.join(BUILD_DIR, f))

def main():
    print("=== Starting Bytecode Compilation ===")
    
    clean_build_dir()
    
    # Process folders
    for folder in SOURCE_DIRS:
        if os.path.exists(folder):
            compile_and_copy(folder, os.path.join(BUILD_DIR, folder))
        else:
            print(f"WARNING: Source folder not found: {folder}")
            
    process_root_files()
    
    print("\n=== Compilation Complete ===")
    print(f"Build ready in: {os.path.abspath(BUILD_DIR)}")
    print("You can now configure electron-builder to use this directory.")

if __name__ == '__main__':
    main()
