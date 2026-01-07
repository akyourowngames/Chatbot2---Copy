

import React, { useState, useEffect } from 'react';
import {
  User,
  Shield,
  Zap,
  Activity,
  LogOut,
  Bell,
  Cpu,
  Terminal,
  ChevronRight,
  Monitor,
  Menu,
  X,
  ChevronDown
} from 'lucide-react';
import { SettingsTab } from './types';
import ProfileSection from './components/ProfileSection';
import SecuritySection from './components/SecuritySection';
import DeviceSection from './components/DeviceSection';
import TelemetrySection from './components/TelemetrySection';
import UplinkSection from './components/UplinkSection';
import NotificationSection from './components/NotificationSection';
// Firebase imports for profile sync
import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, onSnapshot } from 'firebase/firestore';

// Firebase Config (same as ProfileSection)
const firebaseConfig = {
  apiKey: "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk",
  authDomain: "kai-g-80f9c.firebaseapp.com",
  projectId: "kai-g-80f9c",
  storageBucket: "kai-g-80f9c.appspot.com",
  messagingSenderId: "125633190886",
  appId: "1:125633190886:web:65e1a7b4f59048a1768853"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>(SettingsTab.PROFILE);
  const [userProfile, setUserProfile] = useState<{ name: string; nickname: string; avatarUrl: string } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mobileDropdownOpen, setMobileDropdownOpen] = useState(false);

  // 🔥 FIREBASE PROFILE SYNC - Listen for profile changes
  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (user) => {
      if (user) {
        // Listen to profile updates in real-time
        const unsubscribeProfile = onSnapshot(
          doc(db, 'users', user.uid, 'data', 'profile'),
          (snapshot) => {
            if (snapshot.exists()) {
              const data = snapshot.data();
              setUserProfile({
                name: data.name || user.displayName || 'KAI_TACTICAL_01',
                nickname: data.nickname || '',
                avatarUrl: data.avatarUrl || user.photoURL || ''
              });
              console.log('[App] ✅ Profile synced from Firebase:', data);
            } else {
              // No profile yet, use auth data
              setUserProfile({
                name: user.displayName || 'KAI_TACTICAL_01',
                nickname: '',
                avatarUrl: user.photoURL || ''
              });
            }
          }
        );
        return () => unsubscribeProfile();
      } else {
        setUserProfile(null);
      }
    });
    return () => unsubscribeAuth();
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case SettingsTab.PROFILE: return <ProfileSection />;
      case SettingsTab.SECURITY: return <SecuritySection />;
      case SettingsTab.DEVICES: return <DeviceSection />;
      case SettingsTab.TELEMETRY: return <TelemetrySection />;
      case SettingsTab.UPLINK: return <UplinkSection />;
      case SettingsTab.NOTIFICATIONS: return <NotificationSection />;
      default: return <ProfileSection />;
    }
  };

  const handleTabChange = (tab: SettingsTab) => {
    setActiveTab(tab);
    setSidebarOpen(false);
    setMobileDropdownOpen(false);
  };

  const getTabLabel = (tab: SettingsTab) => {
    const labels: Record<SettingsTab, string> = {
      [SettingsTab.PROFILE]: 'Operator Profile',
      [SettingsTab.SECURITY]: 'Security Protocols',
      [SettingsTab.DEVICES]: 'Device Link',
      [SettingsTab.NOTIFICATIONS]: 'Neural Alerts',
      [SettingsTab.TELEMETRY]: 'Live Telemetry',
      [SettingsTab.UPLINK]: 'Uplink Config',
    };
    return labels[tab] || tab;
  };

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden font-mono">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/80 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Navigation - Hidden on mobile, shown on desktop */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-[280px] sm:w-72 border-r border-indigo-900/30 bg-[#050505] 
        flex flex-col shrink-0
        transform transition-transform duration-300 ease-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Mobile Close Button */}
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden absolute top-4 right-4 p-2 text-zinc-400 hover:text-white z-50"
        >
          <X size={20} />
        </button>

        <div className="p-4 sm:p-6 border-b border-indigo-900/30">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-indigo-600 rounded flex items-center justify-center border border-indigo-400/50 shadow-[0_0_15px_rgba(99,102,241,0.3)]">
              <Cpu className="text-white w-5 h-5 sm:w-6 sm:h-6" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tighter">KAI OS</h1>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full status-dot shadow-[0_0_5px_#22c55e]"></div>
                <span className="text-[9px] sm:text-[10px] text-green-500 font-bold uppercase tracking-widest">SETTINGS</span>
              </div>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-1 sm:space-y-2 scrollbar-hide">
          <div className="text-[9px] sm:text-[10px] text-zinc-500 font-bold mb-3 sm:mb-4 ml-2 uppercase tracking-[0.15em] sm:tracking-[0.2em]">Management</div>

          <NavItem
            icon={<User size={16} />}
            label="Operator Profile"
            active={activeTab === SettingsTab.PROFILE}
            onClick={() => handleTabChange(SettingsTab.PROFILE)}
          />
          <NavItem
            icon={<Bell size={16} />}
            label="Neural Alerts"
            active={activeTab === SettingsTab.NOTIFICATIONS}
            onClick={() => handleTabChange(SettingsTab.NOTIFICATIONS)}
          />

          <div className="text-[9px] sm:text-[10px] text-zinc-500 font-bold mt-6 sm:mt-8 mb-3 sm:mb-4 ml-2 uppercase tracking-[0.15em] sm:tracking-[0.2em]">Systems</div>

          <NavItem
            icon={<Monitor size={16} />}
            label="Device Link"
            active={activeTab === SettingsTab.DEVICES}
            onClick={() => handleTabChange(SettingsTab.DEVICES)}
          />
          <NavItem
            icon={<Zap size={16} />}
            label="Uplink Config"
            active={activeTab === SettingsTab.UPLINK}
            onClick={() => handleTabChange(SettingsTab.UPLINK)}
          />

          <div className="pt-8 sm:pt-12 mt-auto">
            <button
              onClick={() => window.location.href = '/'}
              className="w-full flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 text-indigo-500/80 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors rounded-sm group"
            >
              <X size={16} className="group-hover:scale-110 transition-transform" />
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider sm:tracking-widest">Back to Chat</span>
            </button>
          </div>
        </nav>

        <div className="p-3 sm:p-4 border-t border-indigo-900/30 bg-[#020202]">
          <div className="text-[9px] sm:text-[10px] text-zinc-600 flex justify-between items-center">
            <span>SYS_VER_2.5.0_PRO</span>
            <Terminal size={10} className="sm:w-3 sm:h-3" />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col bg-[#000000] relative min-w-0">
        {/* Background Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(15,23,42,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(15,23,42,0.1)_1px,transparent_1px)] bg-[size:24px_24px] sm:bg-[size:32px_32px] pointer-events-none opacity-20"></div>

        {/* Header - Responsive */}
        <header className="h-14 sm:h-16 lg:h-20 border-b border-indigo-900/30 flex items-center justify-between px-3 sm:px-5 lg:px-8 bg-black/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Mobile Menu Button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 -ml-2 text-zinc-400 hover:text-white transition-colors"
            >
              <Menu size={20} />
            </button>

            <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-indigo-500 rounded-full hidden sm:block"></div>
            <h2 className="text-xs sm:text-sm font-bold uppercase tracking-[0.15em] sm:tracking-[0.3em] glow-text truncate">
              {activeTab.replace('_', ' ')}
            </h2>
            <div className="hidden sm:flex px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-[9px] sm:text-[10px] text-indigo-400 font-bold rounded-sm">
              SID-176634
            </div>
          </div>

          {/* Mobile Tab Dropdown */}
          <div className="lg:hidden relative">
            <button
              onClick={() => setMobileDropdownOpen(!mobileDropdownOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 border border-indigo-900/50 bg-indigo-950/30 rounded text-[10px] font-bold uppercase tracking-wide text-zinc-300"
            >
              <span className="max-w-[100px] truncate">{getTabLabel(activeTab).split(' ')[0]}</span>
              <ChevronDown size={14} className={`transition-transform ${mobileDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {mobileDropdownOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setMobileDropdownOpen(false)} />
                <div className="absolute right-0 top-full mt-2 w-48 bg-[#0a0a0f] border border-indigo-900/50 rounded-lg shadow-xl z-50 py-1 overflow-hidden">
                  {Object.values(SettingsTab).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => handleTabChange(tab)}
                      className={`w-full text-left px-4 py-2.5 text-[11px] font-bold uppercase tracking-wide transition-colors ${activeTab === tab
                        ? 'bg-indigo-600/20 text-indigo-400'
                        : 'text-zinc-400 hover:bg-indigo-900/10 hover:text-white'
                        }`}
                    >
                      {getTabLabel(tab)}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Desktop Header Actions */}
          <div className="hidden lg:flex items-center gap-4">
            <div className="h-8 w-px bg-indigo-900/30 mx-2"></div>
            <div className="flex items-center gap-2 group cursor-pointer">
              <div className="text-right">
                <p className="text-[10px] font-bold leading-tight">
                  {userProfile?.nickname || userProfile?.name || 'OP_KAI_01'}
                </p>
                <p className="text-[8px] text-indigo-400 font-bold leading-none tracking-tighter uppercase">Clearance Level 5</p>
              </div>
              <div className="w-8 h-8 rounded-sm bg-indigo-900/40 border border-indigo-500/30 overflow-hidden">
                {userProfile?.avatarUrl ? (
                  <img src={userProfile.avatarUrl} alt="Avatar" className="w-full h-full object-cover opacity-80" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-indigo-900/30">
                    <span className="text-sm text-indigo-400">{userProfile?.name?.[0]?.toUpperCase() || 'K'}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Content Scroll Area - Responsive padding */}
        <section className="flex-1 overflow-y-auto p-3 sm:p-5 lg:p-8 z-10 scrollbar-hide">
          <div className="max-w-4xl mx-auto">
            {renderContent()}
          </div>
        </section>
      </main>
    </div>
  );
};

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center justify-between p-3 transition-all rounded-sm group ${active
      ? 'bg-indigo-600/10 border-l-2 border-indigo-600 text-indigo-400'
      : 'text-zinc-500 hover:text-indigo-400 hover:bg-indigo-900/5 border-l-2 border-transparent'
      }`}
  >
    <div className="flex items-center gap-3">
      <span className={`${active ? 'text-indigo-500' : 'text-zinc-600 group-hover:text-indigo-500'} transition-colors`}>
        {icon}
      </span>
      <span className="text-xs font-bold uppercase tracking-widest">{label}</span>
    </div>
    {active && <ChevronRight size={14} className="opacity-50" />}
  </button>
);

export default App;
