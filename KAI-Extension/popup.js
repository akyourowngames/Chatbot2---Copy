// KAI Extension Popup Script

document.addEventListener('DOMContentLoaded', async () => {
    await checkProfile();

    document.getElementById('sync-btn').addEventListener('click', syncFromKAI);
    document.getElementById('test-fill').addEventListener('click', testFill);
    document.getElementById('toggle-manual').addEventListener('click', toggleManualForm);
    document.getElementById('save-manual').addEventListener('click', saveManualProfile);
});

async function checkProfile() {
    const statusEl = document.getElementById('profile-status');

    try {
        // Check chrome.storage for profile
        const result = await chrome.storage.local.get(['firebaseUser', 'userProfile']);

        if (result.firebaseUser && result.firebaseUser.email) {
            statusEl.textContent = `✅ Logged in as ${result.firebaseUser.email}`;
            statusEl.className = 'status-value success';

            if (result.userProfile && result.userProfile.name) {
                statusEl.textContent = `✅ ${result.userProfile.name} (${result.firebaseUser.email})`;
            }
        } else {
            statusEl.textContent = '❌ No profile found';
            statusEl.className = 'status-value error';
        }
    } catch (error) {
        statusEl.textContent = '⚠️ Error checking profile';
        statusEl.className = 'status-value error';
    }
}

async function syncFromKAI() {
    const statusEl = document.getElementById('profile-status');
    const btn = document.getElementById('sync-btn');

    btn.textContent = '🔄 Syncing...';
    btn.disabled = true;

    try {
        // Query the KAI localhost tab
        const tabs = await chrome.tabs.query({});
        const kaiTab = tabs.find(t => t.url && t.url.includes('localhost'));

        if (!kaiTab) {
            statusEl.textContent = '❌ KAI app not open';
            statusEl.className = 'status-value error';
            btn.textContent = '🔄 Sync from KAI App';
            btn.disabled = false;
            return;
        }

        // Execute script in KAI tab to get auth
        const results = await chrome.scripting.executeScript({
            target: { tabId: kaiTab.id },
            func: () => {
                try {
                    // Check kai_extension_auth
                    const kaiAuth = localStorage.getItem('kai_extension_auth');
                    if (kaiAuth) {
                        return JSON.parse(kaiAuth);
                    }

                    // Fallback: Check Firebase auth
                    const authKeys = Object.keys(localStorage).filter(k => k.startsWith('firebase:authUser:'));
                    if (authKeys.length > 0) {
                        const authData = localStorage.getItem(authKeys[0]);
                        if (authData) {
                            const parsed = JSON.parse(authData);
                            return {
                                uid: parsed.uid,
                                email: parsed.email,
                                displayName: parsed.displayName
                            };
                        }
                    }

                    return null;
                } catch (e) {
                    return null;
                }
            }
        });

        if (results && results[0] && results[0].result) {
            const authData = results[0].result;

            // Save to chrome.storage
            await chrome.storage.local.set({ firebaseUser: authData });

            // Send to background to fetch profile
            const response = await chrome.runtime.sendMessage({
                action: 'getProfile',
                user_id: authData.uid
            });

            if (response && response.success) {
                statusEl.textContent = `✅ Synced: ${response.profile.name || authData.email}`;
                statusEl.className = 'status-value success';
            } else {
                statusEl.textContent = `✅ Synced: ${authData.email} (no profile)`;
                statusEl.className = 'status-value success';
            }
        } else {
            statusEl.textContent = '❌ No auth found in KAI app';
            statusEl.className = 'status-value error';
        }
    } catch (error) {
        console.error('Sync error:', error);
        statusEl.textContent = '❌ Sync failed: ' + error.message;
        statusEl.className = 'status-value error';
    }

    btn.textContent = '🔄 Sync from KAI App';
    btn.disabled = false;
}

async function testFill() {
    const btn = document.getElementById('test-fill');
    btn.textContent = '🧪 Testing...';
    btn.disabled = true;

    try {
        // Get active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        // Send message to content script
        const response = await chrome.tabs.sendMessage(tab.id, { action: 'aiFill' });

        if (response && response.success) {
            alert('✅ ' + response.message);
        } else {
            alert('❌ ' + (response?.error || 'Form fill failed'));
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }

    btn.textContent = '🧪 Test Form Fill';
    btn.disabled = false;
}

function toggleManualForm() {
    const form = document.getElementById('manual-form');
    const btn = document.getElementById('toggle-manual');

    if (form.style.display === 'none' || !form.style.display) {
        form.style.display = 'block';
        btn.textContent = 'Hide manual entry';
    } else {
        form.style.display = 'none';
        btn.textContent = 'Or enter profile manually';
    }
}

async function saveManualProfile() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();

    if (!name || !email) {
        alert('Please enter at least your name and email');
        return;
    }

    const nameParts = name.split(' ');
    const profile = {
        name,
        firstName: nameParts[0] || '',
        lastName: nameParts.slice(1).join(' ') || '',
        email,
        phone,
        address: '',
        city: '',
        state: '',
        zip: '',
        country: ''
    };

    const fakeAuth = {
        uid: 'manual_' + Date.now(),
        email,
        displayName: name
    };

    await chrome.storage.local.set({
        firebaseUser: fakeAuth,
        userProfile: profile
    });

    alert('✅ Profile saved! You can now use AI Fill on any form.');

    await checkProfile();
    document.getElementById('manual-form').style.display = 'none';
    document.getElementById('toggle-manual').textContent = 'Or enter profile manually';
}
