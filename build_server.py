import PyInstaller.__main__
import os
import shutil

# Clean previous build
if os.path.exists('dist/api_server'):
    shutil.rmtree('dist/api_server')

print("Starting build of api_server.py...")

PyInstaller.__main__.run([
    'api_server.py',
    '--name=api_server',
    '--onedir',  # Directory based build (faster startup than onefile)
    '--noconsole',  # Hide console window
    '--clean',
    # Hidden imports for libraries that PyInstaller might miss
    '--hidden-import=flask',
    '--hidden-import=flask_cors',
    '--hidden-import=engineio.async_drivers.threading',
    '--hidden-import=socketio',
    '--hidden-import=dns', 
    '--hidden-import=dns.resolver',
    # Data directories to include
    '--add-data=Backend;Backend',
    '--add-data=Data;Data', 
    '--add-data=Config;Config',
    '--add-data=models;models',
    '--add-data=Requirements.txt;.',
    '--add-data=.env;.',
    # Exclude unnecessary modules to save space (optional)
    '--exclude-module=tkinter',
    '--exclude-module=matplotlib',
    '--exclude-module=PyQt5', # We don't need GUI lib for the server
])

print("Build complete. Output in dist/api_server")
