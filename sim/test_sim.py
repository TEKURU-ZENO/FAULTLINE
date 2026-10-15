#!/usr/bin/env python3
"""
Test Suite for FAULTLINE Simulator v0 and Core Graph Invariants.
Validates:
1. Hard invariant: Every fault emits at least one Anomaly on its true cause node.
2. Fault 1 injection, capacity degradation via maxFlow, downstream root detection, and rollback.
3. Fault 8 caller-side retry storm detection via neighbor anomaly traversal.
"""

import os
import pytest
from pathlib import Path
from sim.faults import FAULTS
from sim.engine import SimulatorEngine

try:
    from falkordb import FalkorDB
except ImportError:
    FalkorDB = None

QUERIES_DIR = Path(__file__).parent.parent / "graph" / "queries"

def load_query(filename: str) -> str:
    path = QUERIES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def test_fault_definitions_have_anomalies():
    """Rule 3 Invariant: Every fault MUST emit at least one Anomaly on its true cause."""
    for fid, fault in FAULTS.items():
        causes = fault.get("causes", [])
        assert len(causes) >= 1, f"Fault {fid} ({fault['name']}) has no causes/anomalies defined!"
        target_nodes = [c["target"] for c in causes]
        assert fault["cause_node"] in target_nodes, (
            f"Fault {fid} cause_node '{fault['cause_node']}' does not match any Anomaly target in {target_nodes}!"
        )

@pytest.mark.skipif(FalkorDB is None, reason="falkordb not installed")
def test_simulation_fault_1_e2e():
    """Tests Fault 1: Bad Deploy on paymentservice."""
    sim = SimulatorEngine(graph_name="tenant:demo")
    sim.heal()

    # 1. Baseline Capacity via maxFlow
    q_maxflow = load_query("03_surviving_capacity.cypher")
    res_base = sim.g.query(q_maxflow, {"source": "frontend", "sink": "orders-pg"})
    assert res_base.result_set, "maxFlow query returned no rows"
    base_flow = res_base.result_set[0][0]
    assert base_flow == 1200.0, f"Expected nominal capacity 1200.0, got {base_flow}"

    # 2. Inject Fault 1
    sim.inject_fault(1)
    
    # 3. Assert maxFlow degraded to 10%
    res_fault = sim.g.query(q_maxflow, {"source": "frontend", "sink": "orders-pg"})
    fault_flow = res_fault.result_set[0][0]
    assert fault_flow <= 120.0, f"Expected capacity <= 120.0 under Fault 1, got {fault_flow}"

    # 4. Assert Query 1 (Downstream) identifies paymentservice as top candidate
    q_root = load_query("01_find_root_candidates_downstream.cypher")
    res_root = sim.g.query(q_root, {"since": sim.current_time - 1800})
    assert res_root.result_set, "Query 1 returned no root candidates"
    top_candidate = res_root.result_set[0][0]
    assert top_candidate == "paymentservice", f"Expected top candidate 'paymentservice', got '{top_candidate}'"

    # 5. Execute Rollback Remediation
    success = sim.execute_action("rollback", {"service": "paymentservice", "version": "v2.4.0"})
    assert success, "Rollback action failed to resolve Fault 1"

    # 6. Verify Full Recovery
    sim.heal()
    res_recovered = sim.g.query(q_maxflow, {"source": "frontend", "sink": "orders-pg"})
    recovered_flow = res_recovered.result_set[0][0]
    assert recovered_flow == 1200.0, f"Expected recovered capacity 1200.0, got {recovered_flow}"

@pytest.mark.skipif(FalkorDB is None, reason="falkordb not installed")
def test_simulation_fault_8_caller_anomaly_trap():
    """Tests Fault 8: Cartservice retry storm (caller anomaly vs victim alert)."""
    sim = SimulatorEngine(graph_name="tenant:demo")
    sim.heal()

    # 1. Inject Fault 8
    sim.inject_fault(8)

    # 2. Assert Alert on victim valkey-cart and Anomaly on caller cartservice
    res_alerts = sim.g.query("MATCH (a:Alert)-[:FIRED_ON]->(target) RETURN target.name")
    alert_targets = [r[0] for r in res_alerts.result_set]
    assert "valkey-cart" in alert_targets, "Expected Alert fired on victim valkey-cart"

    res_anoms = sim.g.query("MATCH (an:Anomaly)-[:OBSERVED_ON]->(target) RETURN target.name")
    anom_targets = [r[0] for r in res_anoms.result_set]
    assert "cartservice" in anom_targets, "Expected Anomaly observed on culprit cartservice"

    # 3. Assert Query 1 (Neighbors Branch) catches cartservice
    q_neighbors = load_query("01_find_root_candidates_neighbors.cypher")
    res_neighbors = sim.g.query(q_neighbors, {"since": sim.current_time - 1800})
    assert res_neighbors.result_set, "Query 1 neighbors returned no candidates"
    top_neighbor = res_neighbors.result_set[0][0]
    assert top_neighbor == "cartservice", f"Expected top neighbor candidate 'cartservice', got '{top_neighbor}'"

    # 4. Remediate via Circuit Breaker
    success = sim.execute_action("circuit_breaker", {"service": "cartservice", "enabled": True})
    assert success, "Circuit breaker action failed to resolve Fault 8"
    sim.heal()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
