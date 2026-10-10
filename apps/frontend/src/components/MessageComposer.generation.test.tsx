import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";
import { MessageComposer } from "./MessageComposer";
import { sendConversationMessage } from "../services/api";

vi.mock("../services/api", () => ({ sendConversationMessage: vi.fn() }));
afterEach(() => vi.clearAllMocks());

it("keeps the draft after a provider error, announces pending and permits retry", async () => {
  let reject!: (reason: Error) => void;
  vi.mocked(sendConversationMessage).mockImplementationOnce(() => new Promise((_, fail) => { reject = fail; }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(<QueryClientProvider client={client}><MessageComposer token="synthetic" tenantId="tenant-a" conversationId="own" /></QueryClientProvider>);
  fireEvent.change(screen.getByRole("textbox", { name: "Pregunta" }), { target: { value: "¿Qué es budget?" } });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
  expect(await screen.findByRole("status")).toHaveTextContent("preparando la respuesta");
  expect(screen.getByRole("textbox", { name: "Pregunta" })).toBeDisabled();
  reject(new Error("No se pudo generar una respuesta verificable."));
  expect(await screen.findByRole("alert")).toHaveTextContent("verificable");
  expect(screen.getByRole("textbox", { name: "Pregunta" })).toHaveValue("¿Qué es budget?");
  expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
  vi.mocked(sendConversationMessage).mockRejectedValueOnce(new Error("Segunda respuesta controlada"));
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
  await waitFor(() => expect(sendConversationMessage).toHaveBeenCalledTimes(2));
  expect(sendConversationMessage).toHaveBeenLastCalledWith("synthetic", "tenant-a", "own", { content: "¿Qué es budget?" });
});
