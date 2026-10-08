import { useEffect, useRef, useState } from "react";
import { checkHealthProvider, fetchSystemHealth, getSessionGeneration, HealthDiagnosticError } from "../services/api";
import { HEALTH_FUTURE_TOLERANCE_MS, isHealthObservationTime } from "../services/contracts";
import type { HealthComponent, HealthReason, SystemHealth } from "../services/contracts";

const PROVIDER_INTERVAL_MS = 600_000;
interface HealthView {
  scope: string;
  data?: SystemHealth;
  provider?: HealthComponent;
  diagnosticError: boolean;
  providerReason?: HealthReason;
  retryAfter?: number;
  uncertain: boolean;
  loading: boolean;
  checking: boolean;
  now: number;
}
interface Episode {
  scope: string;
  entry: string;
  opened: boolean;
  openedEntries: Set<string>;
  checking: boolean;
  nextDue?: number;
  provider?: HealthComponent;
  reason?: HealthReason;
  retryAfter?: number;
  uncertainSince?: number;
  read?: Promise<SystemHealth>;
  readOwner?: symbol;
  listeners: Set<() => void>;
}
// In-memory coordination only. Timers and requests belong to mounted consumers;
// a remount of the same navigation entry preserves its already dispatched intent.
let episode: Episode | undefined;
const refusal = (reason?: HealthReason) => reason === "busy" || reason === "cooldown" || reason === "budget_unavailable";
const attemptTime = (provider?: HealthComponent) => provider?.last_attempt_at ? Date.parse(provider.last_attempt_at) : -Infinity;
function actionKey() {
  return globalThis.crypto?.randomUUID?.() ?? ("health-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2));
}
function emptyView(scope: string): HealthView {
  return { scope, loading: true, checking: false, diagnosticError: false, uncertain: false, now: Date.now() };
}

export function useSystemHealth(token: string, tenantId?: string, panelEntryKey?: string) {
  const scope = getSessionGeneration() + ":" + token + ":" + (tenantId ?? "");
  const [view, setView] = useState<HealthView>(() => emptyView(scope));
  const refreshRef = useRef<() => void>(() => {});

  useEffect(() => {
    if (!token || !tenantId || !panelEntryKey) return;
    const generation = getSessionGeneration();
    if (!episode || episode.scope !== scope) {
      episode = { scope, entry: panelEntryKey, opened: false, openedEntries: new Set(), checking: false, listeners: new Set() };
    } else if (episode.entry !== panelEntryKey) {
      episode.entry = panelEntryKey;
      episode.opened = episode.openedEntries.has(panelEntryKey);
    }
    const record = episode;
    const owner = Symbol();
    let disposed = false;
    let polling: ReturnType<typeof setInterval> | undefined;
    let periodic: ReturnType<typeof setTimeout> | undefined;
    const controllers = new Map<AbortController, ReturnType<typeof setTimeout>>();
    const current = () => !disposed && generation === getSessionGeneration()
      && episode === record && record.entry === panelEntryKey;
    const visible = () => document.visibilityState === "visible";
    const update = (change: Partial<HealthView>) => {
      if (current()) setView((previous) => ({ ...(previous.scope === scope ? previous : emptyView(scope)), ...change }));
    };
    const timed = async <T,>(seconds: number, operation: (signal: AbortSignal) => Promise<T>) => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), seconds * 1000);
      controllers.set(controller, timer);
      try { return await operation(controller.signal); }
      finally { clearTimeout(timer); controllers.delete(controller); }
    };
    const publish = () => record.listeners.forEach((listener) => listener());
    const check = async () => {
      if (!current() || !visible()) return;
      if (record.checking) { record.opened = true; record.openedEntries.add(panelEntryKey); return; }
      // Claim synchronously before awaiting: duplicate consumers, manual clicks
      // and the periodic timer all share one dispatch and one next deadline.
      record.checking = true;
      record.opened = true;
      record.openedEntries.add(panelEntryKey);
      record.nextDue = performance.now() + PROVIDER_INTERVAL_MS;
      record.reason = undefined;
      record.retryAfter = undefined;
      const dispatchedAt = Date.now();
      publish();
      try {
        const provider = await timed(35, (signal) => checkHealthProvider(token, tenantId, actionKey(), signal));
        if (current()) {
          record.provider = provider;
          record.reason = provider.reason_code;
          record.uncertainSince = undefined;
        }
      } catch (error) {
        if (episode === record && generation === getSessionGeneration()) {
          record.reason = error instanceof HealthDiagnosticError ? error.reason : "timeout";
          record.retryAfter = error instanceof HealthDiagnosticError ? error.retryAfter : undefined;
          if (!refusal(record.reason)) record.uncertainSince = dispatchedAt;
          if (error instanceof HealthDiagnosticError && error.status === 403) {
            record.provider = undefined;
            update({ data: undefined, diagnosticError: true });
          }
        }
      } finally {
        record.checking = false;
        publish();
      }
    };
    const schedule = () => {
      clearTimeout(periodic);
      periodic = undefined;
      if (current() && visible() && !record.checking && record.opened && record.nextDue !== undefined) {
        periodic = setTimeout(() => { void check(); }, Math.max(0, record.nextDue - performance.now()));
      }
    };
    const sync = () => {
      update({ provider: record.provider, providerReason: record.reason, retryAfter: record.retryAfter,
        checking: record.checking, uncertain: record.uncertainSince !== undefined, now: Date.now() });
      schedule();
    };
    record.listeners.add(sync);
    const read = async () => {
      if (!current() || !visible()) return;
      update({ loading: true });
      const operation = record.read ?? timed(7, (signal) => fetchSystemHealth(token, tenantId, signal));
      if (!record.read) { record.read = operation; record.readOwner = owner; }
      try {
        const data = await operation;
        if (!current()) return;
        if (data.tenant_id !== tenantId) throw new Error("Invalid health scope");
        const observed = data.components.find((component) => component.id === "openrouter");
        const attempt = attemptTime(observed);
        // A passive snapshot cannot roll back a later attempt or resolve a
        // client timeout using an observation from before that dispatch.
        if (observed && attempt >= attemptTime(record.provider)
          && (record.uncertainSince === undefined || attempt >= record.uncertainSince - HEALTH_FUTURE_TOLERANCE_MS)) {
          record.provider = observed;
          if (!refusal(record.reason)) record.reason = observed.reason_code;
          record.uncertainSince = undefined;
          publish();
        }
        update({ data, diagnosticError: false, loading: false, now: Date.now() });
      } catch (error) {
        if (error instanceof HealthDiagnosticError && error.status === 403) {
          record.provider = undefined;
          update({ data: undefined });
        }
        update({ diagnosticError: true, loading: false, now: Date.now() });
      } finally {
        if (record.read === operation) { record.read = undefined; record.readOwner = undefined; }
      }
    };
    refreshRef.current = () => {
      if (current() && visible() && !record.checking) { void read(); void check(); }
    };
    const visibility = () => {
      clearInterval(polling);
      clearTimeout(periodic);
      polling = undefined;
      periodic = undefined;
      if (current() && visible()) {
        void read();
        polling = setInterval(() => { void read(); }, 30_000);
        // StrictMode cleanup cancels its first opening intent before dispatch.
        void Promise.resolve().then(() => {
          if (!current() || !visible()) return;
          if (!record.opened || (record.nextDue !== undefined && performance.now() >= record.nextDue)) void check();
          else schedule();
        });
      }
    };
    sync();
    visibility();
    document.addEventListener("visibilitychange", visibility);
    return () => {
      disposed = true;
      clearInterval(polling);
      clearTimeout(periodic);
      document.removeEventListener("visibilitychange", visibility);
      record.listeners.delete(sync);
      if (episode === record && generation !== getSessionGeneration()) episode = undefined;
      if (record.readOwner === owner) { record.read = undefined; record.readOwner = undefined; }
      controllers.forEach((timer, controller) => { clearTimeout(timer); controller.abort(); });
      controllers.clear();
      refreshRef.current = () => {};
    };
  }, [scope, token, tenantId, panelEntryKey]);

  const scoped = view.scope === scope ? view : emptyView(scope);
  const observed = scoped.data?.components.find((component) => component.id === "openrouter");
  const local = scoped.provider;
  const provider = local && (!observed || attemptTime(local) >= attemptTime(observed)) ? local : observed;
  const verified = isHealthObservationTime(provider?.verified_at, scoped.now) ? provider.verified_at : null;
  const stale = provider?.reason_code === "stale";
  const invalidTime = provider && (!isHealthObservationTime(provider.checked_at, scoped.now)
    || (provider.verified_at != null && !verified));
  const providerStatus = scoped.uncertain || stale || invalidTime ? "unknown" : provider?.status ?? "unknown";
  return { ...scoped, provider, verified, stale, providerStatus, refresh: () => refreshRef.current() };
}
