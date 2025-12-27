// KAI Extension - Background Service Worker (BULLETPROOF EDITION)
// ================================================================
// Handles ALL API calls to bypass CORS restrictions

console.log('[KAI BG] ⚡ Service worker started');

const API_URLS = [
    'http://localhost:5000/api/v1',
    'https://kai-backend-r8bc.onrender.com/api/v1'
];

// ==================== API HELPER ====================

async function makeApiCall(endpoint, options = {}) {
    const method = options.method || 'GET';
    const body = options.body;

    for (const baseUrl of API_URLS) {
        try {
            const fetchOptions = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };

            if (body && method !== 'GET') {
                fetchOptions.body = typeof body === 'string' ? body : JSON.stringify(body);
            }

            const url = endpoint.startsWith('/') ? `${baseUrl}${endpoint}` : `${baseUrl}/${endpoint}`;
            console.log(`[KAI BG] API Call: ${method} ${url}`);

            const response = await fetch(url, fetchOptions);

            if (response.ok) {
                const data = await response.json();
                console.log('[KAI BG] ✅ API Success:', data);
                return data;
            } else {
                console.log(`[KAI BG] ⚠️ API ${response.status} from ${baseUrl}`);
            }
        } catch (error) {
            console.log(`[KAI BG] ❌ API Error from ${baseUrl}:`, error.message);
        }
    }

    throw new Error('All API endpoints failed');
}

// ==================== MESSAGE HANDLER ====================

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[KAI BG] Message received:', request.action);

    // Handle async operations
    handleMessage(request, sender)
        .then(response => {
            console.log('[KAI BG] Sending response:', response);
            sendResponse(response);
        })
        .catch(error => {
            console.error('[KAI BG] Error:', error);
            sendResponse({ success: false, error: error.message });
        });

    return true; // Keep channel open for async
});

async function handleMessage(request, sender) {
    const { action } = request;

    switch (action) {
        case 'ping':
            return { status: 'pong', operatorMode: true };

        case 'saveAuth':
            await chrome.storage.local.set({ firebaseUser: request.user });
            console.log('[KAI BG] Auth saved:', request.user?.email);
            return { success: true };

        case 'getUser':
            const userResult = await chrome.storage.local.get(['firebaseUser']);
            return { user: userResult.firebaseUser || null };

        case 'getProfile':
            return await getProfileFromBackend(request.user_id);

        case 'operatorAnalyze':
            return await analyzeDOM(request.dom, request.profile, request.query);

        case 'operatorExecute':
            return await reportExecution(request.actions, request.results, request.url);

        case 'chat':
            return await sendChat(request.query, request.user_id);

        // ==================== BROWSER AUTOMATION ====================

        case 'openTab':
            const newTab = await chrome.tabs.create({ url: request.url, active: request.active !== false });
            return { success: true, tabId: newTab.id, message: `Opened: ${request.url}` };

        case 'closeTab':
            if (request.tabId) {
                await chrome.tabs.remove(request.tabId);
            } else if (sender?.tab?.id) {
                await chrome.tabs.remove(sender.tab.id);
            }
            return { success: true, message: 'Tab closed' };

        case 'navigate':
            const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (activeTab) {
                await chrome.tabs.update(activeTab.id, { url: request.url });
            }
            return { success: true, message: `Navigating to: ${request.url}` };

        case 'goBack':
            await chrome.tabs.goBack();
            return { success: true, message: 'Going back' };

        case 'goForward':
            await chrome.tabs.goForward();
            return { success: true, message: 'Going forward' };

        case 'refresh':
            const [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (currentTab) {
                await chrome.tabs.reload(currentTab.id);
            }
            return { success: true, message: 'Page refreshed' };

        case 'getTabs':
            const allTabs = await chrome.tabs.query({ currentWindow: true });
            return {
                success: true,
                tabs: allTabs.map(t => ({ id: t.id, title: t.title?.substring(0, 40), url: t.url }))
            };

        case 'switchTab':
            if (request.tabId) {
                await chrome.tabs.update(request.tabId, { active: true });
            } else if (request.index !== undefined) {
                const tabs = await chrome.tabs.query({ currentWindow: true });
                if (request.index >= 0 && request.index < tabs.length) {
                    await chrome.tabs.update(tabs[request.index].id, { active: true });
                }
            }
            return { success: true, message: 'Switched tab' };

        case 'newWindow':
            await chrome.windows.create({ url: request.url || 'about:blank' });
            return { success: true, message: 'New window opened' };

        // ==================== MACROS & TEMPLATES ====================

        case 'getMacros':
            return await getMacros(request.user_id);

        case 'saveMacro':
            return await saveMacro(request.user_id, request.macro);

        case 'deleteMacro':
            return await deleteMacro(request.user_id, request.macro_id);

        case 'getTemplates':
            return await getTemplates(request.user_id);

        case 'saveTemplate':
            return await saveTemplate(request.user_id, request.template);

        case 'deleteTemplate':
            return await deleteTemplate(request.user_id, request.template_id);

        case 'getMemory':
            return await getExtensionMemory(request.user_id);

        case 'updateMemory':
            return await updateExtensionMemory(request.user_id, request.data);

        case 'trackAction':
            return await trackAction(request.user_id, request.action, request.site, request.details);

        default:
            return { success: false, error: `Unknown action: ${action}` };
    }
}

// ==================== PROFILE FETCHING ====================

async function getProfileFromBackend(userId) {
    if (!userId) {
        return { success: false, error: 'No user_id provided' };
    }

    try {
        const data = await makeApiCall(`/users/profile?user_id=${userId}`);

        if (data.success && data.profile) {
            // Store in chrome.storage for caching
            await chrome.storage.local.set({ userProfile: data.profile });
            return { success: true, profile: data.profile };
        }

        return { success: false, error: 'No profile in response' };
    } catch (error) {
        // Try to return cached profile
        const cached = await chrome.storage.local.get(['userProfile']);
        if (cached.userProfile) {
            console.log('[KAI BG] Using cached profile');
            return { success: true, profile: cached.userProfile, cached: true };
        }

        return { success: false, error: error.message };
    }
}

// ==================== DOM ANALYSIS ====================

async function analyzeDOM(dom, profile, query) {
    try {
        const data = await makeApiCall('/operator/analyze', {
            method: 'POST',
            body: { dom, profile, query }
        });

        return {
            success: true,
            actions: data.actions || [],
            summary: data.summary || '',
            page_type: data.page_type || 'unknown'
        };
    } catch (error) {
        // Return fallback actions based on profile
        console.log('[KAI BG] AI analysis failed, using fallback');
        return generateFallbackActions(dom, profile);
    }
}

function generateFallbackActions(dom, profile) {
    const actions = [];
    const usedSelectors = new Set(); // Prevent duplicate fills

    // Get all form fields
    const allFields = [];
    if (dom.forms) {
        dom.forms.forEach(form => {
            if (form.fields) allFields.push(...form.fields);
        });
    }
    if (dom.inputs) {
        allFields.push(...dom.inputs);
    }

    // Smart field matching with priority order
    for (const field of allFields) {
        if (!field.selector || !field.visible) continue;
        if (usedSelectors.has(field.selector)) continue;

        const label = (field.label || field.placeholder || field.name || field['aria-label'] || '').toLowerCase();
        const fieldType = (field.type || '').toLowerCase();
        let value = '';
        let matchType = '';

        // STRICT EMAIL matching - ONLY for email fields
        if (fieldType === 'email' || (label.includes('email') && !label.includes('name'))) {
            value = profile.email || '';
            matchType = 'email';
        }
        // STRICT PHONE matching - ONLY for phone fields
        else if (fieldType === 'tel' || label.includes('phone') || label.includes('mobile') || label.includes('telephone')) {
            value = profile.phone || '';
            matchType = 'phone';
        }
        // First name matching
        else if (label.includes('first') && (label.includes('name') || label.includes('given'))) {
            value = profile.firstName || (profile.name || '').split(' ')[0] || '';
            matchType = 'firstName';
        }
        // Last name matching
        else if (label.includes('last') && (label.includes('name') || label.includes('family') || label.includes('surname'))) {
            value = profile.lastName || (profile.name || '').split(' ').slice(1).join(' ') || '';
            matchType = 'lastName';
        }
        // Full name matching - EXCLUDE if it contains "email", "user", "account"
        else if (label.includes('name') && !label.includes('email') && !label.includes('user') && !label.includes('account') && !label.includes('company')) {
            value = profile.name || '';
            matchType = 'name';
        }
        // Address matching
        else if ((label.includes('address') || label.includes('street')) && !label.includes('email')) {
            value = profile.address || '';
            matchType = 'address';
        }
        // City matching
        else if (label.includes('city') || label.includes('town')) {
            value = profile.city || '';
            matchType = 'city';
        }
        // State matching
        else if (label.includes('state') || label.includes('province') || label.includes('region')) {
            value = profile.state || '';
            matchType = 'state';
        }
        // Zip matching
        else if (label.includes('zip') || label.includes('postal') || label.includes('pin')) {
            value = profile.zip || '';
            matchType = 'zip';
        }
        // Country matching
        else if (label.includes('country') || label.includes('nation')) {
            value = profile.country || '';
            matchType = 'country';
        }

        // Only add action if we have a value AND a match type
        if (value && matchType) {
            usedSelectors.add(field.selector);
            actions.push({
                type: 'fill',
                selector: field.selector,
                value: value,
                description: `Fill ${matchType}: ${value.substring(0, 20)}...`
            });
        }
    }

    console.log('[KAI BG] Fallback generated', actions.length, 'actions');
    return {
        success: true,
        actions,
        summary: `Smart match: ${actions.length} fields`,
        fallback: true
    };
}

// ==================== EXECUTION REPORTING ====================

async function reportExecution(actions, results, url) {
    try {
        await makeApiCall('/operator/execute', {
            method: 'POST',
            body: { actions, results, url }
        });
        return { success: true };
    } catch (error) {
        // Non-critical, just log
        console.log('[KAI BG] Execution report failed (non-critical)');
        return { success: true }; // Don't fail for this
    }
}

// ==================== CHAT ====================

async function sendChat(query, userId) {
    try {
        const data = await makeApiCall('/chat', {
            method: 'POST',
            body: { query, user_id: userId || 'extension' }
        });

        return {
            success: true,
            response: data.response || data.text || 'Response received'
        };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ==================== MACROS ====================

async function getMacros(userId) {
    if (!userId) return { success: false, error: 'No user ID' };

    // Try cloud first, fall back to local
    try {
        const data = await makeApiCall(`/extension/macros?user_id=${userId}`);
        if (data.success) {
            // Cache locally
            await chrome.storage.local.set({ cachedMacros: data.macros });
            return { success: true, macros: data.macros };
        }
    } catch (e) {
        console.log('[KAI BG] Using cached macros');
    }

    // Fall back to local
    const local = await chrome.storage.local.get(['cachedMacros']);
    return { success: true, macros: local.cachedMacros || [], cached: true };
}

async function saveMacro(userId, macro) {
    if (!userId || !macro) return { success: false, error: 'User ID and macro required' };

    try {
        const data = await makeApiCall('/extension/macros', {
            method: 'POST',
            body: { user_id: userId, macro }
        });
        return { success: true, macro_id: data.macro_id };
    } catch (e) {
        // Save locally as fallback
        const local = await chrome.storage.local.get(['cachedMacros']);
        const macros = local.cachedMacros || [];
        macro.id = macro.id || `local_${Date.now()}`;
        macros.push(macro);
        await chrome.storage.local.set({ cachedMacros: macros });
        return { success: true, macro_id: macro.id, cached: true };
    }
}

async function deleteMacro(userId, macroId) {
    if (!userId || !macroId) return { success: false, error: 'User ID and macro ID required' };

    try {
        await makeApiCall(`/extension/macros/${macroId}?user_id=${userId}`, { method: 'DELETE' });
        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

// ==================== TEMPLATES ====================

async function getTemplates(userId) {
    if (!userId) return { success: false, error: 'No user ID' };

    try {
        const data = await makeApiCall(`/extension/templates?user_id=${userId}`);
        if (data.success) {
            await chrome.storage.local.set({ cachedTemplates: data.templates });
            return { success: true, templates: data.templates };
        }
    } catch (e) {
        console.log('[KAI BG] Using cached templates');
    }

    const local = await chrome.storage.local.get(['cachedTemplates']);
    return { success: true, templates: local.cachedTemplates || [], cached: true };
}

async function saveTemplate(userId, template) {
    if (!userId || !template) return { success: false, error: 'User ID and template required' };

    try {
        const data = await makeApiCall('/extension/templates', {
            method: 'POST',
            body: { user_id: userId, template }
        });
        return { success: true, template_id: data.template_id };
    } catch (e) {
        // Save locally
        const local = await chrome.storage.local.get(['cachedTemplates']);
        const templates = local.cachedTemplates || [];
        template.id = template.id || `local_${Date.now()}`;
        templates.push(template);
        await chrome.storage.local.set({ cachedTemplates: templates });
        return { success: true, template_id: template.id, cached: true };
    }
}

async function deleteTemplate(userId, templateId) {
    if (!userId || !templateId) return { success: false, error: 'User ID and template ID required' };

    try {
        await makeApiCall(`/extension/templates/${templateId}?user_id=${userId}`, { method: 'DELETE' });
        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

// ==================== MEMORY ====================

async function getExtensionMemory(userId) {
    if (!userId) return { success: false, error: 'No user ID' };

    try {
        const data = await makeApiCall(`/extension/memory?user_id=${userId}`);
        if (data.success) {
            await chrome.storage.local.set({ extensionMemory: data.memory });
            return { success: true, memory: data.memory };
        }
    } catch (e) {
        console.log('[KAI BG] Using cached memory');
    }

    const local = await chrome.storage.local.get(['extensionMemory']);
    return { success: true, memory: local.extensionMemory || {}, cached: true };
}

async function updateExtensionMemory(userId, data) {
    if (!userId) return { success: false, error: 'No user ID' };

    try {
        await makeApiCall('/extension/memory', {
            method: 'POST',
            body: { user_id: userId, ...data }
        });
        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

async function trackAction(userId, action, site, details) {
    if (!userId || !action) return { success: false, error: 'User ID and action required' };

    try {
        await makeApiCall('/extension/track-action', {
            method: 'POST',
            body: { user_id: userId, action, site, details }
        });
        return { success: true };
    } catch (e) {
        // Non-critical, don't fail
        console.log('[KAI BG] Action tracking failed (non-critical)');
        return { success: true };
    }
}

// ==================== LIFECYCLE ====================

chrome.runtime.onInstalled.addListener(() => {
    console.log('[KAI BG] ⚡ Extension installed - Operator Mode Ready');
});

// Keep service worker alive
chrome.runtime.onStartup.addListener(() => {
    console.log('[KAI BG] ⚡ Browser started');
});
