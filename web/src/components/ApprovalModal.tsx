"use client";

import React, { useEffect } from "react";

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

export default function ApprovalModal({ isOpen, actionPlan, onApprove, onReject }: ApprovalModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onReject();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, onReject]);

  if (!isOpen || !actionPlan) return null;

  return (
    <div className="fixed inset-0 z-modal flex items-center justify-center bg-ink-950/80 p-4 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-title"
        className="rise-in w-full max-w-md overflow-hidden rounded-2xl border border-ink-700/60 bg-ink-850 shadow-[0_24px_64px_-16px_rgba(5,7,10,0.9)]"
      >
        <div className="px-6 pb-4 pt-6">
          <div className="text-2xs font-medium text-warn">Approval required</div>
          <h3 id="approval-title" className="mt-1 text-lg font-semibold tracking-[-0.02em] text-ink-100">
            <span className="font-mono">{actionPlan.action}</span> on{" "}
            <span className="font-mono">{actionPlan.target_node}</span>
          </h3>
          <p className="mt-2 max-w-[60ch] text-[13px] leading-relaxed text-ink-300 [text-wrap:pretty]">{actionPlan.rationale}</p>
        </div>

        <div className="px-6 pb-5">
          <div className="mb-1.5 text-2xs text-ink-500">Parameters</div>
          <pre className="overflow-x-auto rounded-lg bg-ink-950 p-3 font-mono text-2xs leading-relaxed text-ink-300">
            {JSON.stringify(actionPlan.parameters, null, 2)}
          </pre>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-ink-800 bg-ink-900/60 px-6 py-4">
          <button
            onClick={onReject}
            className="rounded-lg px-3.5 py-2 text-[13px] text-ink-300 transition-colors duration-200 hover:bg-ink-800 hover:text-ink-100"
          >
            Reject
          </button>
          <button
            onClick={onApprove}
            autoFocus
            className="rounded-lg bg-ink-100 px-4 py-2 text-[13px] font-medium text-ink-950 transition-[background-color,transform] duration-200 hover:bg-white active:scale-[0.98]"
          >
            Approve and execute
          </button>
        </div>
      </div>
    </div>
  );
}
