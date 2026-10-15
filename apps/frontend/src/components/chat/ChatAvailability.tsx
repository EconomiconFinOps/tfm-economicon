import { useChatCapabilities } from '../../hooks/useChatCapabilities';
import type { ChatScope } from '../../services/chat';
import { ChatPanel } from './ChatPanel';

export function AvailableChatPanel({ scope, userRole }: { scope: ChatScope; userRole: string }) {
  const availability = useChatCapabilities(scope);
  return availability.isSuccess && availability.data.chat_enabled === true
    ? <ChatPanel scope={scope} userRole={userRole} /> : null;
}
