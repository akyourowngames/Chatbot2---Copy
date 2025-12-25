// KAI Extension - Popup Script

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle-widget');
    const analyzeBtn = document.getElementById('analyze-page');
    const fillBtn = document.getElementById('fill-form');
    const statusEl = document.getElementById('status');

    // Toggle widget
    toggleBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        chrome.tabs.sendMessage(tab.id, { action: 'toggleWidget' }, (response) => {
            if (chrome.runtime.lastError) {
                statusEl.textContent = 'Please refresh the page first';
            } else {
                window.close();
            }
        });
    });

    // Analyze page (triggers widget to open and analyze)
    analyzeBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        chrome.tabs.sendMessage(tab.id, { action: 'toggleWidget' });
        // Widget will be visible, user can click analyze button
        window.close();
    });

    // Fill form
    fillBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        chrome.tabs.sendMessage(tab.id, { action: 'toggleWidget' });
        window.close();
    });
});
