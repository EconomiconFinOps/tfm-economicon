// LoginPage: en la nueva arquitectura de rutas (JUP-095, grupo 6, sub-ronda
// b -- ver Addendum de design.md) vive fuera del arbol protegido por
// `SessionGate`, como ruta hermana de "/". Ya no recibe el callback
// `onLogin` desde `App.jsx`: reproduce ella misma, en el `onSuccess` de su
// mutacion, lo que hoy hace `App.jsx.handleLogin` (App.jsx:74-81) --
// construir `{ accessToken, user }` y persistirlo en localStorage -- y
// navega a "/" con `useNavigate()` de react-router. La logica de formulario
// (estado, submit, mensaje de error, estado pendiente del boton) se conserva
// tal cual del origen; solo cambian el tipado y la presentacion (Tailwind).
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { login } from "../services/api";
import { SESSION_KEY } from "../layouts/SessionGate";

// `services/api.js` no esta tipado todavia (checkJs: false): la frontera
// JS->TS llega laxa, igual que en SessionGate.tsx (ver comentario de
// `SessionUser`/`Session` alli). Tipamos explicitamente lo que necesitamos
// de la respuesta de `/auth/login` en vez de propagar `any`.
interface LoginFormState {
  email: string;
  password: string;
}

interface LoginResponseUser {
  full_name?: string;
  email?: string;
  id?: string;
  [key: string]: unknown;
}

interface LoginResponse {
  access_token: string;
  user: LoginResponseUser;
}

export function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<LoginFormState>({
    email: "operator@example.com",
    password: "secret"
  });

  const mutation = useMutation({
    mutationFn: (payload: LoginFormState) => login(payload),
    onSuccess: (payload: LoginResponse) => {
      // Verbatim de App.jsx.handleLogin (App.jsx:74-81): mismo shape de
      // sesion, misma clave de localStorage. Aqui no hay estado de sesion
      // que actualizar (eso vive en SessionGate, que lee localStorage de
      // forma perezosa al montar) -- basta con persistir y navegar.
      const nextSession = {
        accessToken: payload.access_token,
        user: payload.user
      };
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      navigate("/", { replace: true });
    }
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate(form);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f1419] px-4 text-white">
      <section className="w-full max-w-md rounded-lg border border-[#2d3748] bg-[#1a1f2e] p-8 shadow-xl">
        <p className="text-sm uppercase tracking-wide text-slate-400">Operator login</p>
        <h1 className="mt-2 text-xl font-bold text-white">Access the tenant control tower</h1>
        <p className="mt-2 text-sm text-slate-400">
          This demo build uses the seeded operator account so the team can validate
          auth, tenant isolation and assistant flows end-to-end.
        </p>

        <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-slate-400" htmlFor="login-email">
              Email
            </label>
            <input
              id="login-email"
              className="rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2 text-sm text-white outline-none focus:border-[#0078d4]"
              type="email"
              value={form.email}
              onChange={(event) =>
                setForm((current) => ({ ...current, email: event.target.value }))
              }
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-slate-400" htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              className="rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2 text-sm text-white outline-none focus:border-[#0078d4]"
              type="password"
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
            />
          </div>

          {mutation.error ? (
            <p className="text-sm text-red-400">{mutation.error.message}</p>
          ) : null}

          <button
            className="mt-2 rounded-md bg-[#0078d4] px-4 py-2 text-sm font-medium text-white hover:bg-[#0078d4]/80 disabled:opacity-60"
            type="submit"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </div>
  );
}
