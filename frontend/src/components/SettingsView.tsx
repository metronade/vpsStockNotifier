import { useEffect, useState } from 'react';
import { api } from '../api';
import type { TelegramSettings, TelegramTestResult } from '../types';

export function SettingsView() {
  const [settings, setSettings] = useState<TelegramSettings>({
    bot_token: '',
    chat_id: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TelegramTestResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api
      .getTelegram()
      .then(setSettings)
      .catch((exc) => setMessage(exc instanceof Error ? exc.message : String(exc)))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await api.saveTelegram(settings);
      setMessage('Saved.');
    } catch (exc) {
      setMessage(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testTelegram(settings);
      setTestResult(result);
    } catch (exc) {
      setTestResult({
        ok: false,
        error: exc instanceof Error ? exc.message : String(exc),
      });
    } finally {
      setTesting(false);
    }
  }

  if (loading) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-semibold mb-1">Telegram Settings</h2>
      <p className="text-sm text-slate-400 mb-6">
        Configure the bot that delivers stock-change notifications.
      </p>

      <form onSubmit={handleSave} className="space-y-4">
        <label className="block">
          <span className="block text-sm font-medium text-slate-300 mb-1.5">
            Bot Token
          </span>
          <input
            type="password"
            value={settings.bot_token}
            onChange={(e) =>
              setSettings({ ...settings, bot_token: e.target.value })
            }
            placeholder="123456:ABC-DEF..."
            className="input"
            autoComplete="off"
          />
          <span className="block text-xs text-slate-500 mt-1">
            Create a bot via{' '}
            <a
              href="https://t.me/BotFather"
              target="_blank"
              rel="noreferrer"
              className="text-sky-400 hover:underline"
            >
              @BotFather
            </a>{' '}
            to get a token.
          </span>
        </label>

        <label className="block">
          <span className="block text-sm font-medium text-slate-300 mb-1.5">
            Chat ID
          </span>
          <input
            type="text"
            value={settings.chat_id}
            onChange={(e) =>
              setSettings({ ...settings, chat_id: e.target.value })
            }
            placeholder="-1001234567890 or @channelname"
            className="input"
            autoComplete="off"
          />
          <span className="block text-xs text-slate-500 mt-1">
            Use a numeric ID for private chats/channels. Tip: add{' '}
            <a
              href="https://t.me/userinfobot"
              target="_blank"
              rel="noreferrer"
              className="text-sky-400 hover:underline"
            >
              @userinfobot
            </a>{' '}
            to look up IDs.
          </span>
        </label>

        {message && (
          <div className="p-3 rounded bg-slate-800/60 border border-slate-700 text-sm">
            {message}
          </div>
        )}

        {testResult && (
          <div
            className={`p-3 rounded border text-sm ${
              testResult.ok
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}
          >
            {testResult.ok
              ? 'Test message delivered.'
              : `Test failed: ${testResult.error ?? 'unknown error'}`}
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="btn-secondary"
          >
            {testing ? 'Sending…' : 'Send test message'}
          </button>
        </div>
      </form>
    </div>
  );
}
