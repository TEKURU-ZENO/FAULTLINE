"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import GraphCanvas, { GraphNode, GraphEdge } from "@/components/GraphCanvas";
import ImpactMeters from "@/components/ImpactMeters";
import ReasoningFeed, { InvestigationStep } from "@/components/ReasoningFeed";
import ChaosRail from "@/components/ChaosRail";
import ApprovalModal from "@/components/ApprovalModal";
import PostmortemDrawer from "@/components/PostmortemDrawer";

const API_BASE = "http://localhost:8000";

export default function DashboardPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [survivingCapacity, setSurvivingCapacity] = useState<number>(1200);
  const [nominalCapacity, setNominalCapacity] = useState<number>(1200);
  const [blastRadiusCount, setBlastRadiusCount] = useState<number>(0);
  const [activeTenant, setActiveTenant] = useState<string>("tenant:demo");
  const [incidentStatus, setIncidentStatus] = useState<"healthy" | "firing" | "investigating" | "resolved">("healthy");
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  
  const [steps, setSteps] = useState<InvestigationStep[]>([]);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [pulsedNodes, setPulsedNodes] = useState<string[]>([]);
  const [highlightedPath, setHighlightedPath] = useState<string[]>([]);

  const [approvalModalOpen, setApprovalModalOpen] = useState<boolean>(false);
  const [pendingPlan, setPendingPlan] = useState<any>(null);

  const [postmortemOpen, setPostmortemOpen] = useState<boolean>(false);
  const [postmortemReport, setPostmortemReport] = useState<any>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Fetch graph topology
  const fetchGraph = useCallback(async (tenant: string = activeTenant) => {
    try {
      const res = await fetch(`${API_BASE}/api/graph?tenant=${tenant}`);
      if (!res.ok) return;
      const data = await res.json();
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
      setSurvivingCapacity(data.surviving_capacity || 1200);
      setNominalCapacity(data.nominal_capacity || 1200);

      // Check if alerts exist
      const alerting = (data.nodes || []).filter((n: GraphNode) => n.state === "alerting");
      if (alerting.length > 0) {
        setIncidentStatus("firing");
      }
    } catch (e) {
      console.error("Failed to load graph:", e);
    }
  }, [activeTenant]);

  useEffect(() => {
    fetchGraph(activeTenant);
  }, [fetchGraph, activeTenant]);

  // 2. Setup Server-Sent Events (SSE) Stream
  useEffect(() => {
    const sse = new EventSource(`${API_BASE}/api/events`);

    sse.addEventListener("step", (event: MessageEvent) => {
      const payload = JSON.parse(event.data);
      const data = payload.data;
      
      setSteps((prev) => [
        ...prev,
        {
          step_idx: data.step_idx,
          agent: "agent",
          log: data.log,
          cypher: data.cypher,
          duration_ms: data.duration_ms,
        },
      ]);

      // Pulse nodes mentioned in log
      if (data.confirmed_root_cause) {
        setPulsedNodes([data.confirmed_root_cause]);
        setHighlightedPath(["frontend", "checkoutservice", data.confirmed_root_cause]);
      }
    });

    sse.addEventListener("fault_injected", () => {
      setIncidentStatus("firing");
      setElapsedSeconds(0);
      fetchGraph();
      if (!timerRef.current) {
        timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
      }
    });

    sse.addEventListener("system_healed", () => {
      setIncidentStatus("healthy");
      setHighlightedPath([]);
      setPulsedNodes([]);
      setSteps([]);
      fetchGraph();
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setElapsedSeconds(0);
    });

    sse.addEventListener("postmortem", (event: MessageEvent) => {
      const payload = JSON.parse(event.data);
      setPostmortemReport(payload.data);
      setPostmortemOpen(true);
      setIncidentStatus("resolved");
      setIsInvestigating(false);
      fetchGraph();
    });

    return () => {
      sse.close();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchGraph]);

  // 3. Keyboard Shortcut 'i' to Inject Demo Fault
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "i" && !e.metaKey && !e.ctrlKey) {
        handleInject(1);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Handlers
  const handleInject = async (faultId: number) => {
    try {
      await fetch(`${API_BASE}/api/chaos/inject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fault_id: faultId, tenant: activeTenant }),
      });
      fetchGraph();
    } catch (e) {
      console.error(e);
    }
  };

  const handleHeal = async () => {
    try {
      await fetch(`${API_BASE}/api/chaos/heal`, { method: "POST" });
      fetchGraph();
    } catch (e) {
      console.error(e);
    }
  };

  const handleInvestigate = async (autoApprove: boolean) => {
    setIsInvestigating(true);
    setIncidentStatus("investigating");
    setSteps([]);
    try {
      await fetch(`${API_BASE}/api/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant: activeTenant, auto_approve: autoApprove }),
      });
    } catch (e) {
      console.error(e);
      setIsInvestigating(false);
    }
  };

  const activeAlertCount = nodes.filter((n) => n.state === "alerting").length;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#080c14] text-slate-100">
      {/* Top Strip: Impact Meters */}
      <ImpactMeters
        survivingCapacity={survivingCapacity}
        nominalCapacity={nominalCapacity}
        blastRadiusCount={blastRadiusCount || (activeAlertCount > 0 ? 3 : 0)}
        activeAlertCount={activeAlertCount}
        incidentStatus={incidentStatus}
        elapsedSeconds={elapsedSeconds}
      />

      {/* Main 3-Pane Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Chaos & Controls Rail */}
        <ChaosRail
          onInject={handleInject}
          onHeal={handleHeal}
          onInvestigate={handleInvestigate}
          onTenantChange={(t) => {
            setActiveTenant(t);
            fetchGraph(t);
          }}
          activeTenant={activeTenant}
          isInvestigating={isInvestigating}
          onOpenPostmortem={() => setPostmortemOpen(true)}
          hasPostmortem={!!postmortemReport}
        />

        {/* Center: Live Topology & Causal Path Graph */}
        <main className="flex-1 h-full p-4 flex flex-col min-w-0 bg-[#080c14]">
          <div className="flex-1 w-full h-full relative">
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              pulsedNodes={pulsedNodes}
              highlightedPath={highlightedPath}
              onNodeClick={(node) => setPulsedNodes([node.name])}
            />
          </div>
        </main>

        {/* Right: Agent Reasoning Feed */}
        <ReasoningFeed
          steps={steps}
          isInvestigating={isInvestigating}
          onStepSelect={(cited) => setPulsedNodes(cited)}
        />
      </div>

      {/* Human Approval Modal */}
      <ApprovalModal
        isOpen={approvalModalOpen}
        actionPlan={pendingPlan}
        onApprove={() => setApprovalModalOpen(false)}
        onReject={() => setApprovalModalOpen(false)}
      />

      {/* Evidence-Linked Postmortem Drawer */}
      <PostmortemDrawer
        isOpen={postmortemOpen}
        onClose={() => setPostmortemOpen(false)}
        report={postmortemReport}
        onSelectNode={(name) => setPulsedNodes([name])}
      />
    </div>
  );
}
