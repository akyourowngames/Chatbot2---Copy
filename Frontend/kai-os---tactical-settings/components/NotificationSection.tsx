
import React from 'react';
import { Bell, AlertTriangle, MessageSquare, Info } from 'lucide-react';

const NotificationSection: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="space-y-2">
         <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-4">Neural Event Channels</h3>
         
         <NotificationToggle 
           icon={<AlertTriangle size={16} className="text-red-500" />}
           label="Critical System Alerts"
           description="Visual and haptic feedback for hardware failure or security breaches."
           enabled={true}
         />
         
         <NotificationToggle 
           icon={<MessageSquare size={16} className="text-indigo-500" />}
           label="Operator Comms"
           description="Voice-to-text notifications for incoming tactical messages."
           enabled={true}
         />

         <NotificationToggle 
           icon={<Info size={16} className="text-cyan-500" />}
           label="Status Updates"
           description="Routine telemetry reports and background sync status."
           enabled={false}
         />
         
         <NotificationToggle 
           icon={<Bell size={16} className="text-yellow-500" />}
           label="Scheduled Operations"
           description="Reminders for upcoming mission windows and uplink maintenance."
           enabled={true}
         />
      </div>

      <div className="grid grid-cols-2 gap-6 pt-4">
         <div className="space-y-2">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Alert Priority Threshold</label>
            <select className="w-full bg-black border border-zinc-800 p-3 text-[10px] font-bold text-zinc-400 uppercase tracking-widest focus:outline-none focus:border-indigo-500">
              <option>LEVEL_1 - MINIMAL</option>
              <option>LEVEL_2 - STANDARD</option>
              <option>LEVEL_3 - HIGH_ONLY</option>
            </select>
         </div>
         <div className="space-y-2">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Notification Sound</label>
            <div className="flex items-center gap-2">
               <select className="flex-1 bg-black border border-zinc-800 p-3 text-[10px] font-bold text-zinc-400 uppercase tracking-widest focus:outline-none focus:border-indigo-500">
                 <option>KAI_SYSTEM_CHIME</option>
                 <option>NEURAL_TAP_PULSE</option>
                 <option>TACTICAL_BUZZ_SHORT</option>
               </select>
               <button className="p-3 border border-zinc-800 hover:bg-zinc-900 text-zinc-500">
                  <Bell size={16} />
               </button>
            </div>
         </div>
      </div>

      <div className="p-4 bg-indigo-600/5 border border-indigo-500/10 flex items-start gap-4">
         <div className="p-2 bg-indigo-500/20 rounded-sm">
           <Info size={18} className="text-indigo-400" />
         </div>
         <div className="flex-1">
           <h4 className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-1">Silence Protocol</h4>
           <p className="text-[9px] text-zinc-500 uppercase leading-normal">Enabling this will suppress all non-critical visual notifications to maximize focus during high-intensity operations.</p>
         </div>
         <button className="px-4 py-2 border border-zinc-800 text-[10px] font-bold uppercase tracking-widest hover:border-indigo-500/50 transition-all">Enable</button>
      </div>
    </div>
  );
};

const NotificationToggle: React.FC<{icon: React.ReactNode, label: string, description: string, enabled: boolean}> = ({ icon, label, description, enabled }) => (
  <div className="p-4 border border-zinc-900 bg-black flex items-center justify-between hover:border-zinc-800 transition-colors">
     <div className="flex items-center gap-4">
        <div className="p-2 bg-zinc-900 rounded-sm">
           {icon}
        </div>
        <div>
           <div className="text-[10px] font-bold uppercase tracking-widest">{label}</div>
           <p className="text-[9px] text-zinc-600 uppercase tracking-tight">{description}</p>
        </div>
     </div>
     <button className={`w-10 h-5 rounded-full relative transition-colors ${enabled ? 'bg-indigo-600' : 'bg-zinc-800'}`}>
        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${enabled ? 'left-5.5' : 'left-0.5'}`}></div>
     </button>
  </div>
);

export default NotificationSection;
