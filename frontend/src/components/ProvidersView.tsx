import { useEffect, useState } from 'react';
import { api } from '../api';
import type { Provider } from '../types';
import { DriverBadge, ScanStatusDot } from './Badge';
import { AddProviderModal } from './AddProviderModal';

interface ProvidersViewProps {
  onOpenProvider: (id: number) => void;
}

export function ProvidersView({ onOpenProvider }: ProvidersViewProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setProviders(await api.listProviders());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">Providers</h2>
          <p className="text-sm text-slate-400">
            {providers.length} configured
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="btn-secondary">
            Refresh
          </button>
          <button onClick={() => setShowAdd(true)} className="btn-primary">
            + Add Provider
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30 text-sm text-rose-300 mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">Loading…</p>
      ) : providers.length === 0 ? (
        <EmptyState onAdd={() => setShowAdd(true)} />
      ) : (
        <div className="grid gap-3">
          {providers.map((p) => (
            <ProviderCard
              key={p.id}
              provider={p}
              onOpen={() => onOpenProvider(p.id)}
            />
          ))}
        </div>
      )}

      {showAdd && (
        <AddProviderModal
          onClose={() => setShowAdd(false)}
          onSaved={load}
        />
      )}
    </div>
  );
}

function ProviderCard({
  provider,
  onOpen,
}: {
  provider: Provider;
  onOpen: () => void;
}) {
  const lastScan = provider.last_scan_at
    ? formatRelative(provider.last_scan_at)
    : 'never';
  return (
    <button
      onClick={onOpen}
      className="w-full text-left p-4 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 hover:bg-slate-900 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <ScanStatusDot status={provider.last_scan_status} />
            <h3 className="font-medium truncate">{provider.name}</h3>
            {!provider.is_active && (
              <span className="text-xs text-slate-500">(paused)</span>
            )}
          </div>
          <p className="text-xs text-slate-500 truncate">{provider.url}</p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <DriverBadge type={provider.driver_type} />
          <span className="text-xs text-slate-500">
            every {formatDuration(provider.scan_interval_seconds)}
          </span>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
        <span>Last scan: {lastScan}</span>
        {provider.last_error && (
          <span className="text-rose-400 truncate ml-3">
            {provider.last_error}
          </span>
        )}
      </div>
    </button>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="text-center py-16 border border-dashed border-slate-800 rounded-lg">
      <h3 className="text-lg font-medium mb-1">No providers yet</h3>
      <p className="text-sm text-slate-400 mb-4">
        Add a VPS shop to start monitoring stock changes.
      </p>
      <button onClick={onAdd} className="btn-primary">
        + Add your first provider
      </button>
    </div>
  );
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h`;
}
