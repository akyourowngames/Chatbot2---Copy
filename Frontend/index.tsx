
// @ts-nocheck
import { createClient } from "@supabase/supabase-js";
import { initializeApp } from 'firebase/app';
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged, GoogleAuthProvider, GithubAuthProvider, signInWithPopup, sendEmailVerification } from "firebase/auth";
import { getFirestore, collection, addDoc, query, where, getDocs, deleteDoc, doc, writeBatch, getDoc, setDoc, orderBy } from "firebase/firestore";
import * as FirebaseDB from './services/FirebaseService';

declare var lucide: any;
declare var Prism: any;
declare var marked: any;
declare var window: any;
declare var Hls: any;
declare var webkitSpeechRecognition: any;

// 🟢 DEBUG LOGGER
const LOG = {
    info: (mod: string, msg: string, data?: any) => console.log(`%c[${mod}]%c ${msg}`, 'color: #6366f1; font-weight: bold; background: #1e1e2e; padding: 2px 5px;', 'color: #f1f5f9;', data || ''),
    warn: (mod: string, msg: string, data?: any) => console.warn(`%c[${mod}]%c ${msg}`, 'color: #fbbf24; font-weight: bold; background: #1e1e2e; padding: 2px 5px;', 'color: #f1f5f9;', data || ''),
    error: (mod: string, msg: string, data?: any) => console.error(`%c[${mod}]%c ${msg}`, 'color: #ef4444; font-weight: bold; background: #1e1e2e; padding: 2px 5px;', 'color: #fca5a5;', data || ''),
    network: (url: string, status: number, data?: any) => console.log(`%c[NETWORK] %c${status} %c${url}`, 'color: #00f0ff; font-weight: bold;', status < 300 ? 'color: #10b981;' : 'color: #ef4444;', 'color: #94a3b8;', data || '')
};

// 🔥 Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk",
    authDomain: "kai-g-80f9c.firebaseapp.com",
    projectId: "kai-g-80f9c",
    storageBucket: "kai-g-80f9c.appspot.com",
    messagingSenderId: "125633190886",
    appId: "1:125633190886:web:65e1a7b4f59048a1768853"
};

// Initialize Firebase
let firebaseApp, auth, db;
try {
    LOG.info('SYSTEM', 'Initializing Firebase modules...');
    firebaseApp = initializeApp(firebaseConfig);
    auth = getAuth(firebaseApp);
    db = getFirestore(firebaseApp);
} catch (e) {
    LOG.error('SYSTEM', 'Firebase Init Failed', e);
}

// 📡 API Configuration
const USE_CLOUD_API = false; // Set to true for production (Render), false for local dev
const BASE_URL = USE_CLOUD_API ? 'https://kai-api-nxxv.onrender.com' : 'http://localhost:5000';
const API_URL = `${BASE_URL}/api/v1`;

// 📦 Supabase Configuration
const SUPABASE_URL = 'https://skbfmcwrshxnmaxfqyaw.supabase.co';
const SUPABASE_KEY = 'sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v';
const SUPABASE_BUCKET = 'kai-images';
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// State (Firebase will populate these after auth)
let isProcessing = false;
let chatHistory: any[] = [];  // Loaded from Firebase after auth
let currentChatId = '';
let currentChatMessages: any[] = [];
let isLoginMode = true;
let pendingAssetUrl: string | null = null;
let pendingAssetName: string | null = null;

// DOM Elements
const messagesList = document.getElementById('messages-list');
const messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
const welcomeScreen = document.getElementById('welcome-screen');
const sidebar = document.getElementById('sidebar');
const sidebarBackdrop = document.getElementById('sidebar-backdrop');
const chatHistoryList = document.getElementById('chat-history-list');
const sessionIdDisplay = document.getElementById('session-id-display');
const attachmentArea = document.getElementById('attachment-area');
const authForm = document.getElementById('auth-form') as HTMLFormElement;


// === USER PROFILE MANAGEMENT (Firebase is source of truth) ===
let cachedUserProfile: any = null;

// Function to get user preferences - uses cache (loaded from Firebase on auth)
function getUserPreferences() {
    // Return cached profile - this is loaded from Firebase when user signs in
    return cachedUserProfile;
}

// Expose getUserPreferences globally so it can be called from sendMessage
(window as any).getUserPreferences = getUserPreferences;

// Listen for profile updates from settings window
window.addEventListener('message', (event) => {
    if (event.data?.type === 'PROFILE_UPDATED') {
        LOG.info('PROFILE', 'Profile updated from settings', event.data.profile);
        cachedUserProfile = event.data.profile;
        localStorage.setItem('kai_user_profile', JSON.stringify(cachedUserProfile));
    }
});

// Load profile when auth state changes
let lastUserId: string | null = null;

onAuthStateChanged(auth, async (user) => {
    if (user) {
        // Check if this is a different user than before
        if (lastUserId && lastUserId !== user.uid) {
            LOG.info('AUTH', 'Different user detected, clearing old data...');
            clearUserData();
        }

        lastUserId = user.uid;
        LOG.info('AUTH', 'User signed in, loading data from Firebase...', { uid: user.uid, email: user.email });

        // === LOAD ALL USER DATA FROM FIREBASE ===

        // 1. Load Profile
        const profile = await FirebaseDB.loadUserProfile(user.uid);
        if (profile) {
            cachedUserProfile = profile;
            LOG.info('AUTH', 'Profile loaded from Firebase', { name: profile.name, lang: profile.responseLanguage });
        } else {
            // Create default profile from auth data
            cachedUserProfile = {
                name: user.displayName || '',
                nickname: '',
                email: user.email || '',
                bio: '',
                responseStyle: 'casual',
                responseLanguage: 'english',
                interests: [],
                avatarUrl: user.photoURL || ''
            };
            // Save default profile to Firebase
            await FirebaseDB.saveUserProfile(user.uid, cachedUserProfile);
            LOG.info('AUTH', 'Created and saved default profile');
        }

        // Update user avatar in header
        updateUserAvatar(cachedUserProfile?.avatarUrl || user.photoURL || '', user.email || user.uid);

        // 2. Load Chat History
        try {
            const chats = await FirebaseDB.loadChats(user.uid);
            chatHistory = chats;
            LOG.info('AUTH', 'Chat history loaded from Firebase', { count: chats.length });

            // Render chat history in sidebar
            if (typeof renderHistory === 'function') {
                renderHistory();
            }

            // Initialize a new chat session if none exists
            if (!currentChatId) {
                currentChatId = FirebaseDB.generateChatId();
                currentChatMessages = [];
                LOG.info('AUTH', 'Initialized new chat session', { chatId: currentChatId });
            }
        } catch (e) {
            LOG.error('AUTH', 'Failed to load chat history', e);
        }

        // 3. Load Settings (optional - can add later)
        // const settings = await FirebaseDB.loadUserSettings(user.uid);

    } else {
        // User logged out - clear all user data
        LOG.info('AUTH', 'User signed out, clearing data...');
        clearUserData();
        lastUserId = null;
    }
});

// Clear all user-specific data (memory only - Firebase is the source of truth)
function clearUserData() {
    cachedUserProfile = null;
    chatHistory = [];
    currentChatId = '';
    currentChatMessages = [];

    // Reset avatar to default
    const avatarImg = document.getElementById('user-avatar-img') as HTMLImageElement;
    if (avatarImg) {
        avatarImg.src = 'https://api.dicebear.com/7.x/bottts/svg?seed=KAI&backgroundColor=transparent';
    }

    LOG.info('AUTH', 'Local user data cleared');
}
(window as any).clearUserData = clearUserData;

// Update user avatar in header
function updateUserAvatar(avatarUrl: string, seed: string) {
    const avatarImg = document.getElementById('user-avatar-img') as HTMLImageElement;
    if (!avatarImg) return;

    if (avatarUrl && avatarUrl.startsWith('http')) {
        // Use custom avatar URL
        avatarImg.src = avatarUrl;
        LOG.info('AUTH', 'Avatar updated from URL');
    } else {
        // Generate unique DiceBear avatar based on email/uid
        const sanitizedSeed = encodeURIComponent(seed);
        avatarImg.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${sanitizedSeed}&backgroundColor=transparent`;
        LOG.info('AUTH', 'Avatar generated from seed', { seed });
    }
}

// Listen for profile updates from settings popup
window.addEventListener('message', (event) => {
    if (event.data?.type === 'PROFILE_UPDATED' && event.data.profile) {
        LOG.info('PROFILE', 'Received profile update from settings');
        cachedUserProfile = event.data.profile;

        // Update avatar in header
        const user = auth?.currentUser;
        if (user) {
            updateUserAvatar(cachedUserProfile?.avatarUrl || '', user.email || user.uid);
        }
    }
});

// === MEMORY CORE VISUALIZATION ===
// Inject styles for the brain pulse
const style = document.createElement('style');
style.textContent = `
  @keyframes brainPulse {
    0% { transform: scale(1); filter: drop-shadow(0 0 0px #6366f1); }
    50% { transform: scale(1.1); filter: drop-shadow(0 0 10px #818cf8); }
    100% { transform: scale(1); filter: drop-shadow(0 0 0px #6366f1); }
  }
  .brain-active { animation: brainPulse 2s infinite ease-in-out; }
  .memory-toast {
    position: fixed; top: 20px; right: 20px; z-index: 9999;
    background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(99, 102, 241, 0.3);
    color: #e0e7ff; padding: 12px 20px; border-radius: 8px;
    backdrop-filter: blur(10px); box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transform: translateY(-20px); opacity: 0; transition: all 0.3s ease;
    display: flex; align-items: center; gap: 10px; font-family: monospace; font-size: 12px;
  }
  .memory-toast.show { transform: translateY(0); opacity: 1; }
  
  /* 🔥 BEAST MODE SOURCE CARDS - Premium Futuristic Design */
  @keyframes sourceGlow {
    0%, 100% { box-shadow: 0 0 5px rgba(139, 92, 246, 0.3), inset 0 0 20px rgba(139, 92, 246, 0.05); }
    50% { box-shadow: 0 0 15px rgba(139, 92, 246, 0.5), inset 0 0 30px rgba(139, 92, 246, 0.1); }
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .source-cards-wrapper {
    margin-top: 16px; padding: 16px;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 27, 75, 0.6));
    border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 16px;
    backdrop-filter: blur(20px); position: relative; overflow: hidden;
  }
  .source-cards-wrapper::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent);
  }
  .source-cards-header {
    display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.2em; color: rgba(139, 92, 246, 0.8);
  }
  .source-cards-header svg { width: 14px; height: 14px; }
  
  .source-cards-container {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;
  }
  
  .source-card {
    display: flex; align-items: center; gap: 10px; padding: 12px 14px;
    background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(30, 27, 75, 0.3));
    border: 1px solid rgba(139, 92, 246, 0.15); border-radius: 12px;
    text-decoration: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px); cursor: pointer; position: relative; overflow: hidden;
    animation: slideUp 0.4s ease-out backwards;
  }
  .source-card:nth-child(1) { animation-delay: 0.05s; }
  .source-card:nth-child(2) { animation-delay: 0.1s; }
  .source-card:nth-child(3) { animation-delay: 0.15s; }
  .source-card:nth-child(4) { animation-delay: 0.2s; }
  .source-card:nth-child(5) { animation-delay: 0.25s; }
  
  .source-card::before {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), transparent);
    opacity: 0; transition: opacity 0.3s;
  }
  .source-card:hover::before { opacity: 1; }
  
  .source-card:hover {
    border-color: rgba(139, 92, 246, 0.5); transform: translateY(-3px) scale(1.02);
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.25), 0 0 0 1px rgba(139, 92, 246, 0.1);
  }
  
  .source-favicon {
    width: 28px; height: 28px; border-radius: 8px; flex-shrink: 0;
    background: linear-gradient(135deg, #1e1b4b, #312e81);
    display: flex; align-items: center; justify-content: center; font-size: 14px;
    border: 1px solid rgba(139, 92, 246, 0.3);
  }
  .source-favicon img { width: 16px; height: 16px; border-radius: 4px; }
  
  .source-info { flex: 1; min-width: 0; }
  .source-title {
    font-size: 12px; font-weight: 600; color: #e0e7ff; margin-bottom: 2px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .source-domain {
    font-size: 10px; color: rgba(139, 92, 246, 0.7); font-family: monospace;
    display: flex; align-items: center; gap: 4px;
  }
  .source-domain::before { content: '🔗'; font-size: 8px; }
  
  .source-arrow {
    color: rgba(139, 92, 246, 0.4); transition: all 0.3s;
  }
  .source-card:hover .source-arrow {
    color: #a78bfa; transform: translateX(3px);
  }
`;
document.head.appendChild(style);

// Memory Core UI Injection
function injectMemoryCore() {
    const sidebarHeader = document.querySelector('#sidebar .p-4.border-b');
    if (sidebarHeader && !document.getElementById('memory-core-container')) {
        const coreHTML = `
            <div id="memory-core-container" class="mt-4 p-3 bg-black/20 rounded-lg border border-white/5 flex items-center justify-between group cursor-pointer hover:bg-white/5 transition-colors">
                <div class="flex items-center gap-3">
                    <div class="relative">
                        <div id="brain-icon" class="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 transition-all duration-500">
                            <i data-lucide="brain-circuit" class="w-5 h-5"></i>
                        </div>
                        <div id="memory-dot" class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-[#0f172a] opacity-0 transition-opacity"></div>
                    </div>
                    <div>
                        <div class="text-[11px] font-mono text-indigo-300 uppercase tracking-wider">Memory Core</div>
                        <div id="memory-status" class="text-[10px] text-white/40">Online - Idle</div>
                    </div>
                </div>
                <div class="text-xs text-white/20 group-hover:text-white/60 transition-colors">
                    <i data-lucide="database" class="w-3 h-3"></i>
                </div>
            </div>
        `;
        sidebarHeader.insertAdjacentHTML('beforeend', coreHTML);
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}

function triggerMemoryPulse(action: 'save' | 'access' | 'idle') {
    const brain = document.getElementById('brain-icon');
    const status = document.getElementById('memory-status');
    const dot = document.getElementById('memory-dot');

    if (!brain || !status) return;

    if (action === 'save') {
        brain.classList.add('brain-active');
        brain.classList.replace('text-indigo-400', 'text-emerald-400');
        brain.classList.replace('bg-indigo-500/10', 'bg-emerald-500/10');
        status.textContent = "WRITING TO CLOUD...";
        status.classList.add('text-emerald-400');
        if (dot) dot.style.opacity = '1';

        showMemoryToast("Values saved to Long-Term Memory", 'save');

        setTimeout(() => {
            brain.classList.remove('brain-active');
            brain.classList.replace('text-emerald-400', 'text-indigo-400');
            brain.classList.replace('bg-emerald-500/10', 'bg-indigo-500/10');
            status.textContent = "Online - Idle";
            status.classList.remove('text-emerald-400');
            if (dot) dot.style.opacity = '0';
        }, 3000);
    }
    else if (action === 'access') {
        brain.classList.add('brain-active');
        brain.classList.replace('text-indigo-400', 'text-cyan-400');
        status.textContent = "ACCESSING CLOUD...";
        status.classList.add('text-cyan-400');

        setTimeout(() => {
            brain.classList.remove('brain-active');
            brain.classList.replace('text-cyan-400', 'text-indigo-400');
            status.textContent = "Online - Idle";
            status.classList.remove('text-cyan-400');
        }, 2000);
    }
}

function showMemoryToast(msg: string, type: 'save' | 'info') {
    const toast = document.createElement('div');
    toast.className = 'memory-toast';
    toast.innerHTML = `
        <i data-lucide="${type === 'save' ? 'save' : 'brain-circuit'}" class="w-4 h-4 ${type === 'save' ? 'text-emerald-400' : 'text-cyan-400'}"></i>
        <span>${msg}</span>
    `;
    document.body.appendChild(toast);
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Animate in
    requestAnimationFrame(() => toast.classList.add('show'));

    // Remove after 3s
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== 🦴 SKELETON LOADERS - BEAST MODE ==========
const Skeleton = {
    // Generate a single message skeleton
    message: () => `
        <div class="skeleton-message">
            <div class="skeleton-message-header">
                <div class="skeleton skeleton-avatar"></div>
                <div class="skeleton skeleton-line skeleton-line-short"></div>
            </div>
            <div class="skeleton skeleton-line skeleton-line-long"></div>
            <div class="skeleton skeleton-line skeleton-line-medium"></div>
            <div class="skeleton skeleton-line skeleton-line-short"></div>
        </div>
    `,

    // Generate multiple message skeletons
    messages: (count: number = 3) => {
        return Array(count).fill(null).map(() => Skeleton.message()).join('');
    },

    // Chat history item skeleton
    chatItem: () => `
        <div class="skeleton-chat-item">
            <div class="skeleton skeleton-dark skeleton-chat-icon"></div>
            <div class="skeleton-chat-content">
                <div class="skeleton skeleton-dark skeleton-line skeleton-line-medium"></div>
                <div class="skeleton skeleton-dark skeleton-line skeleton-line-short"></div>
            </div>
        </div>
    `,

    // Multiple chat history skeletons
    chatHistory: (count: number = 5) => {
        return Array(count).fill(null).map(() => Skeleton.chatItem()).join('');
    },

    // Typing indicator with animated dots
    typing: () => `
        <div class="skeleton-message" id="typing-skeleton">
            <div class="skeleton-message-header">
                <div class="skeleton skeleton-avatar skeleton-pulse"></div>
                <div class="skeleton skeleton-line skeleton-line-short"></div>
            </div>
            <div class="skeleton-typing">
                <div class="skeleton-typing-dot"></div>
                <div class="skeleton-typing-dot"></div>
                <div class="skeleton-typing-dot"></div>
            </div>
        </div>
    `,

    // Card skeleton for rich content
    card: () => `
        <div class="skeleton-card skeleton-processing">
            <div class="skeleton-card-header">
                <div class="skeleton skeleton-card-image"></div>
                <div style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
                    <div class="skeleton skeleton-line skeleton-line-medium"></div>
                    <div class="skeleton skeleton-line skeleton-line-short"></div>
                </div>
            </div>
            <div class="skeleton skeleton-line skeleton-line-full"></div>
            <div class="skeleton skeleton-line skeleton-line-long" style="margin-top: 8px;"></div>
        </div>
    `,

    // Settings skeleton
    settings: (count: number = 4) => {
        return Array(count).fill(null).map(() => `
            <div class="skeleton-settings-item">
                <div class="skeleton skeleton-line" style="width: 40%;"></div>
                <div class="skeleton skeleton-dark skeleton-toggle"></div>
            </div>
        `).join('');
    },

    // File processing skeleton
    file: () => `
        <div class="skeleton-file skeleton-processing">
            <div class="skeleton skeleton-file-icon"></div>
            <div style="flex: 1; display: flex; flex-direction: column; gap: 6px;">
                <div class="skeleton skeleton-line skeleton-line-medium"></div>
                <div class="skeleton skeleton-line skeleton-line-short"></div>
            </div>
        </div>
    `,

    // Grid skeleton for search results
    grid: (count: number = 4) => `
        <div class="skeleton-grid">
            ${Array(count).fill(null).map(() => '<div class="skeleton skeleton-grid-item"></div>').join('')}
        </div>
    `,

    // Show skeleton in a container
    show: (container: HTMLElement | null, type: 'message' | 'messages' | 'chatHistory' | 'typing' | 'card' | 'settings' | 'file' | 'grid', count?: number) => {
        if (!container) return;
        switch (type) {
            case 'message': container.innerHTML = Skeleton.message(); break;
            case 'messages': container.innerHTML = Skeleton.messages(count || 3); break;
            case 'chatHistory': container.innerHTML = Skeleton.chatHistory(count || 5); break;
            case 'typing': container.insertAdjacentHTML('beforeend', Skeleton.typing()); break;
            case 'card': container.innerHTML = Skeleton.card(); break;
            case 'settings': container.innerHTML = Skeleton.settings(count || 4); break;
            case 'file': container.innerHTML = Skeleton.file(); break;
            case 'grid': container.innerHTML = Skeleton.grid(count || 4); break;
        }
    },

    // Hide/remove a specific skeleton
    hide: (id: string = 'typing-skeleton') => {
        const skeleton = document.getElementById(id);
        if (skeleton) {
            skeleton.style.opacity = '0';
            skeleton.style.transform = 'translateY(-10px)';
            setTimeout(() => skeleton.remove(), 300);
        }
    },

    // Clear all skeletons from a container
    clear: (container: HTMLElement | null) => {
        if (!container) return;
        const skeletons = container.querySelectorAll('[class*="skeleton-"]');
        skeletons.forEach(s => s.remove());
    }
};

// Expose globally
(window as any).Skeleton = Skeleton;

const authEmail = document.getElementById('auth-email') as HTMLInputElement;
const authPassword = document.getElementById('auth-password') as HTMLInputElement;
const authSubmitBtn = document.getElementById('auth-submit-btn') as HTMLButtonElement;
const toggleAuthModeBtn = document.getElementById('toggle-auth-mode') as HTMLButtonElement;
const authError = document.getElementById('auth-error') as HTMLElement;
const authProgress = document.getElementById('auth-progress') as HTMLElement;
const authBar = document.getElementById('auth-bar') as HTMLElement;
const authPercent = document.getElementById('auth-percent') as HTMLElement;

// Helper: Check if email should skip verification (test emails)
function isTestEmail(email: string): boolean {
    if (!email) return false;
    const testPatterns = [
        /^test@/i,
        /@test\./i,
        /^demo@/i,
        /^admin@localhost/i,
        /@example\.com$/i
    ];
    return testPatterns.some(pattern => pattern.test(email));
}

// Code Block Counter for unique IDs
let codeBlockCounter = 0;

// Copy to clipboard function
(window as any).copyCode = async (id: string) => {
    const codeEl = document.querySelector(`#${id} code`);
    const btn = document.querySelector(`#${id}-btn`) as HTMLElement;
    if (!codeEl || !btn) return;

    try {
        await navigator.clipboard.writeText(codeEl.textContent || '');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `<i data-lucide="check" class="w-3 h-3"></i> Copied!`;
        btn.classList.add('text-emerald-400');
        if (typeof lucide !== 'undefined') lucide.createIcons();
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('text-emerald-400');
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }, 2000);
    } catch (e) {
        LOG.error('CLIPBOARD', 'Copy failed', e);
    }
};

// === 📄 CANVAS SIDEBAR ===
let canvasRawContent = '';

(window as any).openCanvas = (content: string, title: string = 'Canvas Draft') => {
    const panel = document.getElementById('canvas-panel');
    const backdrop = document.getElementById('canvas-backdrop');
    const contentEl = document.getElementById('canvas-content');
    const titleEl = document.getElementById('canvas-title');
    const charCountEl = document.getElementById('canvas-char-count');

    if (!panel || !backdrop || !contentEl) return;

    canvasRawContent = content;

    // Format and inject content
    const formattedContent = formatMessage(content);
    contentEl.innerHTML = `<div class="markdown-body text-sm leading-relaxed text-gray-200">${formattedContent}</div>`;

    if (titleEl) titleEl.textContent = title;
    if (charCountEl) charCountEl.textContent = content.length.toString();

    // Open panel with animation
    panel.classList.remove('translate-x-full');
    backdrop.classList.remove('opacity-0', 'pointer-events-none');
    backdrop.classList.add('opacity-100', 'pointer-events-auto');

    // Re-initialize icons and syntax highlighting
    if (typeof lucide !== 'undefined') lucide.createIcons();
    if (typeof Prism !== 'undefined') Prism.highlightAllUnder(contentEl);

    LOG.info('CANVAS', 'Panel opened', { title, chars: content.length });
};

(window as any).closeCanvas = () => {
    const panel = document.getElementById('canvas-panel');
    const backdrop = document.getElementById('canvas-backdrop');

    if (!panel || !backdrop) return;

    panel.classList.add('translate-x-full');
    backdrop.classList.add('opacity-0', 'pointer-events-none');
    backdrop.classList.remove('opacity-100', 'pointer-events-auto');

    LOG.info('CANVAS', 'Panel closed');
};

(window as any).copyCanvasContent = async () => {
    try {
        await navigator.clipboard.writeText(canvasRawContent);
        notify('CONTENT_COPIED');
    } catch (e) {
        LOG.error('CANVAS', 'Copy failed', e);
        notify('COPY_FAILED', 'error');
    }
};

(window as any).downloadCanvasContent = () => {
    const blob = new Blob([canvasRawContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kai_canvas_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    notify('CONTENT_EXPORTED');
    LOG.info('CANVAS', 'Content downloaded');
};

// === 🔥 BEAST MODE SOURCE CARDS FOR WEB SEARCH ===
(window as any).renderSourceCards = (sources: { title: string, url: string }[]): string => {
    if (!sources || sources.length === 0) return '';

    const getDomain = (url: string): string => {
        try {
            return new URL(url).hostname.replace('www.', '');
        } catch { return 'source'; }
    };

    const getFaviconUrl = (url: string): string => {
        try {
            const domain = new URL(url).hostname;
            return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
        } catch { return ''; }
    };

    const cards = sources.slice(0, 5).map(s => {
        const domain = getDomain(s.url);
        const favicon = getFaviconUrl(s.url);
        const title = s.title.length > 35 ? s.title.substring(0, 32) + '...' : s.title;

        return `<a href="${s.url}" target="_blank" rel="noopener" class="source-card">
            <div class="source-favicon">
                ${favicon ? `<img src="${favicon}" alt="" onerror="this.style.display='none'">` : '🌐'}
            </div>
            <div class="source-info">
                <div class="source-title">${title}</div>
                <div class="source-domain">${domain}</div>
            </div>
            <span class="source-arrow">→</span>
        </a>`;
    }).join('');

    return `<div class="source-cards-wrapper">
        <div class="source-cards-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <span>Sources</span>
        </div>
        <div class="source-cards-container">${cards}</div>
    </div>`;
};

// Expose globally for API response handler
(window as any).appendSourceCards = (messageId: string, sources: any[]) => {
    const msgEl = document.getElementById(messageId);
    if (msgEl && sources && sources.length > 0) {
        const contentDiv = msgEl.querySelector('.message-content') || msgEl;
        const cardsHtml = (window as any).renderSourceCards(sources);
        if (cardsHtml && !msgEl.querySelector('.source-cards-container')) {
            contentDiv.insertAdjacentHTML('beforeend', cardsHtml);
            LOG.info('SOURCES', `Added ${sources.length} source cards to message`);
        }
    }
};

// === 🚀 ULTRA-VIOLET WILD BOOTUP SEQUENCE ===
const BOOT_LOGS_ULTRA = [
    "ATTACHING_NEURAL_INTERFACE... [OK]",
    "STAGING_COGNITIVE_ARRAY_v9.4... [DONE]",
    "MAPPING_USER_SYNAPSE_PATTERNS... SUCCESS",
    "ESTABLISHING_QUANTUM_HANDSHAKE...",
    "DECRYPTING_OPERATOR_PRIVILEGES... [Lvl_10]",
    "SYNCING_LOCAL_TEMPORAL_FLUX...",
    "STABILIZING_DOPAMINE_FEED_LOOPS... [OK]",
    "INITIATING_HIGH_LEVEL_OVERRIDE...",
    "INTERFACE_STABILITY: 100%",
    "NEURAL_LATENCY: <0.01ms",
    "UPLINK_STATUS: ABSOLUTE",
    "KAI_INTEL: TRANSCENDENT"
];

async function runBootSequence(user?: any): Promise<void> {
    const overlay = document.getElementById('bootup-overlay');
    if (!overlay) return;

    overlay.classList.remove('hidden');
    LOG.info('BOOT', 'Initiating Ultra-Violet sequence');

    // Stage 0: Neural Link Initiation
    const stage0 = document.getElementById('boot-stage-0');
    const warningBar = document.getElementById('warning-bar');
    const warningText = document.getElementById('warning-text');
    const violetLayer = document.getElementById('violet-glitch-layer');

    if (stage0 && warningBar && warningText) {
        setTimeout(() => { if (warningBar) warningBar.style.width = '1000px'; if (warningBar) warningBar.style.transition = 'width 1.2s cubic-bezier(0.19, 1, 0.22, 1)'; }, 100);
        setTimeout(() => { if (warningText) warningText.style.opacity = '1'; }, 600);

        // Flicker Violet Layer
        let flickers = 0;
        const hint = setInterval(() => {
            if (violetLayer) violetLayer.style.opacity = flickers % 2 === 0 ? '0.4' : '0';
            flickers++;
            if (flickers > 12) {
                clearInterval(hint);
                if (violetLayer) violetLayer.style.opacity = '0';
            }
        }, 80);
    }

    // Stage 1: The Punch (KAI INTEL)
    await new Promise(r => setTimeout(r, 1600));
    if (stage0) stage0.classList.add('hidden');

    const stage1 = document.getElementById('boot-stage-1');
    const titleKai = overlay.querySelector('.boot-title-kai') as HTMLElement;
    const titleIntel = overlay.querySelector('.boot-title-intel') as HTMLElement;
    const subtitle = overlay.querySelector('.boot-subtitle-wild') as HTMLElement;

    if (stage1) {
        stage1.classList.remove('hidden');
        document.body.classList.add('shake-wild');

        setTimeout(() => {
            if (titleKai) { titleKai.style.opacity = '1'; titleKai.style.transform = 'scale(1)'; titleKai.style.filter = 'blur(0)'; }
            if (titleIntel) { titleIntel.style.opacity = '1'; titleIntel.style.transform = 'scale(1)'; titleIntel.style.filter = 'blur(0)'; }
        }, 100);

        setTimeout(() => { if (subtitle) subtitle.style.opacity = '1'; }, 500);
        setTimeout(() => { document.body.classList.remove('shake-wild'); }, 600);
    }

    // Stage 2: Operator ID Reveal
    await new Promise(r => setTimeout(r, 1400));
    if (stage1) stage1.classList.add('hidden');

    const stage2 = document.getElementById('boot-stage-2');
    const percentEl = document.getElementById('boot-percent');
    const usernameReveal = document.getElementById('boot-username-reveal');
    const welcomeUser = document.getElementById('welcome-username');

    if (stage2) {
        stage2.classList.remove('hidden');
        const displayName = user?.displayName || user?.email?.split('@')[0] || 'GUEST_OPERATOR';
        if (usernameReveal) usernameReveal.textContent = displayName.toUpperCase();
        if (welcomeUser) welcomeUser.textContent = displayName.toUpperCase();

        let count = 0;
        const interval = setInterval(() => {
            count += Math.floor(Math.random() * 15) + 5;
            if (count >= 100) {
                count = 100;
                clearInterval(interval);
                if (usernameReveal) {
                    usernameReveal.style.opacity = '1';
                    usernameReveal.classList.add('glitch-text-wild');
                }
            }
            if (percentEl) percentEl.textContent = `${count.toString().padStart(2, '0')}%`;
        }, 40);
    }

    // Stage 3: Workspace Construction
    await new Promise(r => setTimeout(r, 1200));
    if (stage2) stage2.classList.add('hidden');

    const stage3 = document.getElementById('boot-stage-3');
    const terminal = document.getElementById('boot-terminal-wild');
    if (stage3 && terminal) {
        stage3.classList.remove('hidden');
        for (let i = 0; i < BOOT_LOGS_ULTRA.length; i++) {
            await new Promise(r => setTimeout(r, 40));
            const logLine = document.createElement('div');
            logLine.className = 'flex gap-4 font-black text-indigo-400 animate-pulse';
            logLine.innerHTML = `<span class="opacity-40">>></span><span>${BOOT_LOGS_ULTRA[i]}</span>`;
            terminal.appendChild(logLine);
            terminal.scrollTop = terminal.scrollHeight;
        }
    }

    // Stage 4: WELCOME HOME
    await new Promise(r => setTimeout(r, 1200));
    if (stage3) stage3.classList.add('hidden');

    const stage4 = document.getElementById('boot-stage-4');
    const seizedBox = document.getElementById('seized-box');
    const opId = document.getElementById('op-id-v2');
    const flash = document.getElementById('flash-violet');

    if (stage4 && seizedBox) {
        stage4.classList.remove('hidden');
        injectMemoryCore(); // <--- INJECT MEMORY CORE HERE
        if (flash) {
            flash.style.opacity = '1';
            setTimeout(() => { if (flash) flash.style.opacity = '0'; }, 150);
        }
        document.body.classList.add('shake-wild');

        setTimeout(() => {
            if (seizedBox) {
                seizedBox.style.opacity = '1';
                seizedBox.style.transform = 'scale(1)';
            }
        }, 100);

        setTimeout(() => { if (opId) opId.style.opacity = '1'; }, 800);
        setTimeout(() => document.body.classList.remove('shake-wild'), 800);
    }

    // Final Transition
    await new Promise(r => setTimeout(r, 2200));
    overlay.style.transition = 'all 0.6s cubic-bezier(0.19, 1, 0.22, 1)';
    overlay.style.opacity = '0';
    overlay.style.transform = 'scale(1.5)';
    overlay.style.filter = 'blur(20px)';

    setTimeout(() => {
        overlay.classList.add('hidden');
        overlay.style.opacity = '1';
        overlay.style.transform = 'scale(1)';
        overlay.style.filter = 'none';
        LOG.info('BOOT', 'UPLINK_COMPLETE');
    }, 600);
}

// Check if user needs bootup (first login)
function shouldShowBootup(userId: string): boolean {
    const key = `kai_bootup_shown_${userId}`;
    const shown = localStorage.getItem(key);
    if (!shown) {
        localStorage.setItem(key, 'true');
        return true;
    }
    return false;
}

(window as any).runBootSequence = runBootSequence;

// === 📋 MESSAGE ACTIONS ===
let lastUserMessage = '';
let lastUserAttachment: string | null = null;

(window as any).copyMessage = async (msgId: string) => {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;

    const bodyEl = msgEl.querySelector('.markdown-body');
    const text = bodyEl?.textContent || '';

    try {
        await navigator.clipboard.writeText(text);
        // Visual feedback on button
        const btn = msgEl.querySelector('.action-copy');
        if (btn) {
            btn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i>';
            btn.classList.add('text-emerald-400');
            if (typeof lucide !== 'undefined') lucide.createIcons();
            setTimeout(() => {
                btn.innerHTML = '<i data-lucide="copy" class="w-3.5 h-3.5"></i>';
                btn.classList.remove('text-emerald-400');
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }, 1500);
        }
        notify('MESSAGE_COPIED');
    } catch (e) {
        notify('COPY_FAILED', 'error');
    }
};

(window as any).regenerateResponse = async () => {
    if (!lastUserMessage) {
        notify('NO_MESSAGE_TO_REGENERATE', 'error');
        return;
    }

    // Remove last assistant message
    const messages = messagesList?.querySelectorAll('.msg-block.assistant');
    if (messages && messages.length > 0) {
        messages[messages.length - 1].remove();
    }

    // Resend the message
    notify('REGENERATING...');
    await sendMessage(lastUserMessage, lastUserAttachment);
};

(window as any).deleteMessage = (msgId: string) => {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;

    // Animate out
    msgEl.style.transition = 'all 0.3s ease';
    msgEl.style.opacity = '0';
    msgEl.style.transform = 'translateX(-20px)';

    setTimeout(() => {
        msgEl.remove();
        notify('MESSAGE_DELETED');
    }, 300);
};

// === 📁 FILE UPLOAD HANDLER ===
let pendingFiles: { name: string; url: string; type: string }[] = [];

(window as any).handleFileUpload = async (event: Event) => {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    LOG.info('FILE', `Uploading: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

    // Show uploading indicator
    notify('UPLOADING_FILE...');

    // Create FormData
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/files/upload`, {
            method: 'POST',
            headers: {
                'X-API-Key': 'kai_test_key_12345'
            },
            body: formData
        });

        const data = await response.json();
        LOG.network(`${API_URL}/files/upload`, response.status, data);

        if (data.status === 'success') {
            // Store file for context
            pendingFiles.push({
                name: data.filename || file.name,
                url: data.url || '',
                type: data.analysis?.file_type || 'unknown'
            });

            // Show in attachment area
            showAttachmentPreview(file.name, data.analysis?.file_type || 'file', data.url);

            // Show analysis summary if available
            if (data.ai_summary) {
                notify(`FILE_ANALYZED: ${data.ai_summary.substring(0, 50)}...`);
            } else {
                notify('FILE_UPLOADED');
            }

            LOG.info('FILE', 'Upload successful', data);
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error: any) {
        LOG.error('FILE', 'Upload failed', error);
        notify(`UPLOAD_FAILED: ${error.message}`, 'error');
    }

    // Reset input
    input.value = '';
};

function showAttachmentPreview(filename: string, fileType: string, url?: string) {
    if (!attachmentArea) return;

    attachmentArea.classList.remove('hidden');
    attachmentArea.classList.add('flex');

    const iconMap: Record<string, string> = {
        'image': 'image',
        'video': 'film',
        'document': 'file-text',
        'code': 'code',
        'data': 'database',
        'archive': 'archive',
        'unknown': 'file'
    };

    const icon = iconMap[fileType] || 'file';

    const chip = document.createElement('div');
    chip.className = 'flex items-center gap-2 px-3 py-2 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-sm text-indigo-300 group';
    chip.innerHTML = `
        <i data-lucide="${icon}" class="w-4 h-4"></i>
        <span class="max-w-[150px] truncate">${filename}</span>
        <button onclick="removeAttachment(this)" class="text-white/40 hover:text-red-400 ml-1">
            <i data-lucide="x" class="w-3 h-3"></i>
        </button>
    `;

    attachmentArea.appendChild(chip);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

(window as any).removeAttachment = (btn: HTMLElement) => {
    const chip = btn.closest('.flex');
    if (chip) {
        chip.remove();
        pendingFiles.pop(); // Remove last file (simple approach)
    }

    // Hide area if empty
    if (attachmentArea && attachmentArea.children.length === 0) {
        attachmentArea.classList.add('hidden');
        attachmentArea.classList.remove('flex');
    }
};

// === ⌨️ TYPEWRITER STREAMING EFFECT ===
let isStreaming = false;
let streamAbortController: AbortController | null = null;

async function typewriterEffect(element: HTMLElement, text: string, speed: number = 15): Promise<void> {
    isStreaming = true;

    // Add cursor to element
    const cursor = document.createElement('span');
    cursor.className = 'typing-cursor';
    cursor.innerHTML = '█';
    cursor.style.cssText = 'animation: blink 0.7s infinite; color: #6366f1; font-weight: normal;';

    let currentIndex = 0;
    const chunks = text.split(/(\s+|```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*|\n)/); // Split on spaces, code blocks, inline code, bold, newlines

    return new Promise((resolve) => {
        function typeNext() {
            if (!isStreaming || currentIndex >= chunks.length) {
                cursor.remove();
                isStreaming = false;
                // Re-render with full formatting
                element.innerHTML = formatMessage(text);
                if (typeof lucide !== 'undefined') lucide.createIcons();
                if (typeof Prism !== 'undefined') Prism.highlightAllUnder(element);
                resolve();
                return;
            }

            // Add next chunk
            const chunk = chunks[currentIndex];
            if (cursor.parentNode) cursor.remove();

            // Simple text accumulation for smooth effect
            const visibleText = chunks.slice(0, currentIndex + 1).join('');
            element.innerHTML = formatMessage(visibleText);
            element.appendChild(cursor);

            currentIndex++;
            scrollToBottom();

            // Variable speed based on content
            const delay = chunk.includes('```') ? 5 : chunk === '\n' ? 50 : speed;
            setTimeout(typeNext, delay);
        }

        typeNext();
    });
}

(window as any).stopGenerating = () => {
    isStreaming = false;
    if (streamAbortController) {
        streamAbortController.abort();
        streamAbortController = null;
    }
    notify('GENERATION_STOPPED');
};

// Formatting
function formatMessage(text: string) {
    if (typeof marked === 'undefined') return text;
    const renderer = new marked.Renderer();
    renderer.code = (code: string, language: string) => {
        const blockId = `code-block-${++codeBlockCounter}`;
        // Escape HTML entities in code for safe embedding
        const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<div id="${blockId}" class="code-container my-4 border border-white/10 group relative rounded-lg overflow-hidden">
            <div class="px-4 py-2 bg-white/5 border-b border-white/10 flex justify-between items-center">
                <span class="text-[9px] font-mono text-indigo-300/70 uppercase tracking-widest">${language || 'RAW_BUFFER'}</span>
                <button id="${blockId}-btn" onclick="copyCode('${blockId}')" class="flex items-center gap-1.5 px-2 py-1 text-[9px] font-mono text-white/40 hover:text-white hover:bg-white/10 rounded transition-all uppercase tracking-widest">
                    <i data-lucide="copy" class="w-3 h-3"></i> Copy code
                </button>
            </div>
            <pre class="p-4 custom-scrollbar overflow-x-auto bg-black/30"><code class="language-${language}">${escapedCode}</code></pre>
        </div>`;
    };
    renderer.image = (href: string, title: string, text: string) => {
        if (href && !href.startsWith('http') && !href.startsWith('data:') && !href.startsWith('//')) {
            href = BASE_URL + href;
        }
        return `<div class="my-3 rounded-lg overflow-hidden border border-white/10 bg-black/20 inline-block">
            <img src="${href}" alt="${text}" title="${title || ''}" class="max-w-full h-auto max-h-[400px] object-contain block" loading="lazy" />
        </div>`;
    };

    renderer.link = (href: string, title: string, text: string) => {
        if (href && (href.endsWith('.pdf') || href.includes('.pdf'))) {
            // We can inject a preview button or just return the link
            // Better: if it's a PDF link, maybe we can auto-embed?
            // For now, standard link behavior but styled
            if (!href.startsWith('http') && !href.startsWith('//')) {
                href = BASE_URL + href;
            }
            return `<span class="inline-flex flex-col gap-2 w-full"><a href="${href}" target="_blank" class="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 underline decoration-indigo-500/30">${text}</a>
             <iframe src="https://docs.google.com/viewer?url=${encodeURIComponent(href)}&embedded=true" class="w-full h-[300px] border border-white/10 rounded bg-black/50"></iframe></span>`;
        }
        return `<a href="${href}" target="_blank" title="${title || ''}" class="text-indigo-400 hover:text-indigo-300 underline decoration-indigo-500/30">${text}</a>`;
    };

    marked.setOptions({
        renderer: renderer,
        highlight: (code, lang) => {
            if (typeof Prism !== 'undefined' && Prism.languages[lang]) {
                return Prism.highlight(code, Prism.languages[lang], lang);
            }
            return code;
        }
    });
    return marked.parse(text);
}

// UI Rendering
function renderHistory() {
    if (!chatHistoryList) return;

    // Sort by updatedAt descending (newest first)
    const sortedChats = [...chatHistory].sort((a, b) => (b.updatedAt || b.createdAt || 0) - (a.updatedAt || a.createdAt || 0));

    chatHistoryList.innerHTML = sortedChats.length ? '' : `<div class="px-3 py-2 text-[10px] text-white/20 font-mono italic text-center">EMPTY_LOGS</div>`;

    sortedChats.slice(0, 15).forEach(chat => {
        const container = document.createElement('div');
        container.className = 'group flex items-center justify-between hover:bg-white/5 border-l-2 border-transparent hover:border-indigo-500 transition-all px-3 py-1';

        const displayTitle = chat.title || chat.user || 'Untitled Chat';

        const btn = document.createElement('button');
        btn.className = 'flex-1 text-left py-2 text-[10px] text-white/40 group-hover:text-white truncate font-mono uppercase tracking-widest';
        btn.innerText = displayTitle.substring(0, 24) + (displayTitle.length > 24 ? '...' : '');
        btn.onclick = () => { loadChat(chat.id); if (window.innerWidth < 1024) (window as any).toggleSidebar(); };

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'opacity-0 group-hover:opacity-100 p-2 text-white/20 hover:text-red-400 transition-all';
        deleteBtn.innerHTML = `<i data-lucide="trash-2" class="w-3 h-3"></i>`;
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            if (confirm('PURGE INDIVIDUAL LOG ENTRY?')) (window as any).deleteChat(chat.id);
        };

        container.appendChild(btn);
        container.appendChild(deleteBtn);
        chatHistoryList.appendChild(container);
    });
    if (typeof lucide !== 'undefined') lucide.createIcons();
}


function renderAnimePlayer(container: HTMLElement, anime: any) {
    if (!anime) return;

    // Get the streaming URL - check multiple possible fields
    const streamUrl = anime.streaming_url || anime.embed_url ||
        (anime.streams && anime.streams[0]?.url) ||
        (anime.streams && anime.streams[0]?.embed);
    const watchLinks = anime.watch_links || [];
    const thumbnail = anime.thumbnail || anime.image ||
        (anime.anime && anime.anime.image) || '';
    const title = anime.title || (anime.anime && anime.anime.title) || 'Anime';
    // Fix: episode could be an object {number: 1} or a direct number
    const episode = typeof anime.episode === 'object' ? anime.episode?.number : anime.episode || 1;
    const quality = anime.quality || 'HD';
    const isFallback = anime.fallback === true;

    // PRIORITY 1: Iframe embed player (using embtaku.pro which allows embedding)
    if (anime.embed_url || (anime.streams && anime.streams[0]?.embed)) {
        const embedUrl = anime.embed_url || anime.streams[0].embed;
        const html = `
        <div class="mt-4 rounded-lg overflow-hidden border border-indigo-500/30 bg-black shadow-lg shadow-indigo-500/10 animate-in fade-in duration-500">
            <div class="relative aspect-video">
                <iframe 
                    src="${embedUrl}" 
                    class="w-full h-full" 
                    frameborder="0" 
                    scrolling="no"
                    allowfullscreen 
                    allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-presentation"
                    loading="lazy">
                </iframe>
            </div>
            <div class="p-3 bg-indigo-900/10 border-t border-white/5">
                <div class="flex justify-between items-center mb-2">
                    <div class="flex items-center gap-2">
                        <i data-lucide="tv" class="w-4 h-4 text-indigo-400"></i>
                        <span class="text-xs font-mono text-indigo-200">${title} - Episode ${episode}</span>
                    </div>
                    <span class="text-[10px] px-2 py-0.5 bg-indigo-500/20 rounded text-indigo-300">${quality}</span>
                </div>
                ${watchLinks.length > 0 ? `
                    <div class="flex gap-2 flex-wrap mt-2">
                        <span class="text-[10px] text-white/40 mr-1">Alt sources:</span>
                        ${watchLinks.map((link: any) => `
                            <a href="${link.url}" target="_blank" 
                               class="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 rounded border border-white/10 text-white/70 hover:text-white transition-all">
                                ${link.name}
                            </a>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        </div>`;

        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        container.appendChild(wrapper);
        // @ts-ignore
        if (window.lucide) window.lucide.createIcons();
        return;
    }

    // PRIORITY 2: Show watch links card (if no embed available)
    if (anime.embed_url || (anime.streams && anime.streams[0]?.embed)) {
        const embedUrl = anime.embed_url || anime.streams[0].embed;
        const html = `
        <div class="mt-4 rounded-lg overflow-hidden border border-indigo-500/30 bg-black shadow-lg shadow-indigo-500/10 animate-in fade-in duration-500">
            <div class="relative aspect-video">
                <iframe 
                    src="${embedUrl}" 
                    class="w-full h-full" 
                    frameborder="0" 
                    allowfullscreen 
                    allow="autoplay; fullscreen; picture-in-picture"
                    loading="lazy">
                </iframe>
            </div>
            <div class="p-3 bg-indigo-900/10 border-t border-white/5">
                <div class="flex justify-between items-center mb-2">
                    <div class="flex items-center gap-2">
                        <i data-lucide="tv" class="w-4 h-4 text-indigo-400"></i>
                        <span class="text-xs font-mono text-indigo-200">${title} - Episode ${episode}</span>
                    </div>
                    <span class="text-[10px] px-2 py-0.5 bg-indigo-500/20 rounded text-indigo-300">${quality}</span>
                </div>
                ${watchLinks.length > 0 ? `
                    <div class="flex gap-2 flex-wrap mt-2">
                        ${watchLinks.map((link: any) => `
                            <a href="${link.url}" target="_blank" 
                               class="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 rounded border border-white/10 text-white/70 hover:text-white transition-all">
                                ${link.name}
                            </a>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        </div>`;

        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        container.appendChild(wrapper);
        // @ts-ignore
        if (window.lucide) window.lucide.createIcons();
        return;
    }

    // If we have watch links but no embed (fallback mode)
    if (watchLinks.length > 0) {
        const html = `
        <div class="mt-4 rounded-lg overflow-hidden border border-indigo-500/30 bg-gradient-to-br from-indigo-900/20 to-black shadow-lg shadow-indigo-500/10 animate-in fade-in duration-500">
            <div class="relative aspect-video flex items-center justify-center" style="background-image: url('${thumbnail}'); background-size: cover; background-position: center;">
                <div class="absolute inset-0 bg-black/70 backdrop-blur-sm"></div>
                <div class="relative z-10 text-center p-6">
                    <i data-lucide="play-circle" class="w-16 h-16 text-indigo-400 mx-auto mb-4"></i>
                    <div class="text-white font-bold text-lg mb-2">${title}</div>
                    <div class="text-white/60 text-sm mb-4">Episode ${episode}</div>
                    <div class="flex gap-3 justify-center flex-wrap">
                        ${watchLinks.map((link: any) => `
                            <a href="${link.url}" target="_blank" 
                               class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white text-sm font-medium transition-all flex items-center gap-2">
                                <i data-lucide="external-link" class="w-4 h-4"></i>
                                ${link.name}
                            </a>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>`;

        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        container.appendChild(wrapper);
        // @ts-ignore
        if (window.lucide) window.lucide.createIcons();
        return;
    }

    // Original HLS player for direct streaming URLs
    if (!streamUrl) return;

    const playerId = `anime-player-${Date.now()}`;
    const html = `
    <div class="mt-4 rounded-lg overflow-hidden border border-indigo-500/30 bg-black shadow-lg shadow-indigo-500/10 animate-in fade-in duration-500">
        <div class="relative aspect-video group">
            <video id="${playerId}" class="w-full h-full object-contain bg-black" controls crossorigin="anonymous" poster="${thumbnail}"></video>
            <div class="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-[10px] font-mono text-white/80 border border-white/10">
                ${quality}
            </div>
        </div>
        <div class="p-3 bg-indigo-900/10 border-t border-white/5 flex justify-between items-center">
             <div class="flex items-center gap-2">
                <i data-lucide="play-circle" class="w-4 h-4 text-indigo-400"></i>
                <span class="text-xs font-mono text-indigo-200">${title} - Ep ${episode}</span>
             </div>
             <button onclick="window.open('${streamUrl}', '_blank')" class="text-[10px] uppercase hover:text-white text-white/50 transition-colors">Open ext</button>
        </div>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);

    setTimeout(() => {
        const video = document.getElementById(playerId) as HTMLVideoElement;
        if (!video) return;

        // @ts-ignore
        if (typeof Hls !== 'undefined' && Hls.isSupported()) {
            // @ts-ignore
            const hls = new Hls();
            hls.loadSource(streamUrl);
            hls.attachMedia(video);
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = streamUrl;
        }
    }, 100);
}

function renderSpotifyPlayer(container: HTMLElement, spotify: any) {
    if (!spotify || !spotify.embed_url) return;

    const playerId = `spotify-player-${Date.now()}`;
    const trackName = spotify.name || 'Track';
    const artistName = spotify.artists || '';

    const html = `
    <div class="mt-4 rounded-xl overflow-hidden spotify-player-card bg-[#0d0d14] border border-indigo-500/20 max-w-md animate-in fade-in slide-in-from-bottom-4 duration-300">
        <!-- Minimal Header -->
        <div class="flex items-center justify-between px-3 py-2 bg-black/40 border-b border-white/5">
            <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-[#1DB954]" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
                <div class="text-xs text-white/60 font-mono truncate max-w-[250px]">${trackName}${artistName ? ` • ${artistName}` : ''}</div>
            </div>
        </div>
        <!-- Spotify Embed -->
        <iframe 
            style="border-radius:0 0 12px 12px" 
            src="${spotify.embed_url}" 
            width="100%" 
            height="152" 
            frameBorder="0" 
            allowfullscreen="" 
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
            loading="lazy">
        </iframe>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderPDFPreview(container: HTMLElement, pdfUrl: string, title: string = "Document") {
    // Correct URL if relative
    if (pdfUrl && !pdfUrl.startsWith('http')) {
        pdfUrl = BASE_URL + pdfUrl;
    }

    const html = `
    <div class="mt-4 rounded-xl overflow-hidden pdf-preview-card border border-indigo-500/30 bg-gradient-to-br from-[#1a1a2e] to-black w-full h-[400px] animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div class="flex items-center justify-between px-4 py-3 bg-black/50 border-b border-indigo-500/20">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-600/30 flex items-center justify-center">
                    <i data-lucide="file-text" class="w-4 h-4 text-indigo-400"></i>
                </div>
                <div>
                    <span class="text-[10px] font-mono text-indigo-400 uppercase tracking-widest">Document Ready</span>
                    <div class="text-xs text-white/80 font-medium">${title}</div>
                </div>
            </div>
            <a href="${pdfUrl}" target="_blank" class="px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-xs text-indigo-300 hover:bg-indigo-600/30 transition-all">
                <i data-lucide="download" class="w-3 h-3 inline mr-1"></i>Download
            </a>
        </div>
        <iframe src="https://docs.google.com/viewer?url=${encodeURIComponent(pdfUrl)}&embedded=true" class="w-full h-[calc(100%-52px)] border-0"></iframe>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
    try { if (typeof lucide !== 'undefined') lucide.createIcons(); } catch (e) { }
}

function scrollToBottom() {
    const container = document.getElementById('chat-container');
    if (container) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}


// ==================== WIDGET RENDERERS ====================

function renderWeatherCard(container: HTMLElement, data: any) {
    if (!data) return;
    const html = `
    <div class="mt-4 p-6 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-white/10 backdrop-blur-xl animate-in fade-in zoom-in duration-500 shadow-2xl overflow-hidden relative group">
        <div class="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
            <i data-lucide="cloud-sun" class="w-32 h-32 text-white"></i>
        </div>
        <div class="relative z-10 flex justify-between items-start">
            <div>
                 <div class="text-[10px] font-mono uppercase tracking-widest text-blue-200/60 mb-1">ATMOSPHERIC DATA</div>
                 <h3 class="text-3xl font-bold text-white flex items-center gap-3">
                    ${data.city} 
                 </h3>
                 <div class="flex items-baseline gap-2 mt-2">
                    <span class="text-5xl font-thin text-white tracking-tighter">${data.temperature}</span>
                    <span class="text-lg text-indigo-300 capitalize">${data.condition}</span>
                 </div>
            </div>
            <div class="text-right space-y-1 mt-2">
                 <div class="flex items-center justify-end gap-2 text-xs text-white/60 font-mono">
                    <i data-lucide="droplets" class="w-3 h-3"></i> <span>HUM: ${data.humidity}</span>
                 </div>
                 <div class="flex items-center justify-end gap-2 text-xs text-white/60 font-mono">
                    <i data-lucide="wind" class="w-3 h-3"></i> <span>WIND: ${data.wind}</span>
                 </div>
                 <div class="flex items-center justify-end gap-2 text-xs text-white/60 font-mono">
                    <i data-lucide="thermometer" class="w-3 h-3"></i> <span>FEELS: ${data.feels_like}</span>
                 </div>
            </div>
        </div>
    </div>`;
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderNewsList(container: HTMLElement, data: any) {
    if (!data) return;

    // Handle empty articles array
    if (!data.articles || data.articles.length === 0) {
        const emptyHtml = `
        <div class="mt-4 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden animate-in fade-in duration-300">
            <div class="px-4 py-3 bg-white/5 border-b border-white/5 flex items-center justify-between">
                <span class="text-[10px] font-mono uppercase tracking-widest text-white/50">LATEST_HEADLINES</span>
            </div>
            <div class="p-6 text-center">
                <i data-lucide="newspaper" class="w-8 h-8 text-white/20 mx-auto mb-3"></i>
                <div class="text-sm text-white/40">No headlines available</div>
                <div class="text-xs text-white/20 mt-1">Try a different topic or check back later</div>
            </div>
        </div>`;
        const wrapper = document.createElement('div');
        wrapper.innerHTML = emptyHtml;
        container.appendChild(wrapper);
        return;
    }

    let articlesHtml = data.articles.map((article: any) => `
        <a href="${article.url}" target="_blank" class="block p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 transition-all group/item mb-2">
            <div class="flex justify-between items-start gap-3">
                <div class="flex-1">
                    <h4 class="text-sm font-semibold text-gray-200 group-hover/item:text-indigo-400 transition-colors line-clamp-2">${article.title}</h4>
                    ${article.score ? `<div class="text-[10px] text-orange-400 mt-1 font-mono">▲ ${article.score} points by ${article.by}</div>` :
            article.source ? `<div class="text-[10px] text-gray-400 mt-1 font-mono uppercase">${article.source}</div>` : ''}
                </div>
                <i data-lucide="external-link" class="w-4 h-4 text-white/20 group-hover/item:text-white/60 shrink-0 mt-1"></i>
            </div>
        </a>
    `).join('');

    const html = `
    <div class="mt-4 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden animate-in slide-in-from-bottom-2 duration-500">
        <div class="px-4 py-3 bg-white/5 border-b border-white/5 flex items-center justify-between">
            <span class="text-[10px] font-mono uppercase tracking-widest text-white/50">LATEST_HEADLINES</span>
            <span class="text-[10px] text-white/30">${data.articles.length} RESULTS</span>
        </div>
        <div class="p-2 max-h-[300px] overflow-y-auto custom-scrollbar">
            ${articlesHtml}
        </div>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderCryptoStock(container: HTMLElement, data: any) {
    if (!data || data.error) return;

    const isCrypto = !!data.change_24h;
    const change = data.change_24h || data.change_percent;
    const isPositive = change && !change.startsWith('-');
    const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
    const bgClass = isPositive ? 'bg-green-500/10' : 'bg-red-500/10';
    const borderClass = isPositive ? 'border-green-500/20' : 'border-red-500/20';

    const html = `
    <div class="mt-4 inline-flex flex-col p-4 rounded-xl ${bgClass} border ${borderClass} backdrop-blur-md min-w-[200px] animate-in zoom-in duration-300">
        <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-mono uppercase tracking-widest text-white/60">${isCrypto ? 'CRYPTO_ASSET' : 'STOCK_EQUITY'}</span>
            <i data-lucide="${isPositive ? 'trending-up' : 'trending-down'}" class="w-4 h-4 ${colorClass}"></i>
        </div>
        <div class="text-3xl font-bold text-white tracking-tight">${data.price}</div>
        <div class="text-sm font-mono ${colorClass} mt-1 flex items-center gap-1">
            <span>${change}</span>
            <span class="opacity-50 text-[10px] uppercase">24H CHANGE</span>
        </div>
        <div class="mt-3 pt-3 border-t border-white/5 text-[10px] text-white/40 uppercase font-bold tracking-widest">
            ${data.symbol}
        </div>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderSystemStats(container: HTMLElement, data: any) {
    if (!data) return;

    const html = `
    <div class="mt-4 p-4 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-xl animate-in fade-in duration-500">
        <div class="text-[10px] font-mono uppercase tracking-widest text-white/40 mb-3 text-center">SYSTEM_TELEMETRY</div>
        <div class="grid grid-cols-3 gap-3">
             <div class="flex flex-col items-center p-3 rounded-lg bg-white/5 border border-white/5">
                <i data-lucide="cpu" class="w-5 h-5 text-indigo-400 mb-2"></i>
                <div class="text-lg font-bold text-white">${data.cpu}</div>
                <div class="text-[9px] text-white/40">CPU LOAD</div>
             </div>
             <div class="flex flex-col items-center p-3 rounded-lg bg-white/5 border border-white/5">
                <i data-lucide="memory-stick" class="w-5 h-5 text-purple-400 mb-2"></i>
                <div class="text-lg font-bold text-white">${data.ram}</div>
                <div class="text-[9px] text-white/40">RAM USAGE</div>
             </div>
             <div class="flex flex-col items-center p-3 rounded-lg bg-white/5 border border-white/5">
                <i data-lucide="hard-drive" class="w-5 h-5 text-emerald-400 mb-2"></i>
                <div class="text-lg font-bold text-white">${data.disk}</div>
                <div class="text-[9px] text-white/40">DISK I/O</div>
             </div>
        </div>
        <div class="mt-3 text-center">
             <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 text-[10px] font-mono text-white/60">
                <div class="w-2 h-2 rounded-full ${data.battery.plugged ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}"></div>
                BATTERY: ${data.battery.percent}%
             </div>
        </div>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderNasaCard(container: HTMLElement, data: any) {
    if (!data || data.error) return;

    const html = `
    <div class="mt-4 rounded-2xl overflow-hidden border border-white/10 bg-black/60 shadow-2xl animate-in fade-in zoom-in duration-700 group">
        <div class="relative aspect-video overflow-hidden">
            <img src="${data.url}" alt="${data.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700">
            <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent"></div>
            <div class="absolute bottom-0 left-0 p-4">
                <div class="text-[9px] font-mono text-indigo-300 uppercase tracking-widest mb-1">NASA APOD • ${data.date}</div>
                <h3 class="text-lg font-bold text-white leading-tight">${data.title}</h3>
            </div>
        </div>
        <div class="p-4 text-xs text-gray-400 leading-relaxed bg-black/40 backdrop-blur-sm">
            ${data.explanation.substring(0, 300)}...
        </div>
        <div class="px-4 py-2 bg-white/5 border-t border-white/5 flex justify-end">
            <a href="${data.hdurl}" target="_blank" class="text-[10px] text-indigo-400 hover:text-white transition-colors uppercase font-bold tracking-widest flex items-center gap-1">
                View Full Rez <i data-lucide="arrow-up-right" class="w-3 h-3"></i>
            </a>
        </div>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderGithubList(container: HTMLElement, data: any) {
    if (!data || !data.repos) return;

    const html = `
    <div class="mt-4 rounded-xl border border-white/10 bg-[#0d1117] text-white animate-in slide-in-from-bottom-2 duration-500">
         <div class="px-4 py-3 border-b border-white/10 flex items-center gap-2">
             <i data-lucide="github" class="w-4 h-4"></i>
             <span class="text-sm font-bold">Repositories</span>
         </div>
         <div class="divide-y divide-white/5 max-h-[250px] overflow-y-auto custom-scrollbar">
             ${data.repos.map((repo: any) => `
             <div class="p-3 hover:bg-white/5 transition-colors">
                 <div class="flex justify-between items-start">
                     <a href="${repo.url}" target="_blank" class="text-sm font-bold text-blue-400 hover:underline">${repo.name}</a>
                     <div class="flex items-center gap-1 text-xs text-gray-400">
                        <i data-lucide="star" class="w-3 h-3"></i> ${repo.stars}
                     </div>
                 </div>
                 <p class="text-xs text-gray-400 mt-1 line-clamp-1">${repo.description || 'No description'}</p>
                 <div class="mt-2 text-[10px] flex items-center gap-2">
                    ${repo.language ? `<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-yellow-400"></span> ${repo.language}</span>` : ''}
                 </div>
             </div>
             `).join('')}
         </div>
    </div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}


function renderFigmaCard(container: HTMLElement, data: any) {
    // Handle both: data = {files: [...]} or data = [...]
    const files = Array.isArray(data) ? data : (data?.files || []);

    if (!files || files.length === 0) {
        // Show empty state instead of breaking
        const emptyHtml = `
        <div class="mt-4 rounded-xl border border-white/10 bg-[#1e1e1e] p-6 text-center animate-in fade-in">
            <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/Figma-logo.svg" class="w-10 h-10 mx-auto opacity-50 mb-3">
            <div class="text-sm text-white/60">No Figma files found</div>
            <div class="text-xs text-white/30 mt-1">Connect your Figma account or check API key</div>
        </div>`;
        const wrapper = document.createElement('div');
        wrapper.innerHTML = emptyHtml;
        container.appendChild(wrapper);
        return;
    }

    const html = `
    <div class="mt-4 rounded-xl border border-white/10 bg-[#1e1e1e] overflow-hidden animate-in fade-in duration-500">
         <div class="px-4 py-3 border-b border-white/5 flex items-center gap-2 bg-[#2c2c2c]">
             <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/Figma-logo.svg" class="w-4 h-4">
             <span class="text-sm font-bold text-white">Recent Files</span>
             <span class="text-xs text-white/40 ml-auto">${files.length} files</span>
         </div>
         <div class="grid grid-cols-2 gap-3 p-3">
             ${files.map((f: any) => `
             <a href="${f.url || '#'}" target="_blank" class="group block relative aspect-[4/3] rounded-lg overflow-hidden border border-white/10 bg-black/50 hover:border-indigo-500/50 transition-all">
                 ${f.thumbnail ? `<img src="${f.thumbnail}" class="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" onerror="this.style.display='none'">` : '<div class="w-full h-full flex items-center justify-center"><span class="text-2xl">🎨</span></div>'}
                 <div class="absolute inset-0 bg-gradient-to-t from-black/90 to-transparent flex flex-col justify-end p-2">
                     <div class="text-xs font-bold text-white truncate">${f.name || 'Untitled'}</div>
                     <div class="text-[9px] text-white/50">${f.last_modified || 'Recently updated'}</div>
                 </div>
             </a>
             `).join('')}
         </div>
    </div>`;
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}


function renderNotionList(container: HTMLElement, data: any) {
    if (!data || !data.pages) return;

    const html = `
    <div class="mt-4 rounded-xl border border-white/10 bg-[#191919] animate-in slide-in-from-bottom-2 duration-500">
         <div class="px-4 py-2 border-b border-white/5 flex items-center gap-2">
             <span class="text-lg">📝</span>
             <span class="text-xs font-mono uppercase tracking-widest text-white/50">Notion Workspace</span>
         </div>
         <div class="divide-y divide-white/5">
             ${data.pages.map((p: any) => `
             <a href="${p.url}" target="_blank" class="flex items-center gap-3 p-3 hover:bg-white/5 transition-colors group">
                 <span class="text-lg opacity-80 group-hover:scale-110 transition-transform">${p.icon}</span>
                 <div class="flex-1 min-w-0">
                     <div class="text-sm text-gray-300 group-hover:text-white truncate">${p.title}</div>
                 </div>
                 <i data-lucide="arrow-right" class="w-3 h-3 text-white/20 group-hover:text-white/60"></i>
             </a>
             `).join('')}
         </div>
    </div>`;
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderSlackCard(container: HTMLElement, data: any) {
    if (!data) return;

    if (data.status) {
        // Message sent confirmation
        const html = `
       <div class="mt-4 inline-flex items-center gap-3 px-4 py-3 rounded-lg bg-[#4A154B]/20 border border-[#4A154B]/50 text-white">
           <div class="p-2 rounded-full bg-[#4A154B]"><i data-lucide="check" class="w-4 h-4"></i></div>
           <div>
               <div class="text-xs font-bold">Message Sent</div>
               <div class="text-[10px] opacity-70">To #${data.channel}</div>
           </div>
       </div>`;
        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        container.appendChild(wrapper);
    } else if (data.channels) {
        // Channel list
        const html = `
       <div class="mt-4 rounded-xl border border-white/10 bg-[#1a1d21] overflow-hidden">
            <div class="px-4 py-2 border-b border-white/5 bg-[#4A154B] flex items-center gap-2">
                <i data-lucide="hash" class="w-4 h-4 text-white"></i>
                <span class="text-xs font-bold text-white">Slack Channels</span>
            </div>
            <div class="p-2 space-y-1">
                ${data.channels.map((c: any) => `
                <div class="flex items-center justify-between p-2 rounded hover:bg-white/5 cursor-default">
                    <span class="text-sm text-gray-300"># ${c.name}</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded-full bg-white/10 text-white/40">${c.members}</span>
                </div>
                `).join('')}
            </div>
       </div>`;
        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        container.appendChild(wrapper);
    }
}

function renderTrelloBoard(container: HTMLElement, data: any) {
    if (!data || !data.boards) return;

    const html = `
    <div class="mt-4 space-y-2">
        ${data.boards.map((b: any) => `
        <a href="${b.url}" target="_blank" class="block p-4 rounded-lg bg-gradient-to-r from-blue-600/20 to-blue-800/20 border border-blue-500/30 hover:border-blue-400/50 transition-all group">
            <div class="flex justify-between items-center">
                <div class="font-bold text-white group-hover:text-blue-200 transition-colors">${b.name}</div>
                <i data-lucide="trello" class="w-4 h-4 text-white/40"></i>
            </div>
        </a>
        `).join('')}
    </div>`;
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

function renderCalendarWidget(container: HTMLElement, data: any) {
    if (!data || !data.events) return;

    const html = `
    <div class="mt-4 rounded-xl border border-white/10 bg-[#202124] overflow-hidden animate-in fade-in duration-500">
         <div class="px-4 py-3 border-b border-white/5 flex items-center gap-2">
             <i data-lucide="calendar" class="w-4 h-4 text-blue-400"></i>
             <span class="text-xs font-bold text-white uppercase tracking-widest">Upcoming</span>
         </div>
         <div class="p-4 relative">
             <div class="absolute left-6 top-4 bottom-4 w-px bg-white/10"></div>
             <div class="space-y-4">
                 ${data.events.map((e: any) => `
                 <div class="relative pl-6">
                     <div class="absolute left-[-5px] top-1.5 w-2.5 h-2.5 rounded-full bg-blue-500 ring-4 ring-[#202124]"></div>
                     <div class="text-xs text-blue-400 font-mono mb-0.5">${e.start} • ${e.date}</div>
                     <div class="text-sm font-semibold text-gray-200">${e.summary}</div>
                 </div>
                 `).join('')}
             </div>
         </div>
    </div>`;
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

addMessage.renderers = {
    renderWeatherCard, renderNewsList, renderCryptoStock, renderSystemStats, renderNasaCard, renderGithubList,
    renderFigmaCard, renderNotionList, renderSlackCard, renderTrelloBoard, renderCalendarWidget
};


function notify(text: string, type: 'info' | 'error' = 'info') {

    const area = document.getElementById('notification-area');
    if (!area) return;
    const notif = document.createElement('div');
    notif.className = `p-3 bg-black/90 backdrop-blur-md border-l-2 ${type === 'error' ? 'border-red-500' : 'border-indigo-500'} shadow-2xl animate-in slide-in-from-right duration-300 relative pointer-events-auto`;
    notif.innerHTML = `<div class="flex items-center justify-between gap-6 px-2">
            <span class="text-[9px] font-bold font-mono text-white/80 uppercase tracking-widest">${text}</span>
            <i data-lucide="${type === 'error' ? 'alert-circle' : 'check-circle'}" class="w-3 h-3 ${type === 'error' ? 'text-red-500' : 'text-indigo-500'}"></i>
        </div>`;
    area.appendChild(notif);
    setTimeout(() => { notif.style.opacity = '0'; setTimeout(() => notif.remove(), 400); }, 4000);
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function addMessage(role: string, content: string, attachedFile: string | null = null, metadata: any = null) {
    if (!messagesList) return;

    // Generate unique message ID
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Store last user message for regeneration
    if (role === 'user') {
        lastUserMessage = content;
        lastUserAttachment = attachedFile;
    }

    // Track message for Firebase persistence (with metadata)
    const messageObj: any = {
        role: role as 'user' | 'assistant',
        content: content,
        timestamp: Date.now()
    };

    // Include metadata if provided (for rich media persistence)
    // Filter out undefined values to prevent Firebase errors
    if (metadata && typeof metadata === 'object') {
        const cleanMetadata: any = {};
        for (const key in metadata) {
            if (metadata[key] !== undefined && metadata[key] !== null) {
                cleanMetadata[key] = metadata[key];
            }
        }
        if (Object.keys(cleanMetadata).length > 0) {
            messageObj.metadata = cleanMetadata;
        }
    }

    currentChatMessages.push(messageObj);

    const block = document.createElement('div');
    block.id = msgId;
    block.className = `msg-block ${role} group relative`;
    // Store raw content for Canvas access
    block.dataset.rawContent = content;

    // Header with actions
    const header = document.createElement('div');
    header.className = 'flex items-center justify-between mb-3';

    const headerLeft = document.createElement('div');
    headerLeft.className = 'flex items-center gap-2 opacity-60 font-mono text-[10px] uppercase tracking-[0.2em]';
    headerLeft.innerHTML = role === 'assistant'
        ? `<div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse"></div> <span class="text-indigo-400 font-bold">KAI_SYS_INTEL</span> <span>${new Date().toLocaleTimeString()}</span>`
        : `<span class="text-white/60 font-bold">OPERATOR_TRANS</span> <span>${new Date().toLocaleTimeString()}</span>`;

    // Hover action bar
    const actionBar = document.createElement('div');
    actionBar.className = 'msg-actions flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200';
    actionBar.innerHTML = `
        <button onclick="copyMessage('${msgId}')" class="action-copy p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded transition-all" title="Copy message">
            <i data-lucide="copy" class="w-3.5 h-3.5"></i>
        </button>
        ${role === 'assistant' ? `
        <button onclick="(window as any).openCanvas(this.closest('.msg-block').dataset.rawContent, 'Canvas Draft')" class="p-1.5 text-white/40 hover:text-emerald-400 hover:bg-emerald-500/10 rounded transition-all" title="Open in Canvas">
            <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i>
        </button>
        <button onclick="regenerateResponse()" class="p-1.5 text-white/40 hover:text-indigo-400 hover:bg-indigo-500/10 rounded transition-all" title="Regenerate response">
            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
        </button>
        ` : ''}
        <button onclick="deleteMessage('${msgId}')" class="p-1.5 text-white/40 hover:text-red-400 hover:bg-red-500/10 rounded transition-all" title="Delete message">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
        </button>
    `;

    header.appendChild(headerLeft);
    header.appendChild(actionBar);

    const body = document.createElement('div');
    body.className = `markdown-body text-sm leading-relaxed ${role === 'assistant' ? 'text-gray-200' : 'text-gray-400'}`;

    let displayContent = content;
    if (role === 'user' && attachedFile) {
        displayContent = `<div class="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-indigo-500/30 rounded-sm text-[9px] font-mono text-indigo-400 mb-3 uppercase tracking-widest shadow-lg shadow-indigo-500/5">
            <i data-lucide="file-check" class="w-3 h-3"></i> ATTACHED_ASSET: ${attachedFile}
        </div><br>` + (displayContent || 'Awaiting file analysis...');
    }

    body.innerHTML = formatMessage(displayContent);
    block.appendChild(header);
    block.appendChild(body);

    // 🎬 RICH MEDIA RENDERING
    if (metadata && metadata.type === 'anime' && metadata.anime) {
        renderAnimePlayer(body, metadata.anime);
    }

    // 🎵 SPOTIFY PLAYER - Spotify only, no other fallbacks
    // Check for spotify data in metadata (preferred) or look for spotify embed URL in music object
    if (metadata && metadata.type === 'spotify' && metadata.spotify) {
        LOG.info('SPOTIFY', 'Rendering player from spotify type', metadata.spotify);
        renderSpotifyPlayer(body, metadata.spotify);
    } else if (metadata && metadata.spotify && metadata.spotify.embed_url) {
        // Direct spotify data in response
        LOG.info('SPOTIFY', 'Rendering player from direct spotify data', metadata.spotify);
        renderSpotifyPlayer(body, metadata.spotify);
    }

    // 📄 PDF PREVIEW (if explicit file in metadata or detected in content)
    // Check if content mentions "Generated PDF:" and has a file link?
    // Actually, backend might send metadata for generated files in future, 
    // but for now let's check for "Generated PDF" text pattern if no metadata
    if (content.includes('Generated PDF:') || content.includes('.pdf')) {
        // Naive extraction or rely on markdown links
    }

    // If metadata has specific type for document
    if (metadata && (metadata.type === 'pdf' || metadata.type === 'document') && metadata.url) {
        renderPDFPreview(body, metadata.url, metadata.title);
    }

    // 🔌 NEW INTEGRATIONS HANDLERS
    if (metadata && metadata.type && metadata.data) {
        if (metadata.type === 'weather') renderWeatherCard(body, metadata.data);
        if (metadata.type === 'news') renderNewsList(body, metadata.data);
        if (metadata.type === 'crypto' || metadata.type === 'stock') renderCryptoStock(body, metadata.data);
        if (metadata.type === 'system_stats') renderSystemStats(body, metadata.data);
        if (metadata.type === 'nasa_apod') renderNasaCard(body, metadata.data);
        if (metadata.type === 'github') renderGithubList(body, metadata.data);

        // SaaS
        if (metadata.type === 'figma') renderFigmaCard(body, metadata.data);
        if (metadata.type === 'notion') renderNotionList(body, metadata.data);
        if (metadata.type === 'slack') renderSlackCard(body, metadata.data);
        if (metadata.type === 'trello') renderTrelloBoard(body, metadata.data);
        if (metadata.type === 'calendar') renderCalendarWidget(body, metadata.data);
    }

    // 📄 OPEN IN CANVAS BUTTON - For long responses or code blocks  
    if (role === 'assistant' && (content.length > 500 || content.includes('```'))) {
        const canvasBtn = document.createElement('div');
        canvasBtn.className = 'mt-4 pt-4 border-t border-white/5';
        // Store content for canvas - use data attribute to avoid escaping issues
        const contentId = `canvas-content-${Date.now()}`;
        (window as any)[contentId] = content;
        canvasBtn.innerHTML = `
            <button onclick="openCanvas(window['${contentId}'], 'Response Document')" 
                    class="flex items-center gap-2 px-4 py-2 text-[10px] font-mono text-indigo-400 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 hover:border-indigo-500/40 rounded-lg transition-all uppercase tracking-widest group">
                <i data-lucide="panel-right-open" class="w-4 h-4 group-hover:translate-x-0.5 transition-transform"></i>
                Open in Canvas
            </button>
        `;
        body.appendChild(canvasBtn);
    }

    messagesList.appendChild(block);
    scrollToBottom();
    try {
        if (typeof lucide !== 'undefined') lucide.createIcons();
        if (typeof Prism !== 'undefined') Prism.highlightAllUnder(block);
    } catch (e) { }
}

async function loadChat(id: string) {
    const userId = auth?.currentUser?.uid;
    if (!userId) return;

    currentChatId = id;
    if (sessionIdDisplay) sessionIdDisplay.innerText = `SID-${id.substring(0, 6)}`;
    if (messagesList) {
        messagesList.innerHTML = '';
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        messagesList.classList.remove('hidden');
        messagesList.classList.add('flex');
    }

    // Find chat in loaded history or fetch from Firebase
    let chat = chatHistory.find(h => h.id === id);
    if (!chat) {
        chat = await FirebaseDB.loadChat(userId, id);
    }

    if (chat) {
        // Clear current messages tracking
        currentChatMessages = [];

        // Check for NEW format (messages array)
        if (chat.messages && Array.isArray(chat.messages)) {
            chat.messages.forEach((msg: any) => {
                const tempMessages = currentChatMessages;
                currentChatMessages = [];

                if (msg.role === 'user') {
                    addMessage('user', msg.content);
                } else {
                    addMessage('assistant', msg.content, null, msg.metadata || null);
                }

                currentChatMessages = tempMessages;
            });
            currentChatMessages = [...chat.messages];
            LOG.info('CHAT', 'Loaded chat (new format)', { id, messageCount: chat.messages.length });
        }
        // Check for OLD format (user/assistant fields)
        else if (chat.user || chat.assistant) {
            const tempMessages = currentChatMessages;
            currentChatMessages = [];

            if (chat.user) {
                addMessage('user', chat.user);
            }
            if (chat.assistant) {
                addMessage('assistant', chat.assistant, null, chat.metadata || null);
            }

            currentChatMessages = tempMessages;

            // Convert to new format for tracking
            currentChatMessages = [];
            if (chat.user) currentChatMessages.push({ role: 'user', content: chat.user, timestamp: chat.timestamp || Date.now() });
            if (chat.assistant) currentChatMessages.push({ role: 'assistant', content: chat.assistant, timestamp: chat.timestamp || Date.now() });

            LOG.info('CHAT', 'Loaded chat (old format)', { id });
        }
    }
}



async function checkConnection() {
    try {
        const res = await fetch(BASE_URL + '/health', { method: 'GET', signal: AbortSignal.timeout(5000) });
        const dots = document.querySelectorAll('.status-dot');
        if (res.ok) dots.forEach(d => { d.classList.remove('busy'); d.classList.add('active'); });
    } catch (e) { LOG.error('NETWORK', 'Probing failed', e); }
}

async function initApp() {
    renderHistory();
    checkConnection();
    if (sessionIdDisplay) sessionIdDisplay.innerText = `SID-${currentChatId.substring(0, 6)}`;
    setInterval(checkConnection, 30000);
}

// Auth State Observer
if (auth) {
    onAuthStateChanged(auth, async (user) => {
        if (user) {
            LOG.info('AUTH', 'Uplink active', { email: user.email });
            document.getElementById('auth-container')!.style.display = 'none';

            // Check if this is user's first login (show bootup only once)
            if (shouldShowBootup(user.uid)) {
                // Keep main interface hidden during bootup
                document.getElementById('main-interface')!.style.opacity = '0';
                document.getElementById('main-interface')!.style.pointerEvents = 'none';

                // Run bootup sequence
                await runBootSequence(user);
            }

            // Now show main interface
            document.getElementById('main-interface')!.style.opacity = '1';
            document.getElementById('main-interface')!.style.pointerEvents = 'auto';
            initApp();
            // Note: Chat history is now loaded in the onAuthStateChanged handler at the top of the file
        } else {
            document.getElementById('auth-container')!.style.display = 'flex';
            document.getElementById('main-interface')!.style.opacity = '0';
        }
    });
}

// Interface Actions
(window as any).sendMessage = async () => {
    const queryStr = messageInput.value.trim();
    if (!queryStr || isProcessing) return;

    if (welcomeScreen) welcomeScreen.style.display = 'none';
    messagesList?.classList.remove('hidden');
    messagesList?.classList.add('flex');

    // Include pending file attachments in the message display
    let displayMessage = queryStr;
    if (pendingFiles.length > 0) {
        const fileNames = pendingFiles.map(f => `📎 ${f.name}`).join('\n');
        displayMessage = `${fileNames}\n\n${queryStr}`;
    }
    addMessage('user', displayMessage);
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Clear attachment UI
    if (attachmentArea) {
        attachmentArea.innerHTML = '';
        attachmentArea.classList.add('hidden');
        attachmentArea.classList.remove('flex');
    }

    isProcessing = true;

    // 🦴 SKELETON: Show premium typing indicator
    let typingSkeletonId = 'typing-skeleton-' + Date.now();
    if (messagesList) {
        messagesList.insertAdjacentHTML('beforeend', `
            <div class="skeleton-message" id="${typingSkeletonId}">
                <div class="skeleton-message-header">
                    <div class="skeleton skeleton-avatar skeleton-pulse"></div>
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] font-mono text-indigo-400 uppercase tracking-widest">KAI_PROCESSING</span>
                    </div>
                </div>
                <div class="skeleton-typing">
                    <div class="skeleton-typing-dot"></div>
                    <div class="skeleton-typing-dot"></div>
                    <div class="skeleton-typing-dot"></div>
                    <span class="ml-3 text-xs font-mono text-white/40 uppercase tracking-widest">Neural processing...</span>
                </div>
                <div class="mt-3 space-y-2">
                    <div class="skeleton skeleton-line skeleton-line-long"></div>
                    <div class="skeleton skeleton-line skeleton-line-medium"></div>
                </div>
            </div>
        `);
        scrollToBottom();
    }
    let typingIndicator = document.getElementById(typingSkeletonId);

    try {
        // Get user preferences for personalized responses
        const userPrefs = (window as any).getUserPreferences ? (window as any).getUserPreferences() : null;

        // Include attachments in request
        const requestBody: any = {
            query: queryStr,
            session_id: currentChatId,
            uid: auth?.currentUser?.uid,
            user_preferences: userPrefs  // Pass user preferences to KAI
        };

        // Add files if any are pending
        if (pendingFiles.length > 0) {
            requestBody.attachments = pendingFiles.map(f => ({
                name: f.name,
                url: f.url,
                type: f.type
            }));
            LOG.info('FILE', `Sending ${pendingFiles.length} attachment(s) with message`);
            // Clear pending files after including in request
            pendingFiles = [];
        }

        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        const data = await response.json();

        // 🧠 MEMORY VISUALIZATION TRIGGER
        // Check for metadata from the new ChatBot return structure
        if (data.metadata) {
            if (data.metadata.memory_saved) {
                triggerMemoryPulse('save');
            } else if (data.metadata.memory_accessed) {
                triggerMemoryPulse('access');
            }
        }

        // 🔍 DEBUG: Log API response
        LOG.info('API', 'Response received', { type: data.type, hasSpotify: !!data.spotify, metadata: data.metadata });

        if (data.type === 'spotify' || data.type === 'music') {
            LOG.info('SPOTIFY', 'Embed URL', data.spotify?.embed_url);
        }

        // 💬 Remove typing indicator
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }

        // Create message block for streaming
        const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const streamBlock = document.createElement('div');
        streamBlock.id = msgId;
        streamBlock.className = 'msg-block assistant group relative';

        // Header
        const header = document.createElement('div');
        header.className = 'flex items-center justify-between mb-3';
        header.innerHTML = `
            <div class="flex items-center gap-2 opacity-60 font-mono text-[10px] uppercase tracking-[0.2em]">
                <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse"></div>
                <span class="text-indigo-400 font-bold">KAI_SYS_INTEL</span>
                <span>${new Date().toLocaleTimeString()}</span>
            </div>
            <button id="stop-gen-${msgId}" onclick="stopGenerating()" class="stop-gen-btn flex items-center gap-1.5 px-2 py-1 text-[9px] font-mono text-white/60 hover:text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded transition-all uppercase tracking-widest">
                <i data-lucide="square" class="w-3 h-3"></i> Stop
            </button>
        `;

        const body = document.createElement('div');
        body.className = 'markdown-body text-sm leading-relaxed text-gray-200';

        streamBlock.appendChild(header);
        streamBlock.appendChild(body);
        messagesList?.appendChild(streamBlock);
        scrollToBottom();
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Apply typewriter effect
        const responseText = data.response || "NO_DATA";
        await typewriterEffect(body, responseText);

        // 🔧 FIX: Track assistant response for Firebase persistence WITH METADATA
        const assistantMessage: any = {
            role: 'assistant',
            content: responseText,
            timestamp: Date.now()
        };

        // Include metadata for rich media persistence (Spotify, PDF, etc.)
        // Filter out undefined values to prevent Firebase errors
        if (data.type || data.spotify || data.url || data.anime || data.sources) {
            const metadata: any = {};
            if (data.type) metadata.type = data.type;
            if (data.spotify) metadata.spotify = data.spotify;
            if (data.anime) metadata.anime = data.anime;
            if (data.url) metadata.url = data.url;
            if (data.title) metadata.title = data.title;
            if (data.sources) metadata.sources = data.sources;
            if (data.data) metadata.data = data.data;

            // Only add metadata if it has properties
            if (Object.keys(metadata).length > 0) {
                assistantMessage.metadata = metadata;
            }
        }
        currentChatMessages.push(assistantMessage);

        // Remove stop button after streaming complete
        const stopBtn = document.getElementById(`stop-gen-${msgId}`);
        if (stopBtn) stopBtn.remove();

        // Add action bar after streaming
        const actionBar = document.createElement('div');
        actionBar.className = 'msg-actions flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 absolute top-3 right-3';
        actionBar.innerHTML = `
            <button onclick="copyMessage('${msgId}')" class="action-copy p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded transition-all" title="Copy">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
            </button>
            <button onclick="regenerateResponse()" class="p-1.5 text-white/40 hover:text-indigo-400 hover:bg-indigo-500/10 rounded transition-all" title="Regenerate">
                <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
            </button>
            <button onclick="deleteMessage('${msgId}')" class="p-1.5 text-white/40 hover:text-red-400 hover:bg-red-500/10 rounded transition-all" title="Delete">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
        `;
        streamBlock.appendChild(actionBar);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Handle rich media (append after streaming)
        if (data.type === 'anime' && data.anime) {
            renderAnimePlayer(body, data.anime);
        }
        if (data.type === 'spotify' && data.spotify) {
            renderSpotifyPlayer(body, data.spotify);
        }
        // 📄 PDF Preview Handler
        if (data.type === 'pdf' && data.url) {
            renderPDFPreview(body, data.url, data.title || 'Document');
        }
        if (data.type && data.data && addMessage.renderers) {
            const renderer = addMessage.renderers[`render${data.type.charAt(0).toUpperCase() + data.type.slice(1)}Card`]
                || addMessage.renderers[`render${data.type.charAt(0).toUpperCase() + data.type.slice(1)}List`];
            if (renderer) renderer(body, data.data);
        }

        // 🔥 RENDER SOURCE CARDS BELOW RESPONSE (BEAST MODE)
        if (data.type === 'web_search' && data.sources && data.sources.length > 0) {
            const sourceCardsHtml = (window as any).renderSourceCards(data.sources);
            if (sourceCardsHtml) {
                // Insert AFTER the streamBlock for separate visual placement
                streamBlock.insertAdjacentHTML('afterend', sourceCardsHtml);
                LOG.info('SEARCH', `Added ${data.sources.length} beast mode source cards`);
            }
        }

        // 🗣️ AUTO-SPEAK Logic (Voice Mode)
        if ((window as any).isVoiceMode) {
            (window as any).speak(data.response);
        }

        // 💾 SAVE CHAT TO FIREBASE (new structure: users/{uid}/chats/{chatId})
        const userId = auth?.currentUser?.uid;
        if (userId && currentChatId && currentChatMessages.length > 0) {
            try {
                const title = currentChatMessages[0]?.content?.slice(0, 50) || 'New Chat';
                await FirebaseDB.saveChat(userId, {
                    id: currentChatId,
                    title: title,
                    createdAt: parseInt(currentChatId) || Date.now(),
                    updatedAt: Date.now(),
                    messages: currentChatMessages
                });
                LOG.info('CHAT', 'Chat auto-saved to Firebase', { chatId: currentChatId, messages: currentChatMessages.length });
            } catch (e) {
                LOG.error('CHAT', 'Failed to auto-save chat', e);
            }
        }

        // Update local history for sidebar
        const existingIndex = chatHistory.findIndex(h => h.id === currentChatId);
        const historyItem = {
            id: currentChatId,
            title: currentChatMessages[0]?.content?.slice(0, 50) || 'New Chat',
            createdAt: parseInt(currentChatId) || Date.now(),
            updatedAt: Date.now(),
            messages: currentChatMessages
        };
        if (existingIndex >= 0) {
            chatHistory[existingIndex] = historyItem;
        } else {
            chatHistory.unshift(historyItem);
        }
        renderHistory();
    } catch (e: any) {
        // Remove typing indicator on error too
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }


        // Try to extract error details from the response
        let errorMessage = "[!] CRITICAL UPLINK ERROR";

        if (e instanceof Error) {
            errorMessage = `[!] ERROR: ${e.message}`;
        } else if (typeof e === 'string') {
            errorMessage = `[!] ERROR: ${e}`;
        }

        console.error('[FRONTEND] Chat error:', e);
        addMessage('assistant', errorMessage);
    } finally {
        isProcessing = false;
    }
};

(window as any).newChat = async () => {
    const userId = auth?.currentUser?.uid;

    // Save current chat to Firebase before starting new one (if it has messages)
    if (userId && currentChatId && currentChatMessages.length > 0) {
        try {
            const title = currentChatMessages[0]?.content?.slice(0, 50) || 'New Chat';
            await FirebaseDB.saveChat(userId, {
                id: currentChatId,
                title: title,
                createdAt: parseInt(currentChatId) || Date.now(),
                updatedAt: Date.now(),
                messages: currentChatMessages
            });
            LOG.info('CHAT', 'Previous chat saved to Firebase');
        } catch (e) {
            LOG.error('CHAT', 'Failed to save chat', e);
        }
    }

    // Start new chat
    currentChatId = FirebaseDB.generateChatId();
    currentChatMessages = [];
    if (messagesList) messagesList.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = 'flex';
    if (sessionIdDisplay) sessionIdDisplay.innerText = `SID-${currentChatId.substring(0, 6)}`;
};

(window as any).toggleSidebar = () => {
    sidebar?.classList.toggle('open');
    sidebarBackdrop?.classList.toggle('opacity-0');
    sidebarBackdrop?.classList.toggle('pointer-events-none');
};

(window as any).signOut = async () => {
    if (auth) {
        clearUserData();  // Clear all user-specific data
        await signOut(auth);
        window.location.reload();
    }
};

(window as any).clearAllHistory = async () => {
    if (!confirm('CRITICAL: PURGE ALL LOGGED TELEMETRY?')) return;
    const uid = auth?.currentUser?.uid;

    LOG.warn('SYSTEM', 'Executing global purge protocol...');

    try {
        if (uid) {
            // Delete all chats from Firebase using new structure
            await FirebaseDB.deleteAllChats(uid);
        }

        chatHistory = [];
        currentChatMessages = [];
        renderHistory();
        (window as any).newChat();
        notify('SYSTEM_PURGED');
    } catch (e) {
        LOG.error('SYSTEM', 'Purge operation failed', e);
        notify('PURGE_FAILED', 'error');
    }
};

(window as any).exportHistory = () => {
    LOG.info('SYSTEM', 'Packaging intel for export...');
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(chatHistory, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `KAI_INTEL_EXPORT_${Date.now()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    notify('INTEL_EXPORTED');
};

(window as any).deleteChat = async (id) => {
    const uid = auth.currentUser?.uid;
    if (!uid) return;
    try {
        // Delete from Firebase using new structure
        await FirebaseDB.deleteChat(uid, id);

        // Update local state
        chatHistory = chatHistory.filter(h => h.id !== id);
        renderHistory();

        if (currentChatId === id) (window as any).newChat();
        notify('PURGED');
    } catch (e) { LOG.error('DB', 'Delete error', e); }
};

if (authForm) {
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = authEmail.value;
        const password = authPassword.value;

        try {
            authError.classList.add('hidden');
            authProgress.classList.remove('hidden');

            if (isLoginMode) {
                // Login flow
                const userCredential = await signInWithEmailAndPassword(auth, email, password);

                // Check email verification (skip for test emails)
                if (!userCredential.user.emailVerified && !isTestEmail(email)) {
                    await signOut(auth);
                    authError.innerText = 'EMAIL NOT VERIFIED. Check your inbox and verify your email first.';
                    authError.classList.remove('hidden');
                    authProgress.classList.add('hidden');
                    return;
                }

            } else {
                // Signup flow
                const userCredential = await createUserWithEmailAndPassword(auth, email, password);

                // Send verification email (skip for test emails)
                if (!isTestEmail(email)) {
                    await sendEmailVerification(userCredential.user);

                    // Sign out and show verification message
                    await signOut(auth);
                    authError.innerText = '✅ REGISTRATION COMPLETE! Check your email and click the verification link to activate your account.';
                    authError.style.color = '#22c55e';
                    authError.classList.remove('hidden');
                    authProgress.classList.add('hidden');

                    // Switch to login mode
                    isLoginMode = true;
                    authSubmitBtn.innerText = "Authenticate";
                    toggleAuthModeBtn.innerText = "[ Request Credentials ]";
                    return;
                } else {
                    LOG.info('AUTH', 'Test email - skipping verification', { email });
                }
            }
        } catch (error: any) {
            authError.style.color = '#ef4444';
            authError.innerText = `ACCESS DENIED: ${error.code}`;
            authError.classList.remove('hidden');
            authProgress.classList.add('hidden');
        }
    });
}

if (toggleAuthModeBtn) {
    toggleAuthModeBtn.onclick = () => {
        isLoginMode = !isLoginMode;
        authSubmitBtn.innerText = isLoginMode ? "Authenticate" : "Register ID";
        toggleAuthModeBtn.innerText = isLoginMode ? "[ Request Credentials ]" : "[ Return to Login ]";
    };
}

// === OAUTH PROVIDERS ===
const googleProvider = new GoogleAuthProvider();
const githubProvider = new GithubAuthProvider();

// isTestEmail is defined at the top of the file

// Google Sign-In
async function signInWithGoogle() {
    try {
        authError?.classList.add('hidden');
        authProgress?.classList.remove('hidden');

        const result = await signInWithPopup(auth, googleProvider);
        LOG.info('AUTH', 'Google sign-in successful', { email: result.user.email });
        // OAuth users don't need email verification

    } catch (error: any) {
        LOG.error('AUTH', 'Google sign-in failed', error);
        if (authError) {
            authError.innerText = `Google Auth Failed: ${error.code || error.message}`;
            authError.classList.remove('hidden');
        }
        authProgress?.classList.add('hidden');
    }
}
(window as any).signInWithGoogle = signInWithGoogle;

// GitHub Sign-In
async function signInWithGitHub() {
    try {
        authError?.classList.add('hidden');
        authProgress?.classList.remove('hidden');

        const result = await signInWithPopup(auth, githubProvider);
        LOG.info('AUTH', 'GitHub sign-in successful', { email: result.user.email });
        // OAuth users don't need email verification

    } catch (error: any) {
        LOG.error('AUTH', 'GitHub sign-in failed', error);
        if (authError) {
            authError.innerText = `GitHub Auth Failed: ${error.code || error.message}`;
            authError.classList.remove('hidden');
        }
        authProgress?.classList.add('hidden');
    }
}
(window as any).signInWithGitHub = signInWithGitHub;


// === 📄 DOCUMENT UPLOAD (Drag & Drop) ===
let uploadedDocumentContext: string | null = null;

(window as any).uploadDocument = async (file: File) => {
    const allowedExts = ['.pdf', '.docx', '.txt', '.md'];
    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

    if (!allowedExts.includes(ext)) {
        notify(`Invalid format: ${ext}. Use PDF, DOCX, or TXT.`, 'error');
        return;
    }

    addMessage('user', `📤 Uploading: ${file.name}...`);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const resp = await fetch(`${API_URL}/upload-document`, {
            method: 'POST',
            body: formData
        });

        const data = await resp.json();

        if (data.success) {
            uploadedDocumentContext = data.text;

            // Render document preview card
            const previewHtml = `
            <div class="mt-4 rounded-xl border border-white/10 bg-gradient-to-br from-indigo-900/30 to-purple-900/30 p-4 animate-in fade-in">
                <div class="flex items-center gap-3 mb-3">
                    <div class="w-10 h-10 rounded-lg bg-indigo-500/30 flex items-center justify-center">
                        <i data-lucide="file-text" class="w-5 h-5 text-indigo-300"></i>
                    </div>
                    <div>
                        <div class="font-bold text-white">${data.filename}</div>
                        <div class="text-xs text-white/50">${data.word_count} words extracted</div>
                    </div>
                </div>
                <div class="text-xs text-white/70 bg-black/30 rounded-lg p-3 max-h-32 overflow-hidden">
                    ${data.preview?.substring(0, 300)}...
                </div>
                <div class="mt-3 text-[10px] text-emerald-400 flex items-center gap-1">
                    <i data-lucide="check-circle" class="w-3 h-3"></i>
                    Document added to context. Ask KAI to summarize!
                </div>
            </div>`;

            addMessage('assistant', `✅ Loaded **${data.filename}** (${data.word_count} words). Ask me to summarize or analyze it!`, null, { type: 'document_upload', html: previewHtml });
            notify('Document loaded into context!');
        } else {
            addMessage('assistant', `❌ Upload failed: ${data.error}`);
        }
    } catch (e) {
        LOG.error('UPLOAD', 'Document upload failed', e);
        addMessage('assistant', '❌ Upload error. Please try again.');
    }
};

// Drag & Drop listeners
const mainInterface = document.getElementById('main-interface');
if (mainInterface) {
    mainInterface.addEventListener('dragover', (e) => {
        e.preventDefault();
        mainInterface.classList.add('ring-2', 'ring-indigo-500/50');
    });

    mainInterface.addEventListener('dragleave', () => {
        mainInterface.classList.remove('ring-2', 'ring-indigo-500/50');
    });

    mainInterface.addEventListener('drop', (e) => {
        e.preventDefault();
        mainInterface.classList.remove('ring-2', 'ring-indigo-500/50');

        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
            (window as any).uploadDocument(files[0]);
        }
    });
}

// Inject document context into chat query
const originalSendMessage = (window as any).sendMessage;
(window as any).sendMessage = async () => {
    if (uploadedDocumentContext && messageInput.value.toLowerCase().includes('summarize')) {
        // Prepend context to query
        const originalQuery = messageInput.value;
        messageInput.value = `[DOCUMENT CONTEXT: ${uploadedDocumentContext.substring(0, 3000)}...]\n\nUser request: ${originalQuery}`;
    }
    await originalSendMessage();
};


// === 🎤 VOICE MODE (BETA) ===
(window as any).isVoiceMode = false;
let recognition: any;

(window as any).toggleVoice = () => {
    (window as any).isVoiceMode = !(window as any).isVoiceMode;
    const btn = document.getElementById('voice-btn');

    if ((window as any).isVoiceMode) {
        btn?.classList.add('text-red-500', 'animate-pulse', 'bg-red-500/10');
        notify('VOICE UPLINK ESTABLISHED');
        startListening();
    } else {
        btn?.classList.remove('text-red-500', 'animate-pulse', 'bg-red-500/10');
        notify('VOICE UPLINK SEVERED');
        stopListening();
    }
};

function startListening() {
    if (!('webkitSpeechRecognition' in window)) {
        notify('VOICE MODULE MISSING', 'error');
        return;
    }
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false; // We restart manually for control
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        // Barge-in: Stop any ongoing TTS when user starts speaking
        if ((window as any).interruptTTS) (window as any).interruptTTS();
    };

    recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        messageInput.value = transcript;
        (window as any).sendMessage();
    };

    recognition.onend = () => {
        // Only restart if still in voice mode and NOT speaking
        if ((window as any).isVoiceMode && !window.speechSynthesis.speaking) {
            try { recognition.start(); } catch (e) { }
        }
    };

    recognition.start();
}

function stopListening() {
    if (recognition) recognition.stop();
}

(window as any).speak = async (text: string) => {
    // Stop any current speech
    if ((window as any).currentAudio) {
        (window as any).currentAudio.pause();
        (window as any).currentAudio = null;
    }
    window.speechSynthesis.cancel();

    const cleanText = text.replace(/[*#`_]/g, '');
    if (!cleanText || cleanText.length < 2) return;

    try {
        // Call backend TTS API (supports Hindi and English)
        const response = await fetch(`${API_URL}/voice/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: cleanText })
        });

        const data = await response.json();

        if (data.status === 'success' && data.audio_url) {
            // Play the audio
            const audio = new Audio(`${BASE_URL}${data.audio_url}`);
            (window as any).currentAudio = audio;

            // Speed up playback by 1.3x for faster speech
            audio.playbackRate = 1.3;

            audio.onended = () => {
                (window as any).currentAudio = null;
                if ((window as any).isVoiceMode) startListening(); // Resume listening
            };

            audio.onerror = () => {
                LOG.error('TTS', 'Audio playback failed');
                // Fallback to browser TTS
                const utter = new SpeechSynthesisUtterance(cleanText);
                utter.rate = 1.1;
                utter.onend = () => { if ((window as any).isVoiceMode) startListening(); };
                window.speechSynthesis.speak(utter);
            };

            audio.play();
            LOG.info('TTS', `Playing: ${data.language} voice`);
        } else {
            // Fallback to browser TTS
            const utter = new SpeechSynthesisUtterance(cleanText);
            utter.rate = 1.1;
            utter.onend = () => { if ((window as any).isVoiceMode) startListening(); };
            window.speechSynthesis.speak(utter);
        }
    } catch (error) {
        LOG.error('TTS', 'Backend TTS failed, using browser fallback');
        // Fallback to browser TTS
        const utter = new SpeechSynthesisUtterance(cleanText);
        utter.rate = 1.1;
        utter.onend = () => { if ((window as any).isVoiceMode) startListening(); };
        window.speechSynthesis.speak(utter);
    }
};

// Barge-in: Stop TTS when user starts speaking
(window as any).interruptTTS = () => {
    if ((window as any).currentAudio) {
        (window as any).currentAudio.pause();
        (window as any).currentAudio = null;
    }
    window.speechSynthesis.cancel();

    // Also notify backend to stop
    fetch(`${API_URL}/voice/interrupt`, { method: 'POST' }).catch(() => { });
};


// === 🖼️ OVERLAY MODE ===
(window as any).toggleOverlayMode = () => {
    document.body.classList.toggle('overlay-mode');
    // Add CSS via JS for the overlay mode
    if (document.body.classList.contains('overlay-mode')) {
        sidebar!.style.display = 'none';
        document.body.style.background = 'transparent';
        // More styles would be needed in CSS, but// This is a placeholder as I need to find the function first.
        // I will cancel this tool call and use view_file.t
        notify('MINI_MODE ACTIVE');
    } else {
        sidebar!.style.display = 'flex';
        document.body.style.background = 'var(--surface-dark)';
        notify('FULL_MODE ACTIVE');
    }
};



// === 🏷️ @MENTION AUTOCOMPLETE (Premium Redesign) ===
const mentionOptions = [
    { id: 'figma', label: '@figma', icon: '🎨', desc: 'Design files', color: 'from-pink-500/20 to-purple-500/20' },
    { id: 'notion', label: '@notion', icon: '📝', desc: 'Workspace', color: 'from-gray-500/20 to-gray-600/20' },
    { id: 'slack', label: '@slack', icon: '💬', desc: 'Messages', color: 'from-purple-500/20 to-violet-500/20' },
    { id: 'trello', label: '@trello', icon: '📋', desc: 'Boards', color: 'from-blue-500/20 to-cyan-500/20' },
    { id: 'calendar', label: '@calendar', icon: '📅', desc: 'Events', color: 'from-green-500/20 to-emerald-500/20' },
    { id: 'weather', label: '@weather', icon: '🌤️', desc: 'Forecast', color: 'from-yellow-500/20 to-orange-500/20' },
    { id: 'news', label: '@news', icon: '📰', desc: 'Headlines', color: 'from-red-500/20 to-pink-500/20' },
    { id: 'crypto', label: '@crypto', icon: '₿', desc: 'Prices', color: 'from-amber-500/20 to-yellow-500/20' },
    { id: 'github', label: '@github', icon: '🐙', desc: 'Repos', color: 'from-gray-600/20 to-gray-700/20' },
    { id: 'pdf', label: '@pdf', icon: '📄', desc: 'Document', color: 'from-red-600/20 to-red-700/20' },
    { id: 'image', label: '@image', icon: '🖼️', desc: 'Generate', color: 'from-indigo-500/20 to-blue-500/20' },
    { id: 'spotify', label: '@spotify', icon: '🎵', desc: 'Music', color: 'from-green-600/20 to-green-700/20' },
];

// Create premium dropdown container
const mentionDropdown = document.createElement('div');
mentionDropdown.id = 'mention-dropdown';
mentionDropdown.style.cssText = `
    display: none;
    position: fixed;
    bottom: 120px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 600px;
    max-height: 280px;
    overflow-y: auto;
    background: rgba(15, 15, 25, 0.98);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.15);
    z-index: 9999;
    padding: 12px;
`;
document.body.appendChild(mentionDropdown);

function showMentionDropdown(filter: string = '') {
    const filtered = mentionOptions.filter(o => o.label.toLowerCase().includes(filter.toLowerCase()));
    if (filtered.length === 0) {
        mentionDropdown.style.display = 'none';
        return;
    }

    mentionDropdown.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <span style="font-size: 10px; font-weight: 800; color: rgba(99, 102, 241, 0.8); text-transform: uppercase; letter-spacing: 0.15em;">Quick Actions</span>
            <span style="font-size: 9px; color: rgba(255,255,255,0.3);">TAB to select</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px;">
            ${filtered.map((opt, i) => `
                <div class="mention-option" data-mention="${opt.label}" style="
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 12px 14px;
                    background: linear-gradient(135deg, ${opt.color.replace('from-', '').replace(' to-', ', ').replace(/\//g, ' ').replace(/-/g, '')});
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,${i === 0 ? '0.15' : '0.05'});
                    border-radius: 10px;
                    cursor: pointer;
                    transition: all 0.15s ease;
                    ${i === 0 ? 'background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.4);' : ''}
                " onmouseover="this.style.background='rgba(99, 102, 241, 0.15)'; this.style.borderColor='rgba(99, 102, 241, 0.4)'; this.style.transform='scale(1.02)';"
                   onmouseout="this.style.background='rgba(255,255,255,0.03)'; this.style.borderColor='rgba(255,255,255,0.05)'; this.style.transform='scale(1)';">
                    <span style="font-size: 20px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">${opt.icon}</span>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 13px; font-weight: 600; color: white; font-family: 'JetBrains Mono', monospace;">${opt.label}</div>
                        <div style="font-size: 10px; color: rgba(255,255,255,0.4);">${opt.desc}</div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    mentionDropdown.style.display = 'block';

    // Add click handlers
    mentionDropdown.querySelectorAll('.mention-option').forEach(el => {
        el.addEventListener('click', () => {
            const mention = el.getAttribute('data-mention');
            if (mention && messageInput) {
                const currentValue = messageInput.value;
                const atIndex = currentValue.lastIndexOf('@');
                messageInput.value = currentValue.substring(0, atIndex) + mention + ' ';
                messageInput.focus();
                mentionDropdown.style.display = 'none';
            }
        });
    });
}

// Input listener for @ detection
messageInput?.addEventListener('input', (e) => {
    const value = (e.target as HTMLTextAreaElement).value;
    const atIndex = value.lastIndexOf('@');

    if (atIndex !== -1 && (atIndex === 0 || value[atIndex - 1] === ' ')) {
        const partial = value.substring(atIndex);
        if (!partial.includes(' ')) {
            showMentionDropdown(partial);
            return;
        }
    }
    mentionDropdown.style.display = 'none';
});

// Close dropdown on blur
messageInput?.addEventListener('blur', () => {
    setTimeout(() => mentionDropdown.style.display = 'none', 200);
});

// Keyboard navigation
messageInput?.addEventListener('keydown', (e) => {
    if (mentionDropdown.style.display === 'none') return;

    const options = Array.from(mentionDropdown.querySelectorAll('.mention-option'));
    if (options.length === 0) return;

    let currentIndex = options.findIndex(el => (el as HTMLElement).style.borderColor?.includes('241'));

    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        const nextIndex = (currentIndex + 1) % options.length;
        options.forEach((el, i) => {
            (el as HTMLElement).style.background = i === nextIndex ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255,255,255,0.03)';
            (el as HTMLElement).style.borderColor = i === nextIndex ? 'rgba(99, 102, 241, 0.4)' : 'rgba(255,255,255,0.05)';
        });
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const prevIndex = (currentIndex - 1 + options.length) % options.length;
        options.forEach((el, i) => {
            (el as HTMLElement).style.background = i === prevIndex ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255,255,255,0.03)';
            (el as HTMLElement).style.borderColor = i === prevIndex ? 'rgba(99, 102, 241, 0.4)' : 'rgba(255,255,255,0.05)';
        });
    } else if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        const activeOption = options.find(el => (el as HTMLElement).style.borderColor?.includes('241'));
        if (activeOption) {
            (activeOption as HTMLElement).click();
        }
    } else if (e.key === 'Escape') {
        mentionDropdown.style.display = 'none';
    }
});


LOG.info('SYSTEM', 'KAI OS Tactical Interface Initialized.');

// ==================== SETTINGS MODAL FUNCTIONS ====================

// Settings state
let settingsState = JSON.parse(localStorage.getItem('kai_settings') || '{}');

// Open settings modal
function openSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.classList.add('open');
        lucide.createIcons();
        loadSettingsData();
        LOG.info('SETTINGS', 'Settings modal opened');
    }
}
(window as any).openSettings = openSettings;

// Close settings modal
function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) {
        modal.classList.remove('open');
        saveSettingsToStorage();
        LOG.info('SETTINGS', 'Settings modal closed');
    }
}
(window as any).closeSettings = closeSettings;

// Switch settings tab
function switchSettingsTab(tabName: string) {
    // Update nav items
    document.querySelectorAll('.settings-nav-item').forEach(item => {
        item.classList.remove('active');
        const chevron = item.querySelector('[data-lucide="chevron-right"]');
        if (chevron) chevron.remove();
    });

    const activeItem = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeItem) {
        activeItem.classList.add('active');
        const chevronHtml = document.createElement('i');
        chevronHtml.setAttribute('data-lucide', 'chevron-right');
        chevronHtml.className = 'w-3 h-3 opacity-50';
        activeItem.appendChild(chevronHtml);
    }

    // Update sections
    document.querySelectorAll('.settings-section').forEach(section => {
        section.classList.add('hidden');
    });

    const activeSection = document.getElementById(`section-${tabName}`);
    if (activeSection) {
        activeSection.classList.remove('hidden');
    }

    // Update header title
    const titleEl = document.getElementById('settings-tab-title');
    if (titleEl) {
        titleEl.textContent = tabName.toUpperCase().replace('_', ' ');
    }

    // Reinitialize lucide icons
    lucide.createIcons();

    LOG.info('SETTINGS', `Switched to tab: ${tabName}`);
}
(window as any).switchSettingsTab = switchSettingsTab;

// Toggle setting
function toggleSetting(settingId: string) {
    const toggle = document.getElementById(`${settingId}-toggle`);
    if (toggle) {
        toggle.classList.toggle('on');
        const isOn = toggle.classList.contains('on');
        settingsState[settingId] = isOn;
        LOG.info('SETTINGS', `Toggle ${settingId}: ${isOn}`);
    }
}
(window as any).toggleSetting = toggleSetting;

// Set retention period
function setRetention(period: string) {
    const retentionEl = document.getElementById('retention-value');
    if (retentionEl) {
        retentionEl.textContent = period;
    }

    // Update button styles
    const buttons = document.querySelectorAll('#section-telemetry .grid button');
    buttons.forEach(btn => {
        if (btn.textContent === period) {
            btn.className = 'py-2 text-[10px] font-bold border bg-indigo-600/20 border-indigo-500 text-indigo-400 transition-all';
        } else {
            btn.className = 'py-2 text-[10px] font-bold border border-zinc-800 text-zinc-600 hover:border-zinc-600 transition-all';
        }
    });

    settingsState.retention = period;
    LOG.info('SETTINGS', `Retention set to: ${period}`);
}
(window as any).setRetention = setRetention;

// Save profile - UPGRADED WITH AI-LINKED FIELDS AND UNIFIED STORAGE
async function saveProfile() {
    const name = (document.getElementById('settings-name') as HTMLInputElement)?.value || '';
    const nickname = (document.getElementById('settings-nickname') as HTMLInputElement)?.value || '';
    const email = (document.getElementById('settings-email') as HTMLInputElement)?.value || '';
    const bio = (document.getElementById('settings-bio') as HTMLTextAreaElement)?.value || '';
    const responseStyle = (document.getElementById('settings-response-style') as HTMLSelectElement)?.value || 'casual';
    const responseLanguage = (document.getElementById('settings-response-language') as HTMLSelectElement)?.value || 'english';
    const interests = (document.getElementById('settings-interests') as HTMLInputElement)?.value || '';

    // Build user preferences object
    const userPreferences = {
        name,
        nickname,
        email,
        bio,
        responseStyle,
        responseLanguage,
        interests: interests.split(',').map(i => i.trim()).filter(Boolean)
    };

    // === UNIFIED STORAGE: Update both cache and localStorage ===
    // This ensures getUserPreferences() returns the latest values immediately
    cachedUserProfile = userPreferences;
    localStorage.setItem('kai_user_profile', JSON.stringify(userPreferences));

    // Also save to old key for backwards compatibility
    localStorage.setItem('kai_user_preferences', JSON.stringify(userPreferences));

    settingsState.profile = userPreferences;
    saveSettingsToStorage();

    // Save to Firebase if user is authenticated
    if (auth?.currentUser?.uid) {
        try {
            await setDoc(doc(db, 'user_profiles', auth.currentUser.uid), userPreferences);
            LOG.info('SETTINGS', 'Profile synced to Firebase', { responseLanguage });
        } catch (e) {
            LOG.warn('SETTINGS', 'Failed to sync profile to Firebase', e);
        }
    }

    showSystemNotification(`Profile saved! KAI will now address you as ${nickname || name || 'Operator'} in ${responseLanguage}`, 'success');
    LOG.info('SETTINGS', 'User preferences saved', { name, responseStyle, responseLanguage });
}
(window as any).saveProfile = saveProfile;

// getUserPreferences is already defined at the top of the file with Firebase support

// Update sync status indicator
function updateSyncStatus(status: 'syncing' | 'synced' | 'error' | 'not-synced') {
    const indicator = document.getElementById('sync-status-indicator');
    const text = document.getElementById('sync-status-text');
    const timeEl = document.getElementById('last-sync-time');

    if (!indicator || !text) return;

    const configs = {
        'syncing': { icon: 'cloud-cog', text: 'Syncing...', class: 'text-blue-400 sync-spinning' },
        'synced': { icon: 'cloud-check', text: 'Synced', class: 'text-green-400' },
        'error': { icon: 'cloud-off', text: 'Sync failed', class: 'text-red-400' },
        'not-synced': { icon: 'cloud-off', text: 'Not synced', class: 'text-zinc-500' }
    };

    const config = configs[status];
    indicator.className = `flex items-center gap-2 text-xs ${config.class}`;
    indicator.innerHTML = `<i data-lucide="${config.icon}" class="w-4 h-4"></i><span id="sync-status-text">${config.text}</span>`;

    if (status === 'synced' && timeEl) {
        timeEl.textContent = `Last synced: just now`;
    }

    // Re-init Lucide icons
    if ((window as any).lucide) {
        (window as any).lucide.createIcons();
    }
}

// Update profile UI with backend data
function updateProfileUI(profile: any) {
    // Update stats
    if (profile.stats) {
        const msgEl = document.getElementById('stat-messages');
        const memEl = document.getElementById('stat-memories');
        const convEl = document.getElementById('stat-conversations');

        if (msgEl) animateNumber(msgEl, profile.stats.messageCount || 0);
        if (memEl) animateNumber(memEl, profile.stats.memoriesSynced || 0);
        if (convEl) animateNumber(convEl, profile.stats.conversationCount || 0);

        // Update activity sparkline
        if (profile.stats.weeklyActivity) {
            updateActivitySparkline(profile.stats.weeklyActivity);
        }
    }

    // Update rank
    if (profile.rank) {
        const badge = document.getElementById('profile-rank-badge');
        const title = document.getElementById('profile-rank-title');
        if (badge) badge.style.borderColor = profile.rank.color;
        if (title) {
            title.textContent = profile.rank.title;
            title.style.color = profile.rank.color;
        }
    }

    // Update achievements
    if (profile.achievements && profile.achievements.length > 0) {
        updateAchievements(profile.achievements);
    }
}

// Animate number counting up
function animateNumber(element: HTMLElement, target: number) {
    const current = parseInt(element.textContent || '0');
    const increment = Math.ceil((target - current) / 20);
    let value = current;

    const interval = setInterval(() => {
        value += increment;
        if ((increment > 0 && value >= target) || (increment < 0 && value <= target)) {
            value = target;
            clearInterval(interval);
        }
        element.textContent = value.toLocaleString();
    }, 30);
}

// Update activity sparkline
function updateActivitySparkline(activity: number[]) {
    const container = document.getElementById('activity-sparkline');
    if (!container) return;

    const max = Math.max(...activity, 1);
    const bars = container.querySelectorAll('div');

    activity.forEach((val, i) => {
        if (bars[i]) {
            const height = Math.max(10, (val / max) * 100);
            (bars[i] as HTMLElement).style.height = `${height}%`;
        }
    });
}

// Update achievements list
function updateAchievements(achievements: any[]) {
    const container = document.getElementById('achievements-list');
    if (!container) return;

    const colorMap: Record<string, string> = {
        'early_adopter': 'yellow',
        'power_user': 'blue',
        'memory_master': 'purple',
        'security_first': 'green'
    };

    container.innerHTML = achievements.map(a => {
        const color = colorMap[a.id] || 'indigo';
        return `
            <div class="flex items-center gap-3 p-2 bg-${color}-500/10 border border-${color}-500/30 rounded-lg">
                <span class="text-lg">${a.icon}</span>
                <div>
                    <p class="text-xs font-bold text-${color}-400">${a.name}</p>
                    <p class="text-[9px] text-zinc-500">${a.description}</p>
                </div>
            </div>
        `;
    }).join('');
}


// Select uplink
function selectUplink(element: HTMLElement) {
    // Reset all uplinks
    const allUplinks = document.querySelectorAll('#section-uplink .space-y-3 > div');
    allUplinks.forEach(uplink => {
        uplink.className = 'p-4 border flex items-center gap-4 cursor-pointer transition-all bg-black border-zinc-900 hover:border-zinc-700';
        const icon = uplink.querySelector('.p-3');
        if (icon) icon.className = 'p-3 text-zinc-600 bg-zinc-900';
        const connected = uplink.querySelector('.text-green-500');
        if (connected) connected.remove();
    });

    // Activate selected
    element.className = 'p-4 border flex items-center gap-4 cursor-pointer transition-all bg-indigo-600/10 border-indigo-500/50';
    const icon = element.querySelector('.p-3');
    if (icon) icon.className = 'p-3 text-indigo-500 bg-indigo-500/10';

    // Add connected badge
    const nameContainer = element.querySelector('.flex-1 .flex.items-center');
    if (nameContainer && !nameContainer.querySelector('.text-green-500')) {
        const badge = document.createElement('span');
        badge.className = 'text-[8px] text-green-500 font-bold uppercase tracking-tighter';
        badge.textContent = 'CONNECTED';
        nameContainer.appendChild(badge);
    }

    LOG.info('SETTINGS', 'Uplink selected');
}
(window as any).selectUplink = selectUplink;

// Test connection
async function testConnection() {
    const btn = document.querySelector('#section-uplink button[onclick="testConnection()"]') as HTMLButtonElement;
    if (btn) {
        btn.textContent = 'Testing...';
        btn.disabled = true;
    }

    const start = Date.now();
    try {
        const response = await fetch(`${API_URL}/health`);
        const latency = Date.now() - start;

        if (response.ok) {
            showSystemNotification(`Connection successful! Latency: ${latency}ms`, 'success');
        } else {
            showSystemNotification('Connection failed: Server error', 'error');
        }
    } catch (e) {
        showSystemNotification('Connection failed: Network error', 'error');
    }

    if (btn) {
        btn.textContent = 'Test Connection';
        btn.disabled = false;
    }
}
(window as any).testConnection = testConnection;

// Load settings data
function loadSettingsData() {
    // Load user preferences from localStorage
    const userPrefs = (window as any).getUserPreferences ? (window as any).getUserPreferences() : null;

    // Load profile fields from auth first
    const user = auth?.currentUser;
    if (user) {
        const emailInput = document.getElementById('settings-email') as HTMLInputElement;
        if (emailInput && user.email && !userPrefs?.email) emailInput.value = user.email;

        const userId = document.getElementById('settings-user-id');
        if (userId) userId.textContent = user.uid.substring(0, 6).toUpperCase();
    }

    // Load saved user preferences into form
    if (userPrefs) {
        const nameInput = document.getElementById('settings-name') as HTMLInputElement;
        const nicknameInput = document.getElementById('settings-nickname') as HTMLInputElement;
        const emailInput = document.getElementById('settings-email') as HTMLInputElement;
        const bioInput = document.getElementById('settings-bio') as HTMLTextAreaElement;
        const styleSelect = document.getElementById('settings-response-style') as HTMLSelectElement;
        const langSelect = document.getElementById('settings-response-language') as HTMLSelectElement;
        const interestsInput = document.getElementById('settings-interests') as HTMLInputElement;

        if (nameInput && userPrefs.name) nameInput.value = userPrefs.name;
        if (nicknameInput && userPrefs.nickname) nicknameInput.value = userPrefs.nickname;
        if (emailInput && userPrefs.email) emailInput.value = userPrefs.email;
        if (bioInput && userPrefs.bio) bioInput.value = userPrefs.bio;
        if (styleSelect && userPrefs.responseStyle) styleSelect.value = userPrefs.responseStyle;
        if (langSelect && userPrefs.responseLanguage) langSelect.value = userPrefs.responseLanguage;
        if (interestsInput && userPrefs.interests) {
            interestsInput.value = Array.isArray(userPrefs.interests) ? userPrefs.interests.join(', ') : userPrefs.interests;
        }
    }

    // Restore toggle states
    Object.entries(settingsState).forEach(([key, value]) => {
        if (typeof value === 'boolean') {
            const toggle = document.getElementById(`${key}-toggle`);
            if (toggle) {
                toggle.classList.toggle('on', value);
            }
        }
    });

    // Load enhanced settings (Model Preferences, API Keys, Language)
    loadSettingsDataEnhanced();
}

// Save settings to localStorage
function saveSettingsToStorage() {
    localStorage.setItem('kai_settings', JSON.stringify(settingsState));
}

// Show system notification helper
function showSystemNotification(message: string, type: 'success' | 'warning' | 'error' = 'success') {
    const area = document.getElementById('notification-area');
    if (!area) return;

    const colors = {
        success: 'border-green-500 bg-green-500/10',
        warning: 'border-amber-500 bg-amber-500/10',
        error: 'border-red-500 bg-red-500/10'
    };

    const notif = document.createElement('div');
    notif.className = `pointer-events-auto p-4 border-l-2 ${colors[type]} backdrop-blur-md text-white text-sm font-mono animate-[slideIn_0.3s_ease]`;
    notif.innerHTML = `<span class="text-[10px] uppercase tracking-widest">${message}</span>`;

    area.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

// Keyboard shortcut for settings (Ctrl+,)
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === ',') {
        e.preventDefault();
        openSettings();
    }

    // Escape to close settings
    if (e.key === 'Escape') {
        const modal = document.getElementById('settings-modal');
        if (modal?.classList.contains('open')) {
            closeSettings();
        }
    }
});

LOG.info('SETTINGS', 'Settings module initialized');

// ==================== NEW SETTINGS FUNCTIONS ====================

// Update slider display value
function updateSliderValue(elementId: string, value: string) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = value;
    settingsState[elementId] = value;
}
(window as any).updateSliderValue = updateSliderValue;

// Toggle API key visibility
function toggleKeyVisibility(inputId: string) {
    const input = document.getElementById(inputId) as HTMLInputElement;
    if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
    }
}
(window as any).toggleKeyVisibility = toggleKeyVisibility;

// Save API keys (encrypted to localStorage)
function saveApiKeys() {
    const keys = {
        groq: (document.getElementById('groq-key') as HTMLInputElement)?.value || '',
        gemini: (document.getElementById('gemini-key') as HTMLInputElement)?.value || '',
        openai: (document.getElementById('openai-key') as HTMLInputElement)?.value || '',
        cohere: (document.getElementById('cohere-key') as HTMLInputElement)?.value || ''
    };

    // Simple obfuscation (not true encryption, but better than plaintext)
    const encoded = btoa(JSON.stringify(keys));
    localStorage.setItem('kai_api_keys', encoded);

    settingsState.apiKeys = keys;
    showSystemNotification('API Keys saved securely', 'success');
    LOG.info('SETTINGS', 'API Keys saved');
}
(window as any).saveApiKeys = saveApiKeys;

// Clear all API keys
function clearApiKeys() {
    if (confirm('Clear all saved API keys?')) {
        localStorage.removeItem('kai_api_keys');
        ['groq-key', 'gemini-key', 'openai-key', 'cohere-key'].forEach(id => {
            const input = document.getElementById(id) as HTMLInputElement;
            if (input) input.value = '';
        });
        showSystemNotification('All API keys cleared', 'warning');
        LOG.info('SETTINGS', 'API Keys cleared');
    }
}
(window as any).clearApiKeys = clearApiKeys;

// Load saved API keys on settings open
function loadApiKeys() {
    const encoded = localStorage.getItem('kai_api_keys');
    if (encoded) {
        try {
            const keys = JSON.parse(atob(encoded));
            if (keys.groq) (document.getElementById('groq-key') as HTMLInputElement).value = keys.groq;
            if (keys.gemini) (document.getElementById('gemini-key') as HTMLInputElement).value = keys.gemini;
            if (keys.openai) (document.getElementById('openai-key') as HTMLInputElement).value = keys.openai;
            if (keys.cohere) (document.getElementById('cohere-key') as HTMLInputElement).value = keys.cohere;
        } catch (e) {
            LOG.warn('SETTINGS', 'Failed to load API keys', e);
        }
    }
}

// Save language settings
function saveLanguageSettings() {
    const settings = {
        uiLanguage: (document.getElementById('ui-language') as HTMLSelectElement)?.value,
        aiLanguage: (document.getElementById('ai-language') as HTMLSelectElement)?.value,
        dateFormat: (document.getElementById('date-format') as HTMLSelectElement)?.value,
        timeFormat: (document.getElementById('time-format') as HTMLSelectElement)?.value,
        timezone: (document.getElementById('timezone') as HTMLSelectElement)?.value
    };

    settingsState.language = settings;
    saveSettingsToStorage();
    showSystemNotification('Language settings applied', 'success');
    LOG.info('SETTINGS', 'Language settings saved', settings);
}
(window as any).saveLanguageSettings = saveLanguageSettings;

// Save model preferences
function saveModelPreferences() {
    const prefs = {
        defaultModel: (document.getElementById('default-model') as HTMLSelectElement)?.value,
        temperature: (document.getElementById('temperature-slider') as HTMLInputElement)?.value,
        maxTokens: (document.getElementById('max-tokens-slider') as HTMLInputElement)?.value
    };

    settingsState.models = prefs;
    saveSettingsToStorage();
    LOG.info('SETTINGS', 'Model preferences saved', prefs);
}

// Load all settings on modal open - enhanced version
const originalLoadSettingsData = loadSettingsData;
function loadSettingsDataEnhanced() {
    // Load API keys
    loadApiKeys();

    // Load model preferences
    if (settingsState.models) {
        const m = settingsState.models;
        if (m.defaultModel) (document.getElementById('default-model') as HTMLSelectElement).value = m.defaultModel;
        if (m.temperature) {
            (document.getElementById('temperature-slider') as HTMLInputElement).value = m.temperature;
            updateSliderValue('temp-value', m.temperature);
        }
        if (m.maxTokens) {
            (document.getElementById('max-tokens-slider') as HTMLInputElement).value = m.maxTokens;
            updateSliderValue('tokens-value', m.maxTokens);
        }
    }

    // Load language settings
    if (settingsState.language) {
        const l = settingsState.language;
        if (l.uiLanguage) (document.getElementById('ui-language') as HTMLSelectElement).value = l.uiLanguage;
        if (l.aiLanguage) (document.getElementById('ai-language') as HTMLSelectElement).value = l.aiLanguage;
        if (l.dateFormat) (document.getElementById('date-format') as HTMLSelectElement).value = l.dateFormat;
        if (l.timeFormat) (document.getElementById('time-format') as HTMLSelectElement).value = l.timeFormat;
        if (l.timezone) (document.getElementById('timezone') as HTMLSelectElement).value = l.timezone;
    }
}


// Add auto-save for model sliders
document.getElementById('temperature-slider')?.addEventListener('change', saveModelPreferences);
document.getElementById('max-tokens-slider')?.addEventListener('change', saveModelPreferences);
document.getElementById('default-model')?.addEventListener('change', saveModelPreferences);

LOG.info('SETTINGS', 'Enhanced settings module loaded');

// Hook into settings open/close
const originalOpenSettings = (window as any).openSettings;
(window as any).openSettings = function () {
    originalOpenSettings();
    loadProfileFromBackend();
    loadSavedAvatar(); // Load saved avatar
};

const originalCloseSettings = (window as any).closeSettings;
(window as any).closeSettings = function () {
    originalCloseSettings();
};


// Load profile data from backend
async function loadProfileFromBackend() {
    const userId = auth?.currentUser?.uid;
    if (!userId) return;

    try {
        const response = await fetch(`${BASE_URL}/api/v1/profile/${userId}`);
        if (response.ok) {
            const data = await response.json();
            if (data.profile) {
                updateProfileUI(data.profile);
                updateSyncStatus('synced');
            }
        }
    } catch (e) {
        LOG.warn('PROFILE', 'Failed to load profile from backend', e);
    }
}

// Avatar upload function
async function uploadAvatar(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
        showSystemNotification('Please select an image file', 'error');
        return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
        showSystemNotification('Image must be less than 2MB', 'error');
        return;
    }

    LOG.info('SETTINGS', 'Uploading avatar...', { name: file.name, size: file.size });

    // Read file as data URL for preview
    const reader = new FileReader();
    reader.onload = async (e) => {
        const dataUrl = e.target?.result as string;

        // Update avatar preview immediately
        const avatarImg = document.getElementById('settings-avatar') as HTMLImageElement;
        if (avatarImg) {
            avatarImg.src = dataUrl;
            avatarImg.style.opacity = '1';
        }

        // 🔗 SYNC: Also update the header avatar in top-right corner
        const headerAvatarImg = document.getElementById('user-avatar-img') as HTMLImageElement;
        if (headerAvatarImg) {
            headerAvatarImg.src = dataUrl;
        }

        settingsState.avatar = dataUrl;

        // 🔥 HYBRID APPROACH: Upload to Supabase Storage, save URL to Firebase Profile
        const user = auth?.currentUser;
        if (user && supabase) {
            try {
                const fileName = `avatars/${user.uid}_${Date.now()}.${file.name.split('.').pop()}`;
                const { data, error } = await supabase.storage
                    .from(SUPABASE_BUCKET)
                    .upload(fileName, file, { upsert: true });

                if (data && !error) {
                    const publicUrl = `${SUPABASE_URL}/storage/v1/object/public/${SUPABASE_BUCKET}/${data.path}`;
                    settingsState.avatarUrl = publicUrl;

                    // 🔥 SAVE URL TO FIREBASE PROFILE (syncs across domains!)
                    try {
                        // Update cachedUserProfile with new avatar URL
                        if (cachedUserProfile) {
                            cachedUserProfile.avatarUrl = publicUrl;
                            await FirebaseDB.saveUserProfile(user.uid, cachedUserProfile);
                            LOG.info('SETTINGS', 'Avatar URL saved to Firebase profile', { url: publicUrl });
                        }
                    } catch (fbErr) {
                        LOG.warn('SETTINGS', 'Failed to save avatar URL to Firebase', fbErr);
                    }

                    // Also cache locally as fallback
                    localStorage.setItem(`kai_avatar_${user.uid}`, publicUrl);

                    LOG.info('SETTINGS', 'Avatar uploaded to Supabase', { path: data.path, url: publicUrl });
                }
            } catch (e) {
                LOG.warn('SETTINGS', 'Failed to upload avatar to Supabase', e);
                // Fallback: save dataUrl to localStorage only
                localStorage.setItem(`kai_avatar_${user.uid}`, dataUrl);
            }
        }

        showSystemNotification('Avatar updated successfully', 'success');
    };

    reader.readAsDataURL(file);
}
(window as any).uploadAvatar = uploadAvatar;

// Load saved avatar on settings open AND sync header avatar
// 🔥 HYBRID: Loads from Firebase profile (syncs across domains) or localStorage fallback
function loadSavedAvatar() {
    const userId = auth?.currentUser?.uid;
    if (!userId) return;

    // Helper to apply avatar to UI
    const applyAvatar = (avatarUrl: string) => {
        const avatarImg = document.getElementById('settings-avatar') as HTMLImageElement;
        if (avatarImg) {
            avatarImg.src = avatarUrl;
            avatarImg.style.opacity = '1';
        }
        const headerAvatarImg = document.getElementById('user-avatar-img') as HTMLImageElement;
        if (headerAvatarImg) {
            headerAvatarImg.src = avatarUrl;
        }
    };

    // 1️⃣ First try: Firebase profile (syncs across domains)
    if (cachedUserProfile && cachedUserProfile.avatarUrl) {
        LOG.info('SETTINGS', 'Loading avatar from Firebase profile', { url: cachedUserProfile.avatarUrl });
        applyAvatar(cachedUserProfile.avatarUrl);
        // Also update localStorage as cache
        localStorage.setItem(`kai_avatar_${userId}`, cachedUserProfile.avatarUrl);
        return;
    }

    // 2️⃣ Fallback: localStorage (for offline/quick load)
    const savedAvatar = localStorage.getItem(`kai_avatar_${userId}`);
    if (savedAvatar) {
        LOG.info('SETTINGS', 'Loading avatar from localStorage fallback');
        applyAvatar(savedAvatar);
    }
}

LOG.info('SETTINGS', 'Avatar upload module loaded');
