import React, { useState, useEffect } from 'react';
import {
    Monitor,
    Smartphone,
    Plus,
    RefreshCw,
    Copy,
    Check,
    AlertCircle,
    Trash2,
    Wifi,
    WifiOff,
    Clock
} from 'lucide-react';
import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

// Firebase Config
const firebaseConfig = {
    apiKey: "AIzaSyAVv4EhUiVZSf54iZlB-ud05pxIlO8zBWk",
    authDomain: "kai-g-80f9c.firebaseapp.com",
    projectId: "kai-g-80f9c",
    storageBucket: "kai-g-80f9c.appspot.com",
    messagingSenderId: "125633190886",
    appId: "1:125633190886:web:65e1a7b4f59048a1768853"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface Device {
    device_id: string;
    name: string;
    registered_at: string;
    last_seen: string;
    is_online: boolean;
    user_id?: string;
}

const DeviceSection: React.FC = () => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [loading, setLoading] = useState(true);
    const [pairingCode, setPairingCode] = useState<string | null>(null);
    const [pairingExpiry, setPairingExpiry] = useState<number>(0);
    const [copied, setCopied] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [userToken, setUserToken] = useState<string | null>(null);

    // Get Firebase auth token
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (user) => {
            if (user) {
                const token = await user.getIdToken();
                setUserToken(token);
            } else {
                setUserToken(null);
            }
        });
        return () => unsubscribe();
    }, []);

    // Fetch devices
    const fetchDevices = async () => {
        setLoading(true);
        setError(null);
        try {
            const headers: HeadersInit = { 'Content-Type': 'application/json' };
            if (userToken) {
                headers['Authorization'] = `Bearer ${userToken}`;
            }

            const res = await fetch(`${API_BASE}/agent/devices`, { headers });
            const data = await res.json();

            if (data.success) {
                setDevices(data.devices || []);
            } else {
                setError(data.error || 'Failed to fetch devices');
            }
        } catch (err) {
            console.error('Error fetching devices:', err);
            setError('Unable to connect to server');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDevices();
        // Refresh every 30 seconds
        const interval = setInterval(fetchDevices, 30000);
        return () => clearInterval(interval);
    }, [userToken]);

    // Generate pairing code
    const generatePairingCode = async () => {
        setError(null);
        try {
            const headers: HeadersInit = { 'Content-Type': 'application/json' };
            if (userToken) {
                headers['Authorization'] = `Bearer ${userToken}`;
            }

            const res = await fetch(`${API_BASE}/agent/generate-pairing-code`, {
                method: 'POST',
                headers
            });
            const data = await res.json();

            if (data.success) {
                setPairingCode(data.code);
                setPairingExpiry(600); // 10 minutes
            } else {
                setError(data.error || 'Failed to generate pairing code');
            }
        } catch (err) {
            console.error('Error generating code:', err);
            setError('Unable to generate pairing code');
        }
    };

    // Countdown timer for pairing code
    useEffect(() => {
        if (pairingExpiry > 0) {
            const timer = setInterval(() => {
                setPairingExpiry(prev => {
                    if (prev <= 1) {
                        setPairingCode(null);
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [pairingExpiry]);

    // Copy to clipboard
    const copyCode = () => {
        if (pairingCode) {
            navigator.clipboard.writeText(pairingCode);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Format time
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const formatLastSeen = (isoString: string) => {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return `${Math.floor(diffMins / 1440)}d ago`;
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-bold uppercase tracking-wider text-indigo-400">
                        Connected Devices
                    </h2>
                    <p className="text-[10px] text-zinc-500 mt-1 uppercase tracking-widest">
                        Manage your paired PC agents
                    </p>
                </div>
                <button
                    onClick={fetchDevices}
                    className="p-2 text-zinc-500 hover:text-indigo-400 transition-colors"
                    title="Refresh"
                >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            {/* Error Display */}
            {error && (
                <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-xs">
                    <AlertCircle size={14} />
                    <span>{error}</span>
                </div>
            )}

            {/* Device List */}
            <div className="space-y-3">
                {loading && devices.length === 0 ? (
                    <div className="text-center py-8 text-zinc-500">
                        <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-indigo-500" />
                        <p className="text-xs uppercase tracking-widest">Scanning for devices...</p>
                    </div>
                ) : devices.length === 0 ? (
                    <div className="text-center py-8 bg-zinc-900/50 border border-zinc-800 rounded-lg">
                        <Monitor size={32} className="mx-auto mb-3 text-zinc-600" />
                        <p className="text-sm text-zinc-400">No devices connected</p>
                        <p className="text-[10px] text-zinc-600 mt-1">Generate a pairing code to connect your PC</p>
                    </div>
                ) : (
                    devices.map((device) => (
                        <div
                            key={device.device_id}
                            className="flex items-center justify-between p-4 bg-[#0a0a0f] border border-indigo-900/30 rounded-lg hover:border-indigo-500/50 transition-colors group"
                        >
                            <div className="flex items-center gap-4">
                                <div className={`p-2 rounded-lg ${device.is_online ? 'bg-green-500/10' : 'bg-zinc-800'}`}>
                                    <Monitor size={20} className={device.is_online ? 'text-green-400' : 'text-zinc-500'} />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="font-bold text-sm">{device.name}</span>
                                        {device.is_online ? (
                                            <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 border border-green-500/30 rounded-full text-[9px] text-green-400 font-bold uppercase">
                                                <Wifi size={10} />
                                                Online
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-1 px-2 py-0.5 bg-zinc-800 border border-zinc-700 rounded-full text-[9px] text-zinc-500 font-bold uppercase">
                                                <WifiOff size={10} />
                                                Offline
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-3 mt-1 text-[10px] text-zinc-500">
                                        <span className="flex items-center gap-1">
                                            <Clock size={10} />
                                            {formatLastSeen(device.last_seen)}
                                        </span>
                                        <span className="text-zinc-700">|</span>
                                        <span className="font-mono">{device.device_id.slice(0, 8)}...</span>
                                    </div>
                                </div>
                            </div>

                            {/* Device Actions */}
                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button className="p-2 text-zinc-500 hover:text-red-400 transition-colors" title="Remove device">
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Pair New Device Section */}
            <div className="border-t border-zinc-800 pt-8">
                <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-4">
                    Pair New Device
                </h3>

                {pairingCode ? (
                    <div className="bg-indigo-950/30 border border-indigo-500/30 rounded-lg p-6">
                        <div className="text-center">
                            <p className="text-[10px] text-indigo-400 uppercase tracking-widest mb-3">
                                Enter this code on your PC
                            </p>

                            {/* Large Pairing Code Display */}
                            <div className="flex items-center justify-center gap-2 mb-4">
                                <code className="text-3xl font-mono font-bold tracking-[0.3em] text-white bg-black/50 px-6 py-3 rounded-lg border border-indigo-500/50">
                                    {pairingCode}
                                </code>
                                <button
                                    onClick={copyCode}
                                    className="p-3 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 rounded-lg transition-colors"
                                    title="Copy code"
                                >
                                    {copied ? <Check size={18} className="text-green-400" /> : <Copy size={18} className="text-indigo-400" />}
                                </button>
                            </div>

                            {/* Timer */}
                            <div className="flex items-center justify-center gap-2 text-sm text-zinc-400">
                                <Clock size={14} />
                                <span>Expires in <span className="text-indigo-400 font-bold">{formatTime(pairingExpiry)}</span></span>
                            </div>

                            {/* Instructions */}
                            <div className="mt-6 text-left bg-black/30 rounded-lg p-4 border border-zinc-800">
                                <p className="text-[10px] text-zinc-500 uppercase tracking-widest mb-2">Run on your PC:</p>
                                <code className="block text-xs text-green-400 font-mono bg-black/50 p-3 rounded overflow-x-auto">
                                    python -m LocalAgent.agent --register {pairingCode} --api {API_BASE}
                                </code>
                            </div>
                        </div>
                    </div>
                ) : (
                    <button
                        onClick={generatePairingCode}
                        className="w-full flex items-center justify-center gap-3 p-4 bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/30 hover:border-indigo-500/50 rounded-lg transition-all group"
                    >
                        <div className="p-2 bg-indigo-600/20 rounded-lg group-hover:bg-indigo-600/30 transition-colors">
                            <Plus size={20} className="text-indigo-400" />
                        </div>
                        <div className="text-left">
                            <p className="text-sm font-bold text-indigo-400">Generate Pairing Code</p>
                            <p className="text-[10px] text-zinc-500">Connect a new PC to your Kai account</p>
                        </div>
                    </button>
                )}
            </div>

            {/* Info Banner */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 flex items-start gap-3">
                <Smartphone size={18} className="text-zinc-500 mt-0.5 shrink-0" />
                <div className="text-xs text-zinc-500">
                    <p className="font-bold text-zinc-400 mb-1">About Device Pairing</p>
                    <p>Your devices are securely linked to your account. Only you can control your connected PCs.
                        Each device requires the Local Agent to be running to receive commands.</p>
                </div>
            </div>
        </div>
    );
};

export default DeviceSection;
