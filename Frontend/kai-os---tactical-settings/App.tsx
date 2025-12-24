
import React, { useState } from 'react';
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
  Monitor
} from 'lucide-react';
import { SettingsTab } from './types';
import ProfileSection from './components/ProfileSection';
import SecuritySection from './components/SecuritySection';
import TelemetrySection from './components/TelemetrySection';
import UplinkSection from './components/UplinkSection';
import NotificationSection from './components/NotificationSection';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>(SettingsTab.PROFILE);

  const renderContent = () => {
    switch (activeTab) {
      case SettingsTab.PROFILE: return <ProfileSection />;
      case SettingsTab.SECURITY: return <SecuritySection />;
      case SettingsTab.TELEMETRY: return <TelemetrySection />;
      case SettingsTab.UPLINK: return <UplinkSection />;
      case SettingsTab.NOTIFICATIONS: return <NotificationSection />;
      default: return <ProfileSection />;
    }
  };

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden font-mono">
      {/* Sidebar Navigation */}
      <aside className="w-72 border-r border-indigo-900/30 bg-[#050505] flex flex-col shrink-0">
        <div className="p-6 border-b border-indigo-900/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded flex items-center justify-center border border-indigo-400/50 shadow-[0_0_15px_rgba(99,102,241,0.3)]">
              <Cpu className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tighter">KAI OS</h1>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full status-dot shadow-[0_0_5px_#22c55e]"></div>
                <span className="text-[10px] text-green-500 font-bold uppercase tracking-widest">OPERATIONAL</span>
              </div>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide">
          <div className="text-[10px] text-zinc-500 font-bold mb-4 ml-2 uppercase tracking-[0.2em]">Management</div>
          
          <NavItem 
            icon={<User size={18} />} 
            label="Operator Profile" 
            active={activeTab === SettingsTab.PROFILE} 
            onClick={() => setActiveTab(SettingsTab.PROFILE)} 
          />
          <NavItem 
            icon={<Shield size={18} />} 
            label="Security Protocols" 
            active={activeTab === SettingsTab.SECURITY} 
            onClick={() => setActiveTab(SettingsTab.SECURITY)} 
          />
          <NavItem 
            icon={<Bell size={18} />} 
            label="Neural Alerts" 
            active={activeTab === SettingsTab.NOTIFICATIONS} 
            onClick={() => setActiveTab(SettingsTab.NOTIFICATIONS)} 
          />
          
          <div className="text-[10px] text-zinc-500 font-bold mt-8 mb-4 ml-2 uppercase tracking-[0.2em]">Systems</div>
          
          <NavItem 
            icon={<Activity size={18} />} 
            label="Live Telemetry" 
            active={activeTab === SettingsTab.TELEMETRY} 
            onClick={() => setActiveTab(SettingsTab.TELEMETRY)} 
          />
          <NavItem 
            icon={<Zap size={18} />} 
            label="Uplink Config" 
            active={activeTab === SettingsTab.UPLINK} 
            onClick={() => setActiveTab(SettingsTab.UPLINK)} 
          />

          <div className="pt-12 mt-auto">
             <button className="w-full flex items-center gap-3 p-3 text-red-500/80 hover:text-red-400 hover:bg-red-500/10 transition-colors rounded-sm group">
               <LogOut size={18} className="group-hover:translate-x-1 transition-transform" />
               <span className="text-xs font-bold uppercase tracking-widest">Disconnect</span>
             </button>
          </div>
        </nav>

        <div className="p-4 border-t border-indigo-900/30 bg-[#020202]">
          <div className="text-[10px] text-zinc-600 flex justify-between items-center">
             <span>SYS_VER_2.5.0_PRO</span>
             <Terminal size={12} />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col bg-[#000000] relative">
        {/* Background Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(15,23,42,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(15,23,42,0.1)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none opacity-20"></div>

        {/* Header */}
        <header className="h-20 border-b border-indigo-900/30 flex items-center justify-between px-8 bg-black/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-4">
            <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
            <h2 className="text-sm font-bold uppercase tracking-[0.3em] glow-text">{activeTab.replace('_', ' ')}</h2>
            <div className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-400 font-bold rounded-sm">
              SID-176634
            </div>
          </div>

          <div className="flex items-center gap-4">
             <button className="flex items-center gap-2 px-3 py-1.5 border border-indigo-900/50 bg-indigo-950/20 hover:bg-indigo-900/30 transition-all text-[10px] font-bold uppercase tracking-widest text-zinc-400">
               <Monitor size={14} />
               Mini Mode
             </button>
             <div className="h-8 w-px bg-indigo-900/30 mx-2"></div>
             <div className="flex items-center gap-2 group cursor-pointer">
                <div className="text-right">
                   <p className="text-[10px] font-bold leading-tight">OP_KAI_01</p>
                   <p className="text-[8px] text-indigo-400 font-bold leading-none tracking-tighter uppercase">Clearance Level 5</p>
                </div>
                <div className="w-8 h-8 rounded-sm bg-indigo-900/40 border border-indigo-500/30 overflow-hidden">
                  <img src="https://picsum.photos/id/64/100/100" alt="Avatar" className="w-full h-full object-cover opacity-80" />
                </div>
             </div>
          </div>
        </header>

        {/* Content Scroll Area */}
        <section className="flex-1 overflow-y-auto p-8 z-10 scrollbar-hide">
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
    className={`w-full flex items-center justify-between p-3 transition-all rounded-sm group ${
      active 
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
