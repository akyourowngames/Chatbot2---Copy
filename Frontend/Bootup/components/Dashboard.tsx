
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ICONS } from '../constants';
import TelemetryWidget from './TelemetryWidget';
import TerminalLog from './TerminalLog';

const Dashboard: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex h-full w-full bg-[#00050a] overflow-hidden text-cyan-50">
      {/* Sidebar */}
      <aside className="w-72 border-r border-cyan-500/20 flex flex-col p-8 bg-[#000a12]/80 backdrop-blur-xl">
        <div className="flex items-center gap-4 mb-16">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            {ICONS.Cpu}
          </div>
          <div>
            <h1 className="font-black text-2xl tracking-tighter leading-none italic">KAI <span className="text-cyan-500">OS</span></h1>
            <span className="text-[9px] text-cyan-400 tracking-[0.4em] font-bold uppercase animate-pulse">System Active</span>
          </div>
        </div>

        <nav className="space-y-12 flex-1 overflow-y-auto pr-2 scrollbar-hide">
          <div className="space-y-4">
            <h3 className="text-[10px] font-black text-cyan-500/50 tracking-[0.3em] uppercase">Core Functions</h3>
            <button className="w-full flex items-center justify-between p-4 bg-cyan-500/5 border border-cyan-500/20 hover:border-cyan-400 hover:bg-cyan-500/10 rounded-sm group transition-all duration-300">
              <span className="text-xs font-bold tracking-widest uppercase">New Operation</span>
              <span className="text-cyan-500 group-hover:scale-125 transition-transform">+</span>
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-6">
               <h3 className="text-[10px] font-black text-cyan-500/50 tracking-[0.3em] uppercase">System Telemetry</h3>
               <span className="text-cyan-500/50">{ICONS.Activity}</span>
            </div>
            <div className="space-y-6">
                <TelemetryWidget label="Neural_Processor" value={42} />
                <TelemetryWidget label="Memory_Buffer" value={28} />
                <TelemetryWidget label="Uplink_Strength" value={89} />
            </div>
          </div>

          <div>
             <h3 className="text-[10px] font-black text-cyan-500/50 tracking-[0.3em] uppercase mb-6 flex items-center gap-2">
               {ICONS.Terminal}
               Active_Logs
             </h3>
             <TerminalLog />
          </div>
        </nav>

        <div className="pt-8 border-t border-cyan-500/10">
           <button className="w-full flex items-center justify-center gap-3 py-3 border border-red-500/20 text-red-500/60 hover:text-red-500 hover:bg-red-500/5 text-[10px] font-bold uppercase tracking-[0.3em] transition-all rounded-sm">
             {ICONS.LogOut}
             Terminate_Session
           </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative">
        {/* Animated Background Grid */}
        <div className="absolute inset-0 opacity-[0.05] pointer-events-none" 
             style={{ 
               backgroundImage: 'linear-gradient(#22d3ee 1px, transparent 1px), linear-gradient(90deg, #22d3ee 1px, transparent 1px)', 
               backgroundSize: '100px 100px' 
             }} />
        
        <header className="h-20 border-b border-cyan-500/10 px-10 flex items-center justify-between bg-[#000a12]/40 backdrop-blur-md relative z-10">
          <div className="flex items-center gap-6">
            <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_10px_#22d3ee] animate-pulse" />
            <div>
              <h2 className="text-xs font-black tracking-[0.3em] uppercase text-cyan-100">Tactical Command Center</h2>
              <p className="text-[10px] text-cyan-500/50 tracking-widest uppercase">Protocol: STARK_OMEGA</p>
            </div>
          </div>
          
          <div className="flex items-center gap-8">
            <div className="hidden md:flex flex-col items-end">
               <span className="text-[10px] font-bold text-cyan-400 tracking-widest">{currentTime}</span>
               <span className="text-[8px] text-white/30 tracking-tighter uppercase">Global Time Sync</span>
            </div>
            <div className="flex items-center gap-4 border-l border-cyan-500/10 pl-8">
              <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center group cursor-pointer overflow-hidden relative">
                 <img src="https://picsum.photos/100/100?grayscale&blur=2" alt="Avatar" className="opacity-40 grayscale group-hover:scale-110 transition-transform" />
                 <div className="absolute inset-0 border-2 border-transparent group-hover:border-cyan-400 transition-colors" />
              </div>
            </div>
          </div>
        </header>

        {/* Centerpiece Hero */}
        <div className="flex-1 flex flex-col items-center justify-center relative p-12 overflow-hidden">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center text-center max-w-5xl relative z-10"
          >
             <motion.div 
               animate={{ y: [0, -5, 0] }}
               transition={{ repeat: Infinity, duration: 4 }}
               className="bg-cyan-500/10 border border-cyan-500/20 px-6 py-2 rounded-full mb-16 shadow-[0_0_20px_rgba(6,182,212,0.1)]"
             >
                <span className="text-cyan-400 text-[10px] font-black tracking-[0.5em] uppercase">Security Level: Authorized</span>
             </motion.div>

             <div className="mb-12 relative group cursor-pointer">
               <motion.div 
                 animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.4, 0.2] }}
                 transition={{ repeat: Infinity, duration: 3 }}
                 className="absolute -inset-16 bg-cyan-400/20 blur-[80px] rounded-full" 
               />
               <div className="w-32 h-32 bg-cyan-900/20 border border-cyan-400/40 rounded-2xl flex items-center justify-center text-cyan-400 mb-12 relative z-10 shadow-[0_0_40px_rgba(34,211,238,0.1)] group-hover:border-cyan-400 transition-all duration-500">
                 <div className="scale-150 transform">{ICONS.Cpu}</div>
               </div>
             </div>

             <div className="flex items-baseline gap-4 mb-8">
                <h1 className="text-[10rem] font-black italic tracking-tighter text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.1)]">KAI</h1>
                <h1 className="text-[10rem] font-black italic tracking-tighter text-cyan-500 drop-shadow-[0_0_30px_rgba(6,182,212,0.3)]">INTEL</h1>
             </div>

             <div className="flex gap-16 text-cyan-400/30 text-[11px] font-black tracking-[0.6em] uppercase">
                <span className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_5px_#22d3ee]" />
                  SYS_SYNTHESIS
                </span>
                <span className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_5px_#22d3ee]" />
                  DATA_MINING
                </span>
                <span className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_5px_#22d3ee]" />
                  NEURAL_LINK
                </span>
             </div>

             <div className="mt-24 grid grid-cols-3 gap-10 w-full px-12">
                {[
                  { label: "Asset Analysis", icon: ICONS.Activity, color: "cyan" },
                  { label: "Visual Synthesis", icon: ICONS.Layout, color: "cyan" },
                  { label: "Global Uplink", icon: ICONS.Radio, color: "cyan" }
                ].map((card, i) => (
                  <motion.button 
                    key={i} 
                    whileHover={{ y: -10 }}
                    className="group relative p-12 bg-cyan-500/5 border border-cyan-500/10 rounded-xl flex flex-col items-center gap-8 hover:bg-cyan-500/10 hover:border-cyan-400/50 transition-all duration-300 shadow-xl"
                  >
                    <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-cyan-400/30 group-hover:border-cyan-400" />
                    <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-cyan-400/30 group-hover:border-cyan-400" />
                    
                    <span className="text-cyan-400/40 group-hover:text-cyan-400 group-hover:scale-125 transition-all duration-500 transform scale-150">
                      {card.icon}
                    </span>
                    <span className="text-xs font-black uppercase tracking-[0.3em] text-cyan-100 group-hover:text-white">{card.label}</span>
                  </motion.button>
                ))}
             </div>
          </motion.div>
        </div>

        {/* Floating Input Bar (Call to Action) */}
        <div className="sticky bottom-0 w-full p-12 flex justify-center pointer-events-none z-50">
          <div className="w-full max-w-5xl bg-[#00101a]/90 backdrop-blur-2xl border border-cyan-500/30 p-3 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] rounded-xl pointer-events-auto flex items-center gap-6 group hover:border-cyan-400 transition-colors">
            <button className="p-4 text-cyan-500/30 hover:text-cyan-400 transition-colors bg-cyan-500/5 rounded-lg">
              {ICONS.Terminal}
            </button>
            <input 
              type="text" 
              placeholder="ESTABLISH_NEURAL_COMMAND..."
              className="flex-1 bg-transparent border-none focus:ring-0 text-lg font-medium tracking-tight placeholder:text-cyan-900 text-cyan-100 italic"
            />
            <div className="flex items-center gap-4">
              <button className="p-4 text-cyan-500/30 hover:text-cyan-400 transition-colors">
                {ICONS.Mic}
              </button>
              <button className="px-12 py-4 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-black uppercase tracking-[0.3em] transition-all transform hover:scale-[1.02] active:scale-95 flex items-center gap-4 rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.4)]">
                Execute
                <div className="w-2 h-2 rounded-full bg-white shadow-[0_0_5px_white]" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
