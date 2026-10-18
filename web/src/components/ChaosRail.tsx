"use client";

import React, { useState } from "react";
import { Play, RotateCcw, ArrowUpRight, Zap } from "lucide-react";

interface ChaosRailProps {
  onInject: (faultId: number) => void;
  onHeal: () => void;
  onInvestigate: (autoApprove: boolean) => void;
  onTenantChange: (tenant: string) => void;
  activeTenant: string;
  isInvestigating: boolean;
  onOpenPostmortem?: () => void;
  hasPostmortem: boolean;
}

const FAULT_OPTIONS = [
  {
    id: 1,
    target: "paymentservice",
    name: "Bad deploy",
    desc: "v2.4.1 rollout spikes p99 latency and returns 5xx on checkout.",
  },
  {
    id: 2,
    target: "orders-pg",
    name: "Connection pool exhaustion",
    desc: "Leaked connections block checkout and accounting writes.",
  },
  {
    id: 8,
    target: "cartservice → valkey-cart",
    name: "Retry storm",
    desc: "Uncapped client retries amplify load until the cache falls over.",
  },
];

const TENANTS = [
  { value: "tenant:demo", hint: "seeded memory" },
  { value: "tenant:acme", hint: "isolated" },
  { value: "tenant:eval_cold", hint: "zero memory" },
];

function SectionTitle({ children, aside }: { children: React.ReactNode; aside?: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-baseline justify-between">
      <h2 className="text-[13px] font-medium text-ink-200">{children}</h2>
      {aside}
    </div>
  );
}

export default function ChaosRail({
  onInject,
  onHeal,
  onInvestigate,
  onTenantChange,
  activeTenant,
  isInvestigating,
  onOpenPostmortem,
  hasPostmortem,
}: ChaosRailProps) {
  const [selectedFault, setSelectedFault] = useState<number>(1);
  const [autoApprove, setAutoApprove] = useState<boolean>(true);

  return (
    <aside className="flex h-full w-[300px] shrink-0 flex-col border-r border-ink-800 bg-ink-900 text-sm">
      <div className="flex-1 space-y-8 overflow-y-auto px-5 pb-6 pt-5">
        {/* Tenant */}
        <section>
          <SectionTitle>Tenant graph</SectionTitle>
          <div className="grid grid-cols-1 gap-px overflow-hidden rounded-lg bg-ink-800">
            {TENANTS.map((t) => {
              const active = activeTenant === t.value;
              return (
                <button
                  key={t.value}
                  onClick={() => onTenantChange(t.value)}
                  aria-pressed={active}
                  className={`flex items-center justify-between px-3 py-2 text-left transition-colors duration-200 ${
                    active ? "bg-ink-800 text-ink-100" : "bg-ink-850 text-ink-400 hover:bg-ink-800/70 hover:text-ink-200"
                  }`}
                >
                  <span className="font-mono text-xs">{t.value}</span>
                  <span className={`text-2xs ${active ? "text-focus" : "text-ink-500"}`}>{t.hint}</span>
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-2xs leading-relaxed text-ink-500 [text-wrap:pretty]">
            Each tenant is its own FalkorDB graph. State never crosses between them.
          </p>
        </section>

        {/* Faults */}
        <section>
          <SectionTitle aside={<kbd className="rounded border border-ink-700 px-1.5 font-mono text-2xs text-ink-400">i</kbd>}>
            Fault scenario
          </SectionTitle>
          <div role="radiogroup" aria-label="Fault scenario" className="space-y-1.5">
            {FAULT_OPTIONS.map((f) => {
              const active = selectedFault === f.id;
              return (
                <button
                  key={f.id}
                  role="radio"
                  aria-checked={active}
                  onClick={() => setSelectedFault(f.id)}
                  className={`group relative w-full rounded-lg py-2.5 pl-4 pr-3 text-left transition-colors duration-200 ${
                    active ? "bg-ink-800" : "hover:bg-ink-850"
                  }`}
                >
                  <span
                    className={`absolute left-0 top-2.5 bottom-2.5 w-[2px] rounded-full transition-colors duration-200 ${
                      active ? "bg-crit" : "bg-ink-700 group-hover:bg-ink-600"
                    }`}
                  />
                  <div className="flex items-baseline justify-between gap-2">
                    <span className={`text-[13px] font-medium ${active ? "text-ink-100" : "text-ink-300"}`}>{f.name}</span>
                    <span className="font-mono text-2xs text-ink-500">#{f.id}</span>
                  </div>
                  <div className="mt-0.5 font-mono text-2xs text-ink-400">{f.target}</div>
                  <p className="mt-1 text-2xs leading-relaxed text-ink-500 [text-wrap:pretty]">{f.desc}</p>
                </button>
              );
            })}
          </div>

          <button
            onClick={() => onInject(selectedFault)}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-crit/40 bg-crit-dim py-2 text-[13px] font-medium text-crit transition-[background-color,transform] duration-200 hover:bg-crit/20 active:scale-[0.98]"
          >
            <Zap className="h-3.5 w-3.5" strokeWidth={2} />
            Inject fault
          </button>
        </section>

        {/* Commander */}
        <section>
          <SectionTitle>Commander</SectionTitle>
          <label className="mb-3 flex cursor-pointer items-center justify-between rounded-lg bg-ink-850 px-3 py-2.5">
            <span className="text-[13px] text-ink-300">Auto-approve remediation</span>
            <span className="relative inline-flex">
              <input
                type="checkbox"
                checked={autoApprove}
                onChange={(e) => setAutoApprove(e.target.checked)}
                className="peer sr-only"
              />
              <span className="h-[18px] w-8 rounded-full bg-ink-700 transition-colors duration-200 peer-checked:bg-focus/80 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-focus" />
              <span className="absolute left-[3px] top-[3px] h-3 w-3 rounded-full bg-ink-100 transition-transform duration-200 ease-spring peer-checked:translate-x-[14px]" />
            </span>
          </label>

          <button
            onClick={() => onInvestigate(autoApprove)}
            disabled={isInvestigating}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-ink-100 py-2.5 text-[13px] font-medium text-ink-950 transition-[background-color,transform] duration-200 hover:bg-white active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-ink-800 disabled:text-ink-500"
          >
            <Play className="h-3.5 w-3.5" strokeWidth={2.2} fill="currentColor" />
            {isInvestigating ? "Investigating…" : "Run root-cause analysis"}
          </button>

          <button
            onClick={onHeal}
            className="mt-2 flex w-full items-center justify-center gap-1.5 py-1.5 text-xs text-ink-400 transition-colors duration-200 hover:text-ink-200"
          >
            <RotateCcw className="h-3 w-3" />
            Reset and heal system
          </button>
        </section>
      </div>

      {hasPostmortem && (
        <div className="border-t border-ink-800 p-4">
          <button
            onClick={onOpenPostmortem}
            className="group flex w-full items-center justify-between rounded-lg bg-ok-dim px-3 py-2.5 text-[13px] text-ok transition-colors duration-200 hover:bg-ok/20"
          >
            <span className="font-medium">Open postmortem</span>
            <ArrowUpRight className="h-4 w-4 transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
          </button>
        </div>
      )}
    </aside>
  );
}
