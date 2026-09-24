// Accept only validated login responses from the current generation.
// SessionGate revalidates the persisted session after navigation.
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { advanceSessionGeneration, clearSessionMutations, getSessionGeneration, login } from "../services/api";
import { SESSION_KEY } from "../layouts/SessionGate";

interface LoginFormState {
  email: string;
  password: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  // Sin genero explicito en `useState`: se infiere `LoginFormState` igual a
  // partir del literal (mismos dos campos, mismos tipos), y
  // `tools/docker-topology.test.mjs` (gobernanza de JUP-053) localiza este
  // inicializador por texto con una expresion regular que no contempla un
  // argumento de tipo entre `useState` y `(` -- con el generico explicito,
  // ese test de gobernanza no encuentra la coincidencia y falla en CI
  // (job "OpenSpec") aunque el comportamiento sea correcto.
  const [form, setForm] = useState({
    email: "operator@example.com",
    // Contrasena inicialmente vacia (reconciliacion con develop/JUP-053,
    // externalizacion de secretos): no se precarga una credencial de
    // demostracion en el propio codigo del formulario. Las pruebas que
    // ejercitan el login deben introducirla explicitamente.
    password: ""
  });

  const mutation = useMutation({
    mutationFn: async (credentials: LoginFormState) => {
      const generation = getSessionGeneration();
      const payload = await login(credentials);
      return { payload, generation };
    },
    onSuccess: ({ payload, generation }) => {
      if (generation !== getSessionGeneration()) return;
      advanceSessionGeneration();
      queryClient.getQueryCache().clear();
      clearSessionMutations(queryClient);
      window.localStorage.removeItem("finops.activeTenant");
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
