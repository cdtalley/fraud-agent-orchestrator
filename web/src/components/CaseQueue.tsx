import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { listCases, type CaseSummary } from "../api";

export function CaseQueue() {
  const [rows, setRows] = useState<CaseSummary[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await listCases();
        if (!cancelled) setRows(data);
      } catch (e) {
        if (!cancelled)
          setErr(e instanceof Error ? e.message : "Failed to load cases");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/10 bg-panel/80 p-4 backdrop-blur-xl glass-border"
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.35em] text-cyan-neon/80">
          case_queue
        </span>
        <span className="font-mono text-[10px] text-white/35">GET /api/v1/cases</span>
      </div>
      {err && (
        <p className="font-mono text-xs text-amber-400/90">
          {err} (start API with DB; AUTH_DISABLED=true)
        </p>
      )}
      {!err && rows.length === 0 && (
        <p className="font-mono text-xs text-white/40">
          No cases yet — POST /api/v1/cases or use sync triage above.
        </p>
      )}
      <div className="max-h-48 space-y-2 overflow-auto">
        {rows.map((c) => (
          <div
            key={c.id}
            className="flex items-center justify-between rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-[11px]"
          >
            <span className="truncate text-white/80">{c.transaction_id ?? c.id}</span>
            <span className="text-cyan-neon/80">{c.status}</span>
            <span className="text-white/50">{c.decision ?? "—"}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
