import type {
  InitialScanResponse,
  Product,
  Provider,
  ProviderCreate,
  ScanResult,
  StockHistoryEntry,
  TelegramSettings,
  TelegramTestResult,
  Location,
} from './types';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8523';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`;
    try {
      const body = await resp.json();
      if (body.detail) detail += `: ${body.detail}`;
    } catch {
      /* non-JSON error */
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return null as T;
  return (await resp.json()) as T;
}

export const api = {
  listProviders: () => req<Provider[]>('/api/providers'),
  createProvider: (data: ProviderCreate) =>
    req<InitialScanResponse>('/api/providers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getProvider: (id: number) => req<Provider>(`/api/providers/${id}`),
  updateProvider: (id: number, data: Partial<ProviderCreate>) =>
    req<Provider>(`/api/providers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteProvider: (id: number) =>
    req<void>(`/api/providers/${id}`, { method: 'DELETE' }),
  listProducts: (providerId: number) =>
    req<Product[]>(`/api/providers/${providerId}/products`),
  listLocations: (providerId: number) =>
    req<Location[]>(`/api/providers/${providerId}/locations`),
  updateProduct: (providerId: number, productId: number, isMonitored: boolean) =>
    req<Product>(`/api/providers/${providerId}/products/${productId}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_monitored: isMonitored }),
    }),
  updateLocation: (providerId: number, locationId: number, isMonitored: boolean) =>
    req<Location>(`/api/providers/${providerId}/locations/${locationId}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_monitored: isMonitored }),
    }),
  scanNow: (id: number) =>
    req<ScanResult>(`/api/providers/${id}/scan`, { method: 'POST' }),
  getHistory: (id: number, limit = 50) =>
    req<StockHistoryEntry[]>(`/api/providers/${id}/history?limit=${limit}`),
  getTelegram: () => req<TelegramSettings>('/api/settings/telegram'),
  saveTelegram: (data: TelegramSettings) =>
    req<TelegramSettings>('/api/settings/telegram', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  testTelegram: (data: TelegramSettings) =>
    req<TelegramTestResult>('/api/settings/telegram/test', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
