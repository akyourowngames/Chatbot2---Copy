
import React, { useState, useEffect, useRef } from 'react';
import { Camera, Save, Check, Loader2, Upload } from 'lucide-react';
import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc } from 'firebase/firestore';
import { createClient } from '@supabase/supabase-js';

// Firebase Config
const firebaseConfig = {
  apiKey: "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk",
  authDomain: "kai-g-80f9c.firebaseapp.com",
  projectId: "kai-g-80f9c",
  storageBucket: "kai-g-80f9c.appspot.com",
  messagingSenderId: "125633190886",
  appId: "1:125633190886:web:65e1a7b4f59048a1768853"
};

// Supabase Config (for profile images)
const SUPABASE_URL = 'https://skbfmcwrshxnmaxfqyaw.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrYmZtY3dyc2h4bm1heGZxeWF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQxNjYyMzksImV4cCI6MjA0OTc0MjIzOX0.bPoaXy5XxP4vhrE9VK8F8i_5As78GYUdlGAMLqLLjNw';
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

interface UserProfile {
  name: string;
  nickname: string;
  email: string;
  bio: string;
  responseStyle: 'casual' | 'professional' | 'brief' | 'detailed' | 'technical';
  responseLanguage: 'english' | 'hindi' | 'hinglish';
  interests: string[];
  avatarUrl: string;
}

const ProfileSection: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    nickname: '',
    email: '',
    bio: '',
    responseStyle: 'casual',
    responseLanguage: 'english',
    interests: [],
    avatarUrl: ''
  });

  const [interestsInput, setInterestsInput] = useState('');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Listen for auth state and load profile from Firebase
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        setUserId(user.uid);

        // Load profile from Firestore
        try {
          const profileDoc = await getDoc(doc(db, 'users', user.uid, 'data', 'profile'));
          if (profileDoc.exists()) {
            const data = profileDoc.data() as UserProfile;
            setProfile(data);
            setInterestsInput(data.interests?.join(', ') || '');
            console.log('[ProfileSection] Profile loaded from Firebase:', data);
          } else {
            // No profile in Firebase yet, create default from auth data
            const defaultProfile: UserProfile = {
              name: user.displayName || '',
              nickname: '',
              email: user.email || '',
              bio: '',
              responseStyle: 'casual',
              responseLanguage: 'english',
              interests: [],
              avatarUrl: user.photoURL || ''
            };
            setProfile(defaultProfile);
            setInterestsInput('');
            console.log('[ProfileSection] No profile found, using defaults from auth');
          }
        } catch (e) {
          console.error('[ProfileSection] Failed to load profile from Firebase:', e);
          // On error, fallback to auth data
          const defaultProfile: UserProfile = {
            name: user.displayName || '',
            nickname: '',
            email: user.email || '',
            bio: '',
            responseStyle: 'casual',
            responseLanguage: 'english',
            interests: [],
            avatarUrl: user.photoURL || ''
          };
          setProfile(defaultProfile);
          setInterestsInput('');
        }
      } else {
        // User signed out - reset everything
        setUserId(null);
        setProfile({
          name: '',
          nickname: '',
          email: '',
          bio: '',
          responseStyle: 'casual',
          responseLanguage: 'english',
          interests: [],
          avatarUrl: ''
        });
        setInterestsInput('');
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Handle profile image upload to Supabase
  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !userId) return;

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      alert('Image must be smaller than 2MB');
      return;
    }

    setUploadingImage(true);
    try {
      // Convert image to base64 data URL (no Supabase needed - fixes signature error)
      const reader = new FileReader();
      reader.onloadend = async () => {
        const newAvatarUrl = reader.result as string;
        setProfile(prev => ({ ...prev, avatarUrl: newAvatarUrl }));

        // Auto-save avatar to Firebase (main app will sync via Firestore listener)
        const updatedProfile = { ...profile, avatarUrl: newAvatarUrl };
        await setDoc(doc(db, 'users', userId, 'data', 'profile'), updatedProfile, { merge: true });

        console.log('[ProfileSection] ✅ Avatar saved as data URL to Firebase');
        setUploadingImage(false);
      };

      reader.onerror = () => {
        console.error('Failed to read image file');
        alert('Failed to upload image. Please try again.');
        setUploadingImage(false);
      };

      reader.readAsDataURL(file);
    } catch (e) {
      console.error('Failed to upload image:', e);
      alert('Failed to upload image. Please try again.');
      setUploadingImage(false);
    }
  };

  const handleSave = async () => {
    if (!userId) {
      alert('Please sign in to save your profile');
      return;
    }

    setSaving(true);
    try {
      // Parse interests from comma-separated string
      const interestsArray = interestsInput
        .split(',')
        .map(i => i.trim())
        .filter(i => i.length > 0);

      const updatedProfile: UserProfile = {
        ...profile,
        interests: interestsArray
      };

      console.log('[ProfileSection] 💾 Saving profile to Firebase:', updatedProfile);
      console.log('[ProfileSection] User ID:', userId);
      console.log('[ProfileSection] Path:', `users/${userId}/data/profile`);

      // Save to Firebase Firestore (new path structure)
      await setDoc(doc(db, 'users', userId, 'data', 'profile'), updatedProfile);

      console.log('[ProfileSection] ✅ Profile saved successfully!');

      setProfile(updatedProfile);

      // Profile saved to Firebase - main app will auto-sync via Firestore listener
      console.log('[ProfileSection] 📨 Profile saved, main app will sync automatically');

      // Show success feedback
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      console.error('Failed to save profile:', e);
      alert('Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        <span className="ml-3 text-zinc-400">Loading profile...</span>
      </div>
    );
  }

  if (!userId) {
    return (
      <div className="text-center py-12">
        <p className="text-zinc-400 text-sm">Please sign in to manage your profile</p>
      </div>
    );
  }

  return (
    <div className="space-y-5 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Avatar + Basic Info - Stack on mobile, side-by-side on larger */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-8">
        <div className="relative group shrink-0">
          <div className="w-24 h-24 sm:w-32 sm:h-32 cyber-border bg-indigo-950/20 overflow-hidden rounded-lg">
            {profile.avatarUrl ? (
              <img
                src={profile.avatarUrl}
                alt="Profile"
                className="w-full h-full object-cover opacity-90 group-hover:scale-105 transition-transform"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-indigo-900/30">
                <span className="text-3xl sm:text-4xl text-indigo-400">{profile.name?.[0]?.toUpperCase() || '?'}</span>
              </div>
            )}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 sm:flex items-center justify-center transition-opacity cursor-pointer hidden"
            >
              {uploadingImage ? (
                <Loader2 className="text-white animate-spin" />
              ) : (
                <Camera className="text-white" />
              )}
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleAvatarUpload}
            className="hidden"
          />
          <div className="mt-2 sm:mt-4 text-center">
            <span
              onClick={() => fileInputRef.current?.click()}
              className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest underline decoration-indigo-500/30 underline-offset-4 cursor-pointer hover:text-indigo-400 active:text-indigo-300"
            >
              {uploadingImage ? 'Uploading...' : 'Change Avatar'}
            </span>
          </div>
        </div>

        <div className="flex-1 space-y-3 sm:space-y-4 w-full">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="space-y-1">
              <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-1">👤 Your Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => {
                  console.log('[ProfileSection] 📝 Name changed to:', e.target.value);
                  setProfile({ ...profile, name: e.target.value });
                }}
                placeholder="Your Name"
                className="w-full cyber-input p-2.5 sm:p-3 text-sm text-indigo-100 font-bold rounded-sm"
              />
              <p className="text-[8px] text-zinc-600 mt-0.5">KAI will address you by this name</p>
            </div>
            <div className="space-y-1">
              <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-1">🏷️ Nickname (Optional)</label>
              <input
                type="text"
                value={profile.nickname}
                onChange={(e) => {
                  console.log('[ProfileSection] 📝 Nickname changed to:', e.target.value);
                  setProfile({ ...profile, nickname: e.target.value });
                }}
                placeholder="Preferred Name"
                className="w-full cyber-input p-2.5 sm:p-3 text-sm text-indigo-100 font-bold rounded-sm"
              />
              <p className="text-[8px] text-zinc-600 mt-0.5">Casual name KAI can use</p>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-1">📧 Email</label>
            <input
              type="email"
              value={profile.email}
              disabled
              className="w-full cyber-input p-2.5 sm:p-3 text-sm text-zinc-500 font-bold opacity-60 cursor-not-allowed rounded-sm"
            />
          </div>
        </div>
      </div>

      {/* AI Personalization Section */}
      <div className="border-t border-indigo-900/20 pt-5 sm:pt-6">
        <h3 className="text-[11px] sm:text-xs font-bold text-indigo-400 uppercase tracking-widest flex items-center gap-2 mb-4">
          <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full"></span>
          AI Personalization
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4">
          <div className="space-y-1">
            <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Preferred Response Style</label>
            <select
              value={profile.responseStyle}
              onChange={(e) => setProfile({ ...profile, responseStyle: e.target.value as any })}
              className="w-full cyber-input p-2.5 sm:p-3 text-sm text-indigo-100 font-bold rounded-sm appearance-none cursor-pointer"
            >
              <option value="casual">Casual & Friendly</option>
              <option value="professional">Professional</option>
              <option value="brief">Brief & Concise</option>
              <option value="detailed">Detailed & Thorough</option>
              <option value="technical">Technical & Precise</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Response Language</label>
            <select
              value={profile.responseLanguage}
              onChange={(e) => setProfile({ ...profile, responseLanguage: e.target.value as any })}
              className="w-full cyber-input p-2.5 sm:p-3 text-sm text-indigo-100 font-bold rounded-sm appearance-none cursor-pointer"
            >
              <option value="english">English</option>
              <option value="hindi">Hindi</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-1">✨ Your Interests (Comma-Separated)</label>
          <input
            type="text"
            value={interestsInput}
            onChange={(e) => setInterestsInput(e.target.value)}
            placeholder="coding, gaming, anime, music, AI"
            className="w-full cyber-input p-2.5 sm:p-3 text-sm text-indigo-100 rounded-sm"
          />
          <p className="text-[8px] text-zinc-600 mt-0.5">KAI will tailor responses based on your interests</p>
        </div>
      </div>

      {/* About You Section */}
      <div className="space-y-1">
        <label className="text-[9px] sm:text-[10px] text-zinc-500 font-bold uppercase tracking-widest flex items-center gap-1">📝 About You (Bio)</label>
        <textarea
          className="w-full cyber-input p-3 sm:p-4 text-sm text-indigo-100 min-h-[100px] sm:min-h-[120px] rounded-sm resize-none"
          value={profile.bio}
          onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
          placeholder="Tell KAI about yourself..."
        ></textarea>
        <p className="text-[8px] text-zinc-600 mt-0.5">KAI will remember this context in conversations</p>
      </div>

      {/* Save Button - Fixed positioning */}
      <div className="mt-6 sm:mt-8 pt-6 sm:pt-8 border-t border-white/10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4">
          <p className="text-[10px] sm:text-xs text-zinc-500 uppercase tracking-wide">
            Changes sync automatically with KAI
          </p>
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-3.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white text-xs sm:text-sm font-bold uppercase tracking-widest rounded-sm transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-indigo-500/50 active:scale-95"
          >
            {saving ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Syncing...</span>
              </>
            ) : saved ? (
              <>
                <Check size={16} />
                <span>Saved!</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>Save & Sync</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileSection;
