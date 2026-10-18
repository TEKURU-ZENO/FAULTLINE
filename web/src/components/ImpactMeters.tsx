"use client";

import React from "react";

interface ImpactMetersProps {
  survivingCapacity: number;
  nominalCapacity: number;
  blastRadiusCount: number;
  activeAlertCount: number;
  incidentStatus: "healthy" | "firing" | "investigating" | "resolved";
  elapsedSeconds: number;
  connected: boolean;
}

const STATUS_STYLE: Record<ImpactMetersProps["incidentStatus"], { dot: string; text: string; label: string }> = {
  healthy: { dot: "bg-ok", text: "text-ink-200", label: "All systems nominal" },
  firing: { dot: "bg-crit animate-pulse", text: "text-crit", label: "Incident firing" },
  investigating: { dot: "bg-focus animate-pulse", text: "text-focus", label: "Agents investigating" },
  resolved: { dot: "bg-ok", text: "text-ok", label: "Resolved" },
};

function formatTime(secs: number) {
  const mins = Math.floor(secs / 60);
  const s = secs % 60;
  return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function Metric({
  label,
  value,
  unit,
  tone = "text-ink-100",
  children,
}: {
  label: string;
  value: React.ReactNode;
  unit?: string;
  tone?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex min-w-0 flex-col justify-center gap-1 px-5">
      <span className="text-2xs text-ink-400">{label}</span>
      <div className="flex items-baseline gap-1.5">
        <span className={`font-mono text-lg font-medium leading-none tracking-tight tabular ${tone}`}>{value}</span>
        {unit && <span className="font-mono text-2xs text-ink-500">{unit}</span>}
      </div>
      {children}
    </div>
  );
}

export default function ImpactMeters({
  survivingCapacity,
  nominalCapacity,
  blastRadiusCount,
  activeAlertCount,
  incidentStatus,
  elapsedSeconds,
  connected,
}: ImpactMetersProps) {
  const capacityPct = nominalCapacity > 0 ? Math.round((survivingCapacity / nominalCapacity) * 100) : 0;
  const capTone = capacityPct < 50 ? "text-crit" : capacityPct < 90 ? "text-warn" : "text-ink-100";
  const capBar = capacityPct < 50 ? "bg-crit" : capacityPct < 90 ? "bg-warn" : "bg-ok";
  const status = STATUS_STYLE[incidentStatus];

  return (
    <header className="flex h-[68px] shrink-0 items-stretch border-b border-ink-800 bg-ink-900">
      {/* Brand */}
      <div className="flex items-center gap-3 border-r border-ink-800 px-5">
        <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden>
          <rect width="32" height="32" rx="8" fill="#191e24" />
          <path
            d="M6 20 L12 20 L15 9 L18 24 L21 15 L26 15"
            fill="none"
            stroke="#7fb2e5"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-[-0.02em] text-ink-100">Faultline</div>
          <div className="text-2xs text-ink-400">Incident commander on FalkorDB</div>
        </div>
      </div>

      {/* Incident state */}
      <div className="flex items-center gap-2.5 border-r border-ink-800 px-5" role="status" aria-live="polite">
        <span className={`h-2 w-2 rounded-full ${status.dot}`} />
        <span className={`text-sm font-medium ${status.text}`}>{status.label}</span>
        {incidentStatus !== "healthy" && (
          <span className="ml-1 font-mono text-sm text-ink-400 tabular">{formatTime(elapsedSeconds)}</span>
        )}
      </div>

      {/* Metrics */}
      <div className="flex flex-1 items-stretch divide-x divide-ink-800 overflow-x-auto">
        <Metric label="Surviving checkout capacity" value={survivingCapacity.toFixed(0)} unit={`/ ${nominalCapacity} rps`} tone={capTone}>
          <div className="mt-0.5 h-[3px] w-40 overflow-hidden rounded-full bg-ink-800">
            <div
              className={`h-full rounded-full transition-[width] duration-700 ease-spring ${capBar}`}
              style={{ width: `${Math.min(100, capacityPct)}%` }}
            />
          </div>
        </Metric>
        <Metric
          label="Blast radius"
          value={blastRadiusCount}
          unit={blastRadiusCount === 1 ? "service upstream" : "services upstream"}
          tone={blastRadiusCount > 0 ? "text-warn" : "text-ink-100"}
        />
        <Metric
          label="Active alerts"
          value={activeAlertCount}
          unit="firing"
          tone={activeAlertCount > 0 ? "text-crit" : "text-ink-100"}
        />
      </div>

      {/* Connection */}
      <div className="flex items-center gap-2 border-l border-ink-800 px-5 text-2xs text-ink-400">
        <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-ok" : "bg-crit"}`} />
        {connected ? "API connected" : "API offline"}
      </div>
    </header>
  );
}
