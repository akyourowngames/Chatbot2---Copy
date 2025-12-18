import PyInstaller.__main__
import os
import shutil
import sys

# Configuration
EXE_NAME = "KAI_OS"
ENTRY_POINT = "launcher.py"
ICON_FILE = "app_icon.ico"

def build():
    print(f"Building {EXE_NAME} Desktop Executable...")
    
    # 1. Clean previous build
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            # Use a more robust delete for Windows
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: Could not delete {folder}: {e}")

    # 2. Define data folders and files to include
    # (source, destination)
    # destination '.' means the root of the app folder
    data_items = [
        ('Backend', 'Backend'),
        ('Frontend', 'Frontend'),
        ('Data', 'Data'),
        ('Config', 'Config'),
        ('docs', 'docs'),
        ('.env', '.'),
        ('Requirements.txt', '.'),
        ('app_icon.ico', '.'),
        ('Hello-Kai_en_windows_v4_0_0.ppn', '.'),  # Wake word file
    ]

    # Handle models separately (might skip if too huge for some builds)
    if os.path.exists('models'):
        print("Including 'models' folder (this will increase size significantly)...")
        data_items.append(('models', 'models'))

    # Build add-data arguments
    add_data_args = []
    sep = ';' if sys.platform == 'win32' else ':'
    for src, dst in data_items:
        if os.path.exists(src):
            add_data_args.extend(['--add-data', f'{src}{sep}{dst}'])
        else:
            print(f"Warning: {src} not found, skipping.")

    # 3. Define hidden imports
    # Many AI libraries and background utilities aren't auto-detected
    hidden_imports = [
        'PyQt5.sip',
        'google-generativeai',
        'groq',
        'openai',
        'cohere',
        'firebase_admin',
        'cryptography',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'speech_recognition',
        'pvporcupine',
        'pyaudio',
        'flask_cors',
        'bcrypt',
        'pydantic',
        'jose',
        'websockets',
        'psutil',
        'requests',
        'dotenv',
    ]

    # 4. Run PyInstaller
    args = [
        ENTRY_POINT,
        f'--name={EXE_NAME}',
        '--onedir',                # Use directory for speed (better for 2GB+ models)
        '--windowed',              # No console window for the final app
        '--clean',
        '--noconfirm',
    ]

    if os.path.exists(ICON_FILE):
        args.append(f'--icon={ICON_FILE}')

    for item in add_data_args:
        args.append(item)

    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])

    # Run PyInstaller
    print("\nRunning PyInstaller...")
    PyInstaller.__main__.run(args)

    print("\n========================================")
    print(f"   Build Complete: {EXE_NAME}")
    print(f"   Location: dist/{EXE_NAME}")
    print("========================================")
    
    # 5. Create a simple launcher shortcut in the dist folder
    create_shortcut_helper()

def create_shortcut_helper():
    """Create a helper batch file at the root of dist for easy launching"""
    try:
        dist_root = os.path.join('dist', EXE_NAME)
        if os.path.exists(dist_root):
            with open(os.path.join(dist_root, '..', f'Start_{EXE_NAME}.bat'), 'w') as f:
                f.write(f'@echo off\ncd "{EXE_NAME}"\nstart "" "{EXE_NAME}.exe"\n')
            print(f"Created 'Start_{EXE_NAME}.bat' in dist folder.")
    except Exception as e:
        print(f"Note: Could not create helper batch: {e}")

if __name__ == "__main__":
    build()
