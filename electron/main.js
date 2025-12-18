const { app, BrowserWindow, ipcMain, Menu, Tray, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let apiServerProcess;
let tray;

// API Server management
function startAPIServer() {
    console.log('Starting API server...');

    // Get the correct working directory
    // In development: project root
    // In production: resources path/backend (where we unpacked the compiled code)
    const isDev = !app.isPackaged;
    const workingDir = isDev ? process.cwd() : path.join(process.resourcesPath, 'backend');

    console.log('Working directory:', workingDir);
    console.log('Is development:', isDev);

    // Start Python API server
    // In production, we run the compiled bytecode .pyc file
    const serverScript = 'api_server.pyc';

    // Ensure we are pointing to the correct file
    const scriptPath = isDev ? 'api_server.py' : serverScript;
    const spawnArgs = [scriptPath];

    console.log(`Spawning python at ${path.join(workingDir, scriptPath)}`);

    apiServerProcess = spawn('python', spawnArgs, {
        cwd: workingDir,
        shell: true // Important for Windows
    });

    apiServerProcess.stdout.on('data', (data) => {
        console.log(`API Server: ${data}`);
    });

    apiServerProcess.stderr.on('data', (data) => {
        console.error(`API Server Error: ${data}`);
    });

    apiServerProcess.on('error', (error) => {
        console.error('Failed to start API server:', error);
    });

    apiServerProcess.on('close', (code) => {
        console.log(`API Server exited with code ${code}`);
    });

    // Wait for server to start
    return new Promise((resolve) => {
        console.log('Waiting for API server to start...');
        setTimeout(() => {
            console.log('API server should be ready now');
            resolve();
        }, 3000); // Increased to 3 seconds
    });
}

function stopAPIServer() {
    if (apiServerProcess) {
        console.log('Stopping API server...');
        apiServerProcess.kill();
        apiServerProcess = null;
    }
}

// Create main window
async function createWindow() {
    // Start API server first
    await startAPIServer();

    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 700,
        backgroundColor: '#0a0e27',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: false,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../app_icon.ico'),
        frame: true,
        titleBarStyle: 'default',
        show: false
    });

    // Load dashboard
    mainWindow.loadFile('Frontend/dashboard.html');

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Handle window close
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Open external links in browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Create menu
    createMenu();

    // Create tray icon
    createTray();
}

// Create application menu
function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Dashboard',
                    click: () => {
                        if (mainWindow) {
                            mainWindow.loadFile('Frontend/dashboard.html');
                        }
                    }
                },
                {
                    label: 'Chat',
                    click: () => {
                        if (mainWindow) {
                            mainWindow.loadFile('Frontend/chat.html');
                        }
                    }
                },
                { type: 'separator' },
                {
                    label: 'Exit',
                    click: () => {
                        app.isQuitting = true;
                        app.quit();
                    }
                }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: () => {
                        shell.openExternal('https://github.com/yourusername/jarvis-ai');
                    }
                },
                {
                    label: 'About',
                    click: () => {
                        const { dialog } = require('electron');
                        dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'About JARVIS AI',
                            message: 'JARVIS AI v7.0',
                            detail: 'Premium AI Desktop Assistant\n\nFeatures:\n• PC Automation\n• Gesture Control\n• Workflows\n• Live Data\n• And much more!\n\n© 2025 Your Company'
                        });
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// Create system tray
function createTray() {
    try {
        tray = new Tray(path.join(__dirname, '../app_icon.ico'));

        const contextMenu = Menu.buildFromTemplate([
            {
                label: 'Show JARVIS',
                click: () => {
                    if (mainWindow) {
                        mainWindow.show();
                    }
                }
            },
            {
                label: 'Dashboard',
                click: () => {
                    if (mainWindow) {
                        mainWindow.show();
                        mainWindow.loadFile('Frontend/dashboard.html');
                    }
                }
            },
            {
                label: 'Chat',
                click: () => {
                    if (mainWindow) {
                        mainWindow.show();
                        mainWindow.loadFile('Frontend/chat.html');
                    }
                }
            },
            { type: 'separator' },
            {
                label: 'Quit',
                click: () => {
                    app.isQuitting = true;
                    app.quit();
                }
            }
        ]);

        tray.setToolTip('JARVIS AI');
        tray.setContextMenu(contextMenu);

        tray.on('click', () => {
            if (mainWindow) {
                mainWindow.show();
            }
        });
    } catch (error) {
        console.error("Failed to create tray:", error);
    }
}

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('before-quit', () => {
    app.isQuitting = true;
    stopAPIServer();
});

app.on('will-quit', () => {
    stopAPIServer();
});

// IPC handlers
ipcMain.handle('get-app-version', () => {
    return app.getVersion();
});

ipcMain.handle('get-app-path', () => {
    return app.getAppPath();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (error) => {
    console.error('Unhandled Rejection:', error);
});
