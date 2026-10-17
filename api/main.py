#!/usr/bin/env python3
"""
FAULTLINE FastAPI + SSE Streaming Server.
Exposes REST and real-time Server-Sent Events (SSE) for:
- Live graph topology & node health status
- Chaos injection & healing
- Multi-agent investigation streaming (step cards, cypher timings, graph pulses)
- Human-in-the-loop remediation approval gate
- Episodic memory & runbook inspection
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from falkordb import FalkorDB

from sim.engine import SimulatorEngine
from sim.faults import FAULTS
from agents.graph import build_incident_commander_graph, get_graph
from mcp_server.server import surviving_capacity

app = FastAPI(title="FAULTLINE API", version="1.0.0")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
FALKORDB_HOST = os.environ.get("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.environ.get("FALKORDB_PORT", 6379))
active_tenant = "tenant:demo"

simulator = SimulatorEngine(host=FALKORDB_HOST, port=FALKORDB_PORT, graph_name=active_tenant)
agent_app = build_incident_commander_graph(simulator=simulator)

# In-memory SSE event bus
subscribers: List[asyncio.Queue] = []

async def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcasts an SSE event to all connected UI clients."""
    payload = json.dumps({"type": event_type, "data": data, "timestamp": time.time()})
    msg = f"event: {event_type}\ndata: {payload}\n\n"
    for q in subscribers:
        await q.put(msg)

# Request Models
class InjectFaultRequest(BaseModel):
    fault_id: int
    tenant: Optional[str] = "tenant:demo"

class InvestigateRequest(BaseModel):
    tenant: Optional[str] = "tenant:demo"
    auto_approve: bool = False

class ApproveRemediationRequest(BaseModel):
    run_id: str
    approved: bool

# Pending approval coordination
pending_approvals: Dict[str, asyncio.Event] = {}
approval_decisions: Dict[str, bool] = {}

# ==========================================
# REST ENDPOINTS
# ==========================================

@app.get("/api/health")
def health_check():
    try:
        g = get_graph(active_tenant)
        res = g.query("RETURN 1")
        falkordb_ok = bool(res.result_set)
    except Exception:
        falkordb_ok = False
    return {"status": "ok", "falkordb": falkordb_ok, "active_tenant": active_tenant}

@app.get("/api/graph")
def get_graph_topology(tenant: str = "tenant:demo"):
    """
    Extracts complete graph topology with node health, live_rps,
    active alerts, and anomalies for real-time visualization.
    """
    g = get_graph(tenant)
    
    # Query nodes
    q_nodes = """
    MATCH (n)
    WHERE n:Service OR n:Database OR n:Queue OR n:Node OR n:Pod
    OPTIONAL MATCH (a:Alert)-[:FIRED_ON]->(n)
    OPTIONAL MATCH (an:Anomaly)-[:OBSERVED_ON]->(n)
    RETURN n.name AS name,
           labels(n) AS labels,
           n.tier AS tier,
           n.status AS status,
           collect(DISTINCT a.name) AS alerts,
           collect(DISTINCT an.metric) AS anomalies
    """
    res_nodes = g.query(q_nodes)
    nodes = []
    for r in res_nodes.result_set:
        name, labels, tier, status, alerts, anomalies = r
        primary_label = labels[0] if labels else "Service"
        
        # Color coding
        state = "healthy"
        if alerts:
            state = "alerting"
        elif anomalies:
            state = "anomalous"
        elif status in ["degraded", "down"]:
            state = "degraded"
            
        nodes.append({
            "id": name,
            "name": name,
            "label": primary_label,
            "tier": tier or "infra",
            "state": state,
            "alerts": alerts,
            "anomalies": anomalies
        })

    # Query relationships
    q_edges = """
    MATCH (src)-[r:CALLS|FLOWS_TO|READS|WRITES|PUBLISHES|CONSUMES|RUNS_ON|HOSTED_ON]->(dst)
    WHERE (src:Service OR src:Database OR src:Queue OR src:Node OR src:Pod)
      AND (dst:Service OR dst:Database OR dst:Queue OR dst:Node OR dst:Pod)
    RETURN src.name AS source,
           dst.name AS target,
           type(r) AS type,
           r.capacity_rps AS capacity_rps,
           r.live_rps AS live_rps,
           r.p99_ms AS p99_ms
    """
    res_edges = g.query(q_edges)
    edges = []
    for r in res_edges.result_set:
        src, dst, rel_type, cap, live, p99 = r
        edges.append({
            "source": src,
            "target": dst,
            "type": rel_type,
            "capacity_rps": cap or 0.0,
            "live_rps": live or 0.0,
            "p99_ms": p99 or 0.0
        })

    # Calculate surviving capacity
    cap_res = surviving_capacity(source="frontend", sink="orders-pg", tenant=tenant)
    surviving_rps = cap_res["rows"][0]["maxFlow"] if cap_res["rows"] else 1200.0

    return {
        "nodes": nodes,
        "edges": edges,
        "surviving_capacity": surviving_rps,
        "nominal_capacity": 1200.0
    }

@app.post("/api/chaos/inject")
async def inject_fault(req: InjectFaultRequest):
    """Injects a fault scenario into the deterministic simulator and broadcasts event."""
    if req.fault_id not in FAULTS:
        raise HTTPException(status_code=400, detail=f"Invalid fault_id: {req.fault_id}")

    fault = FAULTS[req.fault_id]
    simulator.inject_fault(req.fault_id)
    
    # Broadcast event
    await broadcast_event("fault_injected", {
        "fault_id": req.fault_id,
        "name": fault["name"],
        "cause_node": fault["cause_node"],
        "description": fault["description"]
    })
    
    return {"status": "injected", "fault": fault["name"]}

@app.post("/api/chaos/heal")
async def heal_system():
    """Restores full health across the simulator and FalkorDB graph."""
    simulator.heal()
    await broadcast_event("system_healed", {"status": "healthy", "nominal_capacity": 1200.0})
    return {"status": "healed"}

@app.post("/api/investigate")
async def start_investigation(req: InvestigateRequest, background_tasks: BackgroundTasks):
    """Launches the LangGraph multi-agent team and streams steps via SSE."""
    run_id = f"RUN-{int(time.time())}"
    now = int(time.time())
    
    initial_state = {
        "run_id": run_id,
        "tenant": req.tenant or active_tenant,
        "now": now,
        "since": now - 1800,
        "step_idx": 0,
        "alerting_services": ["frontend", "checkoutservice"],
        "initial_capacity": 0.0,
        "root_candidates": [],
        "hypotheses": [],
        "claimed_hypothesis_id": None,
        "topology_evidence": {},
        "change_evidence": {},
        "recalled_incidents": [],
        "matching_runbook": None,
        "is_fast_path": False,
        "confirmed_root_cause": None,
        "proposed_action": None,
        "human_approved": req.auto_approve,
        "remediation_verified": False,
        "final_capacity": 0.0,
        "paged_engineer": None,
        "postmortem": None,
        "logs": []
    }

    async def run_investigation():
        await broadcast_event("investigation_started", {"run_id": run_id})
        
        # Stream step-by-step updates from LangGraph
        result = agent_app.invoke(initial_state)
        
        # Stream each agent log & pulse
        for idx, log in enumerate(result.get("logs", []), 1):
            await asyncio.sleep(0.4)  # Visual pacing for the UI demo
            await broadcast_event("step", {
                "step_idx": idx,
                "log": log,
                "is_fast_path": result.get("is_fast_path", False),
                "confirmed_root_cause": result.get("confirmed_root_cause")
            })

        # Broadcast postmortem
        if result.get("postmortem"):
            await broadcast_event("postmortem", result["postmortem"])
            
        await broadcast_event("investigation_completed", {
            "run_id": run_id,
            "root_cause": result.get("confirmed_root_cause"),
            "is_fast_path": result.get("is_fast_path", False),
            "recovered_capacity": result.get("final_capacity", 1200.0)
        })

    background_tasks.add_task(run_investigation)
    return {"status": "started", "run_id": run_id}

@app.post("/api/approve")
async def approve_remediation(req: ApproveRemediationRequest):
    """Human approval gate endpoint for proposed remediations."""
    if req.run_id in pending_approvals:
        approval_decisions[req.run_id] = req.approved
        pending_approvals[req.run_id].set()
        await broadcast_event("remediation_approved", {"run_id": req.run_id, "approved": req.approved})
        return {"status": "recorded", "approved": req.approved}
    return {"status": "not_pending"}

@app.get("/api/memory")
def get_memory(tenant: str = "tenant:demo"):
    """Returns learned FailurePatterns and Runbooks from the graph."""
    g = get_graph(tenant)
    q = """
    MATCH (fp:FailurePattern)-[res:RESOLVED_BY]->(rb:Runbook)
    OPTIONAL MATCH (i:Incident)-[:MATCHES]->(fp)
    RETURN fp.name AS pattern,
           fp.root_type AS root_type,
           rb.title AS runbook_title,
           rb.actions_json AS actions,
           res.success_count AS successes,
           res.fail_count AS failures,
           count(i) AS incident_count
    """
    res = g.query(q)
    patterns = []
    for r in res.result_set:
        pat, root, rb_title, actions, succ, fail, inc_cnt = r
        patterns.append({
            "pattern": pat,
            "root_type": root,
            "runbook_title": rb_title,
            "actions": actions,
            "successes": succ,
            "failures": fail,
            "incident_count": inc_cnt
        })
    return {"patterns": patterns}

# ==========================================
# SSE STREAMING ENDPOINT
# ==========================================

@app.get("/api/events")
async def event_stream(request: Request):
    """Server-Sent Events endpoint streaming live graph updates and agent actions."""
    queue = asyncio.Queue()
    subscribers.append(queue)

    async def event_generator():
        try:
            # Send initial ping
            yield f"event: connected\ndata: {json.dumps({'message': 'Connected to FAULTLINE Realtime Engine'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Non-blocking pop with timeout for keep-alive
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if queue in subscribers:
                subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
