// KAI Extension - Background Service Worker
// Simplified without Firebase SDK (CSP restrictions)

console.log('[KAI Extension] Service worker initialized');

chrome.runtime.onInstalled.addListener(() => {
    console.log('[KAI Extension] Installed successfully');
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'ping') {
        sendResponse({ status: 'pong' });
    }

    if (request.action === 'saveAuth') {
        // Content script (on localhost) sends auth data to be stored globally
        chrome.storage.local.set({
            firebaseUser: request.user
        });
        console.log('[KAI Extension] Auth saved:', request.user.email);
        sendResponse({ success: true });
    }

    if (request.action === 'getUser') {
        // Get stored user from chrome.storage
        chrome.storage.local.get(['firebaseUser'], (result) => {
            sendResponse({ user: result.firebaseUser || null });
        });
        return true; // Keep channel open for async response
    }

    return true;
});
