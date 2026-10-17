"use client";

import React from "react";
import { CheckCircle2, X, ExternalLink, Zap, Users, Gauge, ArrowRight } from "lucide-react";

interface PostmortemDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  report: {
    incident_id: string;
    title: string;
    root_cause: string;
    paged_engineer: string;
    action_taken: string;
    initial_capacity_rps: number;
    recovered_capacity_rps: number;
    is_fast_path: boolean;
    total_steps: number;
  } | null;
  onSelectNode?: (name: string) => void;
}

export default function PostmortemDrawer({
  isOpen,
  onClose,
  report,
  onSelectNode,
}: PostmortemDrawerProps) {
  if (!isOpen || !report) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-96 bg-[#0f172a] border-l border-slate-700/80 shadow-2xl flex flex-col select-none text-slate-100">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-200 font-mono">
            Incident Postmortem
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-md text-sm"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs font-mono">
        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">
            Incident Record
          </div>
          <div className="font-bold text-sky-400 text-sm">{report.incident_id}</div>
          <div className="text-[11px] text-slate-300 font-sans mt-1 leading-snug">
            {report.title}
          </div>
        </div>

        {/* Root Cause with Graph Link */}
        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-1.5 flex items-center gap-1">
            <Zap className="w-3 h-3 text-rose-400" /> Confirmed Root Cause
          </div>
          <div
            onClick={() => onSelectNode?.(report.root_cause)}
            className="flex items-center justify-between p-2 rounded bg-rose-950/40 border border-rose-800/80 text-rose-200 font-bold cursor-pointer hover:bg-rose-900/40 transition-colors"
          >
            <span>{report.root_cause}</span>
            <ExternalLink className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <span className="text-[10px] text-slate-500 block mt-1">
            Click to focus node on topology graph
          </span>
        </div>

        {/* Paged Engineer */}
        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-1.5 flex items-center gap-1">
            <Users className="w-3 h-3 text-sky-400" /> Engineer Paged (On-Call + History)
          </div>
          <div className="font-semibold text-slate-200 text-sm">
            {report.paged_engineer}
          </div>
        </div>

        {/* Throughput Recovery */}
        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-2 flex items-center gap-1">
            <Gauge className="w-3 h-3 text-emerald-400" /> Capacity Restoration
          </div>
          <div className="flex items-center justify-between text-xs bg-slate-900 p-2 rounded border border-slate-800">
            <span className="text-rose-400 font-bold">{report.initial_capacity_rps.toFixed(0)} rps</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-emerald-400 font-bold">{report.recovered_capacity_rps.toFixed(0)} rps</span>
          </div>
        </div>

        {/* Investigation Metrics */}
        <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-500">Fast Path Used:</span>
            <span className={`font-bold ${report.is_fast_path ? "text-purple-400" : "text-slate-400"}`}>
              {report.is_fast_path ? "YES (-40% steps)" : "NO (Full Exploration)"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Total Tool Steps:</span>
            <span className="font-bold text-slate-200">{report.total_steps}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Remediation Action:</span>
            <span className="font-bold text-emerald-400 uppercase">{report.action_taken}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
