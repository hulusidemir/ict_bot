import { formatNYTime, formatNYDate, formatPrice } from '../utils/time';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

export default function SignalCard({ signal }) {
  const isLong = signal.direction === 'LONG';

  return (
    <div className="bg-dark-700 rounded-lg border border-dark-600 p-4 hover:border-dark-500 transition-colors">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-white font-bold text-sm">{signal.symbol}</span>
          <span
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${
              isLong ? 'bg-bull/20 text-bull' : 'bg-bear/20 text-bear'
            }`}
          >
            {isLong ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {signal.direction}
          </span>
        </div>
        <div className="text-gray-500 text-xs">
          {formatNYDate(signal.ny_time)} {formatNYTime(signal.ny_time)}
        </div>
      </div>

      {/* Prices */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div>
          <div className="text-gray-500 text-xs mb-0.5">Giriş (FVG)</div>
          <div className="text-white text-sm font-mono">
            {formatPrice(signal.fvg_low)} – {formatPrice(signal.fvg_high)}
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-xs mb-0.5">Hedef</div>
          <div className="text-bull text-sm font-mono">{formatPrice(signal.target)}</div>
        </div>
        <div>
          <div className="text-gray-500 text-xs mb-0.5">Stop Loss</div>
          <div className="text-bear text-sm font-mono">{formatPrice(signal.stop_loss)}</div>
        </div>
      </div>

      {/* Tags */}
      <div className="flex items-center gap-2 flex-wrap">
        {signal.risk_reward && (
          <span className="px-2 py-0.5 rounded text-xs bg-accent/20 text-accent font-medium">
            {signal.risk_reward}R
          </span>
        )}
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            signal.market_condition === 'LRLR'
              ? 'bg-green-500/20 text-green-400'
              : signal.market_condition === 'HRLR'
              ? 'bg-orange-500/20 text-orange-400'
              : 'bg-gray-500/20 text-gray-400'
          }`}
        >
          {signal.market_condition}
        </span>
        {signal.risk_label?.includes('Haber') && (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-red-500/20 text-red-400 font-medium">
            <AlertTriangle size={10} />
            Haber
          </span>
        )}
        {signal.session_tag && (
          <span className="px-2 py-0.5 rounded text-xs bg-dark-600 text-gray-400">
            {signal.session_tag}
          </span>
        )}
        <span
          className={`ml-auto px-2 py-0.5 rounded text-xs font-medium ${
            signal.status === 'ACTIVE'
              ? 'bg-blue-500/20 text-blue-400'
              : signal.status === 'TRIGGERED'
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-gray-500/20 text-gray-400'
          }`}
        >
          {signal.status}
        </span>
      </div>
    </div>
  );
}
