import { NavLink, Outlet } from 'react-router-dom';
import StatusBar from './StatusBar';
import { Activity, Signal, BarChart3, TrendingUp } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: Activity },
  { to: '/signals', label: 'Sinyaller', icon: Signal },
  { to: '/trades', label: 'İşlemler', icon: TrendingUp },
  { to: '/analytics', label: 'Analiz', icon: BarChart3 },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-dark-900 flex flex-col">
      {/* Top Bar */}
      <header className="bg-dark-800 border-b border-dark-600 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
            <Activity size={18} className="text-white" />
          </div>
          <h1 className="text-lg font-bold text-white tracking-tight">ICT Signal Bot</h1>
        </div>
        <StatusBar />
      </header>

      {/* Nav */}
      <nav className="bg-dark-800 border-b border-dark-600 px-6">
        <div className="flex gap-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                  isActive
                    ? 'border-accent text-accent'
                    : 'border-transparent text-gray-400 hover:text-gray-200'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
