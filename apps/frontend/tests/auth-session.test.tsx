import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { environmentManager, timeoutManager, type QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { billing, conversation, ingestJob, loginResponse, operator, session, tenants } from "./fixtures";
import { deferredResponse, jsonResponse, mockBackend, renderApp, restoreSession, SESSION_KEY, TENANT_KEY } from "./test-support";

function seedPrivateCache(client: QueryClient) {
  client.setQueryData(["private-residual"], { private: "abandoned-data" });
  client.getMutationCache().build(client, { mutationKey: ["private-residual"] }, {
    context: undefined, data: "abandoned-mutation", error: null, failureCount: 0,
    failureReason: null, isPaused: false, status: "success", variables: undefined, submittedAt: 0
  });
}

function expectCleared(client: QueryClient) {
  expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
  expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
  expect(client.getQueryCache().getAll().filter((query) => query.state.data !== undefined)).toEqual([]);
  expect(client.getMutationCache().getAll()).toEqual([]);
}

async function signIn(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByLabelText("Password"), "synthetic-password");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
}

async function loggedOut(client: QueryClient) {
  await waitFor(() => expect(window.localStorage.getItem(SESSION_KEY)).toBeNull());
  expect(await screen.findByRole("button", { name: "Sign in" })).toBeEnabled();
  expectCleared(client);
}

function failure(kind: number | "network" | "parsing"): Response {
  if (kind === "network") throw new TypeError("Synthetic connection failure");
  if (kind === "parsing") return new Response("{broken-json", { status: 200 });
  return new Response("Synthetic HTTP failure", { status: kind });
}

const invalidProfiles: [string, unknown][] = [
  ["null", null], ["array", []], ["wrapper", { user: operator }],
  ...(["id", "email", "role"] as const).flatMap((field): [string, unknown][] => [
    [`missing-${field}`, Object.fromEntries(Object.entries(operator).filter(([key]) => key !== field))],
    [`empty-${field}`, { ...operator, [field]: "" }],
    [`nonstring-${field}`, { ...operator, [field]: 42 }]
  ]),
  ["missing-full-name", { id: operator.id, email: operator.email, role: operator.role }],
  ["null-full-name", { ...operator, full_name: null }]
];

describe("JUP-085 runtime session contracts", () => {
  it.each<[string, string | null]>([
    ["absent", null], ["broken-json", "{"], ["null", "null"], ["primitive", "42"], ["array", "[]"],
    ["empty-token", JSON.stringify({ ...session, accessToken: "" })],
    ["nonstring-token", JSON.stringify({ ...session, accessToken: 42 })],
    ...invalidProfiles.map(([name, profile]): [string, string] => [`profile-${name}`, JSON.stringify({ ...session, user: profile })])
  ])("clears storage and both caches for %s without authenticated requests", async (_name, raw) => {
    if (raw !== null) window.localStorage.setItem(SESSION_KEY, raw!);
    window.localStorage.setItem(TENANT_KEY, tenants[0].id);
    const { requests } = mockBackend();
    const { client } = renderApp(["/"], seedPrivateCache);
    await waitFor(() => expect(window.localStorage.getItem(SESSION_KEY)).toBeNull());
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
    expectCleared(client);
    expect(requests).toEqual([]);
  });

  it.each(invalidProfiles)("invalid direct profile %s logs out and abandons parallel tenants", async (_name, profile) => {
    const pending = deferredResponse();
    const { requests } = mockBackend({ "GET /me": () => jsonResponse(profile), "GET /tenants": () => pending.promise });
    restoreSession();
    const { client } = renderApp(["/overview-legacy"]);
    await loggedOut(client);
    await act(async () => pending.resolve({ items: tenants }));
    expectCleared(client);
    expect(requests.map((request) => request.path).sort()).toEqual(["/me", "/tenants"]);
  });

  it.each<[string, unknown]>([
    ["empty-token", { ...loginResponse, access_token: "" }],
    ["missing-token", { token_type: "bearer", user: operator }],
    ["nonstring-token", { ...loginResponse, access_token: 42 }],
    ["wrong-token-type", { ...loginResponse, token_type: "basic" }],
    ["missing-token-type", { access_token: loginResponse.access_token, user: operator }],
    ...invalidProfiles.map(([name, profile]): [string, unknown] => [name, { ...loginResponse, user: profile }])
  ])("rejects login contract %s before persisting or bootstrapping", async (_name, payload) => {
    const user = userEvent.setup();
    const { requests } = mockBackend({ "POST /auth/login": () => jsonResponse(payload) });
    renderApp();
    const persist = vi.spyOn(Storage.prototype, "setItem");
    await signIn(user);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Signing in..." })).not.toBeInTheDocument());
    expect(window.localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(window.localStorage.getItem(TENANT_KEY)).toBeNull();
    expect(persist.mock.calls.filter(([key]) => key === SESSION_KEY)).toEqual([]);
    expect(requests.map((request) => request.path)).toEqual(["/auth/login"]);
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
  });

  it.each(["profile-first", "tenants-first"])("restores in parallel, persists current profile and blocks product data: %s", async (order) => {
    const profile = deferredResponse();
    const bootstrap = deferredResponse();
    const current = { ...operator, full_name: "", email: "current@example.com", role: "admin" };
    const { requests } = mockBackend({ "GET /me": () => profile.promise, "GET /tenants": () => bootstrap.promise });
    restoreSession();
    renderApp(["/overview-legacy"]);
    await waitFor(() => expect(requests).toHaveLength(2));
    for (const request of requests) {
      expect(request.headers.get("Authorization")).toBe(`Bearer ${session.accessToken}`);
      expect(request.headers.has("X-Tenant-Id")).toBe(false);
    }
    expect(requests.map((request) => request.path).sort()).toEqual(["/me", "/tenants"]);
    expect(screen.queryByText(operator.full_name)).not.toBeInTheDocument();
    await act(async () => {
      if (order === "profile-first") profile.resolve(current);
      else bootstrap.resolve({ items: tenants });
    });
    expect(requests).toHaveLength(2);
    expect(screen.queryByText("Monthly Spend")).not.toBeInTheDocument();
    await act(async () => {
      profile.resolve(current);
      bootstrap.resolve({ items: tenants });
    });
    await screen.findByText("Monthly Spend");
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual({ ...session, user: current });
  });

  it("fresh valid login still starts both bootstrap requests before either settles", async () => {
    const user = userEvent.setup();
    const profile = deferredResponse();
    const bootstrap = deferredResponse();
    const { requests } = mockBackend({ "GET /me": () => profile.promise, "GET /tenants": () => bootstrap.promise });
    renderApp();
    await signIn(user);
    await waitFor(() => expect(requests.map((request) => request.path).sort()).toEqual(["/auth/login", "/me", "/tenants"]));
    expect(screen.queryByText(operator.full_name)).not.toBeInTheDocument();
    await act(async () => { profile.resolve(operator); bootstrap.resolve({ items: tenants }); });
    expect(await screen.findByRole("button", { name: "Cerrar sesion" })).toBeEnabled();
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual(session);
    expect(vi.mocked(fetch).mock.calls.every(([, init]) => init?.credentials !== "include")).toBe(true);
  });

  it.each(["pending", "resolved"])("different server id discards %s old tenant results and repeats bootstrap", async (order) => {
    const profile = deferredResponse();
    const oldTenants = deferredResponse();
    const newTenants = deferredResponse();
    const current = { ...operator, id: "new-identity", full_name: "New Identity" };
    let attempts = 0;
    const { requests } = mockBackend({
      "GET /me": () => profile.promise,
      "GET /tenants": () => ++attempts === 1 ? oldTenants.promise : newTenants.promise
    });
    restoreSession(tenants[0].id);
    const { client } = renderApp(["/overview-legacy"], seedPrivateCache);
    await waitFor(() => expect(requests).toHaveLength(2));
    if (order === "resolved") await act(async () => oldTenants.resolve({ items: [tenants[0]] }));
    await act(async () => profile.resolve(current));
    await waitFor(() => expect(attempts).toBe(2));
    expect(screen.queryByText("Monthly Spend")).not.toBeInTheDocument();
    expect(requests.some((request) => request.path === "/billing/summary")).toBe(false);
    await act(async () => newTenants.resolve({ items: [tenants[1]] }));
    await screen.findByText("Monthly Spend");
    await act(async () => oldTenants.resolve({ items: [tenants[0]] }));
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(tenants[1].id);
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual({ ...session, user: current });
    expect(client.getQueryData(["private-residual"])).toBeUndefined();
    expect(requests.filter((request) => request.path === "/billing/summary").every((request) => request.headers.get("X-Tenant-Id") === tenants[1].id)).toBe(true);
  });
});

describe("JUP-097 strict profile policy regressions", () => {
  it.each([401, 403, 422, 503, "network", "parsing"] as const)("current /me error %s clears everything after a previously successful profile", async (kind) => {
    let revalidate = false;
    mockBackend({ "GET /me": () => revalidate ? failure(kind) : jsonResponse(operator) });
    restoreSession();
    const { client } = renderApp();
    await screen.findByRole("button", { name: "Cerrar sesion" });
    seedPrivateCache(client);
    revalidate = true;
    await act(async () => { await client.invalidateQueries({ queryKey: ["profile"] }); });
    await loggedOut(client);
  });

  it.each(["pending", "resolved"])("profile query error abandons %s concurrent tenant work", async (order) => {
    const profile = deferredResponse();
    const bootstrap = deferredResponse();
    const { requests } = mockBackend({ "GET /me": () => profile.promise, "GET /tenants": () => bootstrap.promise });
    restoreSession();
    const { client } = renderApp(["/overview-legacy"]);
    await waitFor(() => expect(requests).toHaveLength(2));
    if (order === "resolved") await act(async () => bootstrap.resolve({ items: tenants }));
    await act(async () => profile.resolve({ detail: "Temporary service failure" }, 503));
    await loggedOut(client);
    await act(async () => bootstrap.resolve({ items: tenants }));
    expectCleared(client);
    expect(requests).toHaveLength(2);
  });

  it("a failed attempt before the query error state does not redefine profile retry timing", async () => {
    const retry = deferredResponse();
    let attempts = 0;
    mockBackend({ "GET /me": () => ++attempts === 1 ? failure(503) : retry.promise });
    restoreSession();
    const { client } = renderApp(["/"], (queryClient) => {
      queryClient.setDefaultOptions({ queries: { retry: 1, retryDelay: 0, gcTime: Infinity } });
    });
    await waitFor(() => expect(attempts).toBe(2));
    expect(window.localStorage.getItem(SESSION_KEY)).not.toBeNull();
    expect(client.getQueryCache().find({ queryKey: ["profile"], exact: false })?.state.status).toBe("pending");
    await act(async () => retry.resolve(operator));
    expect(await screen.findByRole("button", { name: "Cerrar sesion" })).toBeEnabled();
  });
});

describe("global numeric 401 and local cleanup", () => {
  it.each([
    ["/tenants", "/"], ["/billing/summary", "/overview-legacy"], ["/assistant/conversations", "/assistant"]
  ])("current query %s invalidates without reset or retry, even with a non-JSON body", async (path, route) => {
    const { requests } = mockBackend({ [`GET ${path}`]: () => failure(401) });
    restoreSession(tenants[0].id);
    const { client } = renderApp([route], (queryClient) => {
      seedPrivateCache(queryClient);
      queryClient.setDefaultOptions({ queries: { retry: 2, retryDelay: 0, gcTime: Infinity } });
    });
    await loggedOut(client);
    expect(requests.filter((request) => request.path === path)).toHaveLength(1);
  });

  it.each(["ingestion", "conversation"])("current %s mutation 401 clears session and mutation state", async (flow) => {
    const user = userEvent.setup();
    const path = flow === "ingestion" ? "/jobs/ingest" : "/assistant/conversations";
    const { requests } = mockBackend({
      "GET /assistant/conversations": () => jsonResponse({ items: [] }),
      [`POST ${path}`]: () => failure(401)
    });
    restoreSession();
    const { client } = renderApp([flow === "ingestion" ? "/ingest" : "/assistant"]);
    if (flow === "ingestion") {
      await user.type(await screen.findByLabelText("Text content"), "synthetic cost data");
      await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
    } else {
      await user.click(await screen.findByRole("button", { name: "New" }));
    }
    await loggedOut(client);
    expect(requests.filter((request) => request.path === path && request.method === "POST")).toHaveLength(1);
  });

  it("invalidates on numeric 401 before an unresolved error body is read", async () => {
    const body = deferredResponse();
    const response = new Response(null, { status: 401 });
    vi.spyOn(response, "text").mockImplementation(async () => (await body.promise).text());
    mockBackend({ "GET /billing/summary": () => response });
    restoreSession();
    const { client } = renderApp(["/overview-legacy"]);
    try {
      await loggedOut(client);
    } finally {
      await act(async () => body.resolve({ detail: "late body" }));
    }
  });

  it.each([403, 422, 503, "network"] as const)("non-profile query and mutation error %s retain authentication", async (kind) => {
    const user = userEvent.setup();
    mockBackend({ "GET /billing/summary": () => failure(kind), "POST /jobs/ingest": () => failure(kind) });
    restoreSession();
    renderApp(["/overview-legacy"]);
    await screen.findByRole("heading", { name: "Backend unavailable" });
    expect(window.localStorage.getItem(SESSION_KEY)).not.toBeNull();
    await user.click(screen.getByRole("link", { name: "Ingestions" }));
    await user.type(screen.getByLabelText("Text content"), "retained draft");
    await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
    await screen.findByText(/Synthetic/);
    expect(window.localStorage.getItem(SESSION_KEY)).not.toBeNull();
    expect(screen.getByLabelText("Text content")).toHaveValue("retained draft");
  });

  it.each([403, 422, 503, "network"] as const)("tenant bootstrap error %s retains the session", async (kind) => {
    mockBackend({ "GET /tenants": () => failure(kind) });
    restoreSession();
    renderApp();
    await screen.findByRole("button", { name: "Reset session" });
    expect(window.localStorage.getItem(SESSION_KEY)).not.toBeNull();
  });

  it("public health 401 does not invalidate the active session", async () => {
    mockBackend({ "GET /health": () => failure(401) });
    restoreSession();
    renderApp(["/overview-legacy"]);
    await screen.findByRole("heading", { name: "Backend unavailable" });
    expect(window.localStorage.getItem(SESSION_KEY)).not.toBeNull();
    expect(screen.getByRole("button", { name: "Cerrar sesion" })).toBeEnabled();
  });

  it("public login 401 does not invalidate another persisted session", async () => {
    const user = userEvent.setup();
    mockBackend({ "POST /auth/login": () => failure(401) });
    restoreSession();
    renderApp(["/login"]);
    await signIn(user);
    await screen.findByText("Synthetic HTTP failure");
    expect(JSON.parse(window.localStorage.getItem(SESSION_KEY)!)).toEqual(session);
  });

  it("repeated logout clears queries, mutations and drafts without revocation", async () => {
    const user = userEvent.setup();
    const { requests } = mockBackend({ "POST /jobs/ingest": () => jsonResponse(ingestJob) });
    restoreSession();
    const { client } = renderApp(["/ingest"]);
    await user.type(await screen.findByLabelText("Text content"), "old draft");
    await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
    await screen.findByText(ingestJob.job_id);
    await user.dblClick(screen.getByRole("button", { name: "Cerrar sesion" }));
    await loggedOut(client);
    expect(screen.queryByText(ingestJob.job_id)).not.toBeInTheDocument();
    expect(requests.some((request) => /logout|revoke/.test(request.path))).toBe(false);
  });
});

function cacheView(client: QueryClient) {
  return {
    queries: client.getQueryCache().getAll().map((query) => ({
      key: query.queryKey, data: query.state.data, status: query.state.status
    })),
    mutations: client.getMutationCache().getAll().map((mutation) => ({
      data: mutation.state.data, status: mutation.state.status
    }))
  };
}

describe("session generations exclude abandoned HTTP work", () => {
  it.each(["response", "rejection"])("disposes abandoned mutation GC after late %s within three browser GC cycles", async (outcome) => {
    const gcInterval = 5 * 60 * 1000;
    const gcTimers = new Map<number, () => void>();
    let timerId = -1;
    const nativeTimeout = timeoutManager.setTimeout.bind(timeoutManager);
    const nativeClear = timeoutManager.clearTimeout.bind(timeoutManager);
    vi.spyOn(environmentManager, "isServer").mockReturnValue(false);
    // Advance only browser-default mutation GC; UI scheduling remains native.
    vi.spyOn(timeoutManager, "setTimeout").mockImplementation((callback, delay) => {
      if (delay !== gcInterval) return nativeTimeout(callback, delay);
      const id = timerId--;
      gcTimers.set(id, () => callback());
      return id;
    });
    vi.spyOn(timeoutManager, "clearTimeout").mockImplementation((id) => {
      if (typeof id === "number" && id < 0) gcTimers.delete(id);
      else nativeClear(id);
    });
    let resolve!: (response: Response) => void;
    let reject!: (reason: Error) => void;
    const pending = new Promise<Response>((accept, fail) => { resolve = accept; reject = fail; });
    const { requests } = mockBackend({ "POST /jobs/ingest": () => pending });
    const user = userEvent.setup();
    restoreSession();
    const { client, unmount } = renderApp(["/ingest"]);
    try {
      await user.type(await screen.findByLabelText("Text content"), "synthetic abandoned payload");
      await user.click(screen.getByRole("button", { name: "Queue ingestion" }));
      await waitFor(() => expect(requests.filter((request) => request.path === "/jobs/ingest")).toHaveLength(1));
      const mutation = client.getMutationCache().getAll()[0];
      expect(mutation.state.status).toBe("pending");
      expect(mutation.state.variables).toMatchObject({ text_content: "synthetic abandoned payload" });
      expect(mutation.gcTime).toBe(gcInterval);
      await user.click(screen.getByRole("button", { name: "Cerrar sesion" }));
      await loggedOut(client);
      const requestCount = requests.length;
      await act(async () => {
        if (outcome === "response") resolve(jsonResponse(ingestJob));
        else reject(new TypeError("Synthetic abandoned network failure"));
        await new Promise((finish) => setTimeout(finish, 0));
      });
      for (let cycle = 0; cycle < 3; cycle++) {
        await act(async () => {
          for (const [id, callback] of [...gcTimers]) {
            gcTimers.delete(id);
            callback();
          }
          await new Promise((finish) => setTimeout(finish, 0));
        });
      }
      expectCleared(client);
      expect(requests).toHaveLength(requestCount);
      expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled();
      expect(gcTimers.size, "Abandoned mutation must not retain a recurring GC timer after disposal deadline").toBe(0);
    } finally {
      unmount();
      client.clear();
      gcTimers.clear();
    }
  });

  it.each(["network", "body"])("abandoned %s rejection cannot retry a mutation in the next same-token session", async (kind) => {
    const user = userEvent.setup();
    let reject!: (reason: Error) => void;
    const blocked = new Promise<Response>((_resolve, rejectResponse) => { reject = rejectResponse; });
    const response = jsonResponse(null);
    const parse = vi.spyOn(response, "json").mockImplementation(async () => (await blocked).json());
    let submissions = 0;
    const { requests } = mockBackend({
      "GET /assistant/conversations": () => jsonResponse({ items: [] }),
      "POST /assistant/conversations": () => ++submissions === 1
        ? (kind === "network" ? blocked : response)
        : jsonResponse(conversation)
    });
    restoreSession(tenants[0].id);
    const { client, router } = renderApp(["/assistant"], (queryClient) => {
      // A configured retry exposes an abandoned rejection as a new HTTP request.
      queryClient.setDefaultOptions({
        ...queryClient.getDefaultOptions(), mutations: { retry: 1, retryDelay: 0 }
      });
    });
    await user.click(await screen.findByRole("button", { name: "New" }));
    await waitFor(() => expect(submissions).toBe(1));
    if (kind === "body") await waitFor(() => expect(parse).toHaveBeenCalledOnce());
    await user.click(screen.getByRole("button", { name: "Cerrar sesion" }));
    await loggedOut(client);
    await signIn(user);
    await screen.findByRole("button", { name: "Cerrar sesion" });
    await act(async () => { await router.navigate("/assistant"); });
    await user.type(await screen.findByPlaceholderText("New conversation title"), "B draft");
    await waitFor(() => expect(client.isFetching()).toBe(0));
    const savedSession = window.localStorage.getItem(SESSION_KEY);
    const savedTenant = window.localStorage.getItem(TENANT_KEY);
    const savedCache = cacheView(client);
    const requestCount = requests.length;
    const draft = screen.getByPlaceholderText("New conversation title");
    const draftValue = (draft as HTMLInputElement).value;
    await act(async () => {
      reject(kind === "network" ? new TypeError("Abandoned network failure") : new SyntaxError("Abandoned body parsing failure"));
      await new Promise((resolve) => setTimeout(resolve, 0));
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(submissions).toBe(1);
    expect(requests).toHaveLength(requestCount);
    expect(window.localStorage.getItem(SESSION_KEY)).toBe(savedSession);
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(savedTenant);
    expect(cacheView(client)).toEqual(savedCache);
    expect(draft).toHaveValue(draftValue);
  });

  const cases = (["profile", "tenants", "billing", "conversation"] as const).flatMap((flow) =>
    (["success", "401", "503", "body"] as const).flatMap((result) =>
      (["login", "same", "different"] as const).map((next) => ({ flow, result, next }))
    )
  );

  it.each(cases)("late $flow $result leaves $next session unchanged", async ({ flow, result, next }) => {
    const user = userEvent.setup();
    const delayed = deferredResponse();
    const body = deferredResponse();
    let phase: "initial" | "pending" | "next" | "current-error" = "initial";
    const bUser = { ...operator, id: next === "different" ? "session-b-user" : operator.id, full_name: "Session B Operator" };
    const bLogin = { ...loginResponse, access_token: next === "different" ? "session-b-token" : session.accessToken, user: bUser };
    const oldData = flow === "profile" ? { ...operator, full_name: "Obsolete A" }
      : flow === "tenants" ? { items: [{ ...tenants[0], name: "Obsolete A tenant" }] }
      : flow === "billing" ? { ...billing, monthly_spend: 999999 }
      : { ...conversation, id: "obsolete-a-conversation" };
    const heldResponse = jsonResponse(null);
    const parse = vi.spyOn(heldResponse, "json").mockImplementation(async () => (await body.promise).json());
    const pendingResult = () => result === "body" ? heldResponse : delayed.promise;
    const { requests } = mockBackend({
      "POST /auth/login": () => jsonResponse(bLogin),
      "GET /me": () => {
        if (phase === "current-error") return failure(503);
        if (phase === "pending" && flow === "profile") return pendingResult();
        return jsonResponse(phase === "next" ? bUser : operator);
      },
      "GET /tenants": () => phase === "pending" && flow === "tenants" ? pendingResult() : jsonResponse({ items: tenants }),
      "GET /billing/summary": () => phase === "pending" && flow === "billing" ? pendingResult() : jsonResponse(billing),
      "GET /assistant/conversations": () => jsonResponse({ items: [] }),
      "POST /assistant/conversations": () => pendingResult()
    });
    restoreSession(tenants[0].id);
    const route = flow === "conversation" ? "/assistant" : "/overview-legacy";
    const { client, router } = renderApp([route]);
    await screen.findByRole("button", { name: "Cerrar sesion" });
    if (flow === "conversation") await screen.findByRole("button", { name: "New" });
    else await screen.findByText("Monthly Spend");
    const before = requests.length;
    phase = "pending";
    if (flow === "conversation") {
      await user.click(screen.getByRole("button", { name: "New" }));
    } else {
      const key = flow === "billing" ? "billing-summary" : flow;
      act(() => { void client.invalidateQueries({ queryKey: [key] }); });
    }
    await waitFor(() => expect(requests.length).toBeGreaterThan(before));
    if (result === "body") await waitFor(() => expect(parse).toHaveBeenCalledOnce());
    await user.click(screen.getByRole("button", { name: "Cerrar sesion" }));
    await loggedOut(client);
    phase = "next";
    if (next !== "login") {
      await signIn(user);
      await screen.findByRole("button", { name: "Cerrar sesion" });
      await act(async () => { await router.navigate(route); });
      if (flow === "conversation") await screen.findByRole("button", { name: "New" });
      else await screen.findByText("Monthly Spend");
      await waitFor(() => expect(client.isFetching()).toBe(0));
    }
    const savedSession = window.localStorage.getItem(SESSION_KEY);
    const savedTenant = window.localStorage.getItem(TENANT_KEY);
    const savedCache = cacheView(client);
    const requestCount = requests.length;
    const page = document.body.textContent;
    await act(async () => {
      if (result === "body") body.resolve(oldData);
      else delayed.resolve(oldData, result === "success" ? 200 : Number(result));
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(window.localStorage.getItem(SESSION_KEY)).toBe(savedSession);
    expect(window.localStorage.getItem(TENANT_KEY)).toBe(savedTenant);
    expect(cacheView(client)).toEqual(savedCache);
    expect(document.body.textContent).toBe(page);
    expect(requests).toHaveLength(requestCount);
    if (next === "login") expectCleared(client);
    else {
      phase = "current-error";
      await act(async () => { await client.invalidateQueries({ queryKey: ["profile"] }); });
      await loggedOut(client);
    }
  });

  it.each(["response", "body"])("a pending login %s abandoned by logout cannot overwrite the next login", async (delay) => {
    const user = userEvent.setup();
    const old = deferredResponse();
    const body = deferredResponse();
    const response = jsonResponse(null);
    const parse = vi.spyOn(response, "json").mockImplementation(async () => (await body.promise).json());
    let logins = 0;
    const bUser = { ...operator, full_name: "Accepted B" };
    mockBackend({
      "POST /auth/login": () => ++logins === 1 ? (delay === "body" ? response : old.promise) : jsonResponse({ ...loginResponse, user: bUser }),
      "GET /me": () => jsonResponse(logins >= 2 ? bUser : operator)
    });
    restoreSession();
    const { client, router } = renderApp(["/login"]);
    await signIn(user);
    if (delay === "body") await waitFor(() => expect(parse).toHaveBeenCalledOnce());
    await act(async () => { await router.navigate("/"); });
    await user.click(await screen.findByRole("button", { name: "Cerrar sesion" }));
    await loggedOut(client);
    await signIn(user);
    await screen.findByRole("button", { name: "Cerrar sesion" });
    const saved = window.localStorage.getItem(SESSION_KEY);
    await act(async () => {
      const obsolete = { ...loginResponse, access_token: "abandoned-login-token", user: { ...operator, full_name: "Abandoned A" } };
      if (delay === "body") body.resolve(obsolete);
      else old.resolve(obsolete);
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(window.localStorage.getItem(SESSION_KEY)).toBe(saved);
    expect(screen.getByText(bUser.full_name)).toBeVisible();
  });
});
