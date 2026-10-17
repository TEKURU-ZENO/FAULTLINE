"use client";

import React from "react";
import { Gauge, ShieldAlert, Clock, Activity, CheckCircle2 } from "lucide-react";

interface ImpactMetersProps {
  survivingCapacity: number;
  nominalCapacity: number;
  blastRadiusCount: number;
  activeAlertCount: number;
  incidentStatus: "healthy" | "firing" | "investigating" | "resolved";
  elapsedSeconds: number;
}

export default function ImpactMeters({
  survivingCapacity,
  nominalCapacity,
  blastRadiusCount,
  activeAlertCount,
  incidentStatus,
  elapsedSeconds,
}: ImpactMetersProps) {
  const capacityPct = Math.round((survivingCapacity / nominalCapacity) * 100);

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-[#090d16] px-6 flex items-center justify-between z-10">
      {/* Brand & Incident State */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 font-mono font-bold text-lg">
            ⚡
          </div>
          <div>
            <div className="text-base font-bold tracking-tight text-slate-100 flex items-center gap-2">
              FAULTLINE
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                FalkorDB Brain
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              Autonomous Incident Commander
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800 mx-2" />

        {/* Live Status Pill */}
        <div
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium border ${
            incidentStatus === "firing"
              ? "bg-rose-950/50 border-rose-800 text-rose-300 animate-pulse"
              : incidentStatus === "investigating"
              ? "bg-amber-950/50 border-amber-800 text-amber-300"
              : incidentStatus === "resolved"
              ? "bg-emerald-950/50 border-emerald-800 text-emerald-300"
              : "bg-slate-900 border-slate-800 text-slate-400"
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              incidentStatus === "firing"
                ? "bg-rose-500"
                : incidentStatus === "investigating"
                ? "bg-amber-400 animate-ping"
                : incidentStatus === "resolved"
                ? "bg-emerald-400"
                : "bg-slate-500"
            }`}
          />
          <span className="uppercase">{incidentStatus}</span>
        </div>
      </div>

      {/* Impact Gauges */}
      <div className="flex items-center gap-6">
        {/* maxFlow Checkout Capacity Gauge */}
        <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800 px-3.5 py-1.5 rounded-lg">
          <Gauge
            className={`w-4 h-4 ${
              capacityPct < 50
                ? "text-rose-400"
                : capacityPct < 90
                ? "text-amber-400"
                : "text-emerald-400"
            }`}
          />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 leading-none mb-1">
              Surviving Checkout Capacity (maxFlow)
            </div>
            <div className="flex items-baseline gap-1.5">
              <span
                className={`font-mono font-bold text-sm leading-none ${
                  capacityPct < 50
                    ? "text-rose-400"
                    : capacityPct < 90
                    ? "text-amber-400"
                    : "text-emerald-400"
                }`}
              >
                {survivingCapacity.toFixed(0)} rps
              </span>
              <span className="text-[11px] font-mono text-slate-500">
                / {nominalCapacity} rps ({capacityPct}%)
              </span>
            </div>
          </div>
        </div>

        {/* Blast Radius Count */}
        <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800 px-3.5 py-1.5 rounded-lg">
          <ShieldAlert
            className={`w-4 h-4 ${blastRadiusCount > 0 ? "text-amber-400" : "text-slate-500"}`}
          />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 leading-none mb-1">
              Blast Radius
            </div>
            <div className="font-mono font-bold text-sm leading-none text-slate-200">
              {blastRadiusCount} Services Upstream
            </div>
          </div>
        </div>

        {/* Active Alerts */}
        <div className="flex items-center gap-3 bg-slate-900/60 border border-slate-800 px-3.5 py-1.5 rounded-lg">
          <Activity
            className={`w-4 h-4 ${activeAlertCount > 0 ? "text-rose-400" : "text-emerald-400"}`}
          />
          <div>
            <div className="text-[10px] uppercase font-mono text-slate-400 leading-none mb-1">
              Active Alerts
            </div>
            <div className="font-mono font-bold text-sm leading-none text-slate-200">
              {activeAlertCount} Firing
            </div>
          </div>
        </div>

        {/* Elapsed Timer */}
        <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
          <Clock className="w-4 h-4 text-slate-500" />
          <span className="font-mono text-sm font-semibold">{formatTime(elapsedSeconds)}</span>
        </div>
      </div>
    </header>
  );
}
