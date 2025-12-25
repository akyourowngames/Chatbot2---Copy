/**
 * KAI Extension - Content Script (GOOGLE FORMS EDITION)
 * Injects floating widget and ACTUALLY fills forms!
 */

const API_URL = 'http://localhost:5000/api/v1';

// User data - will be fetched from backend
let USER_DATA = {
    name: 'John Doe',
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@example.com',
    phone: '+1234567890',
    address: '123 Main Street',
    city: 'San Francisco',
    state: 'CA',
    zip: '94102',
    message: 'This is an automated test message from KAI.'
};

// Fetch user profile from Firebase-authenticated user
async function loadUserProfile() {
    try {
        let firebaseUser = null;

        // STRATEGY: If on localhost, read from localStorage and save to chrome.storage
        // If on other domains, read from chrome.storage

        if (window.location.hostname === 'localhost') {
            // On localhost - can read Firebase auth from localStorage
            try {
                const authKeys = Object.keys(localStorage).filter(k => k.startsWith('firebase:authUser:'));
                if (authKeys.length > 0) {
                    const authData = localStorage.getItem(authKeys[0]);
                    if (authData) {
                        const parsed = JSON.parse(authData);
                        firebaseUser = {
                            uid: parsed.uid,
                            email: parsed.email,
                            displayName: parsed.displayName
                        };
                        console.log('[KAI] ✅ Found Firebase auth in localStorage:', firebaseUser.email);

                        // Save to chrome.storage for other domains to use
                        chrome.runtime.sendMessage({
                            action: 'saveAuth',
                            user: firebaseUser
                        });
                    }
                }
            } catch (e) {
                console.log('[KAI] Could not check localStorage auth:', e);
            }
        }

        // Fallback: Get from chrome.storage (works on all domains)
        if (!firebaseUser) {
            const result = await new Promise(resolve => {
                chrome.storage.local.get(['firebaseUser'], resolve);
            });
            firebaseUser = result.firebaseUser;
            if (firebaseUser) {
                console.log('[KAI] ✅ Found auth in chrome.storage:', firebaseUser.email);
            }
        }

        if (firebaseUser) {
            const user_id = firebaseUser.uid;

            console.log('[KAI] Fetching profile for user:', firebaseUser.email);

            try {
                // Fetch from backend
                const response = await fetch(`${API_URL}/users/profile?user_id=${user_id}&t=${Date.now()}`);
                const data = await response.json();

                console.log('[KAI] API Response:', data);

                if (data.success && data.profile && data.profile.name) {
                    USER_DATA = {
                        ...data.profile,
                        message: 'This is an automated message from KAI.'
                    };
                    console.log('[KAI] ✅ Loaded profile:', USER_DATA.name, USER_DATA.email);

                    // Cache
                    chrome.storage.local.set({ userProfile: USER_DATA });
                    return;
                } else {
                    console.log('[KAI] ⚠️ No profile data in response, using fallback');
                }
            } catch (error) {
                console.log('[KAI] Backend error:', error);
            }

            // Fallback to Firebase user data
            USER_DATA = {
                name: firebaseUser.displayName || 'User',
                firstName: (firebaseUser.displayName || 'User').split(' ')[0],
                lastName: (firebaseUser.displayName || '').split(' ')[1] || '',
                email: firebaseUser.email,
                phone: '',
                address: '',
                city: '',
                state: '',
                zip: '',
                message: 'This is an automated message from KAI.'
            };
            console.log('[KAI] Using Firebase auth data as fallback');
        } else {
            console.log('[KAI] ⚠️ No user logged in');

            // Try cached profile
            const cached = await new Promise(resolve => {
                chrome.storage.local.get(['userProfile'], resolve);
            });

            if (cached.userProfile) {
                USER_DATA = cached.userProfile;
                console.log('[KAI] Using cached profile');
            }
        }
    } catch (error) {
        console.log('[KAI] Error loading profile:', error);
    }
}

// Listen for user account changes in localStorage
window.addEventListener('storage', (e) => {
    if (e.key === 'kai_user_id' || e.key === 'user_id') {
        console.log('[KAI] User account changed, reloading profile...');
        loadUserProfile();
    }
});


// Create floating widget
function createWidget() {
    if (document.getElementById('kai-widget')) return;

    const widget = document.createElement('div');
    widget.id = 'kai-widget';
    widget.className = 'kai-widget';

    const orb = document.createElement('div');
    orb.className = 'kai-orb';
    orb.textContent = '⚡';

    const panel = document.createElement('div');
    panel.className = 'kai-panel';
    panel.style.display = 'none';

    panel.innerHTML = `
        <div class="kai-header">
            <span>⚡ KAI</span>
            <button class="kai-close">×</button>
        </div>
        <div class="kai-messages" id="kai-msgs"></div>
        <div class="kai-input-area">
            <textarea class="kai-input" id="kai-in" placeholder="Chat..." rows="2"></textarea>
            <div class="kai-buttons">
                <button class="kai-btn" id="kai-chat">💬 Chat</button>
                <button class="kai-btn" id="kai-analyze">📊 Analyze</button>
                <button class="kai-btn" id="kai-fill">📝 Fill Form</button>
                <button class="kai-btn" id="kai-clear">🗑️ Clear</button>
            </div>
        </div>
    `;

    widget.appendChild(orb);
    widget.appendChild(panel);
    document.body.appendChild(widget);

    orb.onclick = () => panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
    panel.querySelector('.kai-close').onclick = () => panel.style.display = 'none';

    setupButtons();
    loadUserProfile(); // Fetch real user data
    addMsg('Ready! 🚀', false);
}

function addMsg(text, isUser) {
    const m = document.createElement('div');
    m.className = 'kai-message';
    m.style.borderLeftColor = isUser ? '#8b5cf6' : '#6366f1';
    m.innerHTML = `<strong style="color:${isUser ? '#a78bfa' : '#818cf8'}">${isUser ? 'You' : 'KAI'}:</strong> ${text}`;
    document.getElementById('kai-msgs').appendChild(m);
    document.getElementById('kai-msgs').scrollTop = 999999;
}

function setupButtons() {
    // Fill Form - ACTUALLY WORKS!
    document.getElementById('kai-fill').onclick = () => {
        addMsg('Scanning for fields...', false);

        // Find ALL text inputs, emails, textareas
        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], input[type="number"], textarea'));

        if (!inputs.length) {
            addMsg('No fields found!', false);
            return;
        }

        addMsg(`Found ${inputs.length} field(s)`, false);
        let filled = 0;

        inputs.forEach((input, i) => {
            // Get label
            let label = '';
            const parent = input.closest('div[role="listitem"]');
            if (parent) {
                const heading = parent.querySelector('[role="heading"]');
                if (heading) label = heading.textContent.toLowerCase();
            }
            if (!label) label = (input.getAttribute('aria-label') || input.placeholder || '').toLowerCase();

            // Match to data
            let value = '';
            if (label.includes('email') || input.type === 'email') value = USER_DATA.email;
            else if (label.includes('phone') || label.includes('tel') || input.type === 'tel') value = USER_DATA.phone;
            else if (label.includes('first') && label.includes('name')) value = USER_DATA.firstName;
            else if (label.includes('last') && label.includes('name')) value = USER_DATA.lastName;
            else if (label.includes('name')) value = USER_DATA.name;
            else if (label.includes('address')) value = USER_DATA.address;
            else if (label.includes('city')) value = USER_DATA.city;
            else if (label.includes('state')) value = USER_DATA.state;
            else if (label.includes('zip') || label.includes('postal')) value = USER_DATA.zip;
            else if (label.includes('message') || label.includes('comment')) value = USER_DATA.message;
            else value = i === 0 ? USER_DATA.name : USER_DATA.email; // Default

            if (value) {
                input.value = value;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.focus();
                input.blur();
                filled++;
            }
        });

        if (filled > 0) {
            addMsg(`✅ Filled ${filled} field(s)!`, false);
        } else {
            addMsg('Could not fill fields', false);
        }
    };

    // Chat
    document.getElementById('kai-chat').onclick = async () => {
        const msg = document.getElementById('kai-in').value.trim();
        if (!msg) return;
        addMsg(msg, true);
        document.getElementById('kai-in').value = '';
        try {
            const r = await fetch(API_URL + '/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: msg, user_id: 'ext' })
            });
            const d = await r.json();
            addMsg(d.response || d.text || 'Got it!', false);
        } catch (e) {
            addMsg('Error: ' + e.message, false);
        }
    };

    //Analyze
    document.getElementById('kai-analyze').onclick = async () => {
        addMsg('Analyzing...', false);
        try {
            const r = await fetch(API_URL + '/automation/analyze-page', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: location.href, title: document.title, text: document.body.innerText.substring(0, 500) })
            });
            const d = await r.json();
            addMsg(d.analysis || 'Done!', false);
        } catch (e) {
            addMsg('Error: ' + e.message, false);
        }
    };

    // Clear
    document.getElementById('kai-clear').onclick = () => {
        document.getElementById('kai-msgs').innerHTML = '';
        addMsg('Cleared!', false);
    };

    // Enter to chat
    document.getElementById('kai-in').onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('kai-chat').click();
        }
    };
}

// Init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
} else {
    createWidget();
}

// Listen for popup messages
chrome.runtime.onMessage.addListener((req, sender, sendResp) => {
    if (req.action === 'ping') {
        sendResp({ status: 'ready' });
    } else if (req.action === 'toggleWidget') {
        const p = document.querySelector('.kai-panel');
        if (p) p.style.display = p.style.display === 'flex' ? 'none' : 'flex';
        sendResp({ success: true });
    } else if (req.action === 'fillForm') {
        const p = document.querySelector('.kai-panel');
        if (p) p.style.display = 'flex';
        setTimeout(() => document.getElementById('kai-fill').click(), 100);
        sendResp({ success: true });
    } else if (req.action === 'authChanged') {
        // User logged in/out in Firebase, reload profile
        console.log('[KAI] Auth state changed:', req.user ? req.user.email : 'logged out');
        loadUserProfile();
        sendResp({ success: true });
    }
    return true;
});
