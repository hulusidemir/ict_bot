import { useState, useEffect } from 'react';
import { formatNYTime, formatPrice, formatR } from '../utils/time';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export default function TradesTable() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const res = await fetch('/api/trades?limit=100');
        const data = await res.json();
        setTrades(data);
      } catch (err) {
        console.error('Failed to fetch trades:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrades();
    const interval = setInterval(fetchTrades, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-gray-400 text-center py-8">Yükleniyor...</div>;
  }

  if (trades.length === 0) {
    return (
      <div className="text-gray-500 text-center py-12">
        <p className="text-lg mb-2">Henüz işlem yok</p>
        <p className="text-sm">Sinyaller tetiklendiğinde simüle işlemler burada görünecek.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 text-xs uppercase border-b border-dark-600">
            <th className="text-left py-3 px-2">Sembol</th>
            <th className="text-left py-3 px-2">Yön</th>
            <th className="text-right py-3 px-2">Giriş</th>
            <th className="text-right py-3 px-2">Hedef</th>
            <th className="text-right py-3 px-2">Stop</th>
            <th className="text-left py-3 px-2">Giriş Zamanı</th>
            <th className="text-center py-3 px-2">Sonuç</th>
            <th className="text-right py-3 px-2">PnL</th>
            <th className="text-left py-3 px-2">Koşul</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t) => (
            <tr
              key={t.id}
              className="border-b border-dark-700 hover:bg-dark-700/50 transition-colors"
            >
              <td className="py-3 px-2 font-medium text-white">{t.symbol}</td>
              <td className="py-3 px-2">
                <span
                  className={`px-2 py-0.5 rounded text-xs font-bold ${
                    t.direction === 'LONG' ? 'bg-bull/20 text-bull' : 'bg-bear/20 text-bear'
                  }`}
                >
                  {t.direction}
                </span>
              </td>
              <td className="py-3 px-2 text-right font-mono text-gray-300">
                {formatPrice(t.entry_price)}
              </td>
              <td className="py-3 px-2 text-right font-mono text-bull">
                {formatPrice(t.target_price)}
              </td>
              <td className="py-3 px-2 text-right font-mono text-bear">
                {formatPrice(t.stop_price)}
              </td>
              <td className="py-3 px-2 text-gray-400 text-xs">
                {formatNYTime(t.entry_ny_time)}
              </td>
              <td className="py-3 px-2 text-center">
                {t.status === 'OPEN' ? (
                  <span className="flex items-center justify-center gap-1 text-yellow-400">
                    <Clock size={14} />
                    <span className="text-xs">Açık</span>
                  </span>
                ) : t.result === 'TP' ? (
                  <span className="flex items-center justify-center gap-1 text-bull">
                    <CheckCircle size={14} />
                    <span className="text-xs">TP</span>
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-1 text-bear">
                    <XCircle size={14} />
                    <span className="text-xs">SL</span>
                  </span>
                )}
              </td>
              <td
                className={`py-3 px-2 text-right font-mono font-bold ${
                  t.pnl_r == null
                    ? 'text-gray-500'
                    : t.pnl_r >= 0
                    ? 'text-bull'
                    : 'text-bear'
                }`}
              >
                {formatR(t.pnl_r)}
              </td>
              <td className="py-3 px-2">
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    t.market_condition === 'LRLR'
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-orange-500/20 text-orange-400'
                  }`}
                >
                  {t.market_condition}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
