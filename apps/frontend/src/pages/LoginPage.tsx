// Accept only validated login responses from the current generation.
// SessionGate revalidates the persisted session after navigation.
import logoPrimary from "@/assets/brand/economicon-primary.png";
import logoInverse from "@/assets/brand/economicon-inverse.png";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router";
import { advanceSessionGeneration, clearSessionMutations, getSessionGeneration, login } from "../services/api";
import { SESSION_KEY } from "../layouts/SessionGate";

interface LoginFormState {
  email: string;
  password: string;
}

// Forma minima y defensiva del estado de navegacion que `SessionGate` deja al
// redirigir por una invalidacion con motivo "expired" (grupo 3, ya
// commiteado). No se exhaustiva a proposito: solo el propio `SessionGate`
// escribe este estado, no hay otros emisores que validar aqui.
function hasSessionExpiredFlag(state: unknown): boolean {
  return (state as { sessionExpired?: boolean } | null)?.sessionExpired === true;
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  // Inicializador perezoso (tarea 4.6): lee `location.state` una sola vez, en
  // el primer render, en vez de en un efecto -- si se hiciera en un efecto
  // habria un primer render donde el aviso todavia no se muestra (parpadeo).
  // El propio estado ya desacopla esta lectura del historial de navegacion:
  // una vez copiada aqui, sustituir la entrada de historial (mas abajo) no
  // afecta a este valor.
  const [sessionExpired] = useState(() => hasSessionExpiredFlag(location.state));

  // Tarea 4.4a: en cuanto se lee la marca, se sustituye la entrada de
  // historial actual sin estado -- para que una recarga de /login no vuelva
  // a mostrar el aviso (la marca no persiste en ningun storage, solo en el
  // estado de navegacion de esta unica entrada). El guard de entrada
  // (`hasSessionExpiredFlag`) es lo que evita llamar a `navigate` en cada
  // montaje/render que no lo necesite: tras el primer `replace`,
  // `location.state` pasa a `null` y el propio guard corta el efecto sin
  // volver a navegar, aunque `location`/`navigate` reaparezcan en las
  // dependencias.
  //
  // Se listan `location` y `navigate` de forma exhaustiva (en vez de `[]`
  // con un comentario de exclusion) porque, en esta version de
  // `eslint-plugin-react-hooks` (4.6.2) sobre ESLint 9, generar el aviso de
  // "falta esta dependencia" para poder silenciarlo con
  // `eslint-disable-next-line` hace crashear el linter entero
  // (`context.getSource is not a function`, incompatibilidad de la API de
  // sugerencias de esa version del plugin con ESLint 9) -- confirmado
  // ejecutando `pnpm lint` con el `eslint-disable` puesto: el proceso
  // fallaba igual porque el crash ocurre al CALCULAR el aviso, antes de que
  // el comentario de desactivacion pueda suprimirlo. Listar las
  // dependencias reales evita que el linter necesite generar ese aviso.
  useEffect(() => {
    if (!hasSessionExpiredFlag(location.state)) return;
    navigate(location.pathname, { replace: true, state: null });
  }, [location, navigate]);
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
    <div className="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
      <section className="w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-xl">
        <div className="flex items-center gap-3">
          <img src={logoPrimary} alt="" className="size-12 object-contain dark:hidden" />
          <img src={logoInverse} alt="" className="hidden size-12 object-contain dark:block" />
          <span className="font-heading text-2xl font-bold text-highlight">Economicon</span>
        </div>
        <p className="mt-6 text-sm uppercase tracking-wide text-muted-foreground">Operator login</p>
        <h1 className="mt-2 text-xl font-bold text-foreground">Access the tenant control tower</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This demo build uses the seeded operator account so the team can validate
          auth, tenant isolation and assistant flows end-to-end.
        </p>

        <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="login-email">
              Email
            </label>
            <input
              id="login-email"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight"
              type="email"
              value={form.email}
              onChange={(event) =>
                setForm((current) => ({ ...current, email: event.target.value }))
              }
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted-foreground" htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              className="rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight"
              type="password"
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
            />
          </div>

          {sessionExpired && mutation.isIdle ? (
            // Tarea 4.3: se oculta con la propia condicion de la mutacion
            // (`isIdle`) en vez de un estado adicional que la duplicaria --
            // en cuanto el operador reintenta el acceso, la mutacion deja de
            // estar idle y este aviso desaparece sin ningun efecto extra.
            <p className="text-sm text-warning" role="status">
              Your session has expired. Sign in again to continue.
            </p>
          ) : null}

          {mutation.error ? (
            <p className="text-sm text-danger">{mutation.error.message}</p>
          ) : null}

          <button
            className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
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
