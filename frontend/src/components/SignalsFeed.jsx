import { useState, useEffect } from 'react';
import useSocket from '../hooks/useSocket';
import SignalCard from './SignalCard';

export default function SignalsFeed() {
  const { signals: liveSignals } = useSocket();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const res = await fetch('/api/signals?limit=50');
        const data = await res.json();
        setSignals(data);
      } catch (err) {
        console.error('Failed to fetch signals:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSignals();
  }, []);

  // Merge live signals
  const allSignals = [...liveSignals, ...signals].reduce((acc, s) => {
    if (!acc.find((x) => x.id === s.id)) acc.push(s);
    return acc;
  }, []);

  if (loading) {
    return <div className="text-gray-400 text-center py-8">Yükleniyor...</div>;
  }

  if (allSignals.length === 0) {
    return (
      <div className="text-gray-500 text-center py-12">
        <p className="text-lg mb-2">Henüz sinyal yok</p>
        <p className="text-sm">Motor çalışıyor, piyasa koşulları oluştuğunda sinyaller burada görünecek.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {allSignals.map((sig) => (
        <SignalCard key={sig.id} signal={sig} />
      ))}
    </div>
  );
}
