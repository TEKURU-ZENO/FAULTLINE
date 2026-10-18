"use client";

import React, { useState, useMemo } from "react";
import { X } from "lucide-react";

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
  loadState?: "loading" | "offline" | "ready";
  onRetry?: () => void;
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

// Deterministic fallback so unknown nodes don't jump between renders
function fallbackCoord(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return { x: 400 + (h % 200), y: 300 + ((h >>> 8) % 200) };
}

const C = {
  crit: "#e5534b",
  warn: "#d9a440",
  ok: "#57ab5a",
  anom: "#d9774b",
  focus: "#7fb2e5",
  edge: "#232a32",
  flow: "#535d69",
  nodeFill: "#13171c",
  nodeStroke: "#535d69",
  label: "#7b8590",
};

const STATE_TEXT: Record<GraphNode["state"], string> = {
  healthy: "text-ok",
  degraded: "text-warn",
  alerting: "text-crit",
  anomalous: "text-anom",
};

function nodeColor(node: GraphNode) {
  if (node.state === "alerting") return C.crit;
  if (node.state === "anomalous") return C.anom;
  if (node.state === "degraded") return C.warn;
  return C.nodeStroke;
}

function NodeShape({ node, x, y, stroke, strokeWidth, fill }: { node: GraphNode; x: number; y: number; stroke: string; strokeWidth: number; fill: string }) {
  // Shape encodes kind; color is reserved for state
  if (node.label === "Database" || node.label === "Queue") {
    return <rect x={x - 12} y={y - 12} width={24} height={24} rx={6} fill={fill} stroke={stroke} strokeWidth={strokeWidth} />;
  }
  if (node.label === "Pod" || node.label === "Node") {
    return (
      <path
        d={`M ${x} ${y - 11} L ${x + 10} ${y - 5.5} L ${x + 10} ${y + 5.5} L ${x} ${y + 11} L ${x - 10} ${y + 5.5} L ${x - 10} ${y - 5.5} Z`}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinejoin="round"
      />
    );
  }
  return <circle cx={x} cy={y} r={11} fill={fill} stroke={stroke} strokeWidth={strokeWidth} />;
}

export default function GraphCanvas({
  nodes,
  edges,
  pulsedNodes = [],
  highlightedPath = [],
  onNodeClick,
  loadState = "ready",
  onRetry,
}: GraphCanvasProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  const positionedNodes = useMemo(
    () =>
      nodes.map((node) => {
        const coord = NODE_LAYOUT[node.name] || fallbackCoord(node.name);
        return { ...node, x: coord.x, y: coord.y };
      }),
    [nodes]
  );

  const nodeMap = useMemo(() => {
    const map = new Map<string, GraphNode & { x: number; y: number }>();
    positionedNodes.forEach((n) => map.set(n.name, n));
    return map;
  }, [positionedNodes]);

  const neighbors = useMemo(() => {
    if (!hovered) return null;
    const set = new Set<string>([hovered]);
    edges.forEach((e) => {
      if (e.source === hovered) set.add(e.target);
      if (e.target === hovered) set.add(e.source);
    });
    return set;
  }, [hovered, edges]);

  const isEdgeInPath = (src: string, dst: string) => {
    for (let i = 0; i < highlightedPath.length - 1; i++) {
      const a = highlightedPath[i];
      const b = highlightedPath[i + 1];
      if ((a === src && b === dst) || (a === dst && b === src)) return true;
    }
    return false;
  };

  const selectNode = (node: GraphNode) => {
    setSelectedNode(node);
    onNodeClick?.(node);
  };

  // Keep the inspector in sync with fresh backend state
  const liveSelected = selectedNode ? nodeMap.get(selectedNode.name) ?? selectedNode : null;

  return (
    <div className="relative h-full w-full select-none overflow-hidden rounded-xl bg-ink-900">
      {/* Ambient vignette so the canvas has depth */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: "radial-gradient(ellipse 70% 60% at 50% 45%, #13171c 0%, #0f1216 60%, #0a0c0f 100%)" }}
        aria-hidden
      />

      <div className="absolute left-5 top-4 z-10">
        <h2 className="text-[13px] font-medium text-ink-200">Live topology</h2>
        <p className="text-2xs text-ink-500">OpenTelemetry Astronomy Shop · {nodes.length} nodes</p>
      </div>

      {loadState !== "ready" && nodes.length === 0 ? (
        <div className="relative flex h-full items-center justify-center">
          {loadState === "loading" ? (
            <div className="grid grid-cols-6 gap-6 opacity-70" aria-label="Loading topology">
              {Array.from({ length: 18 }).map((_, i) => (
                <div key={i} className="skeleton h-6 w-6 rounded-full" style={{ animationDelay: `${i * 60}ms` }} />
              ))}
            </div>
          ) : (
            <div className="max-w-sm text-center">
              <p className="text-sm font-medium text-ink-200">Can&apos;t reach the FAULTLINE API</p>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-500 [text-wrap:pretty]">
                The dashboard expects the API on <span className="font-mono text-ink-300">localhost:8000</span>. Start it
                with <span className="font-mono text-ink-300">make api</span> or{" "}
                <span className="font-mono text-ink-300">docker compose up</span>, then retry.
              </p>
              <button
                onClick={onRetry}
                className="mt-4 rounded-lg bg-ink-800 px-3.5 py-1.5 text-xs font-medium text-ink-200 transition-[background-color,transform] duration-200 hover:bg-ink-700 active:scale-[0.98]"
              >
                Retry connection
              </button>
            </div>
          )}
        </div>
      ) : (
        <svg className="relative h-full w-full" viewBox="0 0 840 680" role="img" aria-label="Service dependency graph">
          <defs>
            <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="0.8" fill="#191e24" />
            </pattern>
            <filter id="soft-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <rect width="100%" height="100%" fill="url(#dots)" />

          {/* Edges */}
          <g>
            {edges.map((edge, idx) => {
              const s = nodeMap.get(edge.source);
              const t = nodeMap.get(edge.target);
              if (!s || !t) return null;

              const inPath = isEdgeInPath(edge.source, edge.target);
              const isFlow = edge.type === "FLOWS_TO";
              const isCapacityDown = isFlow && edge.capacity_rps > 0 && edge.live_rps < edge.capacity_rps;
              const dimmed = neighbors && !(neighbors.has(edge.source) && neighbors.has(edge.target));

              const stroke = inPath ? C.crit : isCapacityDown ? C.warn : isFlow ? C.flow : C.edge;

              return (
                <line
                  key={`edge-${idx}`}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={stroke}
                  strokeWidth={inPath ? 2.5 : isFlow ? 1.5 : 1}
                  strokeDasharray={isFlow && !inPath ? "4 4" : undefined}
                  strokeOpacity={dimmed ? 0.15 : inPath ? 1 : isFlow ? 0.9 : 0.8}
                  strokeLinecap="round"
                  className={isFlow && !inPath ? "flow-dash" : undefined}
                  filter={inPath ? "url(#soft-glow)" : undefined}
                  style={{ transition: "stroke-opacity 200ms" }}
                />
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {positionedNodes.map((node) => {
              const isPulsed = pulsedNodes.includes(node.name);
              const isAlerting = node.state === "alerting";
              const isSelected = liveSelected?.name === node.name;
              const dimmed = neighbors && !neighbors.has(node.name);
              const color = nodeColor(node);
              const active = isPulsed || isSelected;
              const flagged = node.state !== "healthy";

              return (
                <g
                  key={node.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`${node.name}, ${node.state}`}
                  className="cursor-pointer outline-none"
                  style={{ opacity: dimmed ? 0.3 : 1, transition: "opacity 200ms" }}
                  onClick={() => selectNode(node)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      selectNode(node);
                    }
                  }}
                  onMouseEnter={() => setHovered(node.name)}
                  onMouseLeave={() => setHovered(null)}
                  onFocus={() => setHovered(node.name)}
                  onBlur={() => setHovered(null)}
                >
                  {isAlerting && <circle cx={node.x} cy={node.y} r="16" fill="none" stroke={C.crit} strokeWidth="1.5" className="pulse-ring" />}
                  {isPulsed && <circle cx={node.x} cy={node.y} r="18" fill="none" stroke={C.focus} strokeWidth="1.5" className="pulse-ring" />}
                  {active && <circle cx={node.x} cy={node.y} r="18" fill="none" stroke={C.focus} strokeWidth="1.5" strokeOpacity="0.9" />}

                  {/* Larger invisible hit target */}
                  <circle cx={node.x} cy={node.y} r="20" fill="transparent" />

                  <NodeShape
                    node={node}
                    x={node.x}
                    y={node.y}
                    fill={flagged ? `${color}22` : C.nodeFill}
                    stroke={color}
                    strokeWidth={flagged ? 1.75 : 1.25}
                  />
                  {flagged && <circle cx={node.x} cy={node.y} r="3.5" fill={color} />}

                  <text
                    x={node.x}
                    y={node.y + 26}
                    textAnchor="middle"
                    fontSize="9.5"
                    fontWeight={flagged || active ? 500 : 400}
                    fill={isAlerting ? "#f0938d" : active ? C.focus : C.label}
                    className="pointer-events-none font-mono"
                    style={{ letterSpacing: "-0.01em" }}
                  >
                    {node.name}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      )}

      {/* Legend */}
      {nodes.length > 0 && (
        <div className="absolute right-4 top-4 z-10 flex flex-col gap-1.5 rounded-lg bg-ink-950/70 px-3 py-2.5 text-2xs text-ink-400 backdrop-blur">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-crit" />Alerting</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-anom" />Anomalous</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-warn" />Degraded</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full border border-ink-400" />Service</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] border border-ink-400" />Store</span>
            <span className="flex items-center gap-1.5">
              <svg width="9" height="10" viewBox="0 0 9 10" aria-hidden><path d="M4.5 0.5 L8.5 2.75 L8.5 7.25 L4.5 9.5 L0.5 7.25 L0.5 2.75 Z" fill="none" stroke="#7b8590" /></svg>
              Compute
            </span>
            <span className="flex items-center gap-1.5">
              <svg width="16" height="2" aria-hidden><line x1="0" y1="1" x2="16" y2="1" stroke={C.flow} strokeWidth="1.5" strokeDasharray="3 3" /></svg>
              Checkout flow
            </span>
          </div>
        </div>
      )}

      {/* Node inspector */}
      {liveSelected && (
        <div className="slide-in-right absolute bottom-4 left-4 z-flyout w-72 rounded-xl border border-ink-700/60 bg-ink-850/95 p-4 text-xs shadow-[0_16px_48px_-12px_rgba(5,7,10,0.8)] backdrop-blur">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate font-mono text-[13px] font-medium text-ink-100">{liveSelected.name}</div>
              <div className="mt-0.5 text-2xs text-ink-500">
                {liveSelected.label} · {liveSelected.tier}
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              aria-label="Close inspector"
              className="-mr-1 -mt-1 rounded-md p-1 text-ink-500 transition-colors duration-200 hover:bg-ink-800 hover:text-ink-200"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-ink-800 pt-3">
            <span className="text-ink-500">State</span>
            <span className={`font-medium capitalize ${STATE_TEXT[liveSelected.state]}`}>{liveSelected.state}</span>
          </div>

          {liveSelected.alerts.length > 0 && (
            <div className="mt-3">
              <div className="mb-1.5 text-ink-500">Firing alerts</div>
              <ul className="space-y-1">
                {liveSelected.alerts.map((a, i) => (
                  <li key={i} className="rounded-md bg-crit-dim px-2 py-1 font-mono text-2xs text-crit">{a}</li>
                ))}
              </ul>
            </div>
          )}

          {liveSelected.anomalies.length > 0 && (
            <div className="mt-3">
              <div className="mb-1.5 text-ink-500">Anomalies</div>
              <ul className="space-y-1">
                {liveSelected.anomalies.map((an, i) => (
                  <li key={i} className="rounded-md bg-anom-dim px-2 py-1 font-mono text-2xs text-anom">{an}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
