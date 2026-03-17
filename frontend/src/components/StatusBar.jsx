import { useState, useEffect } from 'react';
import { Wifi, WifiOff, Clock } from 'lucide-react';

export default function StatusBar() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        setStatus(data);
      } catch {
        setStatus(null);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const isRunning = status?.status === 'running';

  return (
    <div className="flex items-center gap-4 text-sm">
      {/* NY Time */}
      <div className="flex items-center gap-1.5 text-gray-300">
        <Clock size={14} />
        <span>{status?.ny_time || '—'}</span>
      </div>

      {/* Session */}
      {status?.session && (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-dark-600 text-gray-300">
          {status.session}
        </span>
      )}

      {/* Macro */}
      {status?.macro_active && (
        <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-500/20 text-yellow-400 animate-pulse">
          MACRO
        </span>
      )}

      {/* Connection */}
      <div className="flex items-center gap-1.5">
        {isRunning ? (
          <Wifi size={14} className="text-bull" />
        ) : (
          <WifiOff size={14} className="text-bear" />
        )}
        <span className={isRunning ? 'text-bull' : 'text-bear'}>
          {isRunning ? 'Bağlı' : 'Bağlantı yok'}
        </span>
      </div>
    </div>
  );
}
