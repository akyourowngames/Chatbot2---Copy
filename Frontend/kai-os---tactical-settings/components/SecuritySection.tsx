
import React, { useState } from 'react';
import { Lock, RefreshCw, Key, ShieldCheck } from 'lucide-react';

const SecuritySection: React.FC = () => {
  const [tlsEnabled, setTlsEnabled] = useState(true);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-indigo-950/10 border border-indigo-500/10 p-6 rounded-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
             <ShieldCheck className="text-indigo-500" />
             <div>
               <h3 className="text-xs font-bold uppercase tracking-widest">Transport Layer Security (TLS)</h3>
               <p className="text-[10px] text-zinc-500 mt-1 uppercase">Encrypt all outgoing data packets across the mesh network.</p>
             </div>
          </div>
          <button 
            onClick={() => setTlsEnabled(!tlsEnabled)}
            className={`w-12 h-6 rounded-full relative transition-colors ${tlsEnabled ? 'bg-indigo-600' : 'bg-zinc-800'}`}
          >
            <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${tlsEnabled ? 'left-7' : 'left-1'}`}></div>
          </button>
        </div>

        <div className="space-y-4">
           <div className="flex items-center justify-between p-4 bg-black/40 border border-indigo-900/20">
              <div className="flex items-center gap-3">
                <Key size={16} className="text-indigo-400" />
                <span className="text-[10px] font-bold uppercase tracking-widest">ACCESS_KEY_01</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-[10px] text-zinc-600 font-mono">••••••••••••••••••••••••</span>
                <button className="text-indigo-500 hover:text-indigo-400">
                  <RefreshCw size={14} />
                </button>
              </div>
           </div>
           <button className="w-full py-3 border border-dashed border-indigo-900/30 text-[10px] text-zinc-500 hover:text-indigo-400 hover:border-indigo-500/50 transition-all uppercase font-bold tracking-[0.2em]">
             + Generate Secondary Access Key
           </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <SecurityCard 
          icon={<Lock size={18} className="text-yellow-500" />}
          title="Neural MFA"
          description="Requires biometric neural signature for uplink establishment."
          active={true}
        />
        <SecurityCard 
          icon={<Lock size={18} className="text-zinc-500" />}
          title="Ghost Protocol"
          description="Automated signal scrambling for deep-cover operations."
          active={false}
        />
      </div>

      <div className="p-4 border-l-2 border-red-500 bg-red-500/5">
        <h4 className="text-[10px] text-red-500 font-bold uppercase tracking-widest mb-2">Emergency Purge</h4>
        <p className="text-[10px] text-zinc-400 uppercase leading-relaxed mb-4">Wipe all local session logs, cache, and decrypted credentials immediately. This action cannot be undone.</p>
        <button className="px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-500 hover:bg-red-500 hover:text-white transition-all text-[10px] font-bold uppercase tracking-widest">Execute Purge Sequence</button>
      </div>
    </div>
  );
};

const SecurityCard: React.FC<{icon: React.ReactNode, title: string, description: string, active: boolean}> = ({ icon, title, description, active }) => (
  <div className={`p-4 border transition-all ${active ? 'bg-indigo-600/5 border-indigo-500/30' : 'bg-zinc-950 border-zinc-900 opacity-60'}`}>
    <div className="flex items-center gap-3 mb-2">
      {icon}
      <span className="text-xs font-bold uppercase tracking-widest">{title}</span>
      {active && <span className="ml-auto text-[8px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded-sm">ACTIVE</span>}
    </div>
    <p className="text-[9px] text-zinc-500 uppercase leading-normal">{description}</p>
  </div>
);

export default SecuritySection;
