
// @ts-nocheck
import { createClient } from "@supabase/supabase-js";
import { initializeApp } from 'firebase/app';
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged } from "firebase/auth";
import { getFirestore, collection, addDoc, query, where, getDocs, deleteDoc, doc, writeBatch } from "firebase/firestore";

declare var lucide: any;
declare var Prism: any;
declare var marked: any;
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
const USE_CLOUD_API = true;
const BASE_URL = USE_CLOUD_API ? 'https://kai-api-nxxv.onrender.com' : 'http://localhost:5000';
const API_URL = `${BASE_URL}/api/v1`;

// 📦 Supabase Configuration
const SUPABASE_URL = 'https://skbfmcwrshxnmaxfqyaw.supabase.co';
const SUPABASE_KEY = 'sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v';
const SUPABASE_BUCKET = 'kai-images';
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// State
let isProcessing = false;
let chatHistory: any[] = JSON.parse(localStorage.getItem('kai_chat_history') || '[]');
let currentChatId = Date.now().toString();
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
const authEmail = document.getElementById('auth-email') as HTMLInputElement;
const authPassword = document.getElementById('auth-password') as HTMLInputElement;
const authSubmitBtn = document.getElementById('auth-submit-btn') as HTMLButtonElement;
const toggleAuthModeBtn = document.getElementById('toggle-auth-mode') as HTMLButtonElement;
const authError = document.getElementById('auth-error') as HTMLElement;
const authProgress = document.getElementById('auth-progress') as HTMLElement;
const authBar = document.getElementById('auth-bar') as HTMLElement;
const authPercent = document.getElementById('auth-percent') as HTMLElement;

// Formatting
function formatMessage(text: string) {
    if (typeof marked === 'undefined') return text;
    const renderer = new marked.Renderer();
    renderer.code = (code: string, language: string) => {
        return `<div class="code-container my-4 border border-white/10 group relative">
            <div class="px-4 py-2 bg-white/5 border-b border-white/10 flex justify-between items-center">
                <span class="text-[9px] font-mono text-indigo-300/70 uppercase tracking-widest">${language || 'RAW_BUFFER'}</span>
            </div>
            <pre class="p-4 custom-scrollbar overflow-x-auto"><code class="language-${language}">${code}</code></pre>
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
    const uniqueChats = chatHistory.reduce((acc: any[], current: any) => {
        const x = acc.find(item => item.id === current.id);
        return x ? acc : acc.concat([current]);
    }, []).reverse();

    chatHistoryList.innerHTML = uniqueChats.length ? '' : `<div class="px-3 py-2 text-[10px] text-white/20 font-mono italic text-center">EMPTY_LOGS</div>`;

    uniqueChats.slice(0, 15).forEach(chat => {
        const container = document.createElement('div');
        container.className = 'group flex items-center justify-between hover:bg-white/5 border-l-2 border-transparent hover:border-indigo-500 transition-all px-3 py-1';

        const btn = document.createElement('button');
        btn.className = 'flex-1 text-left py-2 text-[10px] text-white/40 group-hover:text-white truncate font-mono uppercase tracking-widest';
        btn.innerText = chat.user.substring(0, 24) + (chat.user.length > 24 ? '...' : '');
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
    if (!data || !data.articles) return;

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
    const block = document.createElement('div');
    block.className = `msg-block ${role} group`;

    const header = document.createElement('div');
    header.className = 'flex items-center gap-2 mb-3 opacity-60 font-mono text-[10px] uppercase tracking-[0.2em]';
    header.innerHTML = role === 'assistant'
        ? `<div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse"></div> <span class="text-indigo-400 font-bold">KAI_SYS_INTEL</span> <span>${new Date().toLocaleTimeString()}</span>`
        : `<span class="text-white/60 font-bold">OPERATOR_TRANS</span> <span>${new Date().toLocaleTimeString()}</span>`;

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



    messagesList.appendChild(block);
    scrollToBottom();
    try {
        if (typeof lucide !== 'undefined') lucide.createIcons();
        if (typeof Prism !== 'undefined') Prism.highlightAllUnder(block);
    } catch (e) { }
}

async function loadChat(id: string) {
    currentChatId = id;
    if (sessionIdDisplay) sessionIdDisplay.innerText = `SID-${id.substring(0, 6)}`;
    if (messagesList) {
        messagesList.innerHTML = '';
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        messagesList.classList.remove('hidden');
        messagesList.classList.add('flex');
    }
    chatHistory.filter(h => h.id === id).forEach(h => {
        addMessage('user', h.user);
        // Pass saved metadata to restore PDF/Spotify/Anime previews
        addMessage('assistant', h.assistant, null, h.metadata || null);
    });
}

async function loadHistoryFromCloud(uid: string) {
    if (!db) return;
    try {
        const q = query(collection(db, "chat_history"), where("uid", "==", uid));
        const querySnapshot = await getDocs(q);
        const cloudHistory: any[] = [];
        querySnapshot.forEach((doc) => {
            const data = doc.data();
            data.docId = doc.id;
            cloudHistory.push(data);
        });
        cloudHistory.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
        if (cloudHistory.length > 0) {
            chatHistory = cloudHistory;
            localStorage.setItem('kai_chat_history', JSON.stringify(chatHistory));
            renderHistory();
        }
    } catch (e) { LOG.error('DATABASE', 'Sync failure', e); }
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
    onAuthStateChanged(auth, (user) => {
        if (user) {
            LOG.info('AUTH', 'Uplink active', { email: user.email });
            document.getElementById('auth-container')!.style.display = 'none';
            document.getElementById('main-interface')!.style.opacity = '1';
            document.getElementById('main-interface')!.style.pointerEvents = 'auto';
            initApp();
            loadHistoryFromCloud(user.uid);
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

    addMessage('user', queryStr);
    messageInput.value = '';
    messageInput.style.height = 'auto';

    isProcessing = true;

    // 💬 Show typing indicator
    let typingIndicator: HTMLElement | null = null;
    if (messagesList) {
        typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
            <span class="ml-3 text-xs font-mono text-white/50 uppercase tracking-widest">KAI is processing...</span>
        `;
        messagesList.appendChild(typingIndicator);
        scrollToBottom();
    }

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: queryStr, session_id: currentChatId, uid: auth?.currentUser?.uid })
        });
        const data = await response.json();

        // 🔍 DEBUG: Log API response to trace Spotify/media metadata
        LOG.info('API', 'Response received', { type: data.type, hasSpotify: !!data.spotify, hasAnime: !!data.anime });
        if (data.type === 'spotify' || data.type === 'music') {
            LOG.info('SPOTIFY', 'Full response data', data);
            LOG.info('SPOTIFY', 'Embed URL', data.spotify?.embed_url);
        }

        // 💬 Remove typing indicator
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }

        addMessage('assistant', data.response || "NO_DATA", null, data);

        // 🗣️ AUTO-SPEAK Logic (Voice Mode)
        if ((window as any).isVoiceMode) {
            (window as any).speak(data.response);
        }

        const historyItem = { timestamp: Date.now(), user: queryStr, assistant: data.response, id: currentChatId, uid: auth?.currentUser?.uid, metadata: data };
        chatHistory.push(historyItem);
        localStorage.setItem('kai_chat_history', JSON.stringify(chatHistory));
        renderHistory();
        if (db && auth?.currentUser) addDoc(collection(db, "chat_history"), historyItem);
    } catch (e) {
        // Remove typing indicator on error too
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }
        addMessage('assistant', "[!] CRITICAL UPLINK ERROR");
    } finally {
        isProcessing = false;
    }
};

(window as any).newChat = () => {
    currentChatId = Date.now().toString();
    if (messagesList) messagesList.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = 'flex';
    if (sessionIdDisplay) sessionIdDisplay.innerText = `SID-${currentChatId.substring(0, 6)}`;
};

(window as any).toggleSidebar = () => {
    sidebar?.classList.toggle('open');
    sidebarBackdrop?.classList.toggle('opacity-0');
    sidebarBackdrop?.classList.toggle('pointer-events-none');
};

(window as any).signOut = () => auth && signOut(auth).then(() => window.location.reload());

(window as any).clearAllHistory = async () => {
    if (!confirm('CRITICAL: PURGE ALL LOGGED TELEMETRY?')) return;
    const uid = auth?.currentUser?.uid;

    LOG.warn('SYSTEM', 'Executing global purge protocol...');

    try {
        if (db && uid) {
            const q = query(collection(db, "chat_history"), where("uid", "==", uid));
            const snap = await getDocs(q);
            const batch = writeBatch(db);
            snap.forEach(d => batch.delete(doc(db, "chat_history", d.id)));
            await batch.commit();
        }

        chatHistory = [];
        localStorage.removeItem('kai_chat_history');
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
        const q = query(collection(db, "chat_history"), where("uid", "==", uid), where("id", "==", id));
        const snap = await getDocs(q);
        const batch = writeBatch(db);
        snap.forEach(d => batch.delete(doc(db, "chat_history", d.id)));
        await batch.commit();
        chatHistory = chatHistory.filter(h => h.id !== id);
        localStorage.setItem('kai_chat_history', JSON.stringify(chatHistory));
        renderHistory();
        if (currentChatId === id) (window as any).newChat();
        notify('PURGED');
    } catch (e) { LOG.error('DB', 'Delete error', e); }
};

if (authForm) {
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            authError.classList.add('hidden');
            authProgress.classList.remove('hidden');
            if (isLoginMode) await signInWithEmailAndPassword(auth, authEmail.value, authPassword.value);
            else await createUserWithEmailAndPassword(auth, authEmail.value, authPassword.value);
        } catch (error: any) {
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
        // Visual feedback could go here
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

(window as any).speak = (text: string) => {
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#`_]/g, '');
    const utter = new SpeechSynthesisUtterance(cleanText);
    utter.rate = 1.1;
    utter.pitch = 1.0;

    utter.onend = () => {
        if ((window as any).isVoiceMode) startListening(); // Resume listening
    };

    window.speechSynthesis.speak(utter);
};


// === 🖼️ OVERLAY MODE ===
(window as any).toggleOverlayMode = () => {
    document.body.classList.toggle('overlay-mode');
    // Add CSS via JS for the overlay mode
    if (document.body.classList.contains('overlay-mode')) {
        sidebar!.style.display = 'none';
        document.body.style.background = 'transparent';
        // More styles would be needed in CSS, but this is a start
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

