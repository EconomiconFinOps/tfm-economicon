import { useEffect, useRef, useState } from "react";
import { checkHealthProvider, fetchSystemHealth, getSessionGeneration, HealthDiagnosticError } from "../services/api";
import type { HealthComponent, HealthReason, SystemHealth } from "../services/contracts";

interface HealthView {
  scope: string;
  data?: SystemHealth;
  provider?: HealthComponent;
  diagnosticError: boolean;
  providerReason?: HealthReason;
  retryAfter?: number;
  loading: boolean;
  checking: boolean;
  now: number;
}

function actionKey() {
  return globalThis.crypto?.randomUUID?.() ?? `health-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

export function useSystemHealth(token: string, tenantId?: string) {
  const scope = `${getSessionGeneration()}:${token}:${tenantId ?? ""}`;
  const [view, setView] = useState<HealthView>({ scope, loading: true, checking: false, diagnosticError: false, now: Date.now() });
  const refreshRef = useRef<() => void>(() => {});
  const opening = useRef<string>();

  useEffect(() => {
    if (!token || !tenantId) return;
    const generation = getSessionGeneration();
    let disposed = false;
    let getSequence = 0;
    let checking = false;
    let polling: ReturnType<typeof setInterval> | undefined;
    const controllers = new Map<AbortController, ReturnType<typeof setTimeout>>();
    const current = () => !disposed && generation === getSessionGeneration();
    const update = (change: Partial<HealthView>) => {
      if (current()) setView((previous) => ({ ...(previous.scope === scope ? previous : { scope, loading: true, checking: false, diagnosticError: false, now: Date.now() }), ...change }));
    };
    const timed = async <T,>(seconds: number, operation: (signal: AbortSignal) => Promise<T>) => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), seconds * 1000);
      controllers.set(controller, timer);
      try { return await operation(controller.signal); }
      finally { clearTimeout(timer); controllers.delete(controller); }
    };
    const read = async () => {
      if (!current()) return;
      const sequence = ++getSequence;
      update({ loading: true });
      try {
        const data = await timed(7, (signal) => fetchSystemHealth(token, tenantId, signal));
        if (data.tenant_id !== tenantId) throw new Error("Invalid health scope");
        if (sequence === getSequence) update({ data, diagnosticError: false, loading: false, now: Date.now() });
      } catch {
        if (sequence === getSequence) update({ diagnosticError: true, loading: false, now: Date.now() });
      }
    };
    const check = async () => {
      if (!current() || checking) return;
      checking = true;
      update({ checking: true, providerReason: undefined, retryAfter: undefined });
      try {
        const provider = await timed(35, (signal) => checkHealthProvider(token, tenantId, actionKey(), signal));
        update({ provider, providerReason: provider.reason_code, now: Date.now() });
      } catch (error) {
        update({ providerReason: error instanceof HealthDiagnosticError ? error.reason : "timeout",
                 retryAfter: error instanceof HealthDiagnosticError ? error.retryAfter : undefined, now: Date.now() });
      } finally {
        checking = false;
        update({ checking: false });
      }
    };
    refreshRef.current = () => { if (!checking) { void read(); void check(); } };
    void read();
    // StrictMode cleans up its first effect synchronously. Defer the paid intent
    // until that cleanup can cancel it; re-renders never create another intent.
    void Promise.resolve().then(() => {
      if (current() && opening.current !== scope) { opening.current = scope; void check(); }
    });
    const visibility = () => {
      clearInterval(polling);
      polling = undefined;
      if (current() && document.visibilityState === "visible") {
        polling = setInterval(() => { void read(); }, 30_000);
      }
    };
    visibility();
    document.addEventListener("visibilitychange", visibility);
    return () => {
      disposed = true;
      clearInterval(polling);
      document.removeEventListener("visibilitychange", visibility);
      controllers.forEach((timer, controller) => { clearTimeout(timer); controller.abort(); });
      controllers.clear();
      refreshRef.current = () => {};
    };
  }, [scope, token, tenantId]);

  const scoped: HealthView = view.scope === scope ? view : { scope, loading: true, checking: false, diagnosticError: false, now: Date.now() };
  const observed = scoped.data?.components.find((component) => component.id === "openrouter");
  const local = scoped.provider;
  const provider = local && (!observed?.last_attempt_at || Date.parse(local.last_attempt_at ?? "") >= Date.parse(observed.last_attempt_at)) ? local : observed;
  const verified = provider?.verified_at && Date.parse(provider.verified_at) <= scoped.now ? provider.verified_at : null;
  const stale = provider?.reason_code === "stale" || Boolean(verified && Date.parse(verified) + 60_000 <= scoped.now);
  const providerStatus = scoped.checking || scoped.providerReason && scoped.providerReason !== "none" || stale || !verified ? "unknown" : provider?.status ?? "unknown";
  return { ...scoped, provider, verified, stale, providerStatus, refresh: () => refreshRef.current() };
}
