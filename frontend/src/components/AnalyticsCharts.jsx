import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from 'recharts';
import { formatR } from '../utils/time';

const COLORS = { bull: '#22c55e', bear: '#ef4444', accent: '#6366f1', gray: '#6b7280' };

export default function AnalyticsCharts() {
  const [analytics, setAnalytics] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [aRes, wRes] = await Promise.all([
          fetch('/api/analytics'),
          fetch('/api/analytics/weekly'),
        ]);
        setAnalytics(await aRes.json());
        setWeekly(await wRes.json());
      } catch (err) {
        console.error('Failed to fetch analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="text-gray-400 text-center py-8">Yükleniyor...</div>;
  }

  if (!analytics) {
    return <div className="text-gray-500 text-center py-8">Veri yüklenemedi.</div>;
  }

  const winLossData = [
    { name: 'TP', value: analytics.wins, color: COLORS.bull },
    { name: 'SL', value: analytics.losses, color: COLORS.bear },
  ];

  const conditionData = [
    {
      name: 'LRLR',
      win_rate: analytics.by_condition.LRLR.win_rate,
      pnl: analytics.by_condition.LRLR.pnl_r,
      total: analytics.by_condition.LRLR.total,
    },
    {
      name: 'HRLR',
      win_rate: analytics.by_condition.HRLR.win_rate,
      pnl: analytics.by_condition.HRLR.pnl_r,
      total: analytics.by_condition.HRLR.total,
    },
  ];

  // Kümülatif PnL hesapla
  let cumPnl = 0;
  const weeklyWithCum = weekly.map((w) => {
    cumPnl += w.pnl_r;
    return { ...w, cum_pnl: parseFloat(cumPnl.toFixed(2)) };
  });

  return (
    <div className="space-y-6">
      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Toplam İşlem" value={analytics.total_trades} />
        <StatCard
          label="Win Rate"
          value={`${analytics.win_rate}%`}
          color={analytics.win_rate >= 50 ? 'text-bull' : 'text-bear'}
        />
        <StatCard
          label="Toplam PnL"
          value={formatR(analytics.total_pnl_r)}
          color={analytics.total_pnl_r >= 0 ? 'text-bull' : 'text-bear'}
        />
        <StatCard label="Açık İşlem" value={analytics.open_trades} color="text-yellow-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Win/Loss Pie */}
        <div className="bg-dark-700 rounded-lg border border-dark-600 p-4">
          <h3 className="text-white font-semibold mb-4">Win / Loss Dağılımı</h3>
          {analytics.total_trades > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={winLossData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
                  {winLossData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 text-center py-16">Henüz veri yok</div>
          )}
        </div>

        {/* Condition Comparison */}
        <div className="bg-dark-700 rounded-lg border border-dark-600 p-4">
          <h3 className="text-white font-semibold mb-4">LRLR vs HRLR Performansı</h3>
          {conditionData.some((d) => d.total > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={conditionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#24243a" />
                <XAxis dataKey="name" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{ background: '#1a1a26', border: '1px solid #24243a', borderRadius: 8 }}
                />
                <Bar dataKey="win_rate" name="Win Rate %" fill={COLORS.accent} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 text-center py-16">Henüz veri yok</div>
          )}
        </div>
      </div>

      {/* Weekly Cumulative PnL */}
      <div className="bg-dark-700 rounded-lg border border-dark-600 p-4">
        <h3 className="text-white font-semibold mb-4">Haftalık Kümülatif PnL (R)</h3>
        {weeklyWithCum.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={weeklyWithCum}>
              <CartesianGrid strokeDasharray="3 3" stroke="#24243a" />
              <XAxis dataKey="week" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{ background: '#1a1a26', border: '1px solid #24243a', borderRadius: 8 }}
              />
              <Line
                type="monotone"
                dataKey="cum_pnl"
                name="Kümülatif PnL (R)"
                stroke={COLORS.accent}
                strokeWidth={2}
                dot={{ fill: COLORS.accent, r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-gray-500 text-center py-16">Henüz haftalık veri yok</div>
        )}
      </div>

      {/* Weekly Breakdown Table */}
      {weekly.length > 0 && (
        <div className="bg-dark-700 rounded-lg border border-dark-600 p-4">
          <h3 className="text-white font-semibold mb-4">Haftalık Detay</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase border-b border-dark-600">
                <th className="text-left py-2 px-2">Hafta</th>
                <th className="text-right py-2 px-2">İşlem</th>
                <th className="text-right py-2 px-2">Kazanç</th>
                <th className="text-right py-2 px-2">Win Rate</th>
                <th className="text-right py-2 px-2">PnL (R)</th>
              </tr>
            </thead>
            <tbody>
              {weekly.map((w) => (
                <tr key={w.week} className="border-b border-dark-700">
                  <td className="py-2 px-2 text-gray-300">{w.week}</td>
                  <td className="py-2 px-2 text-right text-white">{w.trades}</td>
                  <td className="py-2 px-2 text-right text-bull">{w.wins}</td>
                  <td className="py-2 px-2 text-right text-gray-300">{w.win_rate}%</td>
                  <td
                    className={`py-2 px-2 text-right font-mono font-bold ${
                      w.pnl_r >= 0 ? 'text-bull' : 'text-bear'
                    }`}
                  >
                    {formatR(w.pnl_r)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color = 'text-white' }) {
  return (
    <div className="bg-dark-700 rounded-lg border border-dark-600 p-4">
      <div className="text-gray-500 text-xs uppercase mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
