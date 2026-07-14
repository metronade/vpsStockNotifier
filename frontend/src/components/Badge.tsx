import type { DriverType, ScanStatus, StockState } from '../types';

const STATE_LABELS: Record<StockState, string> = {
  in_stock: 'In Stock',
  out_of_stock: 'Out of Stock',
  unknown: 'Unknown',
};

const STATE_STYLES: Record<StockState, string> = {
  in_stock: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  out_of_stock: 'bg-rose-500/15 text-rose-300 ring-rose-500/30',
  unknown: 'bg-slate-500/15 text-slate-300 ring-slate-500/30',
};

export function StockBadge({ state }: { state: StockState }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs ring-1 ${STATE_STYLES[state]}`}
    >
      {STATE_LABELS[state]}
    </span>
  );
}

const DRIVER_LABELS: Record<DriverType, string> = {
  static_html: 'Static HTML',
  dynamic_dropdown: 'Dropdown',
  complex_spa: 'SPA',
};

const DRIVER_STYLES: Record<DriverType, string> = {
  static_html: 'bg-sky-500/15 text-sky-300 ring-sky-500/30',
  dynamic_dropdown: 'bg-violet-500/15 text-violet-300 ring-violet-500/30',
  complex_spa: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
};

export function DriverBadge({ type }: { type: DriverType }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs ring-1 ${DRIVER_STYLES[type]}`}
    >
      {DRIVER_LABELS[type]}
    </span>
  );
}

export function ScanStatusDot({ status }: { status: ScanStatus | null }) {
  const color =
    status === 'ok'
      ? 'bg-emerald-400'
      : status === 'error'
      ? 'bg-rose-400'
      : 'bg-slate-500';
  const title =
    status === 'ok'
      ? 'Last scan OK'
      : status === 'error'
      ? 'Last scan failed'
      : 'Never scanned';
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${color}`}
      title={title}
    />
  );
}
