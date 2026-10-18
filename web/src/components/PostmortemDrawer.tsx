"use client";

import React, { useEffect } from "react";
import { X, ArrowRight, Crosshair } from "lucide-react";

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

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2.5">
      <dt className="text-xs text-ink-500">{label}</dt>
      <dd className="text-right text-[13px] text-ink-200">{children}</dd>
    </div>
  );
}

export default function PostmortemDrawer({ isOpen, onClose, report, onSelectNode }: PostmortemDrawerProps) {
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, onClose]);

  if (!isOpen || !report) return null;

  const recovered = report.recovered_capacity_rps;
  const initial = report.initial_capacity_rps;
  const gainPct = initial > 0 ? Math.round(((recovered - initial) / initial) * 100) : null;

  return (
    <aside
      role="dialog"
      aria-label="Incident postmortem"
      className="slide-in-right fixed inset-y-0 right-0 z-drawer flex w-[400px] flex-col border-l border-ink-700/60 bg-ink-850 shadow-[-24px_0_64px_-16px_rgba(5,7,10,0.8)]"
    >
      <div className="flex items-start justify-between px-6 pb-5 pt-6">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-2xs">
            <span className="h-1.5 w-1.5 rounded-full bg-ok" />
            <span className="font-medium text-ok">Resolved</span>
            <span className="font-mono text-ink-500">{report.incident_id}</span>
          </div>
          <h3 className="mt-2 text-lg font-semibold leading-snug tracking-[-0.02em] text-ink-100 [text-wrap:balance]">
            {report.title}
          </h3>
        </div>
        <button
          onClick={onClose}
          aria-label="Close postmortem"
          className="-mr-2 rounded-md p-1.5 text-ink-500 transition-colors duration-200 hover:bg-ink-800 hover:text-ink-200"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto px-6 pb-8">
        {/* Root cause */}
        <section>
          <div className="mb-2 text-xs text-ink-500">Root cause</div>
          <button
            onClick={() => onSelectNode?.(report.root_cause)}
            className="group flex w-full items-center justify-between rounded-xl bg-crit-dim px-4 py-3 text-left transition-colors duration-200 hover:bg-crit/20"
          >
            <span className="font-mono text-[15px] font-medium text-crit">{report.root_cause}</span>
            <span className="flex items-center gap-1 text-2xs text-crit/80">
              <Crosshair className="h-3.5 w-3.5" />
              Show on graph
            </span>
          </button>
        </section>

        {/* Capacity */}
        <section>
          <div className="mb-2 text-xs text-ink-500">Checkout capacity</div>
          <div className="flex items-end gap-4 rounded-xl bg-ink-900 px-4 py-4">
            <div>
              <div className="font-mono text-2xl font-medium leading-none tracking-tight text-crit tabular">{initial.toFixed(0)}</div>
              <div className="mt-1 text-2xs text-ink-500">during incident</div>
            </div>
            <ArrowRight className="mb-5 h-4 w-4 text-ink-600" />
            <div>
              <div className="font-mono text-2xl font-medium leading-none tracking-tight text-ok tabular">{recovered.toFixed(0)}</div>
              <div className="mt-1 text-2xs text-ink-500">after remediation</div>
            </div>
            {gainPct !== null && (
              <div className="ml-auto mb-5 font-mono text-xs text-ink-400 tabular">+{gainPct}%</div>
            )}
          </div>
          <div className="mt-1.5 text-right text-2xs text-ink-500">rps, computed with algo.maxFlow</div>
        </section>

        {/* Details */}
        <section>
          <dl className="divide-y divide-ink-800 border-y border-ink-800">
            <Row label="Engineer paged">{report.paged_engineer}</Row>
            <Row label="Action taken">
              <span className="font-mono text-ok">{report.action_taken}</span>
            </Row>
            <Row label="Tool steps">
              <span className="font-mono tabular">{report.total_steps}</span>
            </Row>
            <Row label="Investigation path">
              {report.is_fast_path ? (
                <span className="text-focus">Fast path from memory</span>
              ) : (
                <span className="text-ink-400">Full exploration</span>
              )}
            </Row>
          </dl>
        </section>
      </div>
    </aside>
  );
}
