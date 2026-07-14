import { useState } from 'react';
import { Layout } from './components/Layout';
import { DashboardView } from './components/DashboardView';
import { ProvidersView } from './components/ProvidersView';
import { ProviderDetail } from './components/ProviderDetail';
import { SettingsView } from './components/SettingsView';

type View =
  | { name: 'dashboard' }
  | { name: 'providers' }
  | { name: 'provider'; id: number }
  | { name: 'settings' };

type NavTarget = 'dashboard' | 'providers' | 'settings';

export default function App() {
  const [view, setView] = useState<View>({ name: 'dashboard' });

  const navTarget: NavTarget =
    view.name === 'settings'
      ? 'settings'
      : view.name === 'dashboard'
        ? 'dashboard'
        : 'providers';

  function handleNavChange(target: NavTarget) {
    if (target === 'dashboard') setView({ name: 'dashboard' });
    else if (target === 'providers') setView({ name: 'providers' });
    else setView({ name: 'settings' });
  }

  return (
    <Layout view={navTarget} onViewChange={handleNavChange}>
      {view.name === 'dashboard' && (
        <DashboardView
          onOpenProvider={(id) => setView({ name: 'provider', id })}
        />
      )}
      {view.name === 'providers' && (
        <ProvidersView
          onOpenProvider={(id) => setView({ name: 'provider', id })}
        />
      )}
      {view.name === 'provider' && (
        <ProviderDetail
          providerId={view.id}
          onBack={() => setView({ name: 'providers' })}
        />
      )}
      {view.name === 'settings' && <SettingsView />}
    </Layout>
  );
}
