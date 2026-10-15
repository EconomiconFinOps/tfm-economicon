import { useQuery } from '@tanstack/react-query';
import { getSessionGeneration } from '../services/api';
import { fetchChatCapabilities, type ChatScope } from '../services/chat';

export function useChatCapabilities(scope: ChatScope) {
  return useQuery({
    queryKey: ['chat-capabilities', getSessionGeneration(), scope.userId, scope.tenantId],
    queryFn: ({ signal }) => fetchChatCapabilities(scope, signal),
    retry: false,
    staleTime: 0,
    gcTime: 0
  });
}
