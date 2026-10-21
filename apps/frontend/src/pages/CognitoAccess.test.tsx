import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { CognitoCallbackPage, CognitoLoginPage } from "./CognitoAccess";
import { beginCognitoLogin, completeCognitoLogin } from "../services/cognito";
import { SESSION_KEY } from "../layouts/SessionGate";

vi.mock("../services/cognito", () => ({ beginCognitoLogin: vi.fn(), completeCognitoLogin: vi.fn(), usesCognito: () => true }));
afterEach(() => vi.resetAllMocks());

function show(Component: typeof CognitoCallbackPage) {
  const client = new QueryClient();
  const router = createMemoryRouter([
    { path: "/auth/callback", Component },
    { path: "/", element: <p>Inicio autenticado</p> },
    { path: "/login", element: <p>Volver a iniciar sesión</p> }
  ], { initialEntries: ["/auth/callback?code=secret-code&state=private-state"] });
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

it("offers identity-provider login without a local password form", async () => {
  vi.mocked(beginCognitoLogin).mockReturnValue(new Promise(() => {}));
  show(CognitoLoginPage);
  fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
  await waitFor(() => expect(beginCognitoLogin).toHaveBeenCalledOnce());
  expect(screen.queryByLabelText("Contraseña")).toBeNull();
});

it("persists only the verified profile and short-lived access session", async () => {
  const session = { accessToken: "access-token", expiresAt: Date.now()+900000,
    user: { id: "subject-123", email: "operator@example.com", full_name: "Operator", role: "admin" } };
  vi.mocked(completeCognitoLogin).mockResolvedValue(session);
  show(CognitoCallbackPage);
  await screen.findByText("Inicio autenticado");
  expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual(session);
  expect(window.location.search).toBe("");
});

it("shows a generic failure and retains no session or provider error details", async () => {
  vi.mocked(completeCognitoLogin).mockRejectedValue(new Error("secret-provider-details"));
  show(CognitoCallbackPage);
  expect(await screen.findByRole("alert")).not.toHaveTextContent("secret-provider-details");
  expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
});
