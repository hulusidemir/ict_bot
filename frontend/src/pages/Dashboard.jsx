import { useState, useEffect } from 'react';
import useSocket from '../hooks/useSocket';
import SignalCard from '../components/SignalCard';
import { formatR } from '../utils/time';
import { Activity, TrendingUp, Target, AlertCircle } from 'lucide-react';

export default function Dashboard() {
  const { connected, signals: liveSignals } = useSocket();
  const [stats, setStats] = useState(null);
  const [recentSignals, setRecentSignals] = useState([]);
  const [openTrades, setOpenTrades] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [aRes, sRes, tRes] = await Promise.all([
          fetch('/api/analytics'),
          fetch('/api/signals?limit=5'),
          fetch('/api/trades/open'),
        ]);
        setStats(await aRes.json());
        setRecentSignals(await sRes.json());
        setOpenTrades(await tRes.json());
      } catch (err) {
        console.error('Dashboard fetch error:', err);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  // Merge live signals into recent
  const displaySignals = [...liveSignals, ...recentSignals]
    .reduce((acc, s) => {
      if (!acc.find((x) => x.id === s.id)) acc.push(s);
      return acc;
    }, [])
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <DashCard
          icon={Activity}
          label="Durum"
          value={connected ? 'Aktif' : 'Bağlantı Yok'}
          color={connected ? 'text-bull' : 'text-bear'}
          iconColor={connected ? 'text-bull' : 'text-bear'}
        />
        <DashCard
          icon={Target}
          label="Win Rate"
          value={stats ? `${stats.win_rate}%` : '—'}
          color={stats?.win_rate >= 50 ? 'text-bull' : 'text-bear'}
          iconColor="text-accent"
        />
        <DashCard
          icon={TrendingUp}
          label="Toplam PnL"
          value={stats ? formatR(stats.total_pnl_r) : '—'}
          color={stats?.total_pnl_r >= 0 ? 'text-bull' : 'text-bear'}
          iconColor="text-accent"
        />
        <DashCard
          icon={AlertCircle}
          label="Açık İşlem"
          value={stats?.open_trades ?? '—'}
          color="text-yellow-400"
          iconColor="text-yellow-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Signals */}
        <div>
          <h2 className="text-white font-semibold text-lg mb-3">Son Sinyaller</h2>
          {displaySignals.length > 0 ? (
            <div className="space-y-3">
              {displaySignals.map((s) => (
                <SignalCard key={s.id} signal={s} />
              ))}
            </div>
          ) : (
            <div className="bg-dark-700 rounded-lg border border-dark-600 p-8 text-center text-gray-500">
              Motor çalışıyor, sinyal bekleniyor...
            </div>
          )}
        </div>

        {/* Open Trades */}
        <div>
          <h2 className="text-white font-semibold text-lg mb-3">Açık İşlemler</h2>
          {openTrades.length > 0 ? (
            <div className="space-y-3">
              {openTrades.map((t) => (
                <div
                  key={t.id}
                  className="bg-dark-700 rounded-lg border border-dark-600 p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-bold">{t.symbol}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold ${
                        t.direction === 'LONG'
                          ? 'bg-bull/20 text-bull'
                          : 'bg-bear/20 text-bear'
                      }`}
                    >
                      {t.direction}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <div className="text-gray-500 text-xs">Giriş</div>
                      <div className="text-white font-mono">{t.entry_price}</div>
                    </div>
                    <div>
                      <div className="text-gray-500 text-xs">Hedef</div>
                      <div className="text-bull font-mono">{t.target_price}</div>
                    </div>
                    <div>
                      <div className="text-gray-500 text-xs">Stop</div>
                      <div className="text-bear font-mono">{t.stop_price}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-dark-700 rounded-lg border border-dark-600 p-8 text-center text-gray-500">
              Şu anda açık işlem yok.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DashCard({ icon: Icon, label, value, color = 'text-white', iconColor = 'text-accent' }) {
  return (
    <div className="bg-dark-700 rounded-lg border border-dark-600 p-4 flex items-center gap-3">
      <div className={`p-2 rounded-lg bg-dark-600 ${iconColor}`}>
        <Icon size={20} />
      </div>
      <div>
        <div className="text-gray-500 text-xs uppercase">{label}</div>
        <div className={`text-xl font-bold ${color}`}>{value}</div>
      </div>
    </div>
  );
}
