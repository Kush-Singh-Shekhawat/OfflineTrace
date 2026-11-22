import React from 'react';
import { NavLink } from 'react-router-dom';
import { FileText, Users, Search, ShieldCheck, Activity } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  backendOnline: boolean;
  errorBanner?: string | null;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  backendOnline,
  errorBanner,
}) => {
  const navItems = [
    { to: '/dashboard', label: 'Documents & Release', icon: FileText },
    { to: '/recipients', label: 'Recipients & Keys', icon: Users },
    { to: '/investigate', label: 'Forensic Investigation', icon: Search },
    { to: '/ledger', label: 'Quorum Ledger', icon: ShieldCheck },
  ];

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-2">
        <div className="text-lg font-bold tracking-tight px-2 py-3 border-b border-slate-800">
          OfflineTrace
        </div>
        <nav className="flex flex-col gap-1 mt-2">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/60">
          <span className="text-xs uppercase tracking-wider text-slate-400">
            Air-Gapped PQ Provenance Console
          </span>
          <div className="flex items-center gap-2 text-xs">
            <Activity
              className={`w-4 h-4 ${
                backendOnline ? 'text-emerald-400' : 'text-amber-400'
              }`}
            />
            <span>{backendOnline ? 'Node Connected' : 'Offline / Standby'}</span>
          </div>
        </header>

        {errorBanner && (
          <div className="bg-red-950 border-b border-red-800 text-red-200 px-6 py-2 text-sm">
            {errorBanner}
          </div>
        )}

        <main className="p-6 flex-1">{children}</main>
      </div>
    </div>
  );
};
