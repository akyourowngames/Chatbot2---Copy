/* ═══════════════════════════════════════════════════════════════
   KAI Beast Mode Enhancements
   Login System, Enhanced Music Player, Command Disambiguation
   ═══════════════════════════════════════════════════════════════ */

// ========== LOGIN SYSTEM INTEGRATION ==========

// Render auth button based on authentication state
function renderAuthButton() {
    const container = document.getElementById('authButtonContainer');
    if (!container) {
        console.warn('[Auth] authButtonContainer not found');
        return;
    }

    if (window.authClient && window.authClient.isAuthenticated()) {
        // Show user profile
        const email = localStorage.getItem('userEmail') || 'User';
        const initial = email.charAt(0).toUpperCase();

        container.innerHTML = `
            <div class="user-profile-dropdown">
                <button onclick="toggleUserDropdown()" class="user-profile-btn">
                    <div class="user-avatar">${initial}</div>
                    <span class="text-sm text-gray-200 hidden md:inline">${email.split('@')[0]}</span>
                    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                </button>
                
                <!-- Dropdown menu -->
                <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-gray-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                    <button onclick="handleLogout()" class="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-300 hover:bg-white/5 hover:text-white transition-colors">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                        </svg>
                        Logout
                    </button>
                </div>
            </div>
        `;
    } else {
        // Show login button
        container.innerHTML = `
            <button onclick="openAuthModal()" class="auth-button">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path>
                </svg>
                <span>Login</span>
            </button>
        `;
    }
}

// Toggle user dropdown menu
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdownMenu');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('userDropdownMenu');
    const profileBtn = document.querySelector('.user-profile-btn');

    if (dropdown && !dropdown.classList.contains('hidden') &&
        !dropdown.contains(e.target) && !profileBtn?.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// Open authentication modal
function openAuthModal() {
    alert('🔐 Authentication\n\nLogin features are ready for integration!\n\nTo enable login:\n1. Configure Firebase Authentication\n2. Update auth-client.js\n3. Deploy backend auth endpoints\n\nFor now, the app works without login.');
}

// Handle logout
async function handleLogout() {
    if (!confirm('Are you sure you want to logout?')) return;

    if (window.authClient && window.authClient.logout) {
        await window.authClient.logout();
    }

    // Clear local storage
    localStorage.removeItem('userEmail');
    localStorage.removeItem('authToken');

    // Update UI
    renderAuthButton();
    newChat(); // Clear current chat

    console.log('[Auth] Logged out successfully');
}

// Initialize auth button on page load
document.addEventListener('DOMContentLoaded', () => {
    renderAuthButton();

    // Re-render on auth state changes
    setInterval(() => {
        if (window.authStateChanged) {
            window.authStateChanged = false;
            renderAuthButton();
        }
    }, 1000);
});

// ========== COMMAND DISAMBIGUATION SYSTEM ==========

// Detect command intent to prevent confusion between music/stream
function detectCommandIntent(message) {
    const msg = message.toLowerCase().trim();

    // Music-specific keywords
    const musicKeywords = ['song', 'music', 'track', 'lofi', 'beats', 'spotify', 'album', 'artist', 'playlist'];

    // Stream-specific keywords  
    const streamKeywords = ['radio', 'station', 'stream', 'live', 'broadcast', 'tv', 'channel', 'news'];

    // Video keywords
    const videoKeywords = ['video', 'watch', 'youtube', 'clip', 'movie', 'show'];

    if (msg.startsWith('play ')) {
        const query = msg.substring(5).trim();

        // Check for stream intent
        if (streamKeywords.some(kw => query.includes(kw))) {
            return { type: 'stream', query: message, original: query };
        }

        // Check for video intent
        if (videoKeywords.some(kw => query.includes(kw))) {
            return { type: 'video', query: message, original: query };
        }

        // Check for music intent (default for "play")
        if (musicKeywords.some(kw => query.includes(kw)) || query.length > 0) {
            return { type: 'music', query: message, original: query };
        }
    }

    // Check other command patterns
    if (msg.includes('music') || msg.includes('song')) {
        return { type: 'music', query: message, original: msg };
    }

    if (msg.includes('stream') || msg.includes('radio') || msg.includes('live')) {
        return { type: 'stream', query: message, original: msg };
    }

    return { type: 'general', query: message, original: msg };
}

// Show command disambiguator UI
function showCommandDisambiguator(query) {
    const container = document.getElementById('commandDisambiguatorContainer');
    if (!container) {
        console.warn('[Disambiguator] Container not found');
        return;
    }

    container.innerHTML = `
        <div class="command-disambiguator">
            <div class="disambig-title">What would you like to play?</div>
            <div class="disambig-options">
                <button onclick="disambiguateCommand('${query}', 'music')" class="disambig-option">
                    🎵 Music (YouTube/Spotify)
                </button>
                <button onclick="disambiguateCommand('${query}', 'stream')" class="disambig-option">
                    📻 Radio/Live Stream
                </button>
                <button onclick="disambiguateCommand('${query}', 'video')" class="disambig-option">
                    📺 Video (YouTube)
                </button>
            </div>
        </div>
    `;

    container.style.display = 'block';
}

// Handle disambiguation choice
function disambiguateCommand(query, type) {
    const container = document.getElementById('commandDisambiguatorContainer');
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }

    // Modify query with type hint
    let modifiedQuery = query;

    if (type === 'music') {
        modifiedQuery = `play music ${query}`;
    } else if (type === 'stream') {
        modifiedQuery = `play radio ${query}`;
    } else if (type === 'video') {
        modifiedQuery = `watch video ${query}`;
    }

    document.getElementById('messageInput').value = modifiedQuery;
    sendMessage();
}

// ========== ENHANCED MUSIC PLAYER ==========

let currentMusicData = null;
let isPlaying = false;

// Create enhanced music player with waveform visualizer
function createEnhancedMusicPlayer(musicData) {
    currentMusicData = musicData;

    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'w-full animate-slide-up mt-4';

    const innerDiv = document.createElement('div');
    innerDiv.className = 'max-w-3xl mx-auto flex gap-4 md:gap-6 flex-row';

    const spacer = document.createElement('div');
    spacer.className = 'w-9 h-9 flex-shrink-0';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'flex-1';

    const youtubeWatchUrl = `https://www.youtube.com/watch?v=${musicData.video_id}`;

    contentDiv.innerHTML = `
        <div class="music-player-enhanced">
            <!-- Header -->
            <div class="p-4 flex items-center gap-3 border-b border-white/10">
                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                    </svg>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-semibold text-white truncate">🎵 Now Playing</div>
                    <div class="text-xs text-gray-400">Beast Mode Music</div>
                </div>
                <a href="${youtubeWatchUrl}" target="_blank" 
                   class="p-2 text-gray-400 hover:text-white transition-colors" title="Open in YouTube">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                    </svg>
                </a>
            </div>
            
            <!-- Waveform Visualizer -->
            <div class="waveform-visualizer">
                <div class="waveform-bar"></div>
                <div class="waveform-bar"></div>
                <div class="waveform-bar"></div>
                <div class="waveform-bar"></div>
                <div class="waveform-bar"></div>
                <div class="waveform-bar"></div>
                <div class="waveform-bar"></div>
            </div>
            
            <!-- Video Player -->
            <div class="aspect-video">
                <iframe 
                    id="musicIframe_${musicData.video_id}"
                    src="${musicData.embed_url}?autoplay=1&enablejsapi=1" 
                    class="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            </div>
            
            <!-- Controls -->
            <div class="music-controls">
                <button onclick="togglePlay()" class="music-control-btn play">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                    </svg>
                </button>
                
                <div class="flex-1 flex items-center gap-2">
                    <svg class="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
                    </svg>
                    <div class="volume-slider" onclick="handleVolumeClick(event)">
                        <div class="volume-slider-fill" style="width: 70%"></div>
                    </div>
                </div>
                
                <button onclick="showNowPlayingBar('${musicData.video_id}')" class="music-control-btn" title="Mini Player">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                </button>
            </div>
        </div>
    `;

    innerDiv.appendChild(spacer);
    innerDiv.appendChild(contentDiv);
    messageDiv.appendChild(innerDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTo({ top: messagesDiv.scrollHeight, behavior: 'smooth' });

    isPlaying = true;
}

// Toggle play/pause
function togglePlay() {
    isPlaying = !isPlaying;
    // Update button icon
    const playBtns = document.querySelectorAll('.music-control-btn.play svg');
    playBtns.forEach(btn => {
        if (isPlaying) {
            btn.innerHTML = '<path d="M8 5v14l11-7z"/>';
        } else {
            btn.innerHTML = '<path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>';
        }
    });
}

// Handle volume slider click
function handleVolumeClick(event) {
    const slider = event.currentTarget;
    const rect = slider.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const percentage = (x / rect.width) * 100;

    const fill = slider.querySelector('.volume-slider-fill');
    if (fill) {
        fill.style.width = `${percentage}%`;
    }
}

// Show persistent now playing bar
function showNowPlayingBar(videoId) {
    let nowPlayingBar = document.getElementById('nowPlayingBar');

    if (!nowPlayingBar) {
        nowPlayingBar = document.createElement('div');
        nowPlayingBar.id = 'nowPlayingBar';
        nowPlayingBar.className = 'now-playing-bar';
        document.body.appendChild(nowPlayingBar);
    }

    if (currentMusicData) {
        nowPlayingBar.innerHTML = `
            <img src="${currentMusicData.thumbnail}" alt="Album art" class="now-playing-thumbnail">
            <div class="now-playing-info">
                <div class="now-playing-title">Now Playing</div>
                <div class="now-playing-artist">YouTube Music</div>
            </div>
            <button onclick="togglePlay()" class="music-control-btn">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="${isPlaying ? 'M6 4h4v16H6V4zm8 0h4v16h-4V4z' : 'M8 5v14l11-7z'}"/>
                </svg>
            </button>
            <button onclick="hideNowPlayingBar()" class="music-control-btn">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        `;

        nowPlayingBar.classList.add('active');
    }
}

// Hide now playing bar
function hideNowPlayingBar() {
    const nowPlayingBar = document.getElementById('nowPlayingBar');
    if (nowPlayingBar) {
        nowPlayingBar.classList.remove('active');
    }
}

// ========== INITIALIZATION ==========

console.log('🔥 KAI Beast Mode Enhancements Loaded!');

// Export functions to global scope
window.renderAuthButton = renderAuthButton;
window.openAuthModal = openAuthModal;
window.handleLogout = handleLogout;
window.toggleUserDropdown = toggleUserDropdown;
window.detectCommandIntent = detectCommandIntent;
window.showCommandDisambiguator = showCommandDisambiguator;
window.disambiguateCommand = disambiguateCommand;
window.createEnhancedMusicPlayer = createEnhancedMusicPlayer;
window.togglePlay = togglePlay;
window.showNowPlayingBar = showNowPlayingBar;
window.hideNowPlayingBar = hideNowPlayingBar;
window.handleVolumeClick = handleVolumeClick;
