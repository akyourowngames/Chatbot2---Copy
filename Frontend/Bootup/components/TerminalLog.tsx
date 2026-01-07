
import React from 'react';
import { motion } from 'framer-motion';

const TerminalLog: React.FC = () => {
  const logs = [
    "UPLINK_SECURED: STARK_OMEGA",
    "NEURAL_LATENCY: 0.08ms",
    "ENCRYPTING TEMP_STORAGE...",
    "ACCESS_GRANTED: NODE_42",
    "DECRYPTING OPERATOR_ENCLAVE",
    "BIOMETRICS_SYNC: 100%",
    "SYSTEM_STABILITY: OPTIMAL"
  ];

  return (
    <div className="space-y-4 font-mono">
      {logs.map((log, i) => (
        <motion.div 
          key={i} 
          initial={{ opacity: 0, x: -5 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className="group cursor-default flex items-center gap-3"
        >
          <div className="w-1 h-3 bg-cyan-500/20 group-hover:bg-cyan-400 transition-colors" />
          <div className="text-[9px] font-bold text-cyan-400/40 group-hover:text-cyan-400 transition-colors uppercase tracking-[0.2em]">
            {log}
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default TerminalLog;
