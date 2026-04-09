import { motion } from "framer-motion";
import clsx from "clsx";

const STEPS = [
  { id: "intake", label: "INTAKE", sub: "normalize" },
  { id: "feature", label: "FEATURE", sub: "signals" },
  { id: "risk", label: "RISK", sub: "score + LLM" },
  { id: "policy", label: "POLICY", sub: "enforce" },
  { id: "report", label: "REPORT", sub: "evidence" },
] as const;

type Props = {
  activeIndex: number;
  running: boolean;
};

export function AgentRail({ activeIndex, running }: Props) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-cyan-neon/25 bg-panel/80 p-4 backdrop-blur-xl glass-border">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-[0.35em] text-cyan-neon/80">
          agent_pipeline
        </span>
        <span
          className={clsx(
            "font-mono text-[10px] uppercase tracking-widest",
            running ? "animate-pulse text-magenta-neon" : "text-white/40"
          )}
        >
          {running ? "processing" : "idle"}
        </span>
      </div>
      <div className="flex flex-wrap items-stretch justify-between gap-2">
        {STEPS.map((s, i) => {
          const done = !running && activeIndex >= i;
          const current = running && activeIndex === i;
          return (
            <motion.div
              key={s.id}
              className="relative min-w-[4.5rem] flex-1"
              initial={false}
              animate={{
                scale: current ? 1.03 : 1,
                opacity: done || current ? 1 : 0.45,
              }}
              transition={{ type: "spring", stiffness: 420, damping: 28 }}
            >
              <div
                className={clsx(
                  "rounded-xl border px-2 py-3 text-center transition-colors",
                  done && "border-cyan-neon/50 bg-cyan-dim shadow-[0_0_24px_rgba(0,245,255,0.12)]",
                  current &&
                    "border-magenta-neon/60 bg-magenta-dim shadow-[0_0_28px_rgba(255,43,214,0.18)]",
                  !done && !current && "border-white/10 bg-black/20"
                )}
              >
                <div className="font-display text-[11px] font-semibold tracking-widest text-white">
                  {s.label}
                </div>
                <div className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/45">
                  {s.sub}
                </div>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={clsx(
                    "absolute -right-1 top-1/2 hidden h-px w-2 -translate-y-1/2 sm:block",
                    done ? "bg-cyan-neon/50" : "bg-white/10"
                  )}
                />
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
