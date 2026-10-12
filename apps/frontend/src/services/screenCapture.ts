export type ScreenRoute = "/" | "/overview-legacy" | "/operational" | "/cuts" | "/anomalies" | "/recommendations" | "/ingest" | "/assistant" | "/ownership" | "/system-health";
export interface ScreenCapture {
  schema_version: "2";
  screen_version: string;
  route: ScreenRoute;
  tab_id: string;
  source: "loaded-screen" | "loading" | "error" | "no-adapter" | "refresh_pending";
  identity: { tenant_id: string; user_id: string };
  captured_at: string;
  selection: Record<string, unknown>;
  datasets: Record<string, unknown>[];
}
const routes: readonly string[] = ["/", "/overview-legacy", "/operational", "/cuts", "/anomalies", "/recommendations", "/ingest", "/assistant", "/ownership", "/system-health"];
/** Per authenticated workspace. Only receive/change handlers prepare data. */
export class PreparedScreen {
  readonly tabId = crypto.randomUUID();
  private prepared: { route: string; bytes: string; size: number } | null = null;
  private listeners = new Set<() => void>();
  private revision = 0;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  snapshot = () => this.revision;
  constructor(readonly tenantId: string, readonly userId: string) {}
  prepare(route: string, data?: Pick<ScreenCapture, "source" | "selection" | "datasets">) {
    if (!routes.includes(route)) { this.prepared = null; return; }
    const value: ScreenCapture = {
      schema_version: "2", screen_version: crypto.randomUUID(), route: route as ScreenRoute,
      tab_id: this.tabId, identity: { tenant_id: this.tenantId, user_id: this.userId },
      captured_at: new Date().toISOString(), source: data?.source ?? "no-adapter",
      selection: data?.selection ?? {}, datasets: data?.datasets ?? []
    };
    const bytes = JSON.stringify(value);
    this.prepared = { route, bytes, size: new TextEncoder().encode(bytes).length };
    this.revision++;
    for (const listener of this.listeners) listener();
  }
  ensureRoute(route: string) { if (this.prepared?.route !== route) this.prepare(route); }
  ready(route: string) { return this.prepared?.route === route && this.prepared.size <= 1048576; }
  freeze(route: string): ScreenCapture {
    if (!this.prepared || this.prepared.route !== route) throw new Error("screen_not_ready");
    if (this.prepared.size > 1048576) throw new Error("screen_limit");
    return JSON.parse(this.prepared.bytes) as ScreenCapture;
  }
  clear() { this.prepared = null; }
}
