import { act, render, renderHook, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryRouter, Outlet, RouterProvider } from 'react-router';
import { useState } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { Layout } from '../src/layouts/Layout';
import { useChatSession } from '../src/components/chat/useChatSession';
import { PreparedScreen } from '../src/services/screenCapture';

vi.mock('../src/hooks/useReferenceDate', () => ({ useReferenceDate: () => ({ data: null }) }));
vi.mock('../src/components/chat/ChatPanel', () => ({ ChatPanel: () => <button>Abrir asistente</button> }));
const scope = { token: 'synthetic', tenantId: 't', userId: 'alice' };
const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), {
  status, headers: { 'Content-Type': 'application/json' }
});
let requests: { path: string; method: string; tenant: string | null }[];
let capability: (tenant: string | null) => Promise<Response>;
beforeEach(() => {
  requests = [];
  capability = async () => json({ chat_enabled: false });
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options: RequestInit = {}) => {
    const path = new URL(String(input), 'http://test').pathname;
    const tenant = new Headers(options.headers).get('X-Tenant-Id');
    requests.push({ path, method: options.method ?? 'GET', tenant });
    if (path === '/assistant/capabilities') return capability(tenant);
    return json({ items: [] });
  }));
});

function mount() {
  let switchScope!: (tenant: string) => void;
  function Session() {
    const [tenant, change] = useState('t');
    switchScope = change;
    return <Outlet context={{ token: scope.token, user: { id: scope.userId, role: 'member' },
      activeTenantId: tenant, activeTenant: { id: tenant } }} />;
  }
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([{ Component: Session, children: [{ path: '/', Component: Layout }] }]);
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
  return switchScope;
}

it.each([false, 'false', 1, null])('hides the access for a disabled or invalid flag %s', async flag => {
  capability = async () => json({ chat_enabled: flag });
  mount();
  await waitFor(() => expect(requests.some(item => item.path === '/assistant/capabilities')).toBe(true));
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
  expect(requests.filter(item => item.method === 'POST')).toEqual([]);
});

it('hides while pending, on errors and on responses with unexpected fields', async () => {
  let release!: (value: Response) => void;
  capability = () => new Promise(resolve => { release = resolve; });
  mount();
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
  await waitFor(() => expect(release).toBeDefined());
  await act(async () => release(json({ chat_enabled: true, unexpected: true })));
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
});

it('never mounts the access for an HTTP error', async () => {
  capability = async () => json({ detail: 'unavailable' }, 503);
  mount();
  await waitFor(() => expect(requests).toHaveLength(1));
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
});

it('shows only after true and never carries that answer to another tenant', async () => {
  capability = async tenant => json({ chat_enabled: tenant === 't' });
  const change = mount();
  expect(await screen.findByRole('button', { name: 'Abrir asistente' })).toBeVisible();
  act(() => change('other'));
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
  await waitFor(() => expect(requests.some(item => item.tenant === 'other')).toBe(true));
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
});

it('ignores a late affirmative answer after switching tenant', async () => {
  let release!: (value: Response) => void;
  capability = tenant => tenant === 't' ? new Promise(resolve => { release = resolve; }) : Promise.resolve(json({ chat_enabled: false }));
  const change = mount();
  await waitFor(() => expect(release).toBeDefined());
  act(() => change('other'));
  await act(async () => release(json({ chat_enabled: true })));
  expect(screen.queryByRole('button', { name: 'Abrir asistente' })).toBeNull();
});

it.each([false, 'false'])('rechecks availability before creating a draft conversation (%s)', async enabled => {
  capability = async () => json({ chat_enabled: enabled });
  const prepared = new PreparedScreen('t', 'alice');
  vi.spyOn(prepared, 'freeze').mockReturnValue({} as ReturnType<PreparedScreen['freeze']>);
  const { result } = renderHook(() => useChatSession(scope, prepared));
  await act(async () => result.current.session.send('Hola', '/'));
  expect(requests.some(item => item.path === '/assistant/capabilities')).toBe(true);
  expect(requests.filter(item => item.method === 'POST')).toEqual([]);
  expect(result.current.cell.starting).toBe(false);
  expect(result.current.cell.uncertain).toBe(false);
  expect(result.current.cell.notice).toMatch(/asistente|disponibilidad/i);
});
