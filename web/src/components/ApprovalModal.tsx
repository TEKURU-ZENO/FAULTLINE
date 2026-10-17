"use client";

import React from "react";
import { ShieldCheck, AlertCircle, Check, X } from "lucide-react";

interface ApprovalModalProps {
  isOpen: boolean;
  actionPlan: {
    action: string;
    target_node: string;
    parameters: Record<string, any>;
    rationale: string;
  } | null;
  onApprove: () => void;
  onReject: () => void;
}

export default function ApprovalModal({
  isOpen,
  actionPlan,
  onApprove,
  onReject,
}: ApprovalModalProps) {
  if (!isOpen || !actionPlan) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#0f172a] border border-slate-700/80 rounded-xl shadow-2xl overflow-hidden text-slate-100">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-slate-100 font-mono">
              Remediation Approval Required
            </h3>
            <p className="text-[11px] text-slate-400 font-mono">
              Human-in-the-loop safety gate
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs font-mono">
          <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Proposed Action:</span>
              <span className="font-bold text-sky-400 uppercase">{actionPlan.action}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Target Node:</span>
              <span className="font-bold text-slate-200">{actionPlan.target_node}</span>
            </div>
            <div className="pt-2 border-t border-slate-800/80">
              <span className="text-slate-500 block mb-1">Parameters:</span>
              <pre className="p-2 bg-[#080c14] rounded text-[11px] text-slate-300 overflow-x-auto">
                {JSON.stringify(actionPlan.parameters, null, 2)}
              </pre>
            </div>
          </div>

          <div className="flex items-start gap-2 text-slate-300 text-[11px] font-sans">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>{actionPlan.rationale}</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40 flex items-center justify-end gap-2.5">
          <button
            onClick={onReject}
            className="px-4 py-2 rounded-lg border border-slate-700 bg-slate-800/60 hover:bg-slate-700 text-slate-300 text-xs font-mono font-medium flex items-center gap-1.5 transition-colors"
          >
            <X className="w-3.5 h-3.5" /> Reject
          </button>
          <button
            onClick={onApprove}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-950/60 transition-colors"
          >
            <Check className="w-3.5 h-3.5" /> Approve & Execute
          </button>
        </div>
      </div>
    </div>
  );
}
