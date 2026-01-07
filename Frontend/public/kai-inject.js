/**
 * KAI Inject - Browser Automation Bookmarklet
 * ============================================
 * Injects KAI floating widget into any webpage for instant automation
 */

(function () {
    'use strict';

    // Prevent multiple injections
    if (window.KAI_INJECTED) {
        console.log('[KAI] Already injected!');
        return;
    }
    window.KAI_INJECTED = true;

    // Use Render production API (localhost for development only)
    const API_URL = 'https://kai-api-nxxv.onrender.com/api/v1';

    // === FLOATING WIDGET ===
    const createWidget = () => {
        const container = document.createElement('div');
        container.id = 'kai-widget';
        container.innerHTML = `
            <style>
                #kai-widget {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }
                
                .kai-orb {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5), 0 0 0 0 rgba(99, 102, 241, 0.7);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 28px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    animation: kaiPulse 2s infinite;
                }
                
                @keyframes kaiPulse {
                    0%, 100% { box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5), 0 0 0 0 rgba(99, 102, 241, 0.7); }
                    50% { box-shadow: 0 4px 30px rgba(99, 102, 241, 0.7), 0 0 0 10px rgba(99, 102, 241, 0); }
                }
                
                .kai-orb:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 30px rgba(99, 102, 241, 0.7);
                }
                
                .kai-orb.active {
                    background: linear-gradient(135deg, #10b981, #059669);
                }
                
                .kai-panel {
                    position: absolute;
                    bottom: 80px;
                    right: 0;
                    width: 350px;
                    max-height: 500px;
                    background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 27, 75, 0.98));
                    border: 1px solid rgba(99, 102, 241, 0.4);
                    border-radius: 16px;
                    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
                    backdrop-filter: blur(20px);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                }
                
                .kai-panel.show {
                    display: flex;
                    animation: slideUp 0.3s ease-out;
                }
                
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .kai-header {
                    padding: 16px;
                    background: rgba(99, 102, 241, 0.1);
                    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                
                .kai-title {
                    font-size: 14px;
                    font-weight: 700;
                    color: #818cf8;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }
                
                .kai-close {
                    background: none;
                    border: none;
                    color: #818cf8;
                    cursor: pointer;
                    font-size: 20px;
                    padding: 0;
                    line-height: 1;
                }
                
                .kai-content {
                    padding: 16px;
                    flex: 1;
                    overflow-y: auto;
                    color: #e0e7ff;
                    font-size: 13px;
                }
                
                .kai-status {
                    padding: 8px 12px;
                    background: rgba(99, 102, 241, 0.1);
                    border-radius: 8px;
                    margin-bottom: 12px;
                    font-size: 11px;
                    color: #a5b4fc;
                }
                
                .kai-input-area {
                    padding: 12px;
                    background: rgba(0, 0, 0, 0.3);
                    border-top: 1px solid rgba(99, 102, 241, 0.2);
                }
                
                .kai-input {
                    width: 100%;
                    padding: 10px;
                    background: rgba(15, 23, 42, 0.6);
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 8px;
                    color: #e0e7ff;
                    font-size: 13px;
                    resize: none;
                    outline: none;
                }
                
                .kai-input:focus {
                    border-color: rgba(99, 102, 241, 0.6);
                }
                
                .kai-actions {
                    display: flex;
                    gap: 8px;
                    margin-top: 8px;
                }
                
                .kai-btn {
                    flex: 1;
                    padding: 8px;
                    background: rgba(99, 102, 241, 0.2);
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 6px;
                    color: #c7d2fe;
                    font-size: 11px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .kai-btn:hover {
                    background: rgba(99, 102, 241, 0.3);
                    border-color: rgba(99, 102, 241, 0.5);
                }
            </style>
            
            <div class="kai-orb" id="kai-orb">
                ⚡
            </div>
            
            <div class="kai-panel" id="kai-panel">
                <div class="kai-header">
                    <span class="kai-title">⚡ KAI Assistant</span>
                    <button class="kai-close" id="kai-close">×</button>
                </div>
                
                <div class="kai-content">
                    <div class="kai-status" id="kai-status">
                        Ready to assist on this page
                    </div>
                    <div id="kai-messages"></div>
                </div>
                
                <div class="kai-input-area">
                    <textarea 
                        class="kai-input" 
                        id="kai-input" 
                        placeholder="Ask KAI to help with this page..."
                        rows="2"
                    ></textarea>
                    <div class="kai-actions">
                        <button class="kai-btn" id="kai-analyze">📊 Analyze Page</button>
                        <button class="kai-btn" id="kai-fill">📝 Fill Form</button>
                        <button class="kai-btn" id="kai-voice">🎤 Voice</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(container);

        // Event listeners
        const orb = document.getElementById('kai-orb');
        const panel = document.getElementById('kai-panel');
        const close = document.getElementById('kai-close');
        const input = document.getElementById('kai-input');

        orb.addEventListener('click', () => {
            panel.classList.toggle('show');
        });

        close.addEventListener('click', () => {
            panel.classList.remove('show');
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleCommand(input.value.trim());
                input.value = '';
            }
        });

        document.getElementById('kai-analyze').addEventListener('click', analyzePage);
        document.getElementById('kai-fill').addEventListener('click', fillForm);
        document.getElementById('kai-voice').addEventListener('click', activateVoice);
    };

    // === PAGE ANALYSIS ===
    const analyzePage = async () => {
        updateStatus('Analyzing page...');
        const orb = document.getElementById('kai-orb');
        orb.classList.add('active');

        const pageData = {
            url: window.location.href,
            title: document.title,
            forms: detectForms(),
            text: document.body.innerText.substring(0, 5000)
        };

        try {
            const response = await fetch(`${API_URL}/automation/analyze-page`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pageData)
            });

            const result = await response.json();
            displayMessage('Page Analysis:', result.analysis);
            updateStatus('Analysis complete');
        } catch (error) {
            console.error('[KAI] Analysis error:', error);
            updateStatus('Error: Could not connect to KAI backend');
        } finally {
            orb.classList.remove('active');
        }
    };

    // === FORM DETECTION ===
    const detectForms = () => {
        const forms = [];
        document.querySelectorAll('form').forEach((form, idx) => {
            const fields = [];
            form.querySelectorAll('input, textarea, select').forEach(field => {
                if (field.type !== 'submit' && field.type !== 'button') {
                    fields.push({
                        name: field.name || field.id || `field_${fields.length}`,
                        type: field.type || field.tagName.toLowerCase(),
                        label: findLabel(field),
                        required: field.required,
                        placeholder: field.placeholder
                    });
                }
            });

            if (fields.length > 0) {
                forms.push({ index: idx, fields });
            }
        });
        return forms;
    };

    const findLabel = (field) => {
        // Try to find associated label
        const label = field.labels?.[0];
        if (label) return label.textContent.trim();

        // Try placeholder
        if (field.placeholder) return field.placeholder;

        // Try nearby text
        const parent = field.parentElement;
        const text = parent?.textContent.trim();
        if (text && text.length < 100) return text;

        return field.name || field.id || 'Unknown';
    };

    // === SMART FORM FILLING ===
    const fillForm = async () => {
        updateStatus('Detecting forms...');
        const forms = detectForms();

        if (forms.length === 0) {
            updateStatus('No forms found on this page');
            return;
        }

        updateStatus(`Found ${forms.length} form(s). Filling intelligently...`);
        const orb = document.getElementById('kai-orb');
        orb.classList.add('active');

        try {
            const response = await fetch(`${API_URL}/automation/fill-form-smart`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: window.location.href,
                    forms: forms
                })
            });

            const result = await response.json();

            if (result.success) {
                // Apply the field mappings
                if (result.mappings) {
                    applyFormMappings(result.mappings);
                    updateStatus(`Filled ${Object.keys(result.mappings).length} fields!`);
                    displayMessage('Form Filled:', 'Successfully filled form with your data');
                }
            }
        } catch (error) {
            console.error('[KAI] Fill error:', error);
            updateStatus('Error: Could not connect to KAI backend');
        } finally {
            orb.classList.remove('active');
        }
    };

    const applyFormMappings = (mappings) => {
        Object.entries(mappings).forEach(([selector, value]) => {
            const field = document.querySelector(selector);
            if (field) {
                field.value = value;
                field.dispatchEvent(new Event('input', { bubbles: true }));
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    };

    // === VOICE ACTIVATION ===
    const activateVoice = () => {
        updateStatus('Voice mode coming soon...');
        // TODO: Integrate with existing voice system
    };

    // === COMMAND HANDLER ===
    const handleCommand = async (command) => {
        displayMessage('You:', command);
        updateStatus('Processing...');

        const cmd = command.toLowerCase();

        if (cmd.includes('fill') || cmd.includes('form')) {
            await fillForm();
        } else if (cmd.includes('analyze') || cmd.includes('what')) {
            await analyzePage();
        } else {
            // Send to KAI for general query
            displayMessage('KAI:', 'I can help you analyze pages or fill forms. Try "analyze page" or "fill form"');
            updateStatus('Ready');
        }
    };

    // === UI HELPERS ===
    const updateStatus = (message) => {
        const status = document.getElementById('kai-status');
        if (status) status.textContent = message;
    };

    const displayMessage = (sender, content) => {
        const messages = document.getElementById('kai-messages');
        const msg = document.createElement('div');
        msg.style.cssText = `
            margin-bottom: 12px;
            padding: 8px;
            background: rgba(99, 102, 241, 0.05);
            border-radius: 6px;
            font-size: 12px;
        `;
        msg.innerHTML = `<strong style="color: #818cf8;">${sender}</strong><br>${content}`;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    };

    // === INITIALIZE ===
    console.log('[KAI] Injecting widget...');
    createWidget();
    console.log('[KAI] Widget injected! Click the orb to open.');

    // Auto-analyze on load
    setTimeout(() => {
        const forms = detectForms();
        if (forms.length > 0) {
            updateStatus(`Found ${forms.length} form(s) on this page`);
        }
    }, 1000);

})();
