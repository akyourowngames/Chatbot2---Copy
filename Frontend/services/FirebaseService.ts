// Firebase Database Service
// All user data stored in Firestore with proper isolation

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import {
    getFirestore,
    doc,
    setDoc,
    getDoc,
    collection,
    getDocs,
    deleteDoc,
    query,
    orderBy,
    serverTimestamp,
    Timestamp
} from 'firebase/firestore';

// Firebase Config
const firebaseConfig = {
    apiKey: "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk",
    authDomain: "kai-g-80f9c.firebaseapp.com",
    projectId: "kai-g-80f9c",
    storageBucket: "kai-g-80f9c.appspot.com",
    messagingSenderId: "125633190886",
    appId: "1:125633190886:web:65e1a7b4f59048a1768853"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

// ============ TYPES ============
export interface UserProfile {
    name: string;
    nickname: string;
    email: string;
    bio: string;
    responseStyle: 'casual' | 'professional' | 'brief' | 'detailed' | 'technical';
    responseLanguage: string;
    interests: string[];
    avatarUrl: string;
}

export interface UserSettings {
    theme: 'dark' | 'light' | 'system';
    notifications: boolean;
    retention: '24H' | '7D' | '30D' | 'FULL';
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}

export interface Chat {
    id: string;
    title: string;
    createdAt: number;
    updatedAt: number;
    messages: ChatMessage[];
}

// ============ PROFILE ============
export async function saveUserProfile(userId: string, profile: UserProfile): Promise<void> {
    try {
        await setDoc(doc(db, 'users', userId, 'data', 'profile'), profile);
        console.log('[Firebase] Profile saved');
    } catch (e) {
        console.error('[Firebase] Failed to save profile:', e);
        throw e;
    }
}

export async function loadUserProfile(userId: string): Promise<UserProfile | null> {
    try {
        const docSnap = await getDoc(doc(db, 'users', userId, 'data', 'profile'));
        if (docSnap.exists()) {
            console.log('[Firebase] Profile loaded');
            return docSnap.data() as UserProfile;
        }
        return null;
    } catch (e) {
        console.error('[Firebase] Failed to load profile:', e);
        return null;
    }
}

// ============ SETTINGS ============
export async function saveUserSettings(userId: string, settings: UserSettings): Promise<void> {
    try {
        await setDoc(doc(db, 'users', userId, 'data', 'settings'), settings);
        console.log('[Firebase] Settings saved');
    } catch (e) {
        console.error('[Firebase] Failed to save settings:', e);
        throw e;
    }
}

export async function loadUserSettings(userId: string): Promise<UserSettings | null> {
    try {
        const docSnap = await getDoc(doc(db, 'users', userId, 'data', 'settings'));
        if (docSnap.exists()) {
            console.log('[Firebase] Settings loaded');
            return docSnap.data() as UserSettings;
        }
        return null;
    } catch (e) {
        console.error('[Firebase] Failed to load settings:', e);
        return null;
    }
}

// ============ CHATS ============
export async function saveChat(userId: string, chat: Chat): Promise<void> {
    try {
        await setDoc(doc(db, 'users', userId, 'chats', chat.id), {
            title: chat.title,
            createdAt: chat.createdAt,
            updatedAt: Date.now(),
            messages: chat.messages
        });
        console.log('[Firebase] Chat saved:', chat.id);
    } catch (e) {
        console.error('[Firebase] Failed to save chat:', e);
        throw e;
    }
}

export async function loadChats(userId: string): Promise<Chat[]> {
    try {
        const chatsRef = collection(db, 'users', userId, 'chats');
        const q = query(chatsRef, orderBy('updatedAt', 'desc'));
        const snapshot = await getDocs(q);

        const chats: Chat[] = [];
        snapshot.forEach(doc => {
            chats.push({
                id: doc.id,
                ...doc.data()
            } as Chat);
        });

        console.log('[Firebase] Loaded', chats.length, 'chats');
        return chats;
    } catch (e) {
        console.error('[Firebase] Failed to load chats:', e);
        return [];
    }
}

export async function loadChat(userId: string, chatId: string): Promise<Chat | null> {
    try {
        const docSnap = await getDoc(doc(db, 'users', userId, 'chats', chatId));
        if (docSnap.exists()) {
            return {
                id: docSnap.id,
                ...docSnap.data()
            } as Chat;
        }
        return null;
    } catch (e) {
        console.error('[Firebase] Failed to load chat:', e);
        return null;
    }
}

export async function deleteChat(userId: string, chatId: string): Promise<void> {
    try {
        await deleteDoc(doc(db, 'users', userId, 'chats', chatId));
        console.log('[Firebase] Chat deleted:', chatId);
    } catch (e) {
        console.error('[Firebase] Failed to delete chat:', e);
        throw e;
    }
}

export async function deleteAllChats(userId: string): Promise<void> {
    try {
        const chatsRef = collection(db, 'users', userId, 'chats');
        const snapshot = await getDocs(chatsRef);

        const deletePromises = snapshot.docs.map(doc => deleteDoc(doc.ref));
        await Promise.all(deletePromises);

        console.log('[Firebase] All chats deleted');
    } catch (e) {
        console.error('[Firebase] Failed to delete all chats:', e);
        throw e;
    }
}

// ============ HELPER ============
export function generateChatId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

export function getChatTitle(firstMessage: string): string {
    // Generate title from first message (first 50 chars)
    const title = firstMessage.slice(0, 50).trim();
    return title.length < firstMessage.length ? title + '...' : title;
}
