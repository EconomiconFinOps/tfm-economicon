// Response shapes and request fields from apps/backend/app/schemas.
// Datetimes are serialized as ISO strings; open metadata remains untrusted.
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export function isNonemptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

export function isUserProfile(value: unknown): value is UserProfile {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    && "id" in value && isNonemptyString(value.id)
    && "email" in value && isNonemptyString(value.email)
    && "role" in value && isNonemptyString(value.role)
    && "full_name" in value && typeof value.full_name === "string";
}

export function isLoginResponse(value: unknown): value is LoginResponse {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    && "access_token" in value && isNonemptyString(value.access_token)
    && "token_type" in value && value.token_type === "bearer"
    && "user" in value && isUserProfile(value.user);
}

export interface TenantRecord {
  id: string;
  name: string;
  slug: string;
  plan: string;
}

export interface TenantCollection {
  items: TenantRecord[];
}

export interface BillingSummary {
  monthly_spend: number;
  savings_identified: number;
  open_ingestions: number;
  currency: string;
}

export interface IngestJobRequest {
  tenant_id: string;
  source: string;
  text_content: string;
  artifact_uri?: string | null;
  metadata?: Record<string, unknown>;
}

export interface IngestJobResponse {
  job_id: string;
  status: string;
  queue: string;
}

export interface ConversationCreateRequest {
  title: string;
}

export interface MessageCreateRequest {
  content: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  source: string;
  content: string;
  distance: number;
}

export interface MessageRecord {
  id: string;
  role: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ConversationRecord {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationCollection {
  items: ConversationRecord[];
}

export interface ConversationDetail {
  conversation: ConversationRecord;
  messages: MessageRecord[];
}

export interface AssistantReply {
  conversation: ConversationRecord;
  user_message: MessageRecord;
  assistant_message: MessageRecord;
  retrieved_context: RetrievedChunk[];
}

export interface HealthResponse {
  status: string;
  services: Record<string, string>;
  checked_at: string;
}
