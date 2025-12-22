
import React from 'react';
import { Shield, Cpu, Activity, Database, Layout, Search, Mic, Send, Zap, LogOut, Terminal, Radio } from 'lucide-react';

export const BOOT_LOGS = [
  "INITIALIZING KAI_KERNEL_V2.5.0",
  "STAGING NEURAL PATHWAYS...",
  "CONNECTING TO GLOBAL QUANTUM GRID...",
  "BYPASSING SECURE PROTOCOL LAYER 7",
  "DECRYPTING OPERATOR_ENCLAVE...",
  "AUTHENTICATING BIOMETRICS...",
  "RECALIBRATING TACTICAL PARAMETERS",
  "CORE_STABILITY: 98.4%",
  "NEURAL_LATENCY: 0.12ms",
  "MEM_STACK: ALLOCATED",
  "UPLINK ESTABLISHED",
  "KAI_INTEL: ONLINE"
];

export const ICONS = {
  Shield: <Shield className="w-5 h-5 text-cyan-400" />,
  Cpu: <Cpu className="w-5 h-5 text-cyan-400" />,
  Activity: <Activity className="w-5 h-5 text-cyan-400" />,
  Database: <Database className="w-5 h-5 text-cyan-400" />,
  Layout: <Layout className="w-5 h-5 text-cyan-400" />,
  Search: <Search className="w-5 h-5 text-cyan-400" />,
  Mic: <Mic className="w-5 h-5 text-cyan-400" />,
  Send: <Send className="w-5 h-5 text-cyan-400" />,
  Zap: <Zap className="w-5 h-5 text-amber-400" />,
  LogOut: <LogOut className="w-5 h-5 text-red-500" />,
  Terminal: <Terminal className="w-5 h-5 text-cyan-400" />,
  Radio: <Radio className="w-5 h-5 text-cyan-400" />
};
