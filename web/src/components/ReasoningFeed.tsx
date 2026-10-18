"use client";

import React, { useEffect, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";

export interface InvestigationStep {
  step_idx: number;
  agent: string;
  log: string;
  cypher?: string;
  duration_ms?: number;
  rows_count?: number;
  cited_nodes?: string[];
  is_fast_path?: boolean;
}

interface ReasoningFeedProps {
  steps: InvestigationStep[];
  isInvestigating: boolean;
  onStepSelect?: (citedNodes: string[]) => void;
}

const AGENT_LABELS: Record<string, string> = {
  commander: "Commander",
  historian: "Historian",
  topology_investigator: "Topology",
  change_investigator: "Change",
  remediator: "Remediator",
  scribe: "Scribe",
};

function parseAgentName(log: string): string {
  if (log.includes("[Commander")) return "commander";
  if (log.includes("[Historian")) return "historian";
  if (log.includes("[Topology")) return "topology_investigator";
  if (log.includes("[Change")) return "change_investigator";
  if (log.includes("[Remediator")) return "remediator";
  if (log.includes("[Scribe")) return "scribe";
  return "commander";
}

export default function ReasoningFeed({ steps, isInvestigating, onStepSelect }: ReasoningFeedProps) {
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});
  const listEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [steps.length, isInvestigating]);

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <aside className="flex h-full w-[380px] shrink-0 flex-col border-l border-ink-800 bg-ink-900" aria-label="Agent reasoning trace">
      <div className="flex items-baseline justify-between px-5 pb-3 pt-5">
        <h2 className="text-[13px] font-medium text-ink-200">Reasoning trace</h2>
        <span className="font-mono text-2xs text-ink-500 tabular">
          {steps.length} {steps.length === 1 ? "step" : "steps"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-5 pb-6" aria-live="polite">
        {steps.length === 0 && !isInvestigating ? (
          <div className="flex h-full flex-col justify-center pb-16">
            <div className="mb-5 space-y-2 opacity-60" aria-hidden>
              {[72, 54, 64].map((w, i) => (
                <div key={i} className="flex gap-3">
                  <div className="mt-1 h-2 w-2 shrink-0 rounded-full border border-ink-700" />
                  <div className="h-2 rounded bg-ink-800" style={{ width: `${w}%` }} />
                </div>
              ))}
            </div>
            <p className="text-[13px] font-medium text-ink-300">No investigation yet</p>
            <p className="mt-1 max-w-[30ch] text-xs leading-relaxed text-ink-500 [text-wrap:pretty]">
              Inject a fault, then run root-cause analysis. Every Cypher query the agents run shows up here.
            </p>
          </div>
        ) : (
          <ol className="relative">
            {/* Timeline spine */}
            <span className="absolute bottom-2 left-[3.5px] top-2 w-px bg-ink-800" aria-hidden />

            {steps.map((step, idx) => {
              const agentKey = parseAgentName(step.log);
              const isExpanded = !!expandedIndices[idx];
              const isFastPath = step.log.includes("FAST PATH TRIGGERED");
              const cited = step.cited_nodes || [];

              return (
                <li key={idx} className="rise-in relative pb-4 pl-6" style={{ animationDelay: `${Math.min(idx, 4) * 30}ms` }}>
                  <span
                    className={`absolute left-0 top-[5px] h-2 w-2 rounded-full ring-4 ring-ink-900 ${
                      isFastPath ? "bg-focus" : agentKey === "remediator" ? "bg-ok" : "bg-ink-500"
                    }`}
                  />
                  <div className="flex items-baseline justify-between gap-2">
                    <div className="flex items-baseline gap-2">
                      <span className="text-xs font-medium text-ink-200">{AGENT_LABELS[agentKey]}</span>
                      <span className="font-mono text-2xs text-ink-500 tabular">#{step.step_idx || idx + 1}</span>
                    </div>
                    {step.duration_ms != null && (
                      <span className="font-mono text-2xs text-ink-500 tabular">{step.duration_ms.toFixed(1)} ms</span>
                    )}
                  </div>

                  {isFastPath && (
                    <div className="mt-1.5 inline-flex items-center gap-1.5 rounded bg-focus-dim px-2 py-0.5 text-2xs font-medium text-focus">
                      Fast path · recalled from episodic memory
                    </div>
                  )}

                  <button
                    onClick={() => onStepSelect?.(cited)}
                    disabled={cited.length === 0}
                    className="mt-1 block w-full rounded text-left text-[13px] leading-relaxed text-ink-300 [text-wrap:pretty] enabled:hover:text-ink-100 disabled:cursor-default"
                  >
                    {step.log.replace(/\[.*?\]\s*/, "")}
                  </button>

                  {step.cypher && (
                    <div className="mt-1.5">
                      <button
                        onClick={() => toggleExpand(idx)}
                        aria-expanded={isExpanded}
                        className="flex items-center gap-1 font-mono text-2xs text-ink-500 transition-colors duration-200 hover:text-ink-300"
                      >
                        <ChevronRight className={`h-3 w-3 transition-transform duration-200 ${isExpanded ? "rotate-90" : ""}`} />
                        cypher
                      </button>
                      {isExpanded && (
                        <pre className="rise-in mt-1.5 overflow-x-auto whitespace-pre-wrap rounded-md bg-ink-950 p-3 font-mono text-2xs leading-relaxed text-ink-300">
                          {step.cypher}
                        </pre>
                      )}
                    </div>
                  )}
                </li>
              );
            })}

            {isInvestigating && (
              <li className="relative pb-2 pl-6" aria-label="Agents working">
                <span className="absolute left-0 top-[5px] h-2 w-2 animate-pulse rounded-full bg-focus ring-4 ring-ink-900" />
                <div className="skeleton h-3 w-24 rounded" />
                <div className="skeleton mt-2 h-3 w-full rounded" />
                <div className="skeleton mt-1.5 h-3 w-3/5 rounded" />
              </li>
            )}
          </ol>
        )}
        <div ref={listEndRef} />
      </div>
    </aside>
  );
}
