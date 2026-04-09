import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import { runTriage, type TriageResponse } from "../api";
import { AgentRail } from "./AgentRail";

const DEFAULT_PAYLOAD = `{
  "transaction_id": "txn_demo_01",
  "user_id": "user_neo",
  "timestamp": "2026-04-09T12:00:00Z",
  "amount": 4200.0,
  "currency": "USD",
  "merchant_category": "electronics",
  "country": "GB",
  "user_home_country": "US",
  "card_present": false,
  "auth_attempts_24h": 8,
  "failed_auth_attempts_24h": 5,
  "prior_transactions_1h": 7
}`;

export function TriageConsole() {
  const [text, setText] = useState(DEFAULT_PAYLOAD);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TriageResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [railIndex, setRailIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearRailTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => () => clearRailTimer(), []);

  const startRailAnimation = useCallback(() => {
    clearRailTimer();
    setRailIndex(0);
    let i = 0;
    timerRef.current = setInterval(() => {
      i = Math.min(i + 1, 4);
      setRailIndex(i);
      if (i >= 4) clearRailTimer();
    }, 420);
  }, []);

  const onRun = async () => {
    setError(null);
    setResult(null);
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(text) as Record<string, unknown>;
    } catch {
      setError("Invalid JSON payload.");
      return;
    }
    setLoading(true);
    startRailAnimation();
    try {
      const out = await runTriage(parsed);
      setRailIndex(4);
      setResult(out);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
      clearRailTimer();
    }
  };

  const decision = result?.result.decision;
  const decisionColor =
    decision === "escalate"
      ? "text-magenta-neon text-glow-magenta"
      : decision === "review"
        ? "text-amber-300"
        : "text-cyan-neon text-glow-cyan";

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col gap-4"
      >
        <AgentRail activeIndex={railIndex} running={loading} />
        <div className="rounded-2xl border border-cyan-neon/20 bg-panel/90 p-5 backdrop-blur-2xl glass-border">
          <div className="mb-3 flex flex-wrap items-center gap-3">
            <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-white/50">
              payload_editor
            </span>
            <button
              type="button"
              onClick={() => setText(DEFAULT_PAYLOAD)}
              className="rounded-lg border border-white/15 bg-white/5 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-white/70 transition hover:border-cyan-neon/40 hover:text-cyan-neon"
            >
              load demo
            </button>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            spellCheck={false}
            className="h-[min(52vh,420px)] w-full resize-y rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-xs leading-relaxed text-cyan-neon/90 outline-none ring-0 focus:border-cyan-neon/35"
          />
          {error && (
            <p className="mt-3 font-mono text-xs text-red-400">{error}</p>
          )}
          <button
            type="button"
            disabled={loading}
            onClick={onRun}
            className={clsx(
              "mt-4 w-full rounded-xl border py-3 font-display text-sm font-bold uppercase tracking-[0.25em] transition",
              loading
                ? "cursor-wait border-white/20 bg-white/5 text-white/40"
                : "border-cyan-neon/50 bg-gradient-to-r from-cyan-neon/15 to-magenta-neon/15 text-white shadow-neon hover:border-cyan-neon hover:shadow-[0_0_40px_rgba(0,245,255,0.25)]"
            )}
          >
            {loading ? "orchestrating…" : "execute triage"}
          </button>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, delay: 0.08 }}
        className="rounded-2xl border border-magenta-neon/20 bg-panel/85 p-5 backdrop-blur-2xl glass-border"
      >
        <div className="mb-4 flex items-center justify-between gap-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.3em] text-white/50">
            neural_verdict
          </span>
          {result && (
            <span
              className={clsx(
                "font-display text-xs font-bold uppercase tracking-widest",
                result.audit_verified ? "text-cyan-neon" : "text-red-400"
              )}
            >
              chain {result.audit_verified ? "verified" : "failed"}
            </span>
          )}
        </div>

        <AnimatePresence mode="wait">
          {!result ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex min-h-[280px] flex-col items-center justify-center gap-3 text-center"
            >
              <div className="h-px w-24 bg-gradient-to-r from-transparent via-cyan-neon/50 to-transparent" />
              <p className="max-w-sm font-mono text-xs text-white/40">
                Awaiting orchestration. Multi-agent graph: intake → features → risk
                (deterministic + LLM) → policy → signed audit trail.
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="out"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <div className="font-mono text-[9px] uppercase tracking-widest text-white/40">
                    decision
                  </div>
                  <div className={clsx("mt-1 font-display text-2xl font-extrabold uppercase", decisionColor)}>
                    {result.result.decision}
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <div className="font-mono text-[9px] uppercase tracking-widest text-white/40">
                    risk_score
                  </div>
                  <div className="mt-1 font-display text-2xl font-extrabold text-white tabular-nums">
                    {result.result.risk_score.toFixed(2)}
                  </div>
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-4">
                <div className="font-mono text-[9px] uppercase tracking-widest text-magenta-neon/70">
                  investigator_channel
                </div>
                <p className="mt-2 font-mono text-xs leading-relaxed text-white/75">
                  {result.result.investigator_summary}
                </p>
              </div>
              <details className="group rounded-xl border border-cyan-neon/15 bg-black/20">
                <summary className="cursor-pointer select-none px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-cyan-neon/80">
                  audit_events ({result.audit_events.length})
                </summary>
                <pre className="max-h-[220px] overflow-auto border-t border-white/10 p-4 font-mono text-[10px] leading-relaxed text-white/55">
                  {JSON.stringify(result.audit_events, null, 2)}
                </pre>
              </details>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
