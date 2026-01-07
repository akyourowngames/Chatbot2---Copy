
import React from 'react';
import { Globe, Server, Radio, Zap } from 'lucide-react';

const UplinkSection: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="space-y-4">
        <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Primary Uplink Node</label>
        <div className="grid grid-cols-1 gap-3">
          <UplinkOption 
            icon={<Globe size={18} />}
            title="North_Global_Server (NG-01)"
            description="Optimal latency for North American operations. Standard encryption."
            ping="14ms"
            selected={true}
          />
          <UplinkOption 
            icon={<Server size={18} />}
            title="Eurasia_Core_Relay (EC-09)"
            description="High-security node with cascading signal redundancy."
            ping="120ms"
            selected={false}
          />
          <UplinkOption 
            icon={<Radio size={18} />}
            title="Sat_Deep_Space_Mesh (SM-4)"
            description="Extreme coverage for remote field data collection."
            ping="240ms"
            selected={false}
          />
        </div>
      </div>

      <div className="p-6 bg-indigo-600/5 border border-indigo-500/20 relative overflow-hidden group">
        <div className="absolute -right-8 -bottom-8 opacity-5 group-hover:rotate-12 transition-transform duration-1000">
           <Zap size={160} />
        </div>
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-widest mb-1">Burst Mode Uplink</h4>
            <p className="text-[10px] text-zinc-500 uppercase">Enable short-duration high-bandwidth data transfers.</p>
          </div>
          <button className="px-4 py-2 border border-indigo-500 text-indigo-400 text-[10px] font-bold uppercase tracking-widest hover:bg-indigo-600 hover:text-white transition-all">Optimize Link</button>
        </div>
      </div>

      <div className="flex gap-4">
         <div className="flex-1 p-4 bg-zinc-950 border border-zinc-900">
            <h5 className="text-[10px] font-bold uppercase tracking-widest mb-2">Protocol Stack</h5>
            <select className="w-full bg-black border border-zinc-800 p-2 text-[10px] font-mono text-zinc-400 focus:outline-none focus:border-indigo-500 uppercase">
              <option>IPv6 / Secure_Mesh_v4</option>
              <option>Legacy_TCP_Over_Neural</option>
              <option>Encapsulated_Ghost_Frame</option>
            </select>
         </div>
         <div className="flex-1 p-4 bg-zinc-950 border border-zinc-900">
            <h5 className="text-[10px] font-bold uppercase tracking-widest mb-2">Signal Gain</h5>
            <div className="flex items-center gap-4 pt-2">
               <input type="range" className="flex-1 h-1 bg-zinc-800 appearance-none accent-indigo-500" />
               <span className="text-[10px] font-mono text-indigo-400">+12dB</span>
            </div>
         </div>
      </div>
    </div>
  );
};

const UplinkOption: React.FC<{icon: React.ReactNode, title: string, description: string, ping: string, selected: boolean}> = ({ icon, title, description, ping, selected }) => (
  <div className={`p-4 border flex items-center gap-4 cursor-pointer transition-all ${selected ? 'bg-indigo-600/10 border-indigo-500/50' : 'bg-black border-zinc-900 hover:border-zinc-700'}`}>
     <div className={`p-3 ${selected ? 'text-indigo-500 bg-indigo-500/10' : 'text-zinc-600 bg-zinc-900'}`}>
       {icon}
     </div>
     <div className="flex-1">
       <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[10px] font-bold uppercase tracking-widest">{title}</span>
          {selected && <span className="text-[8px] text-green-500 font-bold uppercase tracking-tighter">CONNECTED</span>}
       </div>
       <p className="text-[9px] text-zinc-600 uppercase tracking-tight leading-none">{description}</p>
     </div>
     <div className="text-right">
       <div className="text-[10px] font-mono text-zinc-500 mb-0.5">{ping}</div>
       <div className="text-[8px] text-zinc-700 uppercase font-bold tracking-widest">Latency</div>
     </div>
  </div>
);

export default UplinkSection;
