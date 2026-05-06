/** Unified API response wrapper */
export interface ApiResponse<T> {
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

/** API error response */
export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta: {
    request_id: string;
    timestamp: string;
  };
}

/** Typed API error */
export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(error: { code: string; message: string; details?: Record<string, unknown> }) {
    super(error.message);
    this.name = "ApiError";
    this.code = error.code;
    this.details = error.details ?? {};
  }
}

/** Task summary from index */
export interface TaskSummary {
  txn_id: string;
  goal: string;
  state: string;
  priority: string;
  created_at: string;
  updated_at: string;
  created_at_ts: number;
  updated_at_ts: number;
  sub_task_count: number;
  review_verdict: string | null;
  sub_tasks?: SubTask[];
  contracts?: Record<string, unknown>[];
  results?: ExecutionResult[];
  sub_task_progress?: {
    completed: number;
    failed: number;
    pending: number;
  };
  involved_roles?: string[];
}

/** Full transaction detail */
export interface Transaction {
  txn_id: string;
  goal: string;
  context: string;
  priority: string;
  state: string;
  interview: Record<string, unknown> | null;
  plan: Record<string, unknown> | null;
  review_verdict: string | null;
  review_notes: string | null;
  spec_review: Record<string, unknown> | null;
  quality_review: Record<string, unknown> | null;
  revision_count: number;
  revision_history: Record<string, unknown>[];
  sub_tasks: SubTask[];
  contracts: Record<string, unknown>[];
  results: ExecutionResult[];
  verify_result: Record<string, unknown> | null;
  integrated_result: string | null;
  audit_trail: AuditEntry[];
  created_at: string;
  updated_at: string;
}

export interface SubTask {
  id: string;
  task: string;
  ministry: string;
  depends_on: string[];
  estimated_minutes: number;
  success_criteria: string[];
}

export interface ExecutionResult {
  ministry: string;
  status: "completed" | "failed" | "skipped";
  result?: string;
  error?: string;
  reason?: string;
  attempts?: number;
}

export interface AuditEntry {
  step: string;
  action: string;
  [key: string]: unknown;
}

/** Real-time governance event */
export interface GovernanceEvent {
  event_id: string;
  global_seq: number;
  txn_id: string;
  txn_seq: number;
  type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

/** Agent state */
export interface AgentState {
  agent_id: string;
  role: string;
  tier: string;
  lifecycle: string;
  version: number;
  updated_at: string | null;
  active_contract_id: string | null;
  memory: AgentMemoryEntry[];
  completed_contracts: string[];
  total_tokens_consumed: number;
  total_tasks_completed: number;
  trust_score: number;
  last_activated: string | null;
  tasks_involved?: AgentTaskInvolvement[];
  current_context?: {
    txn_id: string;
    goal: string;
    stage: string;
  } | null;
}

export interface AgentMemoryEntry {
  timestamp: string;
  contract_id: string;
  summary: string;
  outcome: "success" | "failure";
}

export interface AgentTaskInvolvement {
  txn_id: string;
  goal: string;
  txn_state: string;
  agent_status: "active" | "completed" | "pending" | "failed" | "idle";
  sub_tasks: AgentSubTask[];
  contracts_count: number;
  results_count: number;
}

export interface AgentSubTask {
  id: string;
  task: string;
  status: string;
  success_criteria: string[];
}

/** Pipeline stage */
export interface PipelineStage {
  id: string;
  label: string;
  agent: string;
}

/** Workflow stage with activity data */
export interface WorkflowStage {
  id: string;
  label: string;
  agent_role: string;
  description: string;
  active_transactions: WorkflowTxnRef[];
  completed_transactions: WorkflowTxnRef[];
  active_agents: WorkflowAgentRef[];
  is_active: boolean;
}

export interface WorkflowTxnRef {
  txn_id: string;
  goal: string;
  state: string;
  sub_task_count: number;
}

export interface WorkflowAgentRef {
  role: string;
  lifecycle: string;
  active_contract: string | null;
}

/** Alert */
export interface Alert {
  alert_id: string;
  rule_id: string;
  severity: "critical" | "high" | "warning" | "info";
  txn_id: string;
  message: string;
  triggered_at: string;
  status: "active" | "acknowledged" | "suppressed" | "resolved";
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  suppressed_until: string | null;
  resolved_at: string | null;
}

/** Annotation */
export interface Annotation {
  annotation_id: string;
  txn_id: string;
  event_index: number;
  content: string;
  status: "pending" | "confirmed" | "fixed" | "ignored";
  created_at: string;
  updated_at: string;
  deleted?: boolean;
}

/** Overview stats */
export interface OverviewStats {
  total_transactions: number;
  by_state: Record<string, number>;
  active_count: number;
  error_count: number;
  completed_count: number;
  recent_transactions: TaskSummary[];
  agent_summary: AgentState[];
}
