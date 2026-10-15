import { vi } from 'vitest';

// Legacy chat scenarios model an enabled runtime; availability has its own HTTP tests.
vi.mock('../src/hooks/useChatCapabilities', () => ({
  useChatCapabilities: () => ({ isSuccess: true, data: { chat_enabled: true } })
}));
vi.mock('../src/services/chat', async importOriginal => ({
  ...await importOriginal<typeof import('../src/services/chat')>(),
  fetchChatCapabilities: vi.fn(async () => ({ chat_enabled: true }))
}));
