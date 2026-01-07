
import React from 'react';
import { motion } from 'framer-motion';

interface Props {
  label: string;
  value: number;
}

const TelemetryWidget: React.FC<Props> = ({ label, value }) => {
  return (
    <div className="space-y-3">
      <div className="flex justify-between text-[9px] font-black uppercase tracking-[0.3em] text-cyan-500/70">
        <span>{label}</span>
        <span className="text-cyan-400 shadow-sm">{value}%</span>
      </div>
      <div className="w-full h-1.5 bg-cyan-900/20 overflow-hidden rounded-full border border-cyan-500/10">
        <motion.div 
          className="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 shadow-[0_0_10px_#22d3ee]"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 2.5, ease: "circOut" }}
        />
      </div>
    </div>
  );
};

export default TelemetryWidget;
