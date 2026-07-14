export type DriverType = 'static_html' | 'dynamic_dropdown' | 'complex_spa';
export type ScanStatus = 'pending' | 'ok' | 'error';
export type StockState = 'in_stock' | 'out_of_stock' | 'unknown';
export type EventType = 'state_change' | 'new_location' | 'scan_error';

export interface Provider {
  id: number;
  name: string;
  url: string;
  driver_type: DriverType;
  scan_interval_seconds: number;
  is_active: boolean;
  config_json: Record<string, unknown>;
  last_scan_at: string | null;
  last_scan_status: ScanStatus | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  provider_id: number;
  location_id: number | null;
  key: string;
  display_name: string;
  is_monitored: boolean;
  last_state: StockState;
  last_count: number | null;
}

export interface Location {
  id: number;
  provider_id: number;
  key: string;
  display_name: string;
  is_monitored: boolean;
  first_seen_at: string;
  last_seen_at: string | null;
}

export interface DiscoveredItem {
  key: string;
  display_name: string;
  kind: 'product' | 'location';
  current_state: StockState | null;
}

export interface InitialScanResponse {
  provider: Provider;
  discovered_products: DiscoveredItem[];
  discovered_locations: DiscoveredItem[];
  notes: string[];
}

export interface StockHistoryEntry {
  id: number;
  provider_id: number;
  product_id: number | null;
  location_id: number | null;
  event_type: EventType;
  previous_state: string | null;
  new_state: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface TelegramSettings {
  bot_token: string;
  chat_id: string;
}

export interface ProviderCreate {
  name: string;
  url: string;
  driver_type: DriverType;
  scan_interval_seconds: number;
  is_active?: boolean;
  config_json?: Record<string, unknown>;
}

export interface ScanResult {
  status: 'ok' | 'error';
  error?: string;
  state_changes: number;
  new_locations?: number;
}

export interface TelegramTestResult {
  ok: boolean;
  error?: string;
}
