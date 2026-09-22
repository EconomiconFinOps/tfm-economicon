// Remediacion de mutation testing (JUP-097, RF-090-003, tarea 3.5) para
// `SessionGate.tsx` (mutate acotado al archivo completo, ver
// .claude/harness/stryker.conf.mjs). `SessionGate.test.tsx` y
// `SessionGate.validation.test.tsx` (ya commiteados, bloqueados por el hook
// del harness) solo prueban un caso "todo valido" y un caso "estructura
// invalida con dos campos rotos a la vez" -- eso deja sin matar una gran
// cantidad de mutantes de logica booleana en `isSession` (cada termino de
// la cadena de `||`/`&&` necesita su propio caso donde SOLO ese termino
// cambia, MC/DC basico), mas otros supervivientes puntuales fuera de esa
// funcion. Este archivo anade, sin duplicar la cobertura existente, los
// casos que faltan.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (mismo patron que los otros archivos de
// este directorio).
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useOutletContext } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { SessionGate, SESSION_KEY } from "./SessionGate";

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

function renderRouter(router: ReturnType<typeof createMemoryRouter>) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

// Helper compartido por los casos de sesion invalida: monta SessionGate con
// el valor crudo indicado bajo SESSION_KEY, confirma que redirige a /login,
// que nunca llama a la red (isSession debe rechazar ANTES de disparar
// cualquier query) y que la clave invalida se limpia -- mismo criterio que
// SessionGate.validation.test.tsx.
async function expectSessionRejected(rawValue: string) {
  window.localStorage.setItem(SESSION_KEY, rawValue);

  const fetchSpy = vi.fn();
  vi.stubGlobal("fetch", fetchSpy);

  const router = createMemoryRouter(
    [
      { path: "/login", Component: () => <p>Pantalla de acceso</p> },
      { path: "/", Component: SessionGate }
    ],
    { initialEntries: ["/"] }
  );

  renderRouter(router);

  expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
  expect(fetchSpy).not.toHaveBeenCalled();
  expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
}

describe("isSession: estructura externa (accessToken/user), un termino invalido a la vez", () => {
  // MC/DC del `if` compuesto de `isSession` (SessionGate.tsx:39-45): cada
  // caso deja TODOS los demas terminos en su valor "valido" y rompe solo
  // uno, para que un mutante que fuerce ese termino a `true`/`false` o
  // cambie `||` por `&&` en esa posicion sea el unico que puede sobrevivir
  // -- y no lo hace, porque el resultado observable (redirigir o no) cambia.

  it("rechaza un valor parseado que no es un objeto (termino 'typeof value !== object')", async () => {
    // JSON.parse('"solo-texto"') da un string, no un objeto: `typeof !==
    // "object"` es el primer termino en dispararse.
    await expectSessionRejected(JSON.stringify("solo-texto"));
  });

  it("rechaza un valor null (termino 'value === null', el unico que distingue null de otros objetos)", async () => {
    // `typeof null === "object"` en JS: el primer termino ("typeof !==
    // object") es falso para null, asi que solo el segundo termino
    // ("value === null") puede rechazarlo. Sin este caso, un mutante que
    // fuerce ese termino a `false` sobrevive (null pasaria como sesion).
    await expectSessionRejected("null");
  });

  it("rechaza un accessToken que no es texto (termino 'typeof accessToken !== string')", async () => {
    // La clave existe (no dispara el termino anterior, "!('accessToken' in
    // value)"), pero su tipo es numero: solo el termino de tipo lo detecta.
    await expectSessionRejected(
      JSON.stringify({
        accessToken: 12345,
        user: { id: "u1", email: "a@example.com", full_name: "Ada", role: "operator" }
      })
    );
  });

  it("rechaza una sesion sin la clave 'user' (termino '!(\"user\" in value)')", async () => {
    // accessToken valido, pero la clave "user" no existe en absoluto --
    // distinto del caso ya cubierto por SessionGate.validation.test.tsx
    // (que tiene un "user" parcial, no ausente).
    await expectSessionRejected(JSON.stringify({ accessToken: "tok-1" }));
  });

  it("rechaza un 'user' que no es un objeto (termino 'typeof user !== object')", async () => {
    await expectSessionRejected(JSON.stringify({ accessToken: "tok-1", user: "no-es-un-objeto" }));
  });

  it("rechaza un 'user' que es null (termino 'user === null')", async () => {
    // Igual que con `value === null`: `typeof null === "object"` es cierto,
    // asi que solo el ultimo termino de la cadena distingue este caso.
    await expectSessionRejected(JSON.stringify({ accessToken: "tok-1", user: null }));
  });
});

describe("isSession: campos de 'user' (id/email/full_name/role), un termino invalido a la vez", () => {
  // MC/DC de la cadena de `&&` en el `return` de `isSession`
  // (SessionGate.tsx:46-49): cada caso deja el resto de campos validos y
  // rompe solo uno -- por presencia (falta la clave) o por tipo (la clave
  // existe pero no es texto). SessionGate.validation.test.tsx ya cubre un
  // "user" con DOS campos ausentes a la vez (id y role), lo que solo llega a
  // ejercitar el primer termino de la cadena (cortocircuito): el resto de
  // mutantes de esta cadena sigue vivo sin estos casos.

  function userMissing(field: "id" | "email" | "full_name" | "role") {
    const user: Record<string, string> = {
      id: "u1",
      email: "ada@example.com",
      full_name: "Ada Lovelace",
      role: "operator"
    };
    delete user[field];
    return user;
  }

  function userWrongType(field: "id" | "email" | "full_name" | "role") {
    const user: Record<string, unknown> = {
      id: "u1",
      email: "ada@example.com",
      full_name: "Ada Lovelace",
      role: "operator"
    };
    user[field] = 42; // presente, pero no es texto
    return user;
  }

  it("rechaza un 'user' sin 'email' (resto de campos validos)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userMissing("email") })
    );
  });

  it("rechaza un 'user' sin 'full_name' (resto de campos validos)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userMissing("full_name") })
    );
  });

  it("rechaza un 'user' sin 'role' (resto de campos validos)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userMissing("role") })
    );
  });

  it("rechaza un 'user' con 'id' de tipo incorrecto (presente, pero no texto)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userWrongType("id") })
    );
  });

  it("rechaza un 'user' con 'email' de tipo incorrecto (presente, pero no texto)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userWrongType("email") })
    );
  });

  it("rechaza un 'user' con 'full_name' de tipo incorrecto (presente, pero no texto)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userWrongType("full_name") })
    );
  });

  it("rechaza un 'user' con 'role' de tipo incorrecto (presente, pero no texto)", async () => {
    await expectSessionRejected(
      JSON.stringify({ accessToken: "tok-1", user: userWrongType("role") })
    );
  });
});

describe("loadStoredSession: sin clave persistida, no toca localStorage.removeItem", () => {
  it("no invoca removeItem cuando no hay ninguna sesion guardada", async () => {
    // Sin esta espia, el mutante que convierte `if (!value) { return null; }`
    // en `if (!value) {}` (SessionGate.tsx:73) sobrevive: al no cortar antes,
    // la ejecucion cae en `JSON.parse(null)` -- que en JS interpreta `null`
    // como el texto "null" y devuelve el valor `null` (JSON valido), asi que
    // el resultado final (`session = null`, redirigir a /login) es el mismo
    // que el original. Lo que SI cambia de forma observable es que el
        // mutante, al no cortar antes, llega a llamar `removeItem(SESSION_KEY)`
    // sin necesidad (no habia nada que borrar) -- efecto secundario que este
    // test detecta.
    window.localStorage.clear();
    const removeItemSpy = vi.spyOn(window.localStorage, "removeItem");

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        { path: "/", Component: SessionGate }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
    expect(removeItemSpy).not.toHaveBeenCalledWith(SESSION_KEY);
  });
});

describe("activeTenantId: valor por defecto cuando no hay TENANT_KEY persistida", () => {
  it("expone activeTenantId como cadena vacia, no un valor arbitrario, cuando no hay tenants ni clave guardada", async () => {
    // Sin sesion no se llega a exponer contexto (redirige a /login), asi que
    // para observar el valor por defecto de `activeTenantId`
    // (SessionGate.tsx:94, `window.localStorage.getItem(TENANT_KEY) || ""`)
    // hace falta una sesion valida cuyo bootstrap de tenants resuelva una
    // coleccion VACIA: el efecto de auto-seleccion corta antes de tocar
    // `activeTenantId` (`if (tenants.length === 0) { return; }`), asi que el
    // valor que llega al contexto es el inicial sin modificar. Un mutante
    // que cambie el fallback "" por otro texto arbitrario es indetectable
    // por cualquier otro test porque nunca se compara contra un tenant real
    // -- este test lo expone leyendolo directamente del Outlet context.
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: "tok-1",
        user: { id: "u1", email: "ada@example.com", full_name: "Ada Lovelace", role: "operator" }
      })
    );

    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/tenants")) {
          return { ok: true, json: () => Promise.resolve({ items: [] }) };
        }
        if (href.includes("/me")) {
          return {
            ok: true,
            json: () =>
              Promise.resolve({ id: "u1", email: "ada@example.com", full_name: "Ada Lovelace", role: "operator" })
          };
        }
        throw new Error(`URL inesperada en el test: ${href}`);
      })
    );

    function ChildProbe() {
      const ctx = useOutletContext<{ activeTenantId: string }>();
      return <p>activeTenantId: &quot;{ctx.activeTenantId}&quot;</p>;
    }

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        { path: "/", Component: SessionGate, children: [{ index: true, Component: ChildProbe }] }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    await waitFor(() => {
      expect(screen.getByText('activeTenantId: ""')).toBeInTheDocument();
    });
  });
});

describe("tenants: coleccion vacia por defecto cuando el backend devuelve una respuesta sin 'items'", () => {
  it("expone una lista de tenants vacia (no un valor centinela) cuando /tenants responde sin la clave 'items'", async () => {
    // Ejercita el fallback `tenantsQuery.data?.items ?? []`
    // (SessionGate.tsx:249, tambien usado en la seleccion de `activeTenant`,
    // linea 154): en el camino feliz normal `data` siempre trae `items`, asi
    // que ese `?? []` nunca se alcanza con datos reales. Un backend que
        // responda con un cuerpo sin "items" (contrato roto, pero `response.ok`)
    // es el unico camino que lo alcanza de verdad -- y expone la diferencia
    // entre "[]" y un valor centinela de forma observable via el contexto.
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: "tok-1",
        user: { id: "u1", email: "ada@example.com", full_name: "Ada Lovelace", role: "operator" }
      })
    );

    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/tenants")) {
          // Respuesta ok pero sin la clave "items": contrato roto.
          return { ok: true, json: () => Promise.resolve({}) };
        }
        if (href.includes("/me")) {
          return {
            ok: true,
            json: () =>
              Promise.resolve({ id: "u1", email: "ada@example.com", full_name: "Ada Lovelace", role: "operator" })
          };
        }
        throw new Error(`URL inesperada en el test: ${href}`);
      })
    );

    function ChildProbe() {
      const ctx = useOutletContext<{ tenants: unknown[] }>();
      return <p>tenants: {JSON.stringify(ctx.tenants)}</p>;
    }

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        { path: "/", Component: SessionGate, children: [{ index: true, Component: ChildProbe }] }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    await waitFor(() => {
      expect(screen.getByText("tenants: []")).toBeInTheDocument();
    });
  });
});

describe("handleLogout: limpia tambien la clave de tenant activo", () => {
  it("elimina TENANT_KEY de localStorage al cerrar sesion tras un rechazo de /me", async () => {
    // `SessionGate.profile.test.tsx` ya confirma que SESSION_KEY se limpia
    // tras un rechazo de /me, pero no que TENANT_KEY tambien se borre
    // (SessionGate.tsx:184, dentro de `handleLogout`). Sin esta asercion, un
    // mutante que elimine esa llamada a `removeItem` sobrevive: el resto del
    // comportamiento observable (redirigir a /login, limpiar SESSION_KEY) es
    // identico con o sin ella.
    window.localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        accessToken: "tok-muerto",
        user: { id: "u1", email: "ada@example.com", full_name: "Ada Lovelace", role: "operator" }
      })
    );
    window.localStorage.setItem("finops.activeTenant", "t1");

    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL | Request) => {
        const href = String(url);
        if (href.includes("/tenants")) {
          return { ok: true, json: () => Promise.resolve({ items: [{ id: "t1", name: "Acme", slug: "acme", plan: "pro" }] }) };
        }
        if (href.includes("/me")) {
          return { ok: false, status: 401, text: () => Promise.resolve("Invalid access token.") };
        }
        throw new Error(`URL inesperada en el test: ${href}`);
      })
    );

    const router = createMemoryRouter(
      [
        { path: "/login", Component: () => <p>Pantalla de acceso</p> },
        { path: "/", Component: SessionGate }
      ],
      { initialEntries: ["/"] }
    );

    renderRouter(router);

    expect(await screen.findByText("Pantalla de acceso")).toBeInTheDocument();
    expect(window.localStorage.getItem("finops.activeTenant")).toBeNull();
  });
});
