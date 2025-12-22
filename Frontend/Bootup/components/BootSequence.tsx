
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface BootSequenceProps {
  onComplete: () => void;
}

const BootSequence: React.FC<BootSequenceProps> = ({ onComplete }) => {
  const [stage, setStage] = useState<'stark-wipe' | 'hud-build' | 'data-sync' | 'auth'>('stark-wipe');
  const [dataLogs, setDataLogs] = useState<string[]>([]);

  useEffect(() => {
    // Stage Transitions
    const timers = [
      setTimeout(() => setStage('hud-build'), 2200),
      setTimeout(() => setStage('data-sync'), 4000),
      setTimeout(() => setStage('auth'), 6500),
      setTimeout(() => onComplete(), 8000),
    ];

    return () => timers.forEach(t => clearTimeout(t));
  }, [onComplete]);

  useEffect(() => {
    if (stage === 'data-sync') {
      const logs = [
        "INITIATING SYSTEM 1....",
        "\\NETWARE  196.25.65.9",
        "PROTOCOL: SCANNING 10.5.1.168",
        "CONNECTING...",
        "RELEASING CONFIGURATION...",
        "EXTEND SYSTEM MEMORY: YES",
        "COPY DIR: C:SECRET FILES",
        "CHECKSUM: OK",
        "RUN SYSTEM TOOL...",
        "PURGE ALL ON DIRECTORY...",
        "ENCRYPTING NEURAL_LINK...",
        "BIOMETRICS: VALIDATED",
        "UPLINK STABLE"
      ];
      let i = 0;
      const interval = setInterval(() => {
        if (i < logs.length) {
          setDataLogs(prev => [...prev, logs[i]]);
          i++;
        } else {
          clearInterval(interval);
        }
      }, 150);
      return () => clearInterval(interval);
    }
  }, [stage]);

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center overflow-hidden z-[1000] font-mono">
      <AnimatePresence mode="wait">
        
        {/* STAGE 1: STARK STYLE REVEAL */}
        {stage === 'stark-wipe' && (
          <motion.div 
            key="stark"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 1.2 }}
            className="relative flex flex-col items-center"
          >
            <div className="relative">
              {/* Wipe bar */}
              <motion.div 
                initial={{ left: '-10%', width: '0%' }}
                animate={{ 
                  left: ['-10%', '110%'],
                  width: ['10%', '30%', '10%']
                }}
                transition={{ duration: 1.8, ease: "easeInOut" }}
                className="absolute top-0 bottom-0 bg-cyan-400 z-20 shadow-[0_0_20px_#22d3ee]"
              />
              
              {/* Text Reveal */}
              <div className="flex items-baseline gap-4 overflow-hidden relative">
                <motion.h1 
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                  className="text-7xl font-black italic tracking-tighter text-white"
                >
                  KAI
                </motion.h1>
                <motion.h1 
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.8, duration: 0.5 }}
                  className="text-7xl font-black italic tracking-tighter text-cyan-500"
                >
                  INTEL
                </motion.h1>
              </div>
              
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: '100%' }}
                transition={{ delay: 1.2, duration: 0.4 }}
                className="h-[2px] bg-white/20 mt-2"
              />
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.5 }}
                transition={{ delay: 1.4 }}
                className="text-[10px] tracking-[1em] uppercase text-center mt-4 text-white"
              >
                STARK INDUSTRIES LEGACY CORE
              </motion.p>
            </div>
          </motion.div>
        )}

        {/* STAGE 2: HUD BUILD */}
        {stage === 'hud-build' && (
          <motion.div 
            key="hud"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full h-full relative"
          >
            {/* SVG Wireframe Build */}
            <svg className="absolute inset-0 w-full h-full opacity-30">
              <motion.path 
                d="M 100 100 L 900 100 L 950 150 L 950 850 L 900 900 L 100 900 L 50 850 L 50 150 Z"
                fill="none"
                stroke="#22d3ee"
                strokeWidth="1"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 2, ease: "easeInOut" }}
              />
              <motion.path 
                d="M 200 100 L 200 900 M 800 100 L 800 900 M 50 500 L 950 500"
                stroke="#22d3ee"
                strokeWidth="0.5"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.5, delay: 0.5 }}
              />
            </svg>
            
            <div className="absolute inset-0 flex items-center justify-center">
              <motion.div 
                animate={{ scale: [1, 1.05, 1], opacity: [0.7, 1, 0.7] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="flex flex-col items-center"
              >
                <div className="w-32 h-32 border-2 border-cyan-500/50 rounded-full flex items-center justify-center mb-8 relative">
                   <div className="absolute inset-0 border-t-4 border-cyan-400 rounded-full animate-spin" />
                   <span className="text-cyan-400 text-xs font-bold">SCANNING</span>
                </div>
                <h2 className="text-2xl font-black tracking-[0.5em] text-cyan-400 italic">INITIALIZING_CORE</h2>
              </motion.div>
            </div>
          </motion.div>
        )}

        {/* STAGE 3: DATA SYNC (The Image-inspired stage) */}
        {stage === 'data-sync' && (
          <motion.div 
            key="sync"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="w-full h-full flex flex-col p-12 bg-[#00050a]"
          >
            <div className="flex-1 flex flex-col justify-center items-center">
              {/* Glowing horizontal line */}
              <div className="w-full h-[2px] bg-cyan-400 shadow-[0_0_15px_#22d3ee] relative mb-12">
                 <div className="absolute -left-1 -top-1 w-3 h-3 bg-cyan-400 blur-sm" />
              </div>

              <div className="w-full max-w-4xl border border-cyan-500/20 bg-cyan-900/5 p-8 relative">
                {/* Decorative notches */}
                <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-cyan-400" />
                <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-cyan-400" />
                
                <h3 className="text-4xl font-black text-white mb-6 tracking-tight">INITIATING SYSTEM 1...</h3>
                
                <div className="space-y-1 h-64 overflow-hidden">
                   {dataLogs.map((log, i) => (
                     <motion.div 
                      initial={{ x: -10, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      key={i} 
                      className="text-cyan-400/80 text-lg flex gap-4 font-bold"
                     >
                        <span className="text-cyan-400/30">[{i.toString().padStart(2, '0')}]</span>
                        <span>{log}</span>
                     </motion.div>
                   ))}
                </div>
              </div>

              <div className="w-full h-[2px] bg-cyan-400 shadow-[0_0_15px_#22d3ee] relative mt-12" />
            </div>
          </motion.div>
        )}

        {/* STAGE 4: AUTHORIZATION */}
        {stage === 'auth' && (
          <motion.div 
            key="auth"
            initial={{ opacity: 0, scale: 2 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center"
          >
            <motion.div 
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ duration: 0.1, repeat: 10 }}
              className="bg-green-500 text-black px-12 py-6 text-6xl font-black italic tracking-tighter"
            >
              ACCESS GRANTED
            </motion.div>
            <div className="mt-8 text-green-500 font-bold tracking-[1em] uppercase">Operator Identified</div>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
};

export default BootSequence;
