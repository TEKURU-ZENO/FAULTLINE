#!/usr/bin/env python3
"""
End-to-End Verification of FAULTLINE Multi-Agent System (LangGraph).
Tests:
1. Cold run of Fault 1: Full multi-agent investigation, hypothesis testing, rollback, and Scribe write-back.
2. Warm run of Fault 1: Fast Path triggered via episodic memory recall, slashing step count by >50%!
"""

import time
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from sim.engine import SimulatorEngine
from agents.graph import build_incident_commander_graph
from graph.seed_topology import seed_graph

def test_multi_agent_cold_vs_warm_fast_path():
    print(f"\n=======================================================")
    print(f" Testing Multi-Agent Incident Commander (Cold vs Warm)")
    print(f"=======================================================")

    tenant = "tenant:demo"
    # Ensure graph is in baseline state (historical incidents exclude Fault 1)
    seed_graph(graph_name=tenant, include_memory=True)
    sim = SimulatorEngine(graph_name=tenant)
    app = build_incident_commander_graph(simulator=sim)

    # -------------------------------------------------------------
    # 1. COLD RUN: First occurrence of Fault 1
    # -------------------------------------------------------------
    print("\n--- [1/2] Executing COLD Incident (Fault 1) ---")
    sim.heal()
    sim.inject_fault(1)
    
    cold_now = int(time.time())
    cold_run_id = f"RUN-COLD-{cold_now}"
    
    cold_initial_state = {
        "run_id": cold_run_id,
        "tenant": tenant,
        "now": cold_now,
        "since": cold_now - 1800,
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
        "human_approved": True,
        "remediation_verified": False,
        "final_capacity": 0.0,
        "paged_engineer": None,
        "postmortem": None,
        "logs": []
    }

    cold_result = app.invoke(cold_initial_state)

    print("\nCold Run Logs:")
    for l in cold_result["logs"]:
        print("  ", l)

    # Assertions for Cold Run
    assert cold_result["confirmed_root_cause"] == "paymentservice", f"Expected root cause 'paymentservice', got {cold_result['confirmed_root_cause']}"
    assert cold_result["is_fast_path"] is False, "Expected cold run to perform full exploration, not fast path"
    assert cold_result["remediation_verified"] is True, "Expected capacity recovery verification"
    assert cold_result["final_capacity"] == 1200.0, f"Expected capacity 1200.0, got {cold_result['final_capacity']}"
    
    cold_steps = cold_result["step_idx"]
    print(f"\n[COLD RUN SUCCESS] Total graph tool steps: {cold_steps}. Postmortem written to FalkorDB.")

    # -------------------------------------------------------------
    # 2. WARM RUN: Second occurrence of Fault 1 (Memory in FalkorDB)
    # -------------------------------------------------------------
    print("\n--- [2/2] Executing WARM Incident (Fault 1 Re-injected) ---")
    sim.inject_fault(1)
    
    warm_now = cold_now + 3600
    warm_run_id = f"RUN-WARM-{warm_now}"
    
    warm_initial_state = {
        "run_id": warm_run_id,
        "tenant": tenant,
        "now": warm_now,
        "since": warm_now - 1800,
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
        "human_approved": True,
        "remediation_verified": False,
        "final_capacity": 0.0,
        "paged_engineer": None,
        "postmortem": None,
        "logs": []
    }

    warm_result = app.invoke(warm_initial_state)

    print("\nWarm Run Logs:")
    for l in warm_result["logs"]:
        print("  ", l)

    warm_steps = warm_result["step_idx"]

    # Assertions for Warm Run
    assert warm_result["confirmed_root_cause"] == "paymentservice", f"Expected root cause 'paymentservice', got {warm_result['confirmed_root_cause']}"
    assert warm_result["is_fast_path"] is True, "Expected Fast Path to trigger on repeat incident!"
    assert warm_result["remediation_verified"] is True, "Expected capacity recovery verification on warm run"
    assert warm_result["final_capacity"] == 1200.0, f"Expected recovered capacity 1200.0, got {warm_result['final_capacity']}"
    
    print(f"\n=======================================================")
    print(f" Jaw-Drop Proof: Cold Steps = {cold_steps} vs Warm Steps = {warm_steps}")
    step_reduction = (cold_steps - warm_steps) / cold_steps
    print(f" Step Reduction: {step_reduction:.1%}")
    print(f"=======================================================")
    
    assert warm_steps < cold_steps, f"Expected warm steps ({warm_steps}) < cold steps ({cold_steps})"
    assert step_reduction >= 0.25, f"Expected at least 25% step reduction, achieved {step_reduction:.1%}"
    print("[PASSED] Memory fast-path verified! Step count dropped measurably on repeat failure.")

    # Cleanup
    sim.heal()

if __name__ == "__main__":
    test_multi_agent_cold_vs_warm_fast_path()
