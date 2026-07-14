import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import type {
  Location,
  Product,
  Provider,
  StockHistoryEntry,
} from '../types';
import { useFormatTime } from '../timezone';
import { DriverBadge, ScanStatusDot, StockBadge } from './Badge';

type Tab = 'products' | 'locations' | 'history';

interface ProviderDetailProps {
  providerId: number;
  onBack: () => void;
}

export function ProviderDetail({ providerId, onBack }: ProviderDetailProps) {
  const [provider, setProvider] = useState<Provider | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [history, setHistory] = useState<StockHistoryEntry[]>([]);
  const [tab, setTab] = useState<Tab>('products');
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const formatTime = useFormatTime();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, prods, locs, hist] = await Promise.all([
        api.getProvider(providerId),
        api.listProducts(providerId),
        api.listLocations(providerId),
        api.getHistory(providerId),
      ]);
      setProvider(p);
      setProducts(prods);
      setLocations(locs);
      setHistory(hist);
    } catch (exc) {
      console.error(exc);
    } finally {
      setLoading(false);
    }
  }, [providerId]);

  useEffect(() => {
    load();
  }, [load]);

  async function toggleProduct(product: Product, isMonitored: boolean) {
    setProducts((prev) =>
      prev.map((p) => (p.id === product.id ? { ...p, is_monitored: isMonitored } : p)),
    );
    try {
      await api.updateProduct(providerId, product.id, isMonitored);
    } catch (exc) {
      // revert on failure
      setProducts((prev) =>
        prev.map((p) =>
          p.id === product.id ? { ...p, is_monitored: product.is_monitored } : p,
        ),
      );
      alert(exc instanceof Error ? exc.message : String(exc));
    }
  }

  async function toggleLocation(location: Location, isMonitored: boolean) {
    setLocations((prev) =>
      prev.map((l) => (l.id === location.id ? { ...l, is_monitored: isMonitored } : l)),
    );
    try {
      await api.updateLocation(providerId, location.id, isMonitored);
    } catch (exc) {
      setLocations((prev) =>
        prev.map((l) =>
          l.id === location.id ? { ...l, is_monitored: location.is_monitored } : l,
        ),
      );
      alert(exc instanceof Error ? exc.message : String(exc));
    }
  }

  async function handleScanNow() {
    setScanning(true);
    setScanResult(null);
    try {
      const result = await api.scanNow(providerId);
      setScanResult(
        result.status === 'ok'
          ? `Scan complete — ${result.state_changes} new event(s).`
          : `Scan failed: ${result.error ?? 'unknown error'}`,
      );
      await load();
    } catch (exc) {
      setScanResult(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setScanning(false);
    }
  }

  async function handleDelete() {
    if (!provider) return;
    if (!confirm(`Delete provider "${provider.name}"? This removes all history.`)) {
      return;
    }
    try {
      await api.deleteProvider(providerId);
      onBack();
    } catch (exc) {
      alert(exc instanceof Error ? exc.message : String(exc));
    }
  }

  if (loading || !provider) {
    return <p className="text-slate-400">Loading…</p>;
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="text-sm text-slate-400 hover:text-white mb-4"
      >
        ← Back to providers
      </button>

      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <ScanStatusDot status={provider.last_scan_status} />
            <h2 className="text-xl font-semibold">{provider.name}</h2>
            <DriverBadge type={provider.driver_type} />
            {!provider.is_active && (
              <span className="text-xs text-slate-500">(paused)</span>
            )}
          </div>
          <a
            href={provider.url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-sky-400 hover:underline truncate block"
          >
            {provider.url}
          </a>
          <p className="text-xs text-slate-500 mt-1">
            Scans every {formatInterval(provider.scan_interval_seconds)} · last
            scan {formatTime(provider.last_scan_at)}
          </p>
          {provider.last_error && (
            <p className="text-xs text-rose-400 mt-1">{provider.last_error}</p>
          )}
        </div>
        <div className="flex flex-col gap-2 shrink-0">
          <button
            onClick={handleScanNow}
            disabled={scanning}
            className="btn-primary"
          >
            {scanning ? 'Scanning…' : 'Scan now'}
          </button>
          <button onClick={handleDelete} className="btn-danger">
            Delete
          </button>
        </div>
      </div>

      {scanResult && (
        <div className="mb-4 p-3 rounded bg-slate-800/60 border border-slate-700 text-sm">
          {scanResult}
        </div>
      )}

      <div className="flex gap-1 border-b border-slate-800 mb-4">
        <TabButton active={tab === 'products'} onClick={() => setTab('products')}>
          Products ({products.length})
        </TabButton>
        <TabButton active={tab === 'locations'} onClick={() => setTab('locations')}>
          Locations ({locations.length})
        </TabButton>
        <TabButton active={tab === 'history'} onClick={() => setTab('history')}>
          History
        </TabButton>
      </div>

      {tab === 'products' && (
        <ProductList products={products} onToggle={toggleProduct} />
      )}
      {tab === 'locations' && (
        <LocationList locations={locations} onToggle={toggleLocation} />
      )}
      {tab === 'history' && <HistoryList entries={history} />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-2 text-sm border-b-2 -mb-px transition-colors ${
        active
          ? 'border-sky-500 text-white'
          : 'border-transparent text-slate-400 hover:text-white'
      }`}
    >
      {children}
    </button>
  );
}

function ProductList({
  products,
  onToggle,
}: {
  products: Product[];
  onToggle: (product: Product, isMonitored: boolean) => void;
}) {
  if (products.length === 0) {
    return (
      <p className="text-sm text-slate-500 italic">
        No products recorded yet. Run a scan.
      </p>
    );
  }
  return (
    <div className="space-y-1.5">
      {products.map((p) => (
        <div
          key={p.id}
          className="flex items-center justify-between gap-3 p-3 rounded bg-slate-900/60 border border-slate-800"
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium">{p.display_name}</span>
              <StockBadge state={p.last_state} />
              {p.last_count !== null && p.last_count > 0 && (
                <span className="text-xs text-slate-500">
                  ({p.last_count} reported)
                </span>
              )}
            </div>
            {p.key !== p.display_name && (
              <div className="text-xs text-slate-500 truncate">{p.key}</div>
            )}
          </div>
          <MonitorToggle
            checked={p.is_monitored}
            onChange={(v) => onToggle(p, v)}
          />
        </div>
      ))}
    </div>
  );
}

function LocationList({
  locations,
  onToggle,
}: {
  locations: Location[];
  onToggle: (location: Location, isMonitored: boolean) => void;
}) {
  if (locations.length === 0) {
    return (
      <p className="text-sm text-slate-500 italic">
        No locations detected yet. They will appear here as soon as the dropdown /
        sidebar is scanned.
      </p>
    );
  }
  return (
    <div className="space-y-1.5">
      {locations.map((l) => (
        <div
          key={l.id}
          className="flex items-center justify-between gap-3 p-3 rounded bg-slate-900/60 border border-slate-800"
        >
          <div className="min-w-0">
            <div className="font-medium">{l.display_name}</div>
            <div className="text-xs text-slate-500">
              first seen {formatTime(l.first_seen_at)}
              {l.last_seen_at && ` · last seen ${formatTime(l.last_seen_at)}`}
            </div>
          </div>
          <MonitorToggle
            checked={l.is_monitored}
            onChange={(v) => onToggle(l, v)}
          />
        </div>
      ))}
    </div>
  );
}

function HistoryList({ entries }: { entries: StockHistoryEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="text-sm text-slate-500 italic">
        No events yet. Notifications and state changes will be logged here.
      </p>
    );
  }
  return (
    <div className="space-y-1.5">
      {entries.map((e) => (
        <div
          key={e.id}
          className="p-3 rounded bg-slate-900/60 border border-slate-800 text-sm"
        >
          <div className="flex items-center justify-between gap-3">
            <span className="font-medium">
              {EVENT_LABELS[e.event_type]}
            </span>
            <span className="text-xs text-slate-500">
              {formatTime(e.created_at)}
            </span>
          </div>
          <div className="text-slate-400 mt-0.5">
            {e.previous_state && (
              <>
                <span className="text-rose-400">{e.previous_state}</span> →{' '}
              </>
            )}
            <span className="text-emerald-400">{e.new_state ?? '-'}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function MonitorToggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors ${
        checked ? 'bg-sky-500' : 'bg-slate-700'
      }`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

const EVENT_LABELS: Record<string, string> = {
  state_change: 'State change',
  new_location: 'New location detected',
  scan_error: 'Scan error',
};

function formatInterval(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const hours = Math.floor(seconds / 3600);
  return `${hours}h`;
}
