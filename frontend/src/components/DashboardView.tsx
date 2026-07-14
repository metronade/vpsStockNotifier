import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import type { DashboardProvider, DashboardProduct, StockState } from '../types';
import { DriverBadge, ScanStatusDot } from './Badge';
import { useTimezone } from '../timezone';

interface DashboardViewProps {
  onOpenProvider: (id: number) => void;
}

export function DashboardView({ onOpenProvider }: DashboardViewProps) {
  const [providers, setProviders] = useState<DashboardProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProviders(await api.getDashboard());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">Dashboard</h2>
          <p className="text-sm text-slate-400">
            At-a-glance stock state across all providers.
          </p>
        </div>
        <button onClick={load} className="btn-secondary">
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30 text-sm text-rose-300 mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">Loading…</p>
      ) : providers.length === 0 ? (
        <p className="text-sm text-slate-500 italic">
          No providers yet. Add one on the Providers tab.
        </p>
      ) : (
        <div className="grid gap-3">
          {providers.map((p) => (
            <DashboardCard
              key={p.id}
              provider={p}
              onOpen={() => onOpenProvider(p.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function DashboardCard({
  provider,
  onOpen,
}: {
  provider: DashboardProvider;
  onOpen: () => void;
}) {
  const tz = useTimezone();
  const inStock = provider.products.filter(
    (p) => p.last_state === 'in_stock',
  );
  const outOfStock = provider.products.filter(
    (p) => p.last_state === 'out_of_stock',
  );
  const unknown = provider.products.filter(
    (p) => p.last_state === 'unknown',
  );

  const lastScan = provider.last_scan_at
    ? new Date(provider.last_scan_at).toLocaleString('de-DE', {
        timeZone: tz,
      })
    : 'never';

  return (
    <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
      <button
        onClick={onOpen}
        className="w-full text-left flex items-start justify-between gap-4 mb-3"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <ScanStatusDot status={provider.last_scan_status} />
            <h3 className="font-medium truncate">{provider.name}</h3>
            {!provider.is_active && (
              <span className="text-xs text-slate-500">(paused)</span>
            )}
          </div>
          <p className="text-xs text-slate-500">
            {inStock.length} in stock · {outOfStock.length} out ·{' '}
            {unknown.length} unknown · last scan {lastScan}
          </p>
        </div>
        <DriverBadge type={provider.driver_type} />
      </button>

      {provider.products.length === 0 ? (
        <p className="text-xs text-slate-500 italic">
          No products yet — run a scan.
        </p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {inStock.map((p) => (
            <StockPill key={p.id} product={p} state="in_stock" />
          ))}
          {outOfStock.map((p) => (
            <StockPill key={p.id} product={p} state="out_of_stock" />
          ))}
          {unknown.map((p) => (
            <StockPill key={p.id} product={p} state="unknown" />
          ))}
        </div>
      )}
    </div>
  );
}

const PILL_STYLES: Record<StockState, string> = {
  in_stock: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  out_of_stock: 'bg-rose-500/15 text-rose-300 ring-rose-500/30',
  unknown: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
};

function StockPill({
  product,
  state,
}: {
  product: DashboardProduct;
  state: StockState;
}) {
  return (
    <span
      title={product.key}
      className={`inline-flex items-center px-2 py-1 rounded text-xs ring-1 ${PILL_STYLES[state]}`}
    >
      {product.display_name}
    </span>
  );
}
