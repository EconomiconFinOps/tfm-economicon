import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { beginCognitoLogin, completeCognitoLogin } from "../services/cognito";
import { advanceSessionGeneration, clearSessionMutations, getSessionGeneration } from "../services/api";
import { SESSION_KEY } from "../layouts/SessionGate";

export function CognitoLoginPage() {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  async function start() {
    setBusy(true); setFailed(false);
    try { window.location.assign(await beginCognitoLogin()); }
    catch { setBusy(false); setFailed(true); }
  }
  return <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
    <section className="w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-xl">
      <h1 className="font-heading text-2xl font-bold">Economicon</h1>
      <p className="my-6">Accede con tu cuenta de operador.</p>
      {failed && <p role="alert">No se pudo iniciar el acceso. Vuelve a intentarlo.</p>}
      <button className="rounded-md bg-primary px-4 py-2 text-primary-foreground" disabled={busy} onClick={() => void start()}>
        {busy ? "Abriendo acceso…" : "Iniciar sesión"}
      </button>
    </section>
  </main>;
}

export function CognitoCallbackPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [failed, setFailed] = useState(false);
  const callback = new URL(`${location.pathname}${location.search}`, window.location.origin).href;
  useEffect(() => {
    let active = true;
    const generation = getSessionGeneration();
    // Scrub the one-time code before any application navigation or rendering.
    window.history.replaceState(window.history.state, "", "/auth/callback");
    completeCognitoLogin(callback).then(session => {
      if (!active || generation !== getSessionGeneration()) return;
      advanceSessionGeneration();
      client.getQueryCache().clear(); clearSessionMutations(client);
      window.localStorage.removeItem("finops.activeTenant");
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
      navigate("/", { replace: true });
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [callback, client, navigate]);
  return <main className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
    {failed ? <section><p role="alert">No se pudo completar el acceso. Inicia sesión de nuevo.</p>
      <Link to="/login" replace>Volver al acceso</Link></section>
      : <p role="status">Comprobando el acceso…</p>}
  </main>;
}
