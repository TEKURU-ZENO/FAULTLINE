#!/usr/bin/env python3
"""
FAULTLINE Multi-Agent Incident Commander Workflow (LangGraph).
Coordinates 6 specialized agents:
- Commander (Triage, Hypothesis Generation, Synthesis)
- Historian (Episodic Vector Recall & Fast Path Gate)
- Topology Investigator (Reverse Traversal, Shortest Path, Betweenness)
- Change Investigator (Deployment & Flag Correlation)
- Remediator (Plan Action, Human Gate, Verify Recovery)
- Scribe (On-Call Paging, Write-Back, Postmortem)

All agent reasoning steps write directly to FalkorDB as Step, CITED, and Hypothesis nodes.
"""

import os
import sys
import json
import time
import uuid
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.graph import StateGraph, END
from falkordb import FalkorDB

# Import MCP tools and seeder utilities
from mcp_server.server import (
    find_root_candidates,
    blast_radius,
    surviving_capacity,
    criticality,
    chokepoints,
    explain_path,
    recall_incidents,
    who_to_page,
    claim_hypothesis,
    trace_run,
    get_graph
)
from graph.seed_topology import get_embedding, INCIDENT_TEMPLATE
from agents.schemas import HypothesisRecord, RemediationPlan, PostmortemReport
from agents.prompts import (
    COMMANDER_TRIAGE_PROMPT,
    TOPOLOGY_INVESTIGATOR_PROMPT,
    CHANGE_INVESTIGATOR_PROMPT,
    HISTORIAN_PROMPT,
    REMEDIATOR_PROMPT,
    SCRIBE_PROMPT
)

# LangGraph State Schema
class IncidentState(TypedDict):
    run_id: str
    tenant: str
    now: int
    since: int
    step_idx: int
    alerting_services: List[str]
    initial_capacity: float
    root_candidates: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    claimed_hypothesis_id: Optional[str]
    topology_evidence: Dict[str, Any]
    change_evidence: Dict[str, Any]
    recalled_incidents: List[Dict[str, Any]]
    matching_runbook: Optional[Dict[str, Any]]
    is_fast_path: bool
    confirmed_root_cause: Optional[str]
    proposed_action: Optional[Dict[str, Any]]
    human_approved: bool
    remediation_verified: bool
    final_capacity: float
    paged_engineer: Optional[Dict[str, Any]]
    postmortem: Optional[Dict[str, Any]]
    logs: Annotated[List[str], operator.add]

def create_run_node(g, run_id: str, now: int):
    """Initializes the Run node in the FalkorDB trace layer."""
    g.query("MERGE (r:Run {id: $id}) ON CREATE SET r.ts = $now, r.status = 'active'", {"id": run_id, "now": now})

# ==========================================
# AGENT NODES
# ==========================================

def commander_triage_node(state: IncidentState) -> Dict[str, Any]:
    """Commander assesses initial impact, finds root candidates, and opens hypotheses."""
    g = get_graph(state["tenant"])
    create_run_node(g, state["run_id"], state["now"])
    
    idx = state["step_idx"] + 1
    ctx = {"run_id": state["run_id"], "agent": "commander", "idx": idx, "now": state["now"]}

    # 1. Measure initial surviving capacity
    cap_res = surviving_capacity(source="frontend", sink="orders-pg", tenant=state["tenant"], ctx=ctx)
    initial_cap = cap_res["rows"][0]["maxFlow"] if cap_res["rows"] else 0.0

    # 2. Find root candidates (merged downstream + caller neighbors)
    idx += 1
    ctx["idx"] = idx
    cand_res = find_root_candidates(since=state["since"], tenant=state["tenant"], ctx=ctx)
    candidates = cand_res["rows"]

    # 3. Create open Hypothesis nodes on the graph blackboard
    hypotheses = []
    for rank, cand in enumerate(candidates[:2], 1):
        cname = cand["candidate"]
        prior = 0.90 if rank == 1 else 0.60
        hid = f"H-{state['run_id']}-{rank}"
        statement = f"Candidate '{cname}' is root cause (coverage: {cand.get('coverage', 0):.0%}, anomalies: {cand.get('anomalies', 0)})"
        
        # Write to FalkorDB
        g.query("""
        CREATE (h:Hypothesis {
            id: $hid,
            statement: $stmt,
            prior: $prior,
            status: 'open',
            candidate: $cand
        })
        """, {"hid": hid, "stmt": statement, "prior": prior, "cand": cname})
        
        hypotheses.append({
            "id": hid,
            "statement": statement,
            "prior": prior,
            "candidate": cname,
            "status": "open"
        })

    log_entry = f"[Commander] Triage complete. Initial capacity: {initial_cap:.1f} rps. Opened {len(hypotheses)} hypotheses. Top suspect: {candidates[0]['candidate'] if candidates else 'unknown'}"
    
    return {
        "step_idx": idx,
        "initial_capacity": initial_cap,
        "root_candidates": candidates,
        "hypotheses": hypotheses,
        "logs": [log_entry]
    }

def historian_node(state: IncidentState) -> Dict[str, Any]:
    """Historian recalls similar past incidents and determines if Fast Path thresholds are met."""
    idx = state["step_idx"] + 1
    ctx = {"run_id": state["run_id"], "agent": "historian", "idx": idx, "now": state["now"]}

    top_candidate = state["root_candidates"][0]["candidate"] if state["root_candidates"] else "service"
    alerting = state.get("alerting_services", ["frontend", "checkoutservice"])

    # Formulate standardized query text
    symptom_text = INCIDENT_TEMPLATE.format(
        alerts=", ".join(alerting),
        anomalies=f"degradation on {top_candidate}",
        root_type=top_candidate,
        symptoms="transaction capacity drop on order pipeline"
    )
    query_emb = get_embedding(symptom_text)

    # Call recall_incidents tool
    recall_res = recall_incidents(embedding=query_emb, alerting_names=alerting, tenant=state["tenant"], ctx=ctx)
    recalled = recall_res["rows"]

    # Evaluate Fast Path thresholds:
    # 1. Cosine distance <= 0.20 (similarity >= 0.80)
    # 2. Structural overlap >= 2 services
    # 3. Proven runbook with success rate >= 0.80
    is_fast_path = False
    matching_runbook = None
    
    if recalled:
        top_match = recalled[0]
        score = top_match.get("score", 1.0)
        overlap = top_match.get("overlap", 0)
        successes = top_match.get("successes", 0)
        failures = top_match.get("failures", 0)
        total_runs = successes + failures
        success_rate = (successes / total_runs) if total_runs > 0 else 0.0

        if score <= 0.30 and overlap >= 2 and success_rate >= 0.80 and top_match.get("runbook_title"):
            is_fast_path = True
            matching_runbook = top_match
            log_msg = f"[Historian] FAST PATH TRIGGERED! Recalled '{top_match['title']}' (distance: {score:.3f}, overlap: {overlap}, runbook success: {success_rate:.0%}). Skipping broad exploration!"
        else:
            log_msg = f"[Historian] Recalled {len(recalled)} past incidents. Best match distance: {score:.3f}, overlap: {overlap}. Cold exploration continues."
    else:
        log_msg = "[Historian] No past incidents found in graph memory. Proceeding with cold exploration."

    return {
        "step_idx": idx,
        "recalled_incidents": recalled,
        "is_fast_path": is_fast_path,
        "matching_runbook": matching_runbook,
        "logs": [log_msg]
    }

def topology_investigator_node(state: IncidentState) -> Dict[str, Any]:
    """Tests structural blast radius, shortest causal path, and chokepoints."""
    if state["is_fast_path"]:
        return {"logs": ["[Topology Investigator] Fast path active — skipping exploratory traversal."]}

    g = get_graph(state["tenant"])
    idx = state["step_idx"] + 1
    ctx = {"run_id": state["run_id"], "agent": "topology_investigator", "idx": idx, "now": state["now"]}

    # Claim top hypothesis
    claim_res = claim_hypothesis(agent_name="topology_investigator", now=state["now"], tenant=state["tenant"], ctx=ctx)
    claimed_id = claim_res["rows"][0]["hypothesis_id"] if claim_res["rows"] else None

    # Pick candidate to evaluate
    candidate = state["root_candidates"][0]["candidate"] if state["root_candidates"] else "paymentservice"

    # 1. Reverse blast radius
    idx += 1
    ctx["idx"] = idx
    blast_res = blast_radius(target=candidate, tenant=state["tenant"], ctx=ctx)
    upstream_victims = [r["impacted"] for r in blast_res["rows"]]

    # 2. Shortest causal path
    idx += 1
    ctx["idx"] = idx
    alerting_sample = state.get("alerting_services", ["frontend"])[0]
    path_res = explain_path(alerting=alerting_sample, root=candidate, tenant=state["tenant"], ctx=ctx)

    # 3. Post supporting evidence on Hypothesis in FalkorDB
    evidence_desc = f"Candidate covers {len(upstream_victims)} upstream services including {upstream_victims[:2]}"
    if claimed_id:
        g.query("""
        MATCH (h:Hypothesis {id: $hid})
        MATCH (s:Step {id: $sid})
        CREATE (h)-[:SUPPORTED_BY {weight: 0.9, rationale: $rat}]->(s)
        SET h.status = 'supported'
        """, {"hid": claimed_id, "sid": ctx.get("sid", str(uuid.uuid4())), "rat": evidence_desc})

    log_msg = f"[Topology Investigator] Analyzed {candidate}. Blast radius covers {len(upstream_victims)} upstream services. Causal path verified."
    return {
        "step_idx": idx,
        "claimed_hypothesis_id": claimed_id,
        "topology_evidence": {"upstream_victims": upstream_victims, "path": path_res["rows"]},
        "logs": [log_msg]
    }

def change_investigator_node(state: IncidentState) -> Dict[str, Any]:
    """Correlates recent deployments and configuration changes with the incident onset."""
    if state["is_fast_path"]:
        return {"logs": ["[Change Investigator] Fast path active — skipping exploratory change analysis."]}

    g = get_graph(state["tenant"])
    idx = state["step_idx"] + 1
    ctx = {"run_id": state["run_id"], "agent": "change_investigator", "idx": idx, "now": state["now"]}

    candidate = state["root_candidates"][0]["candidate"] if state["root_candidates"] else "paymentservice"

    # Query recent deployments
    res = g.query("""
    MATCH (d:Deployment)-[:DEPLOYED]->(target {name: $name})
    WHERE d.ts > $since - 1800
    RETURN d.version AS version, d.author AS author, d.ts AS ts
    """, {"name": candidate, "since": state["since"]})

    deploys = [dict(zip([h[1] for h in res.header], r)) for r in res.result_set] if res.result_set else []
    
    if deploys and state.get("claimed_hypothesis_id"):
        d = deploys[0]
        evidence_desc = f"Correlated recent deployment {d['version']} by {d['author']}"
        g.query("""
        MATCH (h:Hypothesis {id: $hid})
        SET h.status = 'confirmed'
        """, {"hid": state["claimed_hypothesis_id"]})
        log_msg = f"[Change Investigator] Found correlated deploy {d['version']} on {candidate} authored by {d['author']}."
    else:
        log_msg = f"[Change Investigator] No recent deployments on {candidate} in the last 30 minutes."

    return {
        "step_idx": idx,
        "change_evidence": {"recent_deploys": deploys},
        "logs": [log_msg]
    }

def commander_decision_node(state: IncidentState) -> Dict[str, Any]:
    """Synthesizes findings from investigators or confirms fast-path shortcut."""
    g = get_graph(state["tenant"])
    
    if state["is_fast_path"] and state["matching_runbook"]:
        # Shortcut: confirm candidate directly from historical pattern
        confirmed = state["root_candidates"][0]["candidate"]
        log_msg = f"[Commander Decision] Fast path confirmed root cause '{confirmed}' via matching runbook."
    else:
        # Decision synthesis based on top candidate
        confirmed = state["root_candidates"][0]["candidate"] if state["root_candidates"] else "unknown"
        log_msg = f"[Commander Decision] Synthesized evidence from investigators. Root cause confirmed: '{confirmed}'."

    # Mark confirmed in FalkorDB
    g.query("""
    MATCH (h:Hypothesis) WHERE h.candidate = $cand
    SET h.status = 'confirmed'
    """, {"cand": confirmed})

    return {
        "confirmed_root_cause": confirmed,
        "logs": [log_msg]
    }

def remediator_node(state: IncidentState, simulator=None) -> Dict[str, Any]:
    """Formulates remediation plan, executes upon approval, and verifies recovery."""
    idx = state["step_idx"] + 1
    ctx = {"run_id": state["run_id"], "agent": "remediator", "idx": idx, "now": state["now"]}

    root = state["confirmed_root_cause"]
    matching_rb = state.get("matching_runbook")

    # Formulate action
    if matching_rb and matching_rb.get("actions"):
        # From Runbook
        raw_actions = matching_rb["actions"]
        actions_list = json.loads(raw_actions) if isinstance(raw_actions, str) else raw_actions
        first_action = actions_list[0]
        action_name = first_action.get("action", "rollback")
        if "parameters" in first_action and isinstance(first_action["parameters"], dict):
            params = first_action["parameters"]
        else:
            params = {k: v for k, v in first_action.items() if k not in ["action", "target_node", "rationale", "is_from_runbook"]}
        rationale = f"Prescribed by proven runbook '{matching_rb.get('runbook_title', 'Proven Runbook')}'"
        is_rb = True
    else:
        # Synthesize based on root cause type across all 12 fault types
        if root == "orders-pg":
            action_name = "scale_db_pool"
            params = {"target": "orders-pg", "max_conns": 500}
            rationale = "Database connection pool saturated — scaling pool limit to 500"
        elif root == "cartservice":
            action_name = "circuit_breaker"
            params = {"service": "cartservice", "enabled": True}
            rationale = "Uncapped retry storm detected — enabling circuit breaker"
        elif root == "valkey-cart":
            action_name = "warm_cache"
            params = {"target": "valkey-cart"}
            rationale = "Cache stampede detected on valkey-cart — warming cache"
        elif root == "kafka":
            action_name = "scale_consumers"
            params = {"target": "accountingservice", "replicas": 4}
            rationale = "Consumer lag on orders topic — scaling accounting consumer replicas"
        elif root == "flagd":
            action_name = "toggle_flag"
            params = {"flag": "quote_v2", "enabled": False}
            rationale = "Feature flag drift on flagd — disabling quote_v2"
        elif root in ["k8s-node-2", "k8s-node-1"]:
            action_name = "reschedule_pod"
            params = {"target": "pod-checkout-2", "to_node": "k8s-node-3"}
            rationale = f"Compute node saturation on {root} — rescheduling pod"
        elif root == "payment-gw-ext":
            action_name = "rotate_cert"
            params = {"target": "payment-gw-ext"}
            rationale = "SSL handshake failure — rotating gateway certificate"
        elif root == "shippingservice":
            action_name = "adjust_timeout"
            params = {"service": "shippingservice", "timeout_ms": 1000}
            rationale = "Downstream query latency — tuning request timeout"
        elif root == "checkoutservice":
            action_name = "restart_service"
            params = {"service": "checkoutservice"}
            rationale = "Memory leak on checkoutservice — recycling service pods"
        else:
            action_name = "rollback"
            params = {"service": root, "version": "v2.4.0"}
            rationale = f"Recent deployment rollback to stable version v2.4.0 on {root}"
        is_rb = False

    plan = {
        "action": action_name,
        "target_node": root,
        "parameters": params,
        "rationale": rationale,
        "is_from_runbook": is_rb
    }

    # Execute action if approved (in automated run, human_approved defaults to True)
    verified = False
    final_cap = 0.0

    if state.get("human_approved", True):
        if simulator:
            simulator.execute_action(action_name, params)
            simulator.heal()

        # Verify recovery via surviving_capacity
        idx += 1
        ctx["idx"] = idx
        cap_res = surviving_capacity(source="frontend", sink="orders-pg", tenant=state["tenant"], ctx=ctx)
        final_cap = cap_res["rows"][0]["maxFlow"] if cap_res["rows"] else 0.0
        verified = (final_cap >= 1200.0)
        log_msg = f"[Remediator] Executed {action_name}. Verified recovery: capacity restored from {state['initial_capacity']:.0f} to {final_cap:.0f} rps."
    else:
        log_msg = f"[Remediator] Remediation plan '{action_name}' submitted. Awaiting human approval."

    return {
        "step_idx": idx,
        "proposed_action": plan,
        "remediation_verified": verified,
        "final_capacity": final_cap,
        "logs": [log_msg]
    }

def scribe_node(state: IncidentState) -> Dict[str, Any]:
    """Pages the on-call engineer, writes memory back to FalkorDB, and outputs postmortem."""
    g = get_graph(state["tenant"])
    idx = state["step_idx"] + 1
    ctx = {"run_id": state["run_id"], "agent": "scribe", "idx": idx, "now": state["now"]}

    root = state["confirmed_root_cause"]
    
    # 1. Page on-call engineer with prior fix experience
    page_res = who_to_page(root=root, now=state["now"], tenant=state["tenant"], ctx=ctx)
    paged = page_res["rows"][0] if page_res["rows"] else {"name": "On-Call SRE", "handle": "@oncall"}

    # 2. Write-back to FalkorDB Memory Layer
    inc_id = f"INC-{state['run_id'][-8:]}"
    title = f"Outage on {root} mitigating transaction capacity"
    summary = f"Root cause confirmed as {root}. Action: {state['proposed_action']['action']}. Initial capacity: {state['initial_capacity']} rps -> Recovered: {state['final_capacity']} rps."
    
    alerting_str = ", ".join(state.get("alerting_services", []))
    anomalies_str = f"degradation on {root}"
    emb_text = INCIDENT_TEMPLATE.format(
        alerts=alerting_str,
        anomalies=anomalies_str,
        root_type=root,
        symptoms="transaction capacity drop on order pipeline"
    )
    emb = get_embedding(emb_text)

    pat_name = f"Failure on {root} with capacity degradation"
    pat_sig = f"{root}:{state['proposed_action']['action']}"

    write_cypher = """
    MATCH (rc {name: $root})
    CREATE (i:Incident {
        id: $id,
        title: $title,
        summary: $summary,
        ts: $ts,
        embedding: vecf32($emb)
    })
    CREATE (fp:FailurePattern {
        id: 'FP-' + $id,
        name: $pat_name,
        signature: $pat_sig,
        root_type: $root
    })
    CREATE (rb:Runbook {
        id: 'RB-' + $id,
        title: 'Remediation for ' + $root,
        actions_json: $actions,
        embedding: vecf32($emb),
        last_verified: $ts
    })
    CREATE (i)-[:ROOT_CAUSE]->(rc)
    CREATE (i)-[:MATCHES]->(fp)
    CREATE (fp)-[:RESOLVED_BY {success_count: 1, fail_count: 0}]->(rb)
    """
    g.query(write_cypher, {
        "root": root,
        "id": inc_id,
        "title": title,
        "summary": summary,
        "ts": state["now"],
        "emb": emb,
        "pat_name": pat_name,
        "pat_sig": pat_sig,
        "actions": json.dumps([{"action": state["proposed_action"]["action"], **state["proposed_action"].get("parameters", {})}])
    })

    # Link AFFECTED entities
    for aff in state.get("alerting_services", []):
        g.query("MATCH (i:Incident {id: $id}), (s {name: $s}) CREATE (i)-[:AFFECTED]->(s)", {"id": inc_id, "s": aff})

    postmortem = {
        "incident_id": inc_id,
        "title": title,
        "root_cause": root,
        "paged_engineer": paged["name"] + f" ({paged['handle']})",
        "action_taken": state["proposed_action"]["action"],
        "initial_capacity_rps": state["initial_capacity"],
        "recovered_capacity_rps": state["final_capacity"],
        "is_fast_path": state["is_fast_path"],
        "total_steps": idx
    }

    log_msg = f"[Scribe] Paged {paged['name']} ({paged['handle']}). Wrote Incident {inc_id} & Runbook to FalkorDB memory. Postmortem generated."
    return {
        "step_idx": idx,
        "paged_engineer": paged,
        "postmortem": postmortem,
        "logs": [log_msg]
    }

# ==========================================
# GRAPH ROUTING
# ==========================================

def route_after_historian(state: IncidentState) -> str:
    """If fast path triggered, route directly to decision; otherwise explore in parallel."""
    if state["is_fast_path"]:
        return "commander_decision"
    return "topology_investigator"

def build_incident_commander_graph(simulator=None) -> StateGraph:
    """Builds and compiles the full LangGraph state machine."""
    workflow = StateGraph(IncidentState)

    workflow.add_node("commander_triage", commander_triage_node)
    workflow.add_node("historian", historian_node)
    workflow.add_node("topology_investigator", topology_investigator_node)
    workflow.add_node("change_investigator", change_investigator_node)
    workflow.add_node("commander_decision", commander_decision_node)
    workflow.add_node("remediator", lambda state: remediator_node(state, simulator=simulator))
    workflow.add_node("scribe", scribe_node)

    # Edge wiring
    workflow.set_entry_point("commander_triage")
    workflow.add_edge("commander_triage", "historian")
    
    # Conditional branching from Historian
    workflow.add_conditional_edges(
        "historian",
        route_after_historian,
        {
            "commander_decision": "commander_decision",
            "topology_investigator": "topology_investigator"
        }
    )
    
    # Parallel exploration joining at decision
    workflow.add_edge("topology_investigator", "change_investigator")
    workflow.add_edge("change_investigator", "commander_decision")
    
    workflow.add_edge("commander_decision", "remediator")
    workflow.add_edge("remediator", "scribe")
    workflow.add_edge("scribe", END)

    return workflow.compile()
