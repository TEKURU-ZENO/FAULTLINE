"use client";

import React, { useState, useMemo } from "react";
import { Zap, AlertTriangle, Activity, Database, Server, Cpu, Layers } from "lucide-react";

export interface GraphNode {
  id: string;
  name: string;
  label: string;
  tier: string;
  state: "healthy" | "degraded" | "alerting" | "anomalous";
  alerts: string[];
  anomalies: string[];
  x?: number;
  y?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  capacity_rps: number;
  live_rps: number;
  p99_ms: number;
}

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  pulsedNodes?: string[];
  highlightedPath?: string[];
  onNodeClick?: (node: GraphNode) => void;
}

// Hand-tuned coordinates for the 28-node Astronomy Shop topology
// Ensures stable, zero-jitter presentation on camera
const NODE_LAYOUT: Record<string, { x: number; y: number }> = {
  // Edge tier (top-left)
  "frontend-proxy": { x: 80, y: 180 },
  "frontend": { x: 220, y: 180 },

  // Compute / Pods
  "pod-checkout-1": { x: 380, y: 120 },
  "pod-checkout-2": { x: 380, y: 240 },
  "pod-payment-1": { x: 540, y: 120 },
  "pod-cart-1": { x: 380, y: 360 },

  // Core Commerce
  "checkoutservice": { x: 380, y: 180 },
  "paymentservice": { x: 540, y: 180 },
  "productcatalogservice": { x: 380, y: 460 },
  "cartservice": { x: 280, y: 360 },
  "currencyservice": { x: 540, y: 270 },
  "shippingservice": { x: 540, y: 360 },
  "emailservice": { x: 540, y: 440 },
  "accountingservice": { x: 540, y: 530 },
  "frauddetectionservice": { x: 380, y: 560 },

  // Supporting
  "recommendationservice": { x: 220, y: 480 },
  "adservice": { x: 120, y: 360 },
  "quoteservice": { x: 680, y: 360 },
  "imageprovider": { x: 120, y: 480 },
  "payment-gw-ext": { x: 680, y: 180 },
  "flagd": { x: 540, y: 40 },

  // Storage & Queues (right / bottom)
  "orders-pg": { x: 740, y: 260 },
  "catalog-pg": { x: 540, y: 620 },
  "valkey-cart": { x: 180, y: 280 },
  "kafka": { x: 460, y: 460 },

  // K8s Nodes
  "k8s-node-1": { x: 440, y: 70 },
  "k8s-node-2": { x: 440, y: 290 },
  "k8s-node-3": { x: 260, y: 260 },
};

export default function GraphCanvas({
  nodes,
  edges,
  pulsedNodes = [],
  highlightedPath = [],
  onNodeClick,
}: GraphCanvasProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Merge backend nodes with hand-tuned coordinates
  const positionedNodes = useMemo(() => {
    return nodes.map((node) => {
      const coord = NODE_LAYOUT[node.name] || { x: 400 + Math.random() * 200, y: 300 + Math.random() * 200 };
      return {
        ...node,
        x: coord.x,
        y: coord.y,
      };
    });
  }, [nodes]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, GraphNode & { x: number; y: number }>();
    positionedNodes.forEach((n) => map.set(n.name, n));
    return map;
  }, [positionedNodes]);

  const getNodeColor = (node: GraphNode) => {
    if (node.state === "alerting") return "#f43f5e"; // Rose / Red
    if (node.state === "anomalous") return "#c084fc"; // Purple
    if (node.state === "degraded") return "#f59e0b"; // Amber
    if (node.label === "Database") return "#38bdf8"; // Cyan
    if (node.label === "Queue") return "#a855f7"; // Violet
    if (node.label === "Pod") return "#34d399"; // Emerald
    return "#64748b"; // Slate
  };

  const isEdgeInPath = (src: string, dst: string) => {
    if (highlightedPath.length < 2) return false;
    for (let i = 0; i < highlightedPath.length - 1; i++) {
      if (
        (highlightedPath[i] === src && highlightedPath[i + 1] === dst) ||
        (highlightedPath[i] === dst && highlightedPath[i + 1] === src)
      ) {
        return true;
      }
    }
    return false;
  };

  return (
    <div className="relative w-full h-full bg-[#080c14] overflow-hidden select-none border border-slate-800/80 rounded-xl">
      {/* Topology Background Grid */}
      <svg className="w-full h-full" viewBox="0 0 840 680">
        <defs>
          <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#0f172a" strokeWidth="0.8" />
          </pattern>
          <filter id="glow-rose" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-cyan" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* 1. Edges */}
        {edges.map((edge, idx) => {
          const s = nodeMap.get(edge.source);
          const t = nodeMap.get(edge.target);
          if (!s || !t) return null;

          const inPath = isEdgeInPath(edge.source, edge.target);
          const isFlow = edge.type === "FLOWS_TO";
          const isCapacityDown = edge.live_rps < edge.capacity_rps && edge.capacity_rps > 0;

          return (
            <g key={`edge-${idx}`}>
              <line
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke={
                  inPath
                    ? "#f43f5e"
                    : isFlow
                    ? isCapacityDown
                      ? "#f59e0b"
                      : "#38bdf8"
                    : "#1e293b"
                }
                strokeWidth={inPath ? 3.5 : isFlow ? 2.0 : 1.2}
                strokeDasharray={isFlow ? (inPath ? "none" : "5 3") : "none"}
                strokeOpacity={inPath ? 1.0 : isFlow ? 0.8 : 0.45}
                filter={inPath ? "url(#glow-rose)" : undefined}
              />
            </g>
          );
        })}

        {/* 2. Nodes */}
        {positionedNodes.map((node) => {
          const isPulsed = pulsedNodes.includes(node.name);
          const isAlerting = node.state === "alerting";
          const isAnomalous = node.state === "anomalous";
          const isDegraded = node.state === "degraded";
          const color = getNodeColor(node);

          return (
            <g
              key={node.id}
              className="cursor-pointer transition-transform duration-200"
              onClick={() => {
                setSelectedNode(node);
                onNodeClick?.(node);
              }}
            >
              {/* Alert pulsing halo */}
              {isAlerting && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="18"
                  fill="none"
                  stroke="#f43f5e"
                  strokeWidth="2"
                  className="pulse-ring-alert"
                />
              )}

              {/* Active Agent Inspection Pulse */}
              {isPulsed && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="22"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2.5"
                  className="pulse-ring-alert"
                  filter="url(#glow-cyan)"
                />
              )}

              {/* Base Node Circle */}
              <circle
                cx={node.x}
                cy={node.y}
                r={node.label === "Database" || node.label === "Queue" ? 14 : 12}
                fill={isAlerting ? "#1e131d" : isAnomalous ? "#1b1429" : "#0f172a"}
                stroke={color}
                strokeWidth={isAlerting || isPulsed ? 2.5 : 1.5}
                className={isPulsed ? "pulse-active" : ""}
              />

              {/* Inner Glyph / Status Dot */}
              <circle
                cx={node.x}
                cy={node.y}
                r="4.5"
                fill={color}
              />

              {/* Node Name Label */}
              <text
                x={node.x}
                y={(node.y || 0) + 24}
                textAnchor="middle"
                fontSize="10"
                fontWeight="500"
                fill={isAlerting ? "#fda4af" : isPulsed ? "#38bdf8" : "#94a3b8"}
                className="pointer-events-none tracking-tight font-mono"
              >
                {node.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Selected Node Inspector Flyout */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 p-4 bg-slate-900/90 backdrop-blur border border-slate-700/80 rounded-lg w-72 shadow-2xl z-20 text-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <span className="font-semibold text-slate-100 flex items-center gap-1.5 font-mono">
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              {selectedNode.name}
            </span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-slate-200 text-sm font-mono"
            >
              ×
            </button>
          </div>
          <div className="space-y-1.5 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Label:</span>
              <span className="font-mono text-slate-300">{selectedNode.label}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Tier:</span>
              <span className="font-mono text-slate-300">{selectedNode.tier}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Status:</span>
              <span
                className={`font-semibold capitalize ${
                  selectedNode.state === "alerting"
                    ? "text-rose-400"
                    : selectedNode.state === "anomalous"
                    ? "text-purple-400"
                    : selectedNode.state === "degraded"
                    ? "text-amber-400"
                    : "text-emerald-400"
                }`}
              >
                {selectedNode.state}
              </span>
            </div>

            {selectedNode.alerts.length > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-800">
                <span className="text-rose-400 font-semibold flex items-center gap-1 mb-1">
                  <AlertTriangle className="w-3 h-3" /> Firing Alerts:
                </span>
                <div className="space-y-0.5">
                  {selectedNode.alerts.map((a, i) => (
                    <div key={i} className="text-rose-300 font-mono text-[11px] bg-rose-950/40 px-1.5 py-0.5 rounded">
                      {a}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedNode.anomalies.length > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-800">
                <span className="text-purple-400 font-semibold flex items-center gap-1 mb-1">
                  <Zap className="w-3 h-3" /> Anomalies:
                </span>
                <div className="space-y-0.5">
                  {selectedNode.anomalies.map((an, i) => (
                    <div key={i} className="text-purple-300 font-mono text-[11px] bg-purple-950/40 px-1.5 py-0.5 rounded">
                      {an}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
