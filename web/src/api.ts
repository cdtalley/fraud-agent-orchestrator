export type CaseSummary = {
  id: string;
  status: string;
  transaction_id: string | null;
  workflow_id: string | null;
  decision: string | null;
  risk_score: number | null;
  created_at: string;
  updated_at: string;
};

export type TriageResponse = {
  result: {
    transaction_id: string;
    decision: string;
    risk_score: number;
    reasons: string[];
    policy_violations: string[];
    investigator_summary: string;
    created_at_utc: string;
  };
  audit_verified: boolean;
  audit_events: Array<{
    timestamp_utc: string;
    step: string;
    payload: Record<string, unknown>;
    prev_hash: string;
    event_hash: string;
  }>;
  lineage?: Record<string, unknown>;
  opa?: Record<string, unknown>;
  evidence_signature?: string;
  needs_hitl?: boolean;
};

export async function runTriage(
  alert: Record<string, unknown>
): Promise<TriageResponse> {
  const r = await fetch("/api/v1/triage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(alert),
  });
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const j = (await r.json()) as { detail?: string };
      if (typeof j.detail === "string") detail = j.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return r.json() as Promise<TriageResponse>;
}

export async function listCases(): Promise<CaseSummary[]> {
  const r = await fetch("/api/v1/cases");
  if (!r.ok) {
    throw new Error(r.statusText);
  }
  return r.json() as Promise<CaseSummary[]>;
}
