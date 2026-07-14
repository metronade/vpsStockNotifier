import type { ReactNode } from 'react';

type View = 'dashboard' | 'providers' | 'settings';

interface LayoutProps {
  view: View;
  onViewChange: (view: View) => void;
  children: ReactNode;
}

export function Layout({ view, onViewChange, children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center text-sm font-bold">
              V
            </div>
            <h1 className="text-lg font-semibold">VPS Stock Notifier</h1>
          </div>
          <nav className="flex gap-1">
            <NavButton
              active={view === 'dashboard'}
              onClick={() => onViewChange('dashboard')}
            >
              Dashboard
            </NavButton>
            <NavButton
              active={view === 'providers'}
              onClick={() => onViewChange('providers')}
            >
              Providers
            </NavButton>
            <NavButton
              active={view === 'settings'}
              onClick={() => onViewChange('settings')}
            >
              Settings
            </NavButton>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}

function NavButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
        active
          ? 'bg-slate-800 text-white'
          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
      }`}
    >
      {children}
    </button>
  );
}
