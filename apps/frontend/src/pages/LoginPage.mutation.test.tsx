// Remediacion de mutacion (JUP-095, grupo 6, sub-ronda b) sobre
// `LoginPage.tsx`. Stryker reporto 5 mutantes supervivientes que
// `LoginPage.test.tsx` (ya commiteado) no mata porque nunca inspecciona el
// cuerpo exacto que se envia a `fetch` ni escribe en los campos del
// formulario:
//   - LoginPage.tsx:39-41 -- los valores por defecto del estado
//     (`email: "operator@example.com"`, `password: "secret"`) pueden mutar a
//     "" o a un objeto vacio sin que ningun test lo note.
//   - LoginPage.tsx:85 y LoginPage.tsx:100 -- los `onChange` de los campos
//     email/password pueden mutar a funciones vacias sin que ningun test lo
//     note, porque ningun test escribe en los campos.
//
// Este archivo agrega los dos casos que faltan; no toca `LoginPage.test.tsx`
// (bloqueado por el hook) ni repite su cobertura de navegacion/persistencia.
//
// Importamos describe/it/expect/vi explicitos: el proyecto no usa
// `globals: true` en vite.config.ts (mismo patron que LoginPage.test.tsx).
import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { LoginPage } from "./LoginPage";

// Mismo patron de limpieza que LoginPage.test.tsx / SessionGate.test.tsx:
// cada test deja su propio estado de localStorage/fetch, para que el orden
// de ejecucion no contamine otros archivos de test.
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

// Instala un mock de `fetch` que resuelve con un payload de sesion valido
// (para que `onSuccess` no reviente) y devuelve el spy para inspeccionar los
// argumentos con los que se invoco.
function stubFetch() {
  const fetchSpy = vi.fn().mockResolvedValue({
    ok: true,
    json: () =>
      Promise.resolve({
        access_token: "tok-abc",
        user: { full_name: "Ada Lovelace", email: "ada@example.com" }
      })
  });
  vi.stubGlobal("fetch", fetchSpy);
  return fetchSpy;
}

function renderLoginPage() {
  const router = createMemoryRouter(
    [
      { path: "/login", Component: LoginPage },
      { path: "/", Component: () => <p>Area protegida</p> }
    ],
    { initialEntries: ["/login"] }
  );
  renderRouter(router);
}

describe("LoginPage - remediacion de mutacion", () => {
  it("envia el body con los valores por defecto del formulario sin tocar los campos", async () => {
    // Mata los 3 mutantes de LoginPage.tsx:39-41: si el estado inicial
    // mutara a "" o a un objeto vacio, el body enviado a fetch ya no seria
    // { email: "operator@example.com", password: "secret" } y esta
    // asercion fallaria.
    const fetchSpy = stubFetch();

    renderLoginPage();

    // Se envia el formulario tal cual, sin fireEvent.change: el test debe
    // observar los valores por defecto, no unos escritos por el propio test.
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    // `mutation.mutate` invoca la mutationFn en un microtask interno de
    // react-query: se espera con waitFor a que fetch quede registrado (mismo
    // patron de espera que usa LoginPage.test.tsx para la navegacion).
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const [, requestInit] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(requestInit.body as string)).toEqual({
      email: "operator@example.com",
      password: "secret"
    });
  });

  it("envia el body con los valores escritos por el usuario en email y password", async () => {
    // Mata los mutantes de LoginPage.tsx:85 y LoginPage.tsx:100: si alguno
    // de los `onChange` mutara a una funcion vacia, el estado del formulario
    // no se actualizaria y el body enviado seguiria siendo el de los
    // valores por defecto en vez de los nuevos.
    const fetchSpy = stubFetch();

    renderLoginPage();

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "nueva@example.com" }
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "otra-clave" }
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
    const [, requestInit] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(requestInit.body as string)).toEqual({
      email: "nueva@example.com",
      password: "otra-clave"
    });
  });
});
