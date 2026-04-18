import { SceneBackground } from "./components/SceneBackground";
import { ScanlineOverlay } from "./components/ScanlineOverlay";
import { CaseQueue } from "./components/CaseQueue";
import { TriageConsole } from "./components/TriageConsole";

export default function App() {
  return (
    <div className="relative min-h-full overflow-x-hidden">
      <SceneBackground />
      <ScanlineOverlay />

      <header className="relative z-10 border-b border-white/5 bg-black/20 px-6 py-6 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1600px] flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.5em] text-magenta-neon/90">
              classified // multi-agent
            </p>
            <h1
              className="glitch font-display text-3xl font-extrabold uppercase tracking-[0.12em] text-white sm:text-4xl"
              data-text="Neural Fraud Orchestrator"
            >
              Neural Fraud Orchestrator
            </h1>
            <p className="mt-2 max-w-xl font-mono text-xs text-white/45">
              Live agent graph · tamper-evident audit chain · policy-aware escalation
            </p>
          </div>
          <div className="font-mono text-[10px] text-white/35">
            <span className="text-cyan-neon/80">SYS</span> v0.2 · local mesh
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-[1600px] space-y-6 px-6 py-8">
        <CaseQueue />
        <TriageConsole />
      </main>

      <footer className="relative z-10 border-t border-white/5 px-6 py-4 text-center font-mono text-[10px] text-white/30">
        Start API:{" "}
        <code className="text-cyan-neon/70">fraud-api</code> or{" "}
        <code className="text-cyan-neon/70">python -m uvicorn fraud_agent_orchestrator.api.main:app --reload</code>
        {" · "}
        UI: <code className="text-magenta-neon/70">cd web && npm run dev</code>
      </footer>
    </div>
  );
}
