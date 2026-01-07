/**
 * Firebase Authentication Client
 * ================================
 * Handles JWT authentication, token storage, and API calls
 */

class AuthClient {
    constructor(apiBaseUrl = null) {
        // Use Render deployment URL
        if (!apiBaseUrl) {
            // Always use Render for production deployment
            this.apiBaseUrl = 'https://kai-api-nxxv.onrender.com/api/v1';

            // Fallback to localhost only if explicitly on localhost
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                this.apiBaseUrl = 'http://localhost:5000/api/v1';
            }
        } else {
            this.apiBaseUrl = apiBaseUrl;
        }

        console.log('[AUTH] API Base URL:', this.apiBaseUrl);

        this.accessToken = null;
        this.refreshToken = null;
        this.user = null;

        // Load tokens from localStorage
        this.loadTokens();
    }

    // ==================== TOKEN MANAGEMENT ====================

    loadTokens() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                this.user = JSON.parse(userStr);
            } catch (e) {
                console.error('[AUTH] Failed to parse user data:', e);
            }
        }
    }

    saveTokens(accessToken, refreshToken, user) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.user = user;

        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        localStorage.setItem('user', JSON.stringify(user));
    }

    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        this.user = null;

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }

    isAuthenticated() {
        return !!this.accessToken;
    }

    getUser() {
        return this.user;
    }

    // ==================== AUTHENTICATION ====================

    async signup(email, password) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async login(email, password) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.saveTokens(data.access_token, data.refresh_token, data.user);
                return { success: true, user: data.user };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            if (this.accessToken) {
                await fetch(`${this.apiBaseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.accessToken}`
                    }
                });
            }
        } catch (error) {
            console.error('[AUTH] Logout error:', error);
        } finally {
            this.clearTokens();
        }
    }

    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            const data = await response.json();

            if (response.ok) {
                this.accessToken = data.access_token;
                localStorage.setItem('access_token', data.access_token);
                return true;
            } else {
                // Refresh token expired, need to login again
                this.clearTokens();
                return false;
            }
        } catch (error) {
            console.error('[AUTH] Token refresh error:', error);
            return false;
        }
    }

    // ==================== API CALLS WITH AUTH ====================

    async apiCall(endpoint, options = {}) {
        // Add Authorization header
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        try {
            let response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                ...options,
                headers
            });

            // If 401 Unauthorized, try to refresh token
            if (response.status === 401 && this.refreshToken) {
                const refreshed = await this.refreshAccessToken();

                if (refreshed) {
                    // Retry request with new token
                    headers['Authorization'] = `Bearer ${this.accessToken}`;
                    response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                        ...options,
                        headers
                    });
                } else {
                    // Refresh failed, show login modal
                    if (typeof showAuthModal === 'function') {
                        showAuthModal('login');
                    }
                    return null;
                }
            }

            return response;
        } catch (error) {
            console.error('[AUTH] API call error:', error);
            throw error;
        }
    }

    async get(endpoint) {
        const response = await this.apiCall(endpoint, { method: 'GET' });
        return response ? await response.json() : null;
    }

    async post(endpoint, data) {
        const response = await this.apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response ? await response.json() : null;
    }

    async put(endpoint, data) {
        const response = await this.apiCall(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return response ? await response.json() : null;
    }

    async delete(endpoint) {
        const response = await this.apiCall(endpoint, { method: 'DELETE' });
        return response ? await response.json() : null;
    }
}

// ==================== WEBSOCKET CLIENT ====================

class RealtimeSyncClient {
    constructor(authClient, wsUrl = 'ws://localhost:8765') {
        this.authClient = authClient;
        this.wsUrl = wsUrl;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = [];
    }

    connect() {
        if (!this.authClient.isAuthenticated()) {
            console.warn('[REALTIME] Not authenticated, cannot connect to WebSocket');
            return;
        }

        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('[REALTIME] WebSocket connected');
                this.reconnectAttempts = 0;

                // Send authentication token
                this.ws.send(JSON.stringify({
                    token: this.authClient.accessToken
                }));

                // Start ping/pong keep-alive
                this.startKeepAlive();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[REALTIME] Message received:', data);

                    // Call all registered handlers
                    this.messageHandlers.forEach(handler => handler(data));
                } catch (error) {
                    console.error('[REALTIME] Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[REALTIME] WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('[REALTIME] WebSocket disconnected');
                this.stopKeepAlive();
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('[REALTIME] Connection error:', error);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.stopKeepAlive();
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;

            console.log(`[REALTIME] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('[REALTIME] Max reconnect attempts reached');
        }
    }

    startKeepAlive() {
        this.keepAliveInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Ping every 30 seconds
    }

    stopKeepAlive() {
        if (this.keepAliveInterval) {
            clearInterval(this.keepAliveInterval);
            this.keepAliveInterval = null;
        }
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    removeMessageHandler(handler) {
        const index = this.messageHandlers.indexOf(handler);
        if (index > -1) {
            this.messageHandlers.splice(index, 1);
        }
    }
}

// ==================== UI HELPERS ====================

function showAuthModal(mode = 'login') {
    const modalHTML = `
        <div class="auth-modal-overlay" id="auth-modal">
            <!-- Floating Particles -->
            <div class="auth-particles">
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
                <div class="auth-particle"></div>
            </div>

            <!-- Modal Container -->
            <div class="auth-modal">
                <!-- Header -->
                <div class="auth-header">
                    <div class="auth-logo">⚡</div>
                    <h1 class="auth-title" id="auth-title">${mode === 'login' ? 'Welcome Back' : 'Create Account'}</h1>
                    <p class="auth-subtitle">Access your premium AI assistant</p>
                </div>

                <!-- Tab Switcher -->
                <div class="auth-tabs">
                    <button class="auth-tab ${mode === 'login' ? 'active' : ''}" data-tab="login">
                        <span>Login</span>
                    </button>
                    <button class="auth-tab ${mode === 'signup' ? 'active' : ''}" data-tab="signup">
                        <span>Sign Up</span>
                    </button>
                </div>

                <!-- Error Message -->
                <div id="auth-error" class="auth-error" style="display: none;">
                    <span class="auth-error-icon">⚠️</span>
                    <span id="auth-error-text"></span>
                </div>

                <!-- Success Message -->
                <div id="auth-success" class="auth-success" style="display: none;">
                    <span>✅</span>
                    <span id="auth-success-text"></span>
                </div>

                <!-- Form -->
                <form id="auth-form" class="auth-form">
                    <!-- Email Input -->
                    <div class="auth-input-group">
                        <label class="auth-input-label">Email Address</label>
                        <div class="auth-input-wrapper">
                            <input 
                                type="email" 
                                id="auth-email" 
                                class="auth-input" 
                                placeholder="your@email.com"
                                required
                                autocomplete="email"
                            />
                            <div class="auth-input-icon">📧</div>
                        </div>
                    </div>

                    <!-- Password Input -->
                    <div class="auth-input-group">
                        <label class="auth-input-label">Password</label>
                        <div class="auth-input-wrapper">
                            <input 
                                type="password" 
                                id="auth-password" 
                                class="auth-input" 
                                placeholder="••••••••"
                                required
                                autocomplete="current-password"
                            />
                            <div class="auth-input-icon">🔒</div>
                            <button type="button" class="auth-password-toggle" id="password-toggle">
                                👁️
                            </button>
                        </div>
                    </div>

                    <!-- Submit Button -->
                    <button type="submit" class="auth-submit" id="auth-submit">
                        <span id="submit-text">${mode === 'login' ? 'Login to JARVIS' : 'Create Account'}</span>
                    </button>
                </form>

                <!-- Divider -->
                <div class="auth-divider">or continue with</div>

                <!-- Social Login -->
                <div class="auth-social">
                    <button class="auth-social-btn" onclick="alert('Google OAuth coming soon!')">
                        <span>🔵</span>
                        <span>Google</span>
                    </button>
                    <button class="auth-social-btn" onclick="alert('GitHub OAuth coming soon!')">
                        <span>⚫</span>
                        <span>GitHub</span>
                    </button>
                </div>

                <!-- Footer -->
                <div class="auth-footer">
                    <p>By continuing, you agree to our <a href="#">Terms</a> and <a href="#">Privacy Policy</a></p>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existing = document.getElementById('auth-modal');
    if (existing) {
        existing.remove();
    }

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Set up event listeners
    const form = document.getElementById('auth-form');
    const tabs = document.querySelectorAll('.auth-tab');
    const errorDiv = document.getElementById('auth-error');
    const errorText = document.getElementById('auth-error-text');
    const successDiv = document.getElementById('auth-success');
    const successText = document.getElementById('auth-success-text');
    const submitBtn = document.getElementById('auth-submit');
    const submitText = document.getElementById('submit-text');
    const titleEl = document.getElementById('auth-title');
    const passwordToggle = document.getElementById('password-toggle');
    const passwordInput = document.getElementById('auth-password');

    let currentMode = mode;

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const newMode = tab.dataset.tab;
            if (newMode === currentMode) return;

            currentMode = newMode;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update UI
            titleEl.textContent = currentMode === 'login' ? 'Welcome Back' : 'Create Account';
            submitText.textContent = currentMode === 'login' ? 'Login to JARVIS' : 'Create Account';

            // Hide messages
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';
        });
    });

    // Password toggle
    passwordToggle.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        passwordToggle.textContent = type === 'password' ? '👁️' : '🙈';
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;

        // Hide messages
        errorDiv.style.display = 'none';
        successDiv.style.display = 'none';

        // Show loading
        submitBtn.disabled = true;
        submitText.innerHTML = '<span class="auth-loading"></span> Processing...';

        const authClient = window.authClient || new AuthClient();
        let result;

        try {
            if (currentMode === 'login') {
                result = await authClient.login(email, password);
            } else {
                result = await authClient.signup(email, password);

                // If signup successful, show success and auto-login
                if (result.success) {
                    successText.textContent = 'Account created! Logging you in...';
                    successDiv.style.display = 'flex';
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    result = await authClient.login(email, password);
                }
            }

            if (result.success) {
                // Show success
                successText.textContent = 'Success! Redirecting...';
                successDiv.style.display = 'flex';

                // Wait a moment then reload
                setTimeout(() => {
                    document.getElementById('auth-modal').remove();
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error(result.error || 'Authentication failed');
            }
        } catch (error) {
            // Show error
            errorText.textContent = error.message || 'Authentication failed. Please try again.';
            errorDiv.style.display = 'flex';

            // Reset button
            submitBtn.disabled = false;
            submitText.textContent = currentMode === 'login' ? 'Login to JARVIS' : 'Create Account';
        }
    });
}

function hideAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.remove();
    }
}

// ==================== GLOBAL INSTANCES ====================

// Create global auth client
window.authClient = new AuthClient();
window.realtimeClient = new RealtimeSyncClient(window.authClient);

// Define global API_URL for compatibility with other scripts (file-manager.js, etc.)
window.API_URL = window.authClient.apiBaseUrl;
window.API_KEY = 'demo_key_12345'; // Match quick-search.js

// WebSocket disabled for Render free tier (doesn't support WebSockets)
// Uncomment below to enable if using a WebSocket-compatible host
/*
if (window.authClient.isAuthenticated()) {
    window.realtimeClient.connect();
}
*/

console.log('[AUTH] Authentication client initialized');
