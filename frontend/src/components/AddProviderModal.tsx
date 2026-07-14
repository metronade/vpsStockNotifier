import { useState } from 'react';
import { api } from '../api';
import type { DriverType, Location, Product } from '../types';

interface AddProviderModalProps {
  onClose: () => void;
  onSaved: () => void;
}

type Phase = 'form' | 'scanning' | 'results' | 'saving';

const DRIVER_DESCRIPTIONS: Record<DriverType, string> = {
  static_html: 'WHMCS-style product cards. Used by Frantech / BuyVM-like shops.',
  dynamic_dropdown:
    'A location/configuration dropdown that reveals stock when an option is selected. Used by Aluy-like shops.',
  complex_spa:
    'Highly interactive page with sliders, hover-revealed controls, or sidebars. Used by Kyun-like shops.',
};

const INTERVAL_OPTIONS = [
  { value: 60, label: '1 minute' },
  { value: 300, label: '5 minutes' },
  { value: 900, label: '15 minutes' },
  { value: 1800, label: '30 minutes' },
  { value: 3600, label: '1 hour' },
  { value: 21600, label: '6 hours' },
  { value: 43200, label: '12 hours' },
  { value: 86400, label: '24 hours' },
];

export function AddProviderModal({ onClose, onSaved }: AddProviderModalProps) {
  const [phase, setPhase] = useState<Phase>('form');
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [driverType, setDriverType] = useState<DriverType>('static_html');
  const [intervalSec, setIntervalSec] = useState(300);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<string[]>([]);
  const [providerId, setProviderId] = useState<number | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [monitoredProducts, setMonitoredProducts] = useState<Set<number>>(new Set());
  const [monitoredLocations, setMonitoredLocations] = useState<Set<number>>(
    new Set(),
  );

  async function handleScan(ev: React.FormEvent) {
    ev.preventDefault();
    setError(null);
    setPhase('scanning');
    try {
      const result = await api.createProvider({
        name: name.trim(),
        url: url.trim(),
        driver_type: driverType,
        scan_interval_seconds: intervalSec,
      });
      setProviderId(result.provider.id);
      setNotes(result.notes);
      // Refetch with IDs (InitialScanResponse items don't carry IDs)
      const [prods, locs] = await Promise.all([
        api.listProducts(result.provider.id),
        api.listLocations(result.provider.id),
      ]);
      setProducts(prods);
      setLocations(locs);
      setMonitoredProducts(new Set(prods.filter((p) => p.is_monitored).map((p) => p.id)));
      setMonitoredLocations(new Set(locs.filter((l) => l.is_monitored).map((l) => l.id)));
      setPhase('results');
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
      setPhase('form');
    }
  }

  async function handleSave() {
    if (providerId === null) return;
    setPhase('saving');
    setError(null);
    try {
      const tasks: Promise<unknown>[] = [];
      for (const p of products) {
        const want = monitoredProducts.has(p.id);
        if (want !== p.is_monitored) {
          tasks.push(api.updateProduct(providerId, p.id, want));
        }
      }
      for (const l of locations) {
        const want = monitoredLocations.has(l.id);
        if (want !== l.is_monitored) {
          tasks.push(api.updateLocation(providerId, l.id, want));
        }
      }
      await Promise.all(tasks);
      onSaved();
      onClose();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
      setPhase('results');
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-20"
      onClick={phase === 'form' ? onClose : undefined}
    >
      <div
        className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-slate-800 sticky top-0 bg-slate-900">
          <h2 className="text-lg font-semibold">
            {phase === 'form' && 'Add Provider'}
            {phase === 'scanning' && 'Scanning…'}
            {phase === 'results' && 'Select items to monitor'}
            {phase === 'saving' && 'Saving…'}
          </h2>
          {phase === 'form' && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white text-xl leading-none"
              aria-label="Close"
            >
              ×
            </button>
          )}
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30 text-sm text-rose-300">
              {error}
            </div>
          )}

          {phase === 'form' && (
            <form onSubmit={handleScan} className="space-y-4">
              <Field label="Provider name">
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Frantech"
                  className="input"
                />
              </Field>
              <Field label="Target URL">
                <input
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://frantech.ca/"
                  className="input"
                />
              </Field>
              <Field label="Driver type">
                <select
                  value={driverType}
                  onChange={(e) => setDriverType(e.target.value as DriverType)}
                  className="input"
                >
                  <option value="static_html">Static HTML (WHMCS)</option>
                  <option value="dynamic_dropdown">Dynamic Dropdown</option>
                  <option value="complex_spa">Complex SPA</option>
                </select>
                <p className="text-xs text-slate-400 mt-1.5">
                  {DRIVER_DESCRIPTIONS[driverType]}
                </p>
              </Field>
              <Field label="Scan interval">
                <select
                  value={intervalSec}
                  onChange={(e) => setIntervalSec(Number(e.target.value))}
                  className="input"
                >
                  {INTERVAL_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </Field>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={onClose} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Scan
                </button>
              </div>
            </form>
          )}

          {phase === 'scanning' && (
            <div className="py-10 flex flex-col items-center gap-3">
              <Spinner />
              <p className="text-sm text-slate-400">
                Opening page and looking for stockable items…
              </p>
            </div>
          )}

          {phase === 'results' && (
            <ResultsStep
              notes={notes}
              products={products}
              locations={locations}
              monitoredProducts={monitoredProducts}
              monitoredLocations={monitoredLocations}
              onToggleProduct={(id) =>
                setMonitoredProducts((prev) => toggleInSet(prev, id))
              }
              onToggleLocation={(id) =>
                setMonitoredLocations((prev) => toggleInSet(prev, id))
              }
              onCancel={onClose}
              onSave={handleSave}
            />
          )}

          {phase === 'saving' && (
            <div className="py-10 flex flex-col items-center gap-3">
              <Spinner />
              <p className="text-sm text-slate-400">Persisting selection…</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultsStep(props: {
  notes: string[];
  products: Product[];
  locations: Location[];
  monitoredProducts: Set<number>;
  monitoredLocations: Set<number>;
  onToggleProduct: (id: number) => void;
  onToggleLocation: (id: number) => void;
  onCancel: () => void;
  onSave: () => void;
}) {
  const {
    notes,
    products,
    locations,
    monitoredProducts,
    monitoredLocations,
    onToggleProduct,
    onToggleLocation,
    onCancel,
    onSave,
  } = props;

  return (
    <div className="space-y-5">
      {notes.length > 0 && (
        <div className="p-3 rounded bg-amber-500/10 border border-amber-500/30 text-sm text-amber-200 space-y-1">
          {notes.map((n, i) => (
            <p key={i}>{n}</p>
          ))}
        </div>
      )}

      <Section
        title="Products"
        empty="No products detected. Adjust the driver config and rescan later."
      >
        {products.map((p) => (
          <CheckboxRow
            key={p.id}
            checked={monitoredProducts.has(p.id)}
            onChange={() => onToggleProduct(p.id)}
            label={p.display_name}
            hint={p.key}
          />
        ))}
      </Section>

      <Section
        title="Locations"
        empty="No locations detected. New ones will be reported automatically."
      >
        {locations.map((l) => (
          <CheckboxRow
            key={l.id}
            checked={monitoredLocations.has(l.id)}
            onChange={() => onToggleLocation(l.id)}
            label={l.display_name}
            hint={l.key}
          />
        ))}
      </Section>

      <div className="flex justify-between items-center pt-2">
        <p className="text-xs text-slate-500">
          Telegram notifications only fire on Out-of-Stock → In-Stock transitions
          of monitored items.
        </p>
        <div className="flex gap-2">
          <button onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
          <button onClick={onSave} className="btn-primary">
            Save selection
          </button>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  empty,
  children,
}: {
  title: string;
  empty: string;
  children: React.ReactNode;
}) {
  const hasChildren = Boolean(
    Array.isArray(children) ? children.filter(Boolean).length : children,
  );
  return (
    <div>
      <h3 className="text-sm font-medium text-slate-300 mb-2">{title}</h3>
      {hasChildren ? (
        <div className="space-y-1.5">{children}</div>
      ) : (
        <p className="text-xs text-slate-500 italic">{empty}</p>
      )}
    </div>
  );
}

function CheckboxRow({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
  hint?: string;
}) {
  return (
    <label className="flex items-center gap-3 p-2 rounded hover:bg-slate-800/50 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-sky-500 focus:ring-sky-500"
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-100">{label}</div>
        {hint && hint !== label && (
          <div className="text-xs text-slate-500 truncate">{hint}</div>
        )}
      </div>
    </label>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-slate-300 mb-1.5">
        {label}
      </span>
      {children}
    </label>
  );
}

function Spinner() {
  return (
    <div className="w-8 h-8 border-2 border-slate-700 border-t-sky-500 rounded-full animate-spin" />
  );
}

function toggleInSet<T>(set: Set<T>, item: T): Set<T> {
  const next = new Set(set);
  if (next.has(item)) {
    next.delete(item);
  } else {
    next.add(item);
  }
  return next;
}
