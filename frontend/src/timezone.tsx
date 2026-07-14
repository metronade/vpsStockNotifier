import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api } from './api';

const DEFAULT_TIMEZONE = 'Europe/Berlin';

const TimezoneContext = createContext<string>(DEFAULT_TIMEZONE);

export function TimezoneProvider({ children }: { children: ReactNode }) {
  const [tz, setTz] = useState<string>(DEFAULT_TIMEZONE);
  useEffect(() => {
    let alive = true;
    api
      .getDisplaySettings()
      .then((s) => {
        if (alive) setTz(s.timezone);
      })
      .catch(() => {
        // keep default on failure
      });
    return () => {
      alive = false;
    };
  }, []);
  return (
    <TimezoneContext.Provider value={tz}>{children}</TimezoneContext.Provider>
  );
}

export function useTimezone(): string {
  return useContext(TimezoneContext);
}

export function useFormatTime() {
  const tz = useTimezone();
  return useMemo(
    () =>
      (iso: string | null): string => {
        if (!iso) return 'never';
        return new Date(iso).toLocaleString('de-DE', { timeZone: tz });
      },
    [tz],
  );
}

export function formatAbsolute(iso: string | null, tz: string): string {
  if (!iso) return 'never';
  return new Date(iso).toLocaleString('de-DE', { timeZone: tz });
}
