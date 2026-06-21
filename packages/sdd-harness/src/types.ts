export interface HarnessConfig {
  config_version: string;
  harness_version: string;
  contracts: {
    workflow: string;
    workflow_approval: string;
  };
  schemas: {
    manifest: string;
    supported_manifest_versions: string[];
    catalog: string;
  };
  paths: {
    stories: string;
    examples: string;
  };
  hash_algorithm: "sha256";
  required_references: string[];
  id_patterns: Record<string, string>;
}

export interface WorkflowContract {
  contract_version: string;
  status: string;
  change_types: string[];
  workflow: {
    stages: string[];
    story_statuses: string[];
    artifact_statuses: string[];
    execution_statuses: string[];
  };
  stage_contracts: Record<string, { required_artifacts: string[] }>;
  forward_transitions: Array<{ id: string; from: string; to: string; gate: string; conditions?: string[]; story_status_after?: string }>;
  artifact_transitions: Array<{ id: string; from: string; to: string }>;
  execution_transitions: Array<{ id: string; from: string; to: string }>;
  acceptance_scenarios: Array<{ id: string }>;
  correction_returns: Array<{ cause: string; from_stages: string[]; to: string; new_version_required: string }>;
  invalidation_rules: Array<{ changed: string; invalidates: string[]; return_to: string | null }>;
  change_type_policies: Record<string, Record<string, unknown>>;
  block_codes: Record<string, string>;
}

export interface ApprovalRecord {
  contract_version: string;
  decision: string;
  artifacts: Array<{ path: string; sha256: string }>;
  approver: { actor_type: string; identity: string };
  approved_at: string;
}

export interface ValidationIssue {
  code: string;
  instance_path: string;
  message: string;
}

export interface ValidationReport {
  valid: boolean;
  path: string;
  schema_version?: string;
  story_id?: string;
  errors: ValidationIssue[];
}

export type JsonObject = Record<string, unknown>;

export type AnyRecord = Record<string, any>;

export interface Actor {
  type: "human" | "agent" | "system";
  identity: string;
}

export interface JournalEvent extends JsonObject {
  event_id: string;
  event_type: string;
  sequence: number;
  previous_event_hash: string | null;
  occurred_at: string;
  actor: Actor;
  story_id: string;
  correlation_id: string;
  data: JsonObject;
  event_hash: string;
}

export interface CommandResult {
  ok: boolean;
  command: string;
  story_id?: string;
  changed: boolean;
  stage?: string;
  status?: string;
  transition?: string;
  blockers: ValidationIssue[];
  next_actions: string[];
  journal_event_id?: string;
  data?: unknown;
}
