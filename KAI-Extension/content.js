/**
 * KAI Extension - Content Script (BEAST MODE v5)
 * ================================================
 * 🎯 Voice Commands | Smart Intent | Full Browser Control
 * 🔥 Macros | Templates | Contextual Memory | Premium UI
 */

console.log('[KAI] ⚡ BEAST MODE v5 ACTIVATED!');

// ==================== STATE ====================

let USER_DATA = null;
let USER_ID = null;
let isListening = false;
let recognition = null;
let commandHistory = [];
let historyIndex = -1;

// Macro Recording State
let isRecording = false;
let recordedActions = [];
let loadedMacros = [];
let loadedTemplates = [];

// Chat History (persistent)
let chatHistory = [];
const SITE_KEY = window.location.hostname.replace(/\./g, '_');

// ==================== PERSISTENCE ====================

async function saveChatState() {
    try {
        await chrome.storage.local.set({
            [`kai_chat_${SITE_KEY}`]: chatHistory.slice(-50), // Keep last 50 messages
            [`kai_recording_${SITE_KEY}`]: { isRecording, recordedActions }
        });
    } catch (e) {
        console.error('[KAI] Failed to save state:', e);
    }
}

async function loadChatState() {
    try {
        const data = await chrome.storage.local.get([`kai_chat_${SITE_KEY}`, `kai_recording_${SITE_KEY}`]);

        // Restore chat history
        chatHistory = data[`kai_chat_${SITE_KEY}`] || [];

        // Restore recording state
        const recordingState = data[`kai_recording_${SITE_KEY}`];
        if (recordingState) {
            isRecording = recordingState.isRecording || false;
            recordedActions = recordingState.recordedActions || [];
            if (isRecording) {
                updateRecordingIndicator(true);
            }
        }

        return chatHistory;
    } catch (e) {
        console.error('[KAI] Failed to load state:', e);
        return [];
    }
}

// ==================== COMMUNICATION ====================

function sendToBackground(message) {
    return new Promise((resolve, reject) => {
        try {
            if (!chrome.runtime?.id) {
                reject(new Error('Extension reloaded - refresh page'));
                return;
            }
            chrome.runtime.sendMessage(message, (response) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    resolve(response || { success: false });
                }
            });
        } catch (error) {
            reject(error);
        }
    });
}

// ==================== PROFILE LOADING ====================

async function loadUserProfile() {
    console.log('[KAI] Loading profile...');
    try {
        const result = await sendToBackground({ action: 'getUser' });
        let firebaseUser = result?.user;

        if (!firebaseUser && window.location.hostname === 'localhost') {
            const kaiAuth = localStorage.getItem('kai_extension_auth');
            if (kaiAuth) {
                firebaseUser = JSON.parse(kaiAuth);
                await sendToBackground({ action: 'saveAuth', user: firebaseUser });
            }
        }

        if (firebaseUser?.uid) {
            USER_ID = firebaseUser.uid; // Set USER_ID for macros/templates

            const profileResult = await sendToBackground({
                action: 'getProfile',
                user_id: firebaseUser.uid
            });

            if (profileResult?.success && profileResult?.profile) {
                const p = profileResult.profile;
                USER_DATA = {
                    name: p.name || firebaseUser.displayName || '',
                    firstName: p.firstName || (p.name || '').split(' ')[0] || '',
                    lastName: p.lastName || (p.name || '').split(' ').slice(1).join(' ') || '',
                    email: p.email || firebaseUser.email || '',
                    phone: p.phone || '',
                    address: p.address || '',
                    city: p.city || '',
                    state: p.state || '',
                    zip: p.zip || '',
                    country: p.country || ''
                };
                console.log('[KAI] ✅ Profile:', USER_DATA.name);

                // Load macros and templates
                await loadMacrosAndTemplates();

                return true;
            }

            USER_DATA = {
                name: firebaseUser.displayName || firebaseUser.email?.split('@')[0] || '',
                firstName: (firebaseUser.displayName || '').split(' ')[0] || '',
                lastName: (firebaseUser.displayName || '').split(' ').slice(1).join(' ') || '',
                email: firebaseUser.email || '',
                phone: '', address: '', city: '', state: '', zip: '', country: ''
            };
            return true;
        }
    } catch (e) {
        console.error('[KAI] Profile error:', e);
    }
    return false;
}

// ==================== VOICE RECOGNITION ====================

function initVoiceRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.log('[KAI] Speech recognition not supported');
        return false;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        updateMicButton(true);
        addMsg('🎤 Listening...', 'info');
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');

        const input = document.getElementById('kai-input');
        if (input) input.value = transcript;

        if (event.results[0].isFinal) {
            processVoiceCommand(transcript);
        }
    };

    recognition.onerror = (event) => {
        console.error('[KAI] Voice error:', event.error);
        isListening = false;
        updateMicButton(false);
        if (event.error !== 'aborted') {
            addMsg(`🎤 Voice error: ${event.error}`, 'error');
        }
    };

    recognition.onend = () => {
        isListening = false;
        updateMicButton(false);
    };

    return true;
}

function toggleVoice() {
    if (!recognition) {
        if (!initVoiceRecognition()) {
            addMsg('❌ Voice not supported in this browser', 'error');
            return;
        }
    }

    if (isListening) {
        recognition.stop();
    } else {
        try {
            recognition.start();
        } catch (e) {
            addMsg('❌ Voice activation failed', 'error');
        }
    }
}

async function processVoiceCommand(transcript) {
    addMsg(`🎤 You: ${transcript}`, 'info');
    document.getElementById('kai-input').value = '';

    const handled = await handleChatCommand(transcript);
    if (!handled) {
        try {
            const result = await sendToBackground({ action: 'chat', query: transcript });
            addMsg(`KAI: ${result.response || result.error}`, result.success ? 'success' : 'error');
            speak(result.response);
        } catch (e) {
            addMsg(`❌ ${e.message}`, 'error');
        }
    }
}

function updateMicButton(active) {
    const btn = document.getElementById('btn-voice');
    if (btn) {
        btn.classList.toggle('listening', active);
        btn.innerHTML = active ? '🔴' : '🎤';
    }
}

// ==================== TEXT-TO-SPEECH ====================

function speak(text, options = {}) {
    if (!('speechSynthesis' in window) || !text) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text.substring(0, 200));
    utterance.rate = options.rate || 1.1;
    utterance.pitch = options.pitch || 1;
    utterance.volume = options.volume || 0.8;

    // Try to get a good voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Alex'));
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
}

// ==================== FIELD DETECTION ====================

function findFormFields() {
    const fields = [];
    const seen = new Set();

    if (location.href.includes('docs.google.com/forms')) {
        document.querySelectorAll('[role="listitem"]').forEach((item) => {
            const heading = item.querySelector('[role="heading"]');
            const input = item.querySelector('input[type="text"], input[type="email"], input[type="tel"], input[type="number"], textarea');
            if (heading && input && !seen.has(input)) {
                seen.add(input);
                fields.push({
                    element: input,
                    label: heading.textContent.trim(),
                    type: input.type || 'text',
                    index: fields.length
                });
            }
        });
        return fields;
    }

    document.querySelectorAll('input, textarea, select').forEach(input => {
        if (['hidden', 'submit', 'button', 'checkbox', 'radio'].includes(input.type)) return;
        if (!isVisible(input) || seen.has(input)) return;
        if (input.closest('#kai-widget')) return;

        seen.add(input);
        fields.push({
            element: input,
            label: findLabel(input),
            type: input.type || 'text',
            name: input.name || '',
            index: fields.length
        });
    });

    return fields;
}

function findLabel(input) {
    if (input.id) {
        const label = document.querySelector(`label[for="${input.id}"]`);
        if (label) return label.textContent.trim();
    }
    if (input.getAttribute('aria-label')) return input.getAttribute('aria-label');
    const parentLabel = input.closest('label');
    if (parentLabel) return parentLabel.textContent.trim();
    const listItem = input.closest('[role="listitem"]');
    if (listItem) {
        const heading = listItem.querySelector('[role="heading"]');
        if (heading) return heading.textContent.trim();
    }
    return input.placeholder || input.name || '';
}

function isVisible(el) {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
}

// ==================== PROFILE MATCHING ====================

function matchFieldToProfile(field, profile) {
    const label = (field.label || '').toLowerCase();
    const name = (field.name || '').toLowerCase();
    const type = (field.type || '').toLowerCase();
    const combined = label + ' ' + name;

    if (type === 'email' || combined.includes('email')) return { key: 'email', value: profile.email };
    if (type === 'tel' || /phone|mobile|cell|telephone/.test(combined)) return { key: 'phone', value: profile.phone };
    if (/first.?name|given.?name/.test(combined)) return { key: 'firstName', value: profile.firstName };
    if (/last.?name|family.?name|surname/.test(combined)) return { key: 'lastName', value: profile.lastName };
    if (/^name$|full.?name|your.?name/.test(combined.replace(/[*:]/g, '').trim())) return { key: 'name', value: profile.name };
    if (/address|street/.test(combined) && !combined.includes('email')) return { key: 'address', value: profile.address };
    if (/city|town/.test(combined)) return { key: 'city', value: profile.city };
    if (/state|province|region/.test(combined)) return { key: 'state', value: profile.state };
    if (/zip|postal|pin.?code/.test(combined)) return { key: 'zip', value: profile.zip };
    if (/country|nation/.test(combined)) return { key: 'country', value: profile.country };

    return null;
}

// ==================== FIELD FILLING ====================

function fillField(input, value, options = {}) {
    if (!value) return false;

    try {
        if (options.highlight) {
            input.style.outline = '3px solid #10b981';
            input.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
            input.style.transition = 'all 0.3s';
            setTimeout(() => {
                input.style.outline = '';
                input.style.backgroundColor = '';
            }, 2000);
        }

        input.focus();

        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
        const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;

        if (input.tagName === 'TEXTAREA' && nativeTextAreaValueSetter) {
            nativeTextAreaValueSetter.call(input, value);
        } else if (nativeInputValueSetter) {
            nativeInputValueSetter.call(input, value);
        } else {
            input.value = value;
        }

        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));

        setTimeout(() => input.blur(), 50);
        return true;
    } catch (e) {
        console.error('[KAI] Fill error:', e);
        return false;
    }
}

async function smartFill(options = {}) {
    if (!USER_DATA) await loadUserProfile();
    if (!USER_DATA?.email) {
        return { success: false, error: 'No profile! Open popup and sync.' };
    }

    const fields = findFormFields();
    if (fields.length === 0) {
        return { success: false, error: 'No form fields found' };
    }

    let filled = 0;
    const usedKeys = new Set();

    for (const field of fields) {
        const match = matchFieldToProfile(field, USER_DATA);
        if (match && match.value && !usedKeys.has(match.key)) {
            if (options.delay) await new Promise(r => setTimeout(r, 100));
            if (fillField(field.element, match.value, { highlight: true })) {
                filled++;
                usedKeys.add(match.key);
            }
        }
    }

    return { success: filled > 0, message: `✅ Filled ${filled}/${fields.length} fields!`, count: filled };
}

// ==================== INTENT CLASSIFIER ====================

const INTENTS = {
    FILL_BY_NUMBER: {
        patterns: [
            /^(?:fill|set|field|input|box)\s*#\s*(\d+)\s+(?:with|to|as|=|:)\s+(.+)/i,
            /^#\s*(\d+)\s*(?:with|to|as|=|:)\s+(.+)/i,
            /^(?:number|no\.?|#|field)\s*(\d+)\s*(?:with|to|as|=|:)\s+(.+)/i,
            /^(\d+)\s*(?:with|to|as|=|:)\s+(.+)/i
        ],
        handler: 'handleFillByNumber'
    },
    FILL_FIELD: {
        patterns: [
            /^(?:fill|set|put|enter|type|input|write)\s+(.+?)\s+(?:with|to|as|=|:)\s+(.+)/i
        ],
        handler: 'handleFillField'
    },
    MY_FIELD: {
        patterns: [
            /(?:my|use my|fill my|enter my|put my)\s+(name|email|phone|address|city|state|zip|country)/i,
            /(?:use|fill|enter|put)\s+(?:my\s+)?(name|email|phone|address|city|state|zip|country)/i
        ],
        handler: 'handleMyField'
    },
    LIST_FIELDS: {
        patterns: [
            /(?:list|show|display|get|what)\s*(?:all\s+)?(?:the\s+)?fields/i,
            /^fields$/i, /scan\s+(?:page|form)/i
        ],
        handler: 'handleListFields'
    },
    SHOW_PROFILE: {
        patterns: [/^profile$/i, /show\s+profile/i, /who\s+am\s+i/i],
        handler: 'handleShowProfile'
    },
    CLEAR: {
        patterns: [/(?:clear|reset|empty)\s+(?:all|fields|form)/i, /^(?:clear|reset)$/i],
        handler: 'handleClear'
    },
    SMART_FILL: {
        patterns: [/(?:smart|auto|quick|fast)\s*fill/i, /fill\s+(?:all|everything|form)/i, /^fill$/i, /^autofill$/i],
        handler: 'handleSmartFill'
    },
    CLICK: {
        patterns: [/(?:click|press|tap|hit)\s+(?:on\s+)?(?:the\s+)?(.+)/i, /^(?:submit|next|continue|send)$/i],
        handler: 'handleClick'
    },
    SCROLL: {
        patterns: [/scroll\s+(?:to\s+)?(?:top|bottom|up|down)/i],
        handler: 'handleScroll'
    },
    SEARCH: {
        patterns: [
            /^search\s+(?:for\s+)?(.+)/i,
            /^google\s+(.+)/i
        ],
        handler: 'handleSearch'
    },
    OPEN_TAB: {
        patterns: [
            /^open\s+(?:tab\s+)?(?:to\s+)?(\w+(?:\.\w+)+)/i,  // open youtube.com
            /^open\s+(?:tab\s+)?(?:to\s+)?(google|youtube|facebook|twitter|instagram|github|reddit|amazon|netflix|linkedin|whatsapp|gmail|maps|stackoverflow|wikipedia|discord|twitch|chatgpt|claude)$/i,  // open google
            /^(?:open|new)\s+tab\s+(.+)/i,  // open tab google
            /^go\s+to\s+(\w+(?:\.\w+)+)/i,  // go to google.com
            /^go\s+to\s+(google|youtube|facebook|twitter|instagram|github|reddit|amazon|netflix|linkedin)$/i,  // go to google
            /^navigate\s+(?:to\s+)?(.+)/i  // navigate to google.com
        ],
        handler: 'handleOpenTab'
    },
    CLOSE_TAB: {
        patterns: [/close\s+(?:this\s+)?(?:tab|page)/i, /^close$/i],
        handler: 'handleCloseTab'
    },
    REFRESH: {
        patterns: [/(?:refresh|reload)\s*(?:page)?/i],
        handler: 'handleRefresh'
    },
    GO_BACK: {
        patterns: [/(?:go\s+)?back/i, /previous\s+page/i],
        handler: 'handleGoBack'
    },
    GO_FORWARD: {
        patterns: [/(?:go\s+)?forward/i],
        handler: 'handleGoForward'
    },
    LIST_TABS: {
        patterns: [/(?:list|show|get)\s+(?:all\s+)?tabs/i, /^tabs$/i, /what\s+tabs/i],
        handler: 'handleListTabs'
    },
    SWITCH_TAB: {
        patterns: [/(?:switch|go)\s+(?:to\s+)?tab\s*#?\s*(\d+)/i, /tab\s*(\d+)/i],
        handler: 'handleSwitchTab'
    },
    NEW_WINDOW: {
        patterns: [/(?:new|open)\s+window/i],
        handler: 'handleNewWindow'
    },
    SCREENSHOT: {
        patterns: [/(?:take\s+)?screenshot/i, /capture\s+(?:page|screen)/i],
        handler: 'handleScreenshot'
    },
    COPY_URL: {
        patterns: [/copy\s+(?:url|link)/i, /get\s+(?:url|link)/i],
        handler: 'handleCopyUrl'
    },
    HIGHLIGHT: {
        patterns: [/highlight\s+(.+)/i, /find\s+(.+)/i],
        handler: 'handleHighlight'
    },
    // MACROS & TEMPLATES
    RECORD: {
        patterns: [/^(?:start\s+)?record(?:ing)?$/i, /^rec$/i],
        handler: 'handleStartRecording'
    },
    STOP_RECORDING: {
        patterns: [
            /^stop\s+(?:recording\s+)?(?:as\s+)?(.+)$/i,  // stop myMacro / stop recording myName
            /^stop\s*recording?$/i,  // stop / stop recording (no capture group)
            /^save\s+(?:recording|macro)\s*(.*)$/i  // save recording myName
        ],
        handler: 'handleStopRecording'
    },
    PLAY_MACRO: {
        patterns: [
            /^(?:play|run|execute)\s+(?:macro\s+)?(.+)/i,
            /^macro\s+(.+)/i
        ],
        handler: 'handlePlayMacro'
    },
    LIST_MACROS: {
        patterns: [/^(?:list|show|get)\s+macros$/i, /^macros$/i],
        handler: 'handleListMacros'
    },
    SAVE_TEMPLATE: {
        patterns: [/^save\s+(?:as\s+)?template\s*(.*)$/i, /^save\s+form$/i],
        handler: 'handleSaveTemplate'
    },
    APPLY_TEMPLATE: {
        patterns: [/^(?:apply|use|load)\s+template\s+(.+)/i, /^template\s+(.+)/i],
        handler: 'handleApplyTemplate'
    },
    LIST_TEMPLATES: {
        patterns: [/^(?:list|show|get)\s+templates$/i, /^templates$/i],
        handler: 'handleListTemplates'
    },
    // SCRAPER COMMANDS
    EXTRACT_TABLE: {
        patterns: [/(?:extract|get|scrape)\s+table(?:s)?/i, /save\s+table(?:s)?\s+(?:as|to)\s+(csv|json)/i],
        handler: 'handleExtractTable'
    },
    EXTRACT_LINKS: {
        patterns: [/(?:extract|get|scrape)\s+(?:all\s+)?links/i, /get\s+(?:all\s+)?(?:urls?|hrefs?)/i],
        handler: 'handleExtractLinks'
    },
    EXTRACT_EMAILS: {
        patterns: [/(?:extract|get|find)\s+(?:all\s+)?emails?/i],
        handler: 'handleExtractEmails'
    },
    EXTRACT_DATA: {
        patterns: [/(?:scrape|extract)\s+(?:page|data|everything)/i, /save\s+(?:page\s+)?data/i],
        handler: 'handleExtractData'
    },
    // WORKFLOW COMMANDS
    RUN_WORKFLOW: {
        patterns: [/^workflow:\s*(.+)/i, /^flow:\s*(.+)/i],
        handler: 'handleRunWorkflow'
    },
    SAVE_WORKFLOW: {
        patterns: [/^save\s+workflow\s+(.+)/i],
        handler: 'handleSaveWorkflow'
    },
    LIST_WORKFLOWS: {
        patterns: [/^(?:list|show)\s+workflows?$/i, /^workflows?$/i],
        handler: 'handleListWorkflows'
    },
    HELP: {
        patterns: [/^(?:help|commands?|\?)$/i, /what\s+can\s+you/i],
        handler: 'handleHelp'
    }
};

function classifyIntent(message) {
    const msg = message.trim();
    for (const [intentName, intentData] of Object.entries(INTENTS)) {
        for (const pattern of intentData.patterns) {
            const match = msg.match(pattern);
            if (match) {
                return {
                    intent: intentName,
                    handler: intentData.handler,
                    match: match,
                    groups: match.slice(1)
                };
            }
        }
    }
    return null;
}

// ==================== INTENT HANDLERS ====================

async function handleChatCommand(msg) {
    const lower = msg.toLowerCase().trim();

    // PRIORITY: Handle recording commands FIRST (before any other matching)
    if (lower === 'stop' || lower === 'stop recording') {
        if (isRecording) {
            return handleStopRecording(null);
        }
    }
    if (lower === 'record' || lower === 'start recording' || lower === 'rec') {
        return handleStartRecording();
    }

    // 🆕 Try natural language parsing first
    if (window.kaiUtils) {
        const naturalCommand = window.kaiUtils.parseNaturalCommand(msg);
        if (naturalCommand && naturalCommand.confidence > 0.7) {
            console.log('[KAI] Natural language detected:', naturalCommand);

            // Execute the parsed intent
            if (naturalCommand.intent === 'FILL_FIELD') {
                return handleFillField(naturalCommand.field, naturalCommand.value);
            }
            if (naturalCommand.intent === 'NAVIGATE' && naturalCommand.url) {
                return handleOpenTab(naturalCommand.url);
            }
        }
    }

    const result = classifyIntent(msg);

    // RECORD COMMANDS: If recording, capture the command as an action
    if (isRecording && result) {
        recordCommand(result.intent, result.groups, msg);
    }

    if (!result) {
        if (lower === 'help' || lower === '?') return handleHelp();
        if (lower === 'fields') return handleListFields();
        if (lower === 'profile') return handleShowProfile();
        if (lower === 'clear') return handleClear();
        if (lower === 'fill' || lower === 'autofill') {
            if (isRecording) recordCommand('SMART_FILL', [], msg);
            return handleSmartFill();
        }

        // 🆕 If nothing matched, try fuzzy command matching
        if (window.kaiUtils) {
            const commands = ['fill', 'click', 'scroll', 'extract', 'workflow', 'macro', 'template'];
            const similar = window.kaiUtils.findSimilarCommands(msg, commands);
            if (similar.length > 0) {
                addMsg(`❌ Command not recognized`, 'error');
                addMsg(`💡 Did you mean: ${similar.slice(0, 3).join(', ')}?`, 'info');
                return true;
            }
        }

        return false;
    }

    console.log('[KAI] Intent:', result.intent);

    switch (result.handler) {
        case 'handleFillByNumber': return handleFillByNumber(parseInt(result.groups[0]), result.groups[1]);
        case 'handleFillField': return handleFillField(result.groups[0], result.groups[1]);
        case 'handleMyField': return handleMyField(result.groups[0]);
        case 'handleListFields': return handleListFields();
        case 'handleShowProfile': return handleShowProfile();
        case 'handleClear': return handleClear();
        case 'handleSmartFill': return handleSmartFill();
        case 'handleClick': return handleClick(result.groups[0] || 'submit');
        case 'handleScroll': return handleScroll(msg);
        case 'handleSearch': return handleSearch(result.groups[0]);
        case 'handleOpenTab': return handleOpenTab(result.groups[0]);
        case 'handleCloseTab': return handleCloseTab();
        case 'handleRefresh': return handleRefresh();
        case 'handleGoBack': return handleGoBack();
        case 'handleGoForward': return handleGoForward();
        case 'handleListTabs': return handleListTabs();
        case 'handleSwitchTab': return handleSwitchTab(parseInt(result.groups[0]));
        case 'handleNewWindow': return handleNewWindow();
        case 'handleScreenshot': return handleScreenshot();
        case 'handleCopyUrl': return handleCopyUrl();
        case 'handleHighlight': return handleHighlight(result.groups[0]);
        // Macro & Template handlers
        case 'handleStartRecording': return handleStartRecording();
        case 'handleStopRecording': return handleStopRecording(result.groups[0]);
        case 'handlePlayMacro': return handlePlayMacro(result.groups[0]);
        case 'handleListMacros': return handleListMacros();
        case 'handleSaveTemplate': return handleSaveTemplate(result.groups[0]);
        case 'handleApplyTemplate': return handleApplyTemplate(result.groups[0]);
        case 'handleListTemplates': return handleListTemplates();
        // Scraper handlers
        case 'handleExtractTable': return handleExtractTable(result.groups[0]);
        case 'handleExtractLinks': return handleExtractLinks();
        case 'handleExtractEmails': return handleExtractEmails();
        case 'handleExtractData': return handleExtractData();
        // Workflow handlers
        case 'handleRunWorkflow': return handleRunWorkflow(result.groups[0]);
        case 'handleSaveWorkflow': return handleSaveWorkflow(result.groups[0]);
        case 'handleListWorkflows': return handleListWorkflows();
        case 'handleHelp': return handleHelp();
        default: return false;
    }
}

function handleFillField(fieldHint, value) {
    const fields = findFormFields();

    // Try smart matching
    const match = window.kaiUtils?.smartMatchField(fieldHint, fields);

    if (match && match.confidence > 0.5) {
        // Track action for undo
        if (window.kaiActionHistory) {
            window.kaiActionHistory.push({
                type: 'fill',
                field: match.field.label,
                oldValue: match.field.element.value,
                newValue: value
            });
        }

        fillField(match.field.element, value, { highlight: true });
        const strategyText = match.confidence < 0.8 ? ` (${match.strategy} match)` : '';
        addMsg(`✅ Filled "${match.field.label}"${strategyText}: ${value} `, 'success');
        speak(`Filled ${match.field.label} `);
        return true;
    }

    // No match found - provide helpful suggestions
    const suggestions = window.kaiUtils?.suggestSimilarFields(fieldHint, fields);

    addMsg(`❌ No field matching "${fieldHint}"`, 'error');

    if (suggestions && suggestions.length > 0) {
        addMsg('💡 Did you mean:', 'info');
        suggestions.slice(0, 3).forEach((sug, i) => {
            const label = sug.label.substring(0, 30);
            addMsg(`  ${i + 1}."${label}"(${sug.reason})`, 'info');
        });
        addMsg(`💬 Try: fill "${suggestions[0].label}" with ${value} `, 'info');
    } else {
        // Show all available fields
        addMsg('📋 Available fields:', 'info');
        fields.slice(0, 5).forEach((f, i) => {
            addMsg(`  #${i + 1}: ${f.label.substring(0, 40)} `, 'info');
        });
    }

    return true;
}

function handleFillByNumber(fieldNum, value) {
    const fields = findFormFields();
    const index = fieldNum - 1;

    if (index >= 0 && index < fields.length) {
        const field = fields[index];
        fillField(field.element, value, { highlight: true });
        addMsg(`✅ Field #${fieldNum} (${field.label}): ${value} `, 'success');
        speak(`Filled field ${fieldNum} `);
    } else {
        addMsg(`❌ Field #${fieldNum} not found(have ${fields.length} fields)`, 'error');
    }
    return true;
}

function handleMyField(fieldType) {
    if (!USER_DATA) { addMsg('❌ No profile loaded!', 'error'); return true; }

    const type = fieldType.toLowerCase().trim();
    const fields = findFormFields();
    const profileMap = {
        'name': { keywords: ['name'], value: USER_DATA.name },
        'email': { keywords: ['email'], value: USER_DATA.email },
        'phone': { keywords: ['phone', 'mobile', 'tel'], value: USER_DATA.phone },
        'address': { keywords: ['address', 'street'], value: USER_DATA.address },
        'city': { keywords: ['city'], value: USER_DATA.city },
        'state': { keywords: ['state', 'province'], value: USER_DATA.state },
        'zip': { keywords: ['zip', 'postal'], value: USER_DATA.zip },
        'country': { keywords: ['country'], value: USER_DATA.country }
    };

    const mapping = profileMap[type];
    if (!mapping?.value) {
        addMsg(`⚠️ Your ${type} is not set in profile`, 'error');
        return true;
    }

    for (const field of fields) {
        const label = field.label.toLowerCase();
        if (mapping.keywords.some(k => label.includes(k))) {
            fillField(field.element, mapping.value, { highlight: true });
            addMsg(`✅ Filled ${type}: ${mapping.value} `, 'success');
            speak(`Filled ${type} `);
            return true;
        }
    }

    addMsg(`❌ No ${type} field found`, 'error');
    return true;
}

function handleListFields() {
    const fields = findFormFields();
    addMsg(`📊 ${fields.length} fields: `, 'info');
    fields.forEach((f, i) => {
        const label = f.label.substring(0, 30) + (f.label.length > 30 ? '...' : '');
        addMsg(`  #${i + 1}: ${label} `, 'info');
    });
    return true;
}

function handleShowProfile() {
    if (!USER_DATA) { addMsg('❌ No profile!', 'error'); return true; }
    addMsg('👤 Profile:', 'info');
    addMsg(`  Name: ${USER_DATA.name || '-'} `, 'info');
    addMsg(`  Email: ${USER_DATA.email || '-'} `, 'info');
    addMsg(`  Phone: ${USER_DATA.phone || '-'} `, 'info');
    return true;
}

function handleClear() {
    const fields = findFormFields();
    fields.forEach(f => {
        f.element.value = '';
        f.element.dispatchEvent(new Event('input', { bubbles: true }));
    });
    addMsg(`🗑️ Cleared ${fields.length} fields`, 'success');
    speak('Fields cleared');
    return true;
}

async function handleSmartFill() {
    addMsg('🤖 Smart filling...', 'info');
    const result = await smartFill({ delay: true });
    addMsg(result.success ? result.message : `❌ ${result.error} `, result.success ? 'success' : 'error');
    if (result.success) speak(`Filled ${result.count} fields`);
    return true;
}

function handleClick(target) {
    const lower = target.toLowerCase().trim();
    const buttons = document.querySelectorAll('button, input[type="submit"], a.btn, [role="button"]');

    for (const btn of buttons) {
        const text = (btn.textContent || btn.value || '').toLowerCase().trim();
        if (text.includes(lower) || lower.includes(text) || ['submit', 'next', 'continue'].includes(lower)) {
            btn.click();
            addMsg(`✅ Clicked: ${btn.textContent?.trim() || btn.value || 'button'} `, 'success');
            speak('Button clicked');
            return true;
        }
    }
    addMsg(`❌ Button "${target}" not found`, 'error');
    return true;
}

function handleScroll(msgOrDirection) {
    const lower = (msgOrDirection || 'down').toLowerCase();

    if (lower === 'top' || lower.includes('top')) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        addMsg('⬆️ Scrolled top', 'success');
    }
    else if (lower === 'bottom' || lower.includes('bottom')) {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        addMsg('⬇️ Scrolled bottom', 'success');
    }
    else if (lower === 'down' || lower.includes('down')) {
        window.scrollBy({ top: 400, behavior: 'smooth' });
        addMsg('⬇️ Scrolled down', 'success');
    }
    else {
        window.scrollBy({ top: -400, behavior: 'smooth' });
        addMsg('⬆️ Scrolled up', 'success');
    }
    return true;
}

async function handleSearch(query) {
    try {
        if (!query) {
            addMsg('❌ Specify search: search how to cook pasta', 'error');
            return true;
        }
        const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
        await sendToBackground({ action: 'openTab', url: searchUrl });
        addMsg(`🔍 Searching: ${query}`, 'success');
        speak(`Searching for ${query}`);
    } catch (e) {
        addMsg(`❌ ${e.message}`, 'error');
    }
    return true;
}

async function handleOpenTab(input) {
    try {
        let urlInput = (input || '').trim().toLowerCase();
        if (!urlInput) {
            addMsg('❌ Specify URL: open google or open youtube.com', 'error');
            return true;
        }

        // Smart URL resolver - convert common site names to URLs
        const siteMap = {
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://www.twitter.com',
            'x': 'https://www.x.com',
            'instagram': 'https://www.instagram.com',
            'linkedin': 'https://www.linkedin.com',
            'github': 'https://www.github.com',
            'reddit': 'https://www.reddit.com',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'spotify': 'https://www.spotify.com',
            'gmail': 'https://mail.google.com',
            'maps': 'https://maps.google.com',
            'drive': 'https://drive.google.com',
            'docs': 'https://docs.google.com',
            'sheets': 'https://sheets.google.com',
            'chatgpt': 'https://chat.openai.com',
            'claude': 'https://claude.ai',
            'wikipedia': 'https://www.wikipedia.org',
            'stackoverflow': 'https://stackoverflow.com',
            'whatsapp': 'https://web.whatsapp.com',
            'telegram': 'https://web.telegram.org',
            'discord': 'https://discord.com',
            'twitch': 'https://www.twitch.tv',
            'tiktok': 'https://www.tiktok.com',
            'pinterest': 'https://www.pinterest.com',
            'ebay': 'https://www.ebay.com',
            'flipkart': 'https://www.flipkart.com',
            'myntra': 'https://www.myntra.com'
        };

        let targetUrl;

        // Check if it's a known site name
        if (siteMap[urlInput]) {
            targetUrl = siteMap[urlInput];
        }
        // Check if it has a domain extension
        else if (/\.(com|org|net|io|co|in|edu|gov|ai|dev|app)$/i.test(urlInput)) {
            targetUrl = urlInput.startsWith('http') ? urlInput : 'https://' + urlInput;
        }
        // Check if it looks like a URL with subdomain
        else if (urlInput.includes('.')) {
            targetUrl = urlInput.startsWith('http') ? urlInput : 'https://' + urlInput;
        }
        // Assume it's a search query or site name - try adding .com
        else {
            // Try as domain first
            targetUrl = `https://www.${urlInput}.com`;
        }

        const result = await sendToBackground({ action: 'openTab', url: targetUrl });
        addMsg(`🌐 Opening: ${targetUrl}`, 'success');
        speak('Tab opened');
    } catch (e) {
        addMsg(`❌ ${e.message}`, 'error');
    }
    return true;
}

async function handleCloseTab() {
    try {
        await sendToBackground({ action: 'closeTab' });
        addMsg('🚪 Tab closed', 'success');
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

async function handleRefresh() {
    try {
        await sendToBackground({ action: 'refresh' });
        addMsg('🔄 Refreshing...', 'success');
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

async function handleGoBack() {
    try {
        await sendToBackground({ action: 'goBack' });
        addMsg('⬅️ Going back', 'success');
        speak('Going back');
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

async function handleGoForward() {
    try {
        await sendToBackground({ action: 'goForward' });
        addMsg('➡️ Going forward', 'success');
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

async function handleListTabs() {
    try {
        const result = await sendToBackground({ action: 'getTabs' });
        if (result.success && result.tabs) {
            addMsg(`📑 ${result.tabs.length} tabs:`, 'info');
            result.tabs.slice(0, 5).forEach((t, i) => {
                addMsg(`  #${i + 1}: ${t.title?.substring(0, 25) || 'Untitled'}`, 'info');
            });
        }
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

async function handleSwitchTab(tabNum) {
    try {
        await sendToBackground({ action: 'switchTab', index: tabNum - 1 });
        addMsg(`📑 Switched to tab #${tabNum}`, 'success');
        speak(`Tab ${tabNum}`);
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

async function handleNewWindow() {
    try {
        await sendToBackground({ action: 'newWindow' });
        addMsg('🪟 New window opened', 'success');
    } catch (e) { addMsg(`❌ ${e.message}`, 'error'); }
    return true;
}

function handleScreenshot() {
    addMsg('📸 Taking screenshot...', 'info');
    // Use html2canvas if available, otherwise show message
    if (window.html2canvas) {
        html2canvas(document.body).then(canvas => {
            const link = document.createElement('a');
            link.download = `kai-screenshot-${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();
            addMsg('✅ Screenshot saved!', 'success');
        });
    } else {
        // Fallback: trigger browser's print dialog
        addMsg('💡 Use Ctrl+Shift+S for screenshot', 'info');
    }
    return true;
}

function handleCopyUrl() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        addMsg(`📋 Copied: ${window.location.href.substring(0, 50)}...`, 'success');
        speak('URL copied');
    }).catch(() => {
        addMsg('❌ Copy failed', 'error');
    });
    return true;
}

function handleHighlight(text) {
    if (!text) { addMsg('❌ Specify text to find', 'error'); return true; }

    const found = window.find(text, false, false, true);
    if (found) {
        addMsg(`🔍 Found: "${text}"`, 'success');
    } else {
        addMsg(`❌ Not found: "${text}"`, 'error');
    }
    return true;
}

// ==================== MACRO RECORDING ====================

function handleStartRecording() {
    if (isRecording) {
        addMsg('⚠️ Already recording! Say "stop" to finish', 'error');
        return true;
    }

    isRecording = true;
    recordedActions = [];
    addMsg('🎬 RECORDING STARTED!', 'success');
    addMsg('💡 Perform actions, then say "stop" to save', 'info');
    speak('Recording started');

    // Visual indicator
    updateRecordingIndicator(true);

    // Save state (so recording persists across refresh)
    saveChatState();

    return true;
}

async function handleStopRecording(macroName) {
    if (!isRecording) {
        addMsg('⚠️ Not recording! Say "record" to start', 'error');
        return true;
    }

    isRecording = false;
    updateRecordingIndicator(false);

    if (recordedActions.length === 0) {
        addMsg('⚠️ No actions recorded', 'error');
        return true;
    }

    const name = macroName?.trim() || `macro_${Date.now()}`;

    const macro = {
        name: name,
        trigger: name.toLowerCase(),
        actions: recordedActions,
        site: window.location.hostname
    };

    try {
        const result = await sendToBackground({
            action: 'saveMacro',
            user_id: USER_ID,
            macro: macro
        });

        addMsg(`✅ Macro "${name}" saved! (${recordedActions.length} actions)`, 'success');
        addMsg(`💡 Play it with: "play ${name}"`, 'info');
        speak(`Macro ${name} saved`);

        // Refresh macros list
        await loadMacrosAndTemplates();
    } catch (e) {
        addMsg(`❌ Failed to save macro: ${e.message}`, 'error');
    }

    recordedActions = [];
    return true;
}

async function handlePlayMacro(macroName) {
    if (!macroName) {
        addMsg('❌ Specify macro: play work_form', 'error');
        return true;
    }

    const name = macroName.toLowerCase().trim();

    // Find macro
    const macro = loadedMacros.find(m =>
        m.name?.toLowerCase() === name ||
        m.trigger?.toLowerCase() === name
    );

    if (!macro) {
        addMsg(`❌ Macro "${macroName}" not found`, 'error');
        addMsg('💡 Use "macros" to list available macros', 'info');
        return true;
    }

    addMsg(`▶️ Playing macro: ${macro.name} (${macro.actions?.length || 0} steps)`, 'info');
    speak(`Playing ${macro.name}`);

    // Execute actions with proper delays
    let stepNum = 0;
    for (const action of macro.actions) {
        stepNum++;

        // Show what we're doing
        addMsg(`  ⏳ Step ${stepNum}: ${action.type}...`, 'info', false);

        // Execute the action
        await executeMacroAction(action);

        // Delay based on action type
        const delay = getActionDelay(action.type);
        await new Promise(r => setTimeout(r, delay));
    }

    addMsg(`✅ Macro "${macro.name}" completed!`, 'success');
    speak('Macro completed');
    return true;
}

// Get appropriate delay for each action type
function getActionDelay(actionType) {
    switch (actionType) {
        case 'open':
        case 'search':
            return 2000; // 2 seconds for navigation
        case 'refresh':
            return 1500;
        case 'autofill':
            return 1000;
        case 'scroll':
        case 'click':
            return 600;
        case 'fill':
            return 500;
        default:
            return 800;
    }
}

async function executeMacroAction(action) {
    switch (action.type) {
        case 'fill':
            const fields = findFormFields();
            const field = fields.find(f =>
                f.label.toLowerCase().includes(action.field.toLowerCase()) ||
                f.name?.toLowerCase().includes(action.field.toLowerCase())
            );
            if (field) {
                let value = action.value;
                // Replace variables
                if (value?.startsWith('$profile.') && USER_DATA) {
                    const key = value.replace('$profile.', '');
                    value = USER_DATA[key] || value;
                }
                fillField(field.element, value, { highlight: true });
            }
            break;
        case 'click':
            handleClick(action.target);
            break;
        case 'wait':
            await new Promise(r => setTimeout(r, action.ms || 1000));
            break;
        case 'scroll':
            handleScroll(action.direction || 'down');
            break;
        case 'open':
            await handleOpenTab(action.url);
            break;
        case 'autofill':
            await handleSmartFill();
            break;
        case 'search':
            await handleSearch(action.query);
            break;
        case 'refresh':
            await handleRefresh();
            break;
        case 'back':
            await handleGoBack();
            break;
        case 'forward':
            await handleGoForward();
            break;
        case 'find':
            handleHighlight(action.text);
            break;
    }
}

async function handleListMacros() {
    await loadMacrosAndTemplates();

    if (loadedMacros.length === 0) {
        addMsg('📭 No macros saved yet', 'info');
        addMsg('💡 Say "record" to create one!', 'info');
        return true;
    }

    addMsg(`📋 ${loadedMacros.length} macros:`, 'info');
    loadedMacros.forEach((m, i) => {
        addMsg(`  ${i + 1}. ${m.name} (${m.actions?.length || 0} actions)`, 'info');
    });
    return true;
}

// ==================== TEMPLATES ====================

async function handleSaveTemplate(templateName) {
    const fields = findFormFields();
    const filledFields = {};

    fields.forEach(f => {
        if (f.element.value?.trim()) {
            const key = f.label || f.name || `field_${f.index}`;
            filledFields[key] = f.element.value;
        }
    });

    if (Object.keys(filledFields).length === 0) {
        addMsg('⚠️ No filled fields to save', 'error');
        return true;
    }

    const name = templateName?.trim() || `template_${Date.now()}`;

    const template = {
        name: name,
        fields: filledFields,
        site: window.location.hostname,
        url: window.location.href
    };

    try {
        await sendToBackground({
            action: 'saveTemplate',
            user_id: USER_ID,
            template: template
        });

        addMsg(`✅ Template "${name}" saved! (${Object.keys(filledFields).length} fields)`, 'success');
        addMsg(`💡 Apply it with: "apply template ${name}"`, 'info');
        speak(`Template ${name} saved`);

        await loadMacrosAndTemplates();
    } catch (e) {
        addMsg(`❌ Failed to save: ${e.message}`, 'error');
    }

    return true;
}

async function handleApplyTemplate(templateName) {
    if (!templateName) {
        addMsg('❌ Specify template: apply template work', 'error');
        return true;
    }

    const name = templateName.toLowerCase().trim();
    const template = loadedTemplates.find(t => t.name?.toLowerCase() === name);

    if (!template) {
        addMsg(`❌ Template "${templateName}" not found`, 'error');
        addMsg('💡 Use "templates" to list available', 'info');
        return true;
    }

    const fields = findFormFields();
    let filled = 0;

    for (const [label, value] of Object.entries(template.fields)) {
        const field = fields.find(f =>
            f.label.toLowerCase().includes(label.toLowerCase())
        );
        if (field) {
            fillField(field.element, value, { highlight: true });
            filled++;
        }
    }

    addMsg(`✅ Applied template: ${filled}/${Object.keys(template.fields).length} fields`, 'success');
    speak(`Template applied`);
    return true;
}

async function handleListTemplates() {
    await loadMacrosAndTemplates();

    if (loadedTemplates.length === 0) {
        addMsg('📭 No templates saved yet', 'info');
        addMsg('💡 Fill a form and say "save template NAME"', 'info');
        return true;
    }

    addMsg(`📋 ${loadedTemplates.length} templates:`, 'info');
    loadedTemplates.forEach((t, i) => {
        addMsg(`  ${i + 1}. ${t.name} (${Object.keys(t.fields || {}).length} fields)`, 'info');
    });
    return true;
}

// ==================== MACRO HELPERS ====================

// Record a KAI command as a macro action
function recordCommand(intent, groups, rawMsg) {
    let action = null;

    switch (intent) {
        case 'SCROLL':
            action = { type: 'scroll', direction: rawMsg.includes('up') ? 'up' : 'down' };
            break;
        case 'CLICK':
            action = { type: 'click', target: groups[0] || 'submit' };
            break;
        case 'FILL_FIELD':
            action = { type: 'fill', field: groups[0], value: groups[1] };
            break;
        case 'FILL_BY_NUMBER':
            action = { type: 'fill', field: `#${groups[0]}`, value: groups[1] };
            break;
        case 'MY_FIELD':
            action = { type: 'fill', field: groups[0], value: `$profile.${groups[0]}` };
            break;
        case 'SMART_FILL':
            action = { type: 'autofill' };
            break;
        case 'OPEN_TAB':
            action = { type: 'open', url: groups[0] };
            break;
        case 'SEARCH':
            action = { type: 'search', query: groups[0] };
            break;
        case 'HIGHLIGHT':
            action = { type: 'find', text: groups[0] };
            break;
        case 'REFRESH':
            action = { type: 'refresh' };
            break;
        case 'GO_BACK':
            action = { type: 'back' };
            break;
        case 'GO_FORWARD':
            action = { type: 'forward' };
            break;
        // Skip non-recordable: HELP, LIST_MACROS, LIST_TEMPLATES, etc.
    }

    if (action) {
        recordedActions.push(action);
        saveChatState(); // Persist
        console.log('[KAI] Recorded action:', action);
    }
}

let trackingInitialized = false; // Flag to prevent duplicate listeners

function trackUserActions() {
    if (trackingInitialized) return; // Only add listeners once
    trackingInitialized = true;

    // Track fill events
    document.addEventListener('input', (e) => {
        if (!isRecording) return;
        if (e.target.closest('#kai-widget')) return;

        const field = findFormFields().find(f => f.element === e.target);
        if (field && e.target.value) {
            // Update or add action
            const existingIdx = recordedActions.findIndex(a =>
                a.type === 'fill' && a.field === field.label
            );

            if (existingIdx >= 0) {
                recordedActions[existingIdx].value = e.target.value;
            } else {
                recordedActions.push({
                    type: 'fill',
                    field: field.label,
                    value: e.target.value
                });
            }
        }
    }, true);

    // Track clicks
    document.addEventListener('click', (e) => {
        if (!isRecording) return;
        if (e.target.closest('#kai-widget')) return;

        const btn = e.target.closest('button, [role="button"], input[type="submit"]');
        if (btn) {
            recordedActions.push({
                type: 'click',
                target: btn.textContent?.trim() || btn.value || 'button'
            });
        }
    }, true);
}

function updateRecordingIndicator(recording) {
    const orb = document.getElementById('kai-orb');
    if (orb) {
        orb.style.background = recording
            ? 'linear-gradient(135deg, #ef4444, #f87171)'
            : 'linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7)';
        orb.innerHTML = recording ? '⏺️' : '⚡';
    }
}

async function loadMacrosAndTemplates() {
    if (!USER_ID) return;

    try {
        const [macrosRes, templatesRes] = await Promise.all([
            sendToBackground({ action: 'getMacros', user_id: USER_ID }),
            sendToBackground({ action: 'getTemplates', user_id: USER_ID })
        ]);

        loadedMacros = macrosRes.macros || [];
        loadedTemplates = templatesRes.templates || [];
    } catch (e) {
        console.error('[KAI] Failed to load macros/templates:', e);
    }
}

function handleHelp() {
    addMsg('🚀 KAI BEAST MODE v5:', 'info');
    addMsg('━━━ FILL ━━━', 'info');
    addMsg('• fill #3 with value', 'info');
    addMsg('• my name/email/phone', 'info');
    addMsg('• autofill', 'info');
    addMsg('━━━ MACROS ━━━', 'info');
    addMsg('• record / stop', 'info');
    addMsg('• play [macro name]', 'info');
    addMsg('• macros', 'info');
    addMsg('━━━ TEMPLATES ━━━', 'info');
    addMsg('• save template [name]', 'info');
    addMsg('• apply template [name]', 'info');
    addMsg('• templates', 'info');
    addMsg('━━━ BROWSER ━━━', 'info');
    addMsg('• open google / search X', 'info');
    addMsg('• tabs / back / forward', 'info');
    addMsg('━━━ VOICE ━━━', 'info');
    addMsg('• Click 🎤 or press V', 'info');
    return true;
}

// ==================== KEYBOARD SHORTCUTS ====================

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger in input fields unless it's our input
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
            if (document.activeElement.id !== 'kai-input') return;
        }

        // V - Toggle Voice
        if (e.key.toLowerCase() === 'v' && !e.ctrlKey && !e.altKey && !e.metaKey) {
            if (document.activeElement.id !== 'kai-input') {
                e.preventDefault();
                toggleVoice();
            }
        }

        // Escape - Close panel
        if (e.key === 'Escape') {
            const panel = document.getElementById('kai-panel');
            if (panel && panel.style.display === 'block') {
                panel.style.display = 'none';
            }
        }

        // Ctrl+Shift+K - Toggle KAI
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            const panel = document.getElementById('kai-panel');
            if (panel) {
                panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
            }
        }

        // Ctrl+Shift+F - Quick fill
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'f') {
            e.preventDefault();
            handleSmartFill();
        }

        // Arrow up/down for command history
        if (document.activeElement.id === 'kai-input') {
            if (e.key === 'ArrowUp' && commandHistory.length > 0) {
                e.preventDefault();
                historyIndex = Math.min(historyIndex + 1, commandHistory.length - 1);
                document.getElementById('kai-input').value = commandHistory[historyIndex] || '';
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                historyIndex = Math.max(historyIndex - 1, -1);
                document.getElementById('kai-input').value = historyIndex >= 0 ? commandHistory[historyIndex] : '';
            }
        }
    });
}

// ==================== WIDGET UI ====================

async function createWidget() {
    if (document.getElementById('kai-widget')) return;

    const widget = document.createElement('div');
    widget.id = 'kai-widget';
    widget.innerHTML = `
        <style>
            #kai-widget { position: fixed; bottom: 20px; right: 20px; z-index: 999999; font-family: 'Segoe UI', system-ui, sans-serif; }
            #kai-orb { width: 60px; height: 60px; background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7); border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 26px; box-shadow: 0 4px 25px rgba(99, 102, 241, 0.5); transition: all 0.3s; animation: orbFloat 3s ease-in-out infinite; }
            #kai-orb:hover { transform: scale(1.15); box-shadow: 0 8px 35px rgba(139, 92, 246, 0.6); }
            @keyframes orbFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
            #kai-panel { display: none; position: absolute; bottom: 75px; right: 0; width: 360px; background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 20px; overflow: hidden; box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6), 0 0 40px rgba(139, 92, 246, 0.15); backdrop-filter: blur(20px); }
            #kai-header { background: linear-gradient(90deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2)); padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(139, 92, 246, 0.3); }
            #kai-header span { color: #c4b5fd; font-weight: 700; font-size: 15px; text-shadow: 0 0 10px rgba(196, 181, 253, 0.3); }
            #kai-close { background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.3); color: #fca5a5; cursor: pointer; font-size: 14px; padding: 4px 10px; border-radius: 6px; transition: all 0.2s; }
            #kai-close:hover { background: rgba(239, 68, 68, 0.4); }
            #kai-msgs { max-height: 220px; overflow-y: auto; padding: 14px; }
            #kai-msgs::-webkit-scrollbar { width: 6px; }
            #kai-msgs::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.3); border-radius: 3px; }
            .kai-msg { background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), transparent); border-left: 3px solid #818cf8; padding: 10px 14px; margin-bottom: 8px; border-radius: 0 10px 10px 0; font-size: 12px; color: #e0e7ff; transition: all 0.2s; animation: msgSlide 0.3s ease; }
            @keyframes msgSlide { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
            .kai-msg.success { border-left-color: #10b981; background: linear-gradient(90deg, rgba(16, 185, 129, 0.15), transparent); }
            .kai-msg.error { border-left-color: #ef4444; background: linear-gradient(90deg, rgba(239, 68, 68, 0.15), transparent); }
            #kai-btns { padding: 14px; display: flex; flex-direction: column; gap: 10px; }
            .kai-btn { padding: 12px 16px; border: none; border-radius: 12px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.25s; display: flex; align-items: center; justify-content: center; gap: 8px; }
            .kai-btn-primary { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); }
            .kai-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5); }
            .kai-btn-secondary { background: rgba(99, 102, 241, 0.12); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.25); }
            .kai-btn-secondary:hover { background: rgba(99, 102, 241, 0.25); border-color: rgba(99, 102, 241, 0.4); }
            .kai-btn-row { display: flex; gap: 8px; }
            .kai-btn-row .kai-btn { flex: 1; padding: 10px 8px; font-size: 12px; }
            #kai-input-row { display: flex; gap: 8px; }
            #kai-input { flex: 1; padding: 12px 14px; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; color: #e0e7ff; font-size: 13px; resize: none; }
            #kai-input:focus { outline: none; border-color: #8b5cf6; box-shadow: 0 0 15px rgba(139, 92, 246, 0.2); }
            #kai-input::placeholder { color: rgba(224, 231, 255, 0.35); }
            #btn-voice { width: 44px; height: 44px; min-width: 44px; padding: 0; border-radius: 50%; font-size: 18px; background: rgba(139, 92, 246, 0.15); }
            #btn-voice.listening { background: linear-gradient(135deg, #ef4444, #f87171); animation: pulse 1s infinite; }
            @keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); } 50% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } }
            .kbd { background: rgba(0,0,0,0.4); padding: 2px 6px; border-radius: 4px; font-size: 10px; color: #a5b4fc; margin-left: 4px; }
        </style>
        <div id="kai-orb">⚡</div>
        <div id="kai-panel">
            <div id="kai-header">
                <span>⚡ KAI BEAST MODE</span>
                <button id="kai-close">✕ ESC</button>
            </div>
            <div id="kai-msgs"></div>
            <div id="kai-btns">
                <button class="kai-btn kai-btn-primary" id="btn-smart-fill">🤖 Smart Fill <span class="kbd">Ctrl+Shift+F</span></button>
                <div class="kai-btn-row">
                    <button class="kai-btn kai-btn-secondary" id="btn-list">📋 Fields</button>
                    <button class="kai-btn kai-btn-secondary" id="btn-clear">🗑️ Clear</button>
                    <button class="kai-btn kai-btn-secondary" id="btn-help">❓ Help</button>
                </div>
                <div id="kai-input-row">
                    <textarea id="kai-input" placeholder="Type command or press V for voice..." rows="1"></textarea>
                    <button class="kai-btn kai-btn-secondary" id="btn-voice">🎤</button>
                </div>
                <button class="kai-btn kai-btn-secondary" id="btn-send">💬 Send <span class="kbd">Enter</span></button>
            </div>
        </div>
    `;

    document.body.appendChild(widget);

    // Event listeners
    document.getElementById('kai-orb').onclick = () => {
        const panel = document.getElementById('kai-panel');
        panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
    };

    document.getElementById('kai-close').onclick = () => {
        document.getElementById('kai-panel').style.display = 'none';
    };

    document.getElementById('btn-smart-fill').onclick = () => handleSmartFill();
    document.getElementById('btn-list').onclick = () => handleListFields();
    document.getElementById('btn-clear').onclick = () => handleClear();
    document.getElementById('btn-help').onclick = () => handleHelp();
    document.getElementById('btn-voice').onclick = () => toggleVoice();

    document.getElementById('btn-send').onclick = async () => {
        const input = document.getElementById('kai-input');
        const msg = input.value.trim();
        if (!msg) return;

        commandHistory.unshift(msg);
        if (commandHistory.length > 20) commandHistory.pop();
        historyIndex = -1;

        addMsg(`You: ${msg}`, 'info');
        input.value = '';

        const handled = await handleChatCommand(msg);
        if (!handled) {
            try {
                const result = await sendToBackground({ action: 'chat', query: msg });
                addMsg(`KAI: ${result.response || result.error}`, result.success ? 'success' : 'error');
                speak(result.response);
            } catch (e) {
                addMsg(`❌ ${e.message}`, 'error');
            }
        }
    };

    const input = document.getElementById('kai-input');
    input.onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('btn-send').click();
        }
    };

    // Load saved state FIRST
    await loadChatState();

    // Restore chat history to UI
    if (chatHistory.length > 0) {
        restoreChatHistory();
        addMsg('━━━ Session Restored ━━━', 'info', false);
    } else {
        addMsg('🔥 BEAST MODE ACTIVE!', 'info');
        addMsg('💡 Press V for voice, Ctrl+Shift+K to toggle', 'info');
    }

    // Show recording status if was recording
    if (isRecording) {
        addMsg('🎬 RECORDING IN PROGRESS...', 'success');
    }

    // Initialize profile
    loadUserProfile().then(() => {
        if (USER_DATA) {
            addMsg(`✅ Profile: ${USER_DATA.name || USER_DATA.email}`, 'success');
        } else {
            addMsg('⚠️ No profile - click extension icon', 'error');
        }
    });

    // Init voice
    initVoiceRecognition();
    initKeyboardShortcuts();
    trackUserActions(); // Initialize tracking once
}

function addMsg(text, type = 'info', save = true) {
    const msgs = document.getElementById('kai-msgs');
    if (!msgs) return;

    const msg = document.createElement('div');
    msg.className = `kai-msg ${type}`;
    msg.textContent = text;
    msgs.appendChild(msg);
    msgs.scrollTop = msgs.scrollHeight;

    // Save to history
    if (save) {
        chatHistory.push({ text, type, time: Date.now() });
        saveChatState();
    }

    while (msgs.children.length > 50) {
        msgs.removeChild(msgs.firstChild);
    }
}

// Restore chat history to UI
function restoreChatHistory() {
    const msgs = document.getElementById('kai-msgs');
    if (!msgs || chatHistory.length === 0) return;

    chatHistory.forEach(item => {
        addMsg(item.text, item.type, false); // false = don't re-save
    });
}

// ==================== INITIALIZATION ====================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
} else {
    createWidget();
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'aiFill' || request.action === 'smartFill') {
        smartFill({ delay: true }).then(sendResponse);
        return true;
    }
    if (request.action === 'ping') {
        sendResponse({ status: 'ready', hasProfile: !!USER_DATA });
    }
    return true;
});

window.KAI = { smartFill, findFormFields, handleChatCommand, toggleVoice, speak, USER_DATA: () => USER_DATA };

// ==================== SCRAPER HANDLERS ====================

function handleExtractTable(format) {
    if (!window.kaiScraper) {
        addMsg('âŒ Scraper not loaded', 'error');
        return true;
    }

    const tables = window.kaiScraper.extractTables();

    if (tables.length === 0) {
        addMsg('âŒ No tables found on page', 'error');
        return true;
    }

    addMsg(`ðŸ“Š Found ${tables.length} table(s)`, 'success');

    tables.forEach((table, i) => {
        addMsg(`  Table ${i + 1}: ${table.rowCount} rows, ${table.headers.length} columns`, 'info');
    });

    // If format specified (csv/json), download the first table
    if (format && tables.length > 0) {
        const fmt = format.toLowerCase();
        const filename = `table_${Date.now()}`;
        window.kaiScraper.download(tables[0].rows, filename, fmt);
        addMsg(`âœ… Downloaded as ${fmt.toUpperCase()}`, 'success');
    } else {
        addMsg('ðŸ’¡ Use "save table as csv" or "save table as json" to download', 'info');
    }

    return true;
}

function handleExtractLinks() {
    if (!window.kaiScraper) {
        addMsg('âŒ Scraper not loaded', 'error');
        return true;
    }

    const links = window.kaiScraper.extractLinks();

    if (links.length === 0) {
        addMsg('âŒ No links found', 'error');
        return true;
    }

    addMsg(`ðŸ”— Found ${links.length} links`, 'success');

    // Show first 10
    links.slice(0, 10).forEach(link => {
        const text = link.text.substring(0, 40) + (link.text.length > 40 ? '...' : '');
        addMsg(`  ${text} â†’ ${link.domain}`, 'info');
    });

    if (links.length > 10) {
        addMsg(`  ... and ${links.length - 10} more`, 'info');
    }

    // Auto-download as JSON
    window.kaiScraper.download(links, `links_${Date.now()}`, 'json');
    addMsg('âœ… Downloaded links.json', 'success');

    return true;
}

function handleExtractEmails() {
    if (!window.kaiScraper) {
        addMsg('âŒ Scraper not loaded', 'error');
        return true;
    }

    const emails = window.kaiScraper.extractEmails();

    if (emails.length === 0) {
        addMsg('âŒ No emails found', 'error');
        return true;
    }

    addMsg(`ðŸ“§ Found ${emails.length} email(s):`, 'success');
    emails.forEach(email => addMsg(`  ${email}`, 'info'));

    // Copy to clipboard
    navigator.clipboard.writeText(emails.join(', ')).then(() => {
        addMsg('âœ… Copied to clipboard', 'success');
    });

    return true;
}

function handleExtractData() {
    if (!window.kaiScraper) {
        addMsg('âŒ Scraper not loaded', 'error');
        return true;
    }

    addMsg('ðŸ” Extracting page data...', 'info');

    const data = {
        url: window.location.href,
        title: document.title,
        tables: window.kaiScraper.extractTables(),
        links: window.kaiScraper.extractLinks().slice(0, 50), // Limit to 50
        emails: window.kaiScraper.extractEmails(),
        phones: window.kaiScraper.extractPhones(),
        products: window.kaiScraper.extractProducts(),
        lists: window.kaiScraper.extractLists(),
        images: window.kaiScraper.extractImages().slice(0, 20), // Limit to 20
        extracted: new Date().toISOString()
    };

    const stats = `Tables: ${data.tables.length}, Links: ${data.links.length}, Emails: ${data.emails.length}, Products: ${data.products.length}`;
    addMsg(`ðŸ“¦ Extracted: ${stats}`, 'success');

    window.kaiScraper.download(data, `page_data_${Date.now()}`, 'json');
    addMsg('âœ… Downloaded page_data.json', 'success');
    speak('Data extracted and downloaded');

    return true;
}

// ==================== WORKFLOW HANDLERS ====================

async function handleRunWorkflow(workflowText) {
    if (!window.kaiWorkflow) {
        addMsg('âŒ Workflow engine not loaded', 'error');
        return true;
    }

    addMsg('âš™ï¸ Parsing workflow...', 'info');

    const workflow = window.kaiWorkflow.parseWorkflow(workflowText);

    if (!workflow.actions || workflow.actions.length === 0) {
        addMsg('âŒ No valid actions found', 'error');
        return true;
    }

    addMsg(`ðŸŽ¬ Running ${workflow.actions.length} step(s)...`, 'info');

    try {
        const result = await window.kaiWorkflow.executeWorkflow(workflow);

        const successCount = result.results.filter(r => r.success).length;
        addMsg(`âœ… Workflow complete: ${successCount}/${result.total} steps succeeded`, 'success');

        // Show any errors
        result.results.forEach((r, i) => {
            if (!r.success) {
                addMsg(`  âŒ Step ${i + 1} failed: ${r.error}`, 'error');
            }
        });

        speak(`Workflow completed, ${successCount} steps succeeded`);
    } catch (error) {
        addMsg(`âŒ Workflow error: ${error.message}`, 'error');
    }

    return true;
}

async function handleSaveWorkflow(name) {
    if (!window.kaiWorkflow) {
        addMsg('âŒ Workflow engine not loaded', 'error');
        return true;
    }

    if (!name) {
        addMsg('âŒ Please provide a name: "save workflow my_workflow"', 'error');
        return true;
    }

    // Get the last executed workflow or ask user to define
    const lastWorkflow = window.kaiWorkflow.currentWorkflow;

    if (!lastWorkflow) {
        addMsg('âŒ No workflow to save. Run a workflow first.', 'error');
        return true;
    }

    lastWorkflow.name = name;
    const id = window.kaiWorkflow.saveWorkflow(lastWorkflow);

    addMsg(`âœ… Saved workflow: "${name}" (${lastWorkflow.actions.length} steps)`, 'success');
    speak(`Workflow ${name} saved`);

    return true;
}

async function handleListWorkflows() {
    if (!window.kaiWorkflow) {
        addMsg('âŒ Workflow engine not loaded', 'error');
        return true;
    }

    await window.kaiWorkflow.loadWorkflows();
    const workflows = window.kaiWorkflow.workflows;

    if (workflows.length === 0) {
        addMsg('ðŸ“‹ No saved workflows', 'info');
        addMsg('ðŸ’¡ Create one with: workflow: fill email, click next', 'info');
        return true;
    }

    addMsg(`ðŸ“‹ ${workflows.length} saved workflow(s):`, 'info');
    workflows.forEach((w, i) => {
        addMsg(`  ${i + 1}. ${w.name} (${w.actions.length} steps)`, 'info');
    });

    return true;
}

