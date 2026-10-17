"use client";

import React, { useState } from "react";
import { Flame, Play, RefreshCw, CheckCircle, Database, Shield, ChevronRight } from "lucide-react";

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
  { id: 1, name: "Fault 1: Bad Deploy on paymentservice", desc: "v2.4.1 deploy causes p99 latency spike and 5xx errors on checkout." },
  { id: 2, name: "Fault 2: DB Pool Exhaustion on orders-pg", desc: "Leaked connections exhaust pool, blocking checkout and accounting writes." },
  { id: 8, name: "Fault 8: Retry Storm Amplification", desc: "Caller cartservice spams uncapped retries, crashing victim valkey-cart." },
];

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
    <div className="w-80 h-full flex flex-col bg-[#090d16] border-r border-slate-800 select-none text-xs">
      {/* Rail Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-rose-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
            Chaos & Controls
          </h2>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Tenant Switcher */}
        <div>
          <label className="text-[10px] font-mono uppercase text-slate-400 font-bold block mb-1.5 flex items-center gap-1.5">
            <Database className="w-3 h-3 text-sky-400" /> FalkorDB Tenant Graph
          </label>
          <select
            value={activeTenant}
            onChange={(e) => onTenantChange(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-sky-500"
          >
            <option value="tenant:demo">tenant:demo (Seeded Memory)</option>
            <option value="tenant:acme">tenant:acme (Isolated Tenant)</option>
            <option value="tenant:eval_cold">tenant:eval_cold (Zero Memory)</option>
          </select>
          <div className="text-[10px] text-slate-500 font-mono mt-1">
            Multigraph isolation: tenant graphs never leak state.
          </div>
        </div>

        {/* Chaos Injection Panel */}
        <div className="space-y-3">
          <label className="text-[10px] font-mono uppercase text-slate-400 font-bold block flex items-center gap-1.5">
            <Flame className="w-3 h-3 text-rose-400" /> Fault Scenarios
          </label>

          <div className="space-y-2">
            {FAULT_OPTIONS.map((f) => (
              <div
                key={f.id}
                onClick={() => setSelectedFault(f.id)}
                className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                  selectedFault === f.id
                    ? "bg-rose-950/30 border-rose-600/80 text-rose-200"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div className="font-semibold text-[11px] mb-0.5">{f.name}</div>
                <div className="text-[10px] text-slate-400 leading-snug">{f.desc}</div>
              </div>
            ))}
          </div>

          <button
            onClick={() => onInject(selectedFault)}
            className="w-full mt-2 py-2 px-3 bg-rose-600 hover:bg-rose-500 text-white rounded-lg font-mono font-semibold text-xs flex items-center justify-center gap-1.5 shadow-lg shadow-rose-950/50 transition-colors"
          >
            <Flame className="w-3.5 h-3.5" />
            Inject Chaos (Press &apos;i&apos;)
          </button>
        </div>

        {/* Investigation Controls */}
        <div className="space-y-3 pt-4 border-t border-slate-800">
          <label className="text-[10px] font-mono uppercase text-slate-400 font-bold block flex items-center gap-1.5">
            <Play className="w-3 h-3 text-sky-400" /> Autonomous Commander
          </label>

          <div className="flex items-center gap-2 mb-2">
            <input
              type="checkbox"
              id="auto-approve"
              checked={autoApprove}
              onChange={(e) => setAutoApprove(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0"
            />
            <label htmlFor="auto-approve" className="text-[11px] text-slate-300 font-mono">
              Auto-approve remediations
            </label>
          </div>

          <button
            onClick={() => onInvestigate(autoApprove)}
            disabled={isInvestigating}
            className="w-full py-2.5 px-3 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg font-mono font-semibold text-xs flex items-center justify-center gap-1.5 shadow-lg shadow-sky-950/50 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            {isInvestigating ? "Investigating..." : "Launch Multi-Agent RCA"}
          </button>

          <button
            onClick={onHeal}
            className="w-full py-1.5 px-3 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-lg font-mono text-xs flex items-center justify-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Reset & Heal System
          </button>
        </div>

        {/* Postmortem Drawer Button */}
        {hasPostmortem && (
          <div className="pt-4 border-t border-slate-800">
            <button
              onClick={onOpenPostmortem}
              className="w-full py-2 px-3 bg-emerald-950/60 border border-emerald-600/60 hover:bg-emerald-900/60 text-emerald-200 rounded-lg font-mono text-xs flex items-center justify-between transition-colors"
            >
              <span className="flex items-center gap-1.5 font-semibold">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> View Postmortem
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-emerald-400" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
