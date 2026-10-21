import { webcrypto, createHash } from "node:crypto";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { beginCognitoLogin, completeCognitoLogin, cognitoLogoutUrl, COGNITO_FLOW_KEY } from "./cognito";
import { fetchProfile } from "./api";

vi.mock("./api", () => ({ fetchProfile: vi.fn() }));
const domain = "https://test-pool.auth.eu-south-2.amazoncognito.com";

beforeEach(() => {
  vi.stubGlobal("crypto", webcrypto);
  vi.stubEnv("VITE_AUTH_PROVIDER", "cognito");
  vi.stubEnv("VITE_COGNITO_DOMAIN", domain);
  vi.stubEnv("VITE_COGNITO_CLIENT_ID", "synthetic-client");
  window.sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.clearAllMocks();
  window.sessionStorage.clear();
});

it("binds a random verifier and state to S256 and the exact callback", async () => {
  const url = new URL(await beginCognitoLogin());
  const flow = JSON.parse(window.sessionStorage.getItem(COGNITO_FLOW_KEY)!);
  expect(url.origin).toBe(domain);
  expect(url.pathname).toBe("/oauth2/authorize");
  expect(url.searchParams.get("state")).toBe(flow.state);
  expect(flow.state.length).toBeGreaterThanOrEqual(43);
  expect(flow.verifier.length).toBeGreaterThanOrEqual(43);
  expect(url.searchParams.get("code_challenge_method")).toBe("S256");
  expect(url.searchParams.get("code_challenge")).toBe(createHash("sha256").update(flow.verifier).digest("base64url"));
  expect(url.searchParams.get("redirect_uri")).toBe(`${window.location.origin}/auth/callback`);
  expect(url.searchParams.has("code_verifier")).toBe(false);
});

it("exchanges a code once, sends only the access token to the API and stores no refresh token", async () => {
  const login = new URL(await beginCognitoLogin());
  const profile = { id: "sub-123", email: "operator@example.com", full_name: "Operator", role: "admin" };
  vi.mocked(fetchProfile).mockResolvedValue(profile);
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({
    access_token: "signed-access-token", token_type: "Bearer", expires_in: 900,
    refresh_token: "must-not-persist", id_token: "not-an-api-token"
  }), { status: 200 }));
  vi.stubGlobal("fetch", fetch);
  const callback = `${window.location.origin}/auth/callback?code=one-time-code&state=${login.searchParams.get("state")}`;
  const first = completeCognitoLogin(callback);
  const second = completeCognitoLogin(callback);
  expect(await second).toEqual(await first);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetchProfile).toHaveBeenCalledWith("signed-access-token");
  const [endpoint, options] = fetch.mock.calls[0];
  expect(endpoint).toBe(`${domain}/oauth2/token`);
  expect(options.body.get("grant_type")).toBe("authorization_code");
  expect(options.body.get("code_verifier")).toBeTruthy();
  expect(window.sessionStorage.getItem(COGNITO_FLOW_KEY)).toBeNull();
  expect(JSON.stringify(await first)).not.toContain("must-not-persist");
  await expect(completeCognitoLogin(callback)).rejects.toThrow();
  expect(fetch).toHaveBeenCalledTimes(1);
});

it.each(["wrong-state", "expired", "wrong-path", "duplicate-code"])("rejects %s before calling the token endpoint", async (failure) => {
  const login = new URL(await beginCognitoLogin());
  let callback = `${window.location.origin}/auth/callback?code=one&state=${login.searchParams.get("state")}`;
  if (failure === "wrong-state") callback = callback.replace("state=", "state=forged");
  if (failure === "expired") vi.spyOn(Date, "now").mockReturnValue(Date.now() + 601000);
  if (failure === "wrong-path") callback = callback.replace("/auth/callback", "/evil");
  if (failure === "duplicate-code") callback += "&code=two";
  const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
  await expect(completeCognitoLogin(callback)).rejects.toThrow();
  expect(fetch).not.toHaveBeenCalled();
});

it("rejects an external identity domain", async () => {
  vi.stubEnv("VITE_COGNITO_DOMAIN", "https://attacker.example.invalid");
  await expect(beginCognitoLogin()).rejects.toThrow();
});

it("logs out through the same client and exact registered return URL", () => {
  const url = new URL(cognitoLogoutUrl());
  expect(url.origin).toBe(domain);
  expect(url.pathname).toBe("/logout");
  expect(url.searchParams.get("client_id")).toBe("synthetic-client");
  expect(url.searchParams.get("logout_uri")).toBe(`${window.location.origin}/`);
});

it.each([
  { access_token: "access", expires_in: 0, token_type: "Bearer" },
  { access_token: "access", expires_in: 900, token_type: "other" },
  { id_token: "id-only", expires_in: 900, token_type: "Bearer" },
])("rejects malformed token responses without requesting a profile", async (payload) => {
  const login = new URL(await beginCognitoLogin());
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 })));
  await expect(completeCognitoLogin(`${window.location.origin}/auth/callback?code=one&state=${login.searchParams.get("state")}`)).rejects.toThrow();
  expect(fetchProfile).not.toHaveBeenCalled();
});
