
import React from 'react';
import { Activity, Cpu, Database } from 'lucide-react';

const TelemetrySection: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-3 gap-4">
        <StatWidget icon={<Cpu size={16} />} label="Neural Load" value="24%" subValue="3.2 GHz" color="text-indigo-500" />
        <StatWidget icon={<Database size={16} />} label="Mem Stack" value="12.8 GB" subValue="Used / 32 GB" color="text-cyan-500" />
        <StatWidget icon={<Activity size={16} />} label="Uplink Sync" value="99.9%" subValue="Latency: 4ms" color="text-green-500" />
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <div className="flex justify-between items-center">
             <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Neural Load Allocation</label>
             <span className="text-[10px] text-indigo-400 font-bold">450 TFLOPs</span>
          </div>
          <input type="range" className="w-full h-1 bg-zinc-900 appearance-none cursor-pointer accent-indigo-500" />
          <p className="text-[8px] text-zinc-600 uppercase">Warning: Exceeding 80% may cause operator burnout.</p>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
             <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Log Retention Period</label>
             <span className="text-[10px] text-indigo-400 font-bold">24 HOURS</span>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {['1 HR', '12 HR', '24 HR', '7 DAYS'].map(time => (
              <button key={time} className={`py-2 text-[10px] font-bold border transition-all ${time === '24 HR' ? 'bg-indigo-600/20 border-indigo-500 text-indigo-400' : 'border-zinc-800 text-zinc-600 hover:border-zinc-600'}`}>
                {time}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="border border-indigo-500/10 bg-indigo-950/5 p-6 space-y-4">
         <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] border-b border-indigo-900/30 pb-4">Background Processes</h3>
         {[
           { name: 'Core_System_Watcher', status: 'Running', pid: '0122' },
           { name: 'Neural_Uplink_Sync', status: 'Idle', pid: '4491' },
           { name: 'Tactical_Overlay_Render', status: 'Running', pid: '9902' },
         ].map(process => (
           <div key={process.pid} className="flex items-center justify-between py-1">
              <div className="flex items-center gap-3">
                 <div className={`w-1.5 h-1.5 rounded-full ${process.status === 'Running' ? 'bg-green-500' : 'bg-zinc-600'}`}></div>
                 <span className="text-[10px] font-mono text-zinc-400 uppercase">{process.name}</span>
              </div>
              <div className="flex items-center gap-4">
                 <span className="text-[8px] text-zinc-600 font-mono">PID: {process.pid}</span>
                 <button className="text-[8px] font-bold text-red-500 uppercase hover:underline">Terminate</button>
              </div>
           </div>
         ))}
      </div>
    </div>
  );
};

const StatWidget: React.FC<{icon: React.ReactNode, label: string, value: string, subValue: string, color: string}> = ({ icon, label, value, subValue, color }) => (
  <div className="bg-black border border-indigo-900/20 p-4 rounded-sm hover:border-indigo-500/40 transition-all group">
    <div className="flex items-center gap-2 mb-3">
       <span className={`${color} opacity-60 group-hover:opacity-100 transition-opacity`}>{icon}</span>
       <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">{label}</span>
    </div>
    <div className="text-xl font-bold tracking-tight mb-1">{value}</div>
    <div className="text-[9px] text-zinc-600 font-bold uppercase">{subValue}</div>
  </div>
);

export default TelemetrySection;
