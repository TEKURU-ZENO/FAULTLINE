"use client";

import React, { useState } from "react";
import { Terminal, ChevronDown, ChevronRight, Brain, Clock, Cpu, CornerDownRight } from "lucide-react";

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

const AGENT_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  commander: { bg: "bg-sky-950/40", text: "text-sky-300", border: "border-sky-800" },
  historian: { bg: "bg-purple-950/40", text: "text-purple-300", border: "border-purple-800" },
  topology_investigator: { bg: "bg-emerald-950/40", text: "text-emerald-300", border: "border-emerald-800" },
  change_investigator: { bg: "bg-amber-950/40", text: "text-amber-300", border: "border-amber-800" },
  remediator: { bg: "bg-rose-950/40", text: "text-rose-300", border: "border-rose-800" },
  scribe: { bg: "bg-slate-900", text: "text-slate-300", border: "border-slate-800" },
};

export default function ReasoningFeed({ steps, isInvestigating, onStepSelect }: ReasoningFeedProps) {
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const parseAgentName = (log: string): string => {
    if (log.includes("[Commander")) return "commander";
    if (log.includes("[Historian")) return "historian";
    if (log.includes("[Topology")) return "topology_investigator";
    if (log.includes("[Change")) return "change_investigator";
    if (log.includes("[Remediator")) return "remediator";
    if (log.includes("[Scribe")) return "scribe";
    return "commander";
  };

  return (
    <div className="w-96 h-full flex flex-col bg-[#090d16] border-l border-slate-800 select-none">
      {/* Feed Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-sky-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
            Agent Reasoning Trace
          </h2>
        </div>
        <div className="text-[11px] font-mono text-slate-500">
          {steps.length} {steps.length === 1 ? "step" : "steps"}
        </div>
      </div>

      {/* Steps List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {steps.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-600">
            <Terminal className="w-8 h-8 mb-2 stroke-[1.5]" />
            <div className="text-xs font-mono font-medium">Waiting for Incident Signals</div>
            <div className="text-[11px] text-slate-600 mt-1">
              Press &apos;i&apos; or inject chaos on the left rail to trigger investigation
            </div>
          </div>
        ) : (
          steps.map((step, idx) => {
            const agentKey = parseAgentName(step.log);
            const style = AGENT_COLORS[agentKey] || AGENT_COLORS.commander;
            const isExpanded = !!expandedIndices[idx];
            const isFastPath = step.log.includes("FAST PATH TRIGGERED");

            return (
              <div
                key={idx}
                onClick={() => onStepSelect?.(step.cited_nodes || [])}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition-all duration-150 ${
                  style.bg
                } ${style.border} ${
                  isFastPath ? "ring-1 ring-purple-500/80 shadow-lg shadow-purple-950/40" : ""
                } hover:border-slate-600`}
              >
                {/* Step Top Bar */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${style.bg} ${style.text} ${style.border} font-semibold`}
                    >
                      {agentKey.replace("_", " ")}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      Step #{step.step_idx || idx + 1}
                    </span>
                  </div>

                  {step.duration_ms && (
                    <span className="flex items-center gap-1 text-[10px] font-mono text-slate-400 bg-slate-900/80 px-1.5 py-0.5 rounded border border-slate-800">
                      <Clock className="w-2.5 h-2.5" />
                      {step.duration_ms.toFixed(1)}ms
                    </span>
                  )}
                </div>

                {/* Fast Path Badge */}
                {isFastPath && (
                  <div className="mb-2 px-2 py-1 rounded bg-purple-900/60 border border-purple-500/50 text-purple-200 text-[11px] font-mono flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
                    FAST PATH ACTIVATED: -40% steps via memory
                  </div>
                )}

                {/* Log Text */}
                <div className="text-slate-200 text-[11px] leading-relaxed font-sans font-medium">
                  {step.log.replace(/\[.*?\]\s*/, "")}
                </div>

                {/* Collapsible Cypher Query */}
                {step.cypher && (
                  <div className="mt-2 pt-2 border-t border-slate-800/80">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(idx);
                      }}
                      className="flex items-center gap-1 text-[10px] font-mono text-slate-400 hover:text-slate-200"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-3 h-3" />
                      ) : (
                        <ChevronRight className="w-3 h-3" />
                      )}
                      <span>Cypher Query ({step.duration_ms?.toFixed(1) || 4.2}ms)</span>
                    </button>

                    {isExpanded && (
                      <pre className="mt-1.5 p-2 bg-[#060a12] border border-slate-800/90 rounded text-[10px] font-mono text-sky-300/90 overflow-x-auto whitespace-pre-wrap">
                        {step.cypher}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}

        {isInvestigating && (
          <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/30 text-xs flex items-center gap-2 text-slate-400 animate-pulse font-mono">
            <Cpu className="w-4 h-4 text-sky-400 animate-spin" />
            <span>Agent team executing Cypher traversals in FalkorDB...</span>
          </div>
        )}
      </div>
    </div>
  );
}
