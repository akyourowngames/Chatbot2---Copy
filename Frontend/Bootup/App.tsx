
import React, { useState, useEffect } from 'react';
import BootSequence from './components/BootSequence';
import Dashboard from './components/Dashboard';

const App: React.FC = () => {
  const [bootStatus, setBootStatus] = useState<'booting' | 'ready'>('booting');

  useEffect(() => {
    // Optional: simulate global sound effect trigger here if needed
  }, []);

  const handleBootComplete = () => {
    setBootStatus('ready');
  };

  return (
    <div className="relative w-screen h-screen bg-[#050505] text-[#e2e8f0] selection:bg-indigo-500/30">
      <div className="scanline pointer-events-none" />
      
      {bootStatus === 'booting' ? (
        <BootSequence onComplete={handleBootComplete} />
      ) : (
        <Dashboard />
      )}
      
      {/* Global Interface Overlays */}
      <div className="fixed inset-0 pointer-events-none border border-indigo-500/10 z-50 pointer-events-none" />
      <div className="fixed top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.4)_100%)] pointer-events-none" />
    </div>
  );
};

export default App;
