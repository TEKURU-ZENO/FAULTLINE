#!/usr/bin/env python3
"""
Test Tracing Contract for FalkorDB MCP Server.
Verifies that FalkorDB accepts the TRACE query:
- Step creation with idx, agent, cypher, duration
- Optional NEXT chaining via FOREACH / CASE
- CITED entity linking via UNWIND
"""

import sys
import uuid
import time
from falkordb import FalkorDB

TRACE = """
MATCH (r:Run {id:$run_id})
CREATE (r)-[:HAS_STEP {idx:$idx}]->(s:Step {id:$sid, idx:$idx, agent:$agent,
  action:$tool, cypher_query:$q, ts:$now, duration_ms:$ms, rows:$rows})
WITH r, s
OPTIONAL MATCH (r)-[:HAS_STEP]->(prev:Step {idx:$idx - 1})
FOREACH (_ IN CASE WHEN prev IS NULL THEN [] ELSE [1] END | CREATE (prev)-[:NEXT]->(s))
WITH s
UNWIND $cited AS n
MATCH (e {name:n})
MERGE (s)-[:CITED]->(e)
"""

def test_trace_query(host="localhost", port=6379, graph_name="tenant:demo"):
    print(f"\n[TEST] Testing TRACE query contract on '{graph_name}'...")
    db = FalkorDB(host=host, port=port)
    g = db.select_graph(graph_name)

    run_id = f"RUN-TRACE-TEST-{int(time.time())}"
    now = int(time.time())
    
    # 1. Create Run node
    g.query("CREATE (:Run {id: $id, ts: $ts, status: 'active'})", {"id": run_id, "ts": now})

    try:
        # 2. Trace Step 1 (prev is NULL -> NEXT should not be created)
        step1_id = str(uuid.uuid4())
        g.query(TRACE, {
            "run_id": run_id,
            "idx": 1,
            "sid": step1_id,
            "agent": "commander",
            "tool": "find_root_candidates",
            "q": "MATCH (a:Alert)...",
            "now": now,
            "ms": 4.25,
            "rows": 3,
            "cited": ["paymentservice", "checkoutservice"]
        })

        # 3. Trace Step 2 (prev is Step 1 -> NEXT should link Step 1 -> Step 2)
        step2_id = str(uuid.uuid4())
        g.query(TRACE, {
            "run_id": run_id,
            "idx": 2,
            "sid": step2_id,
            "agent": "topology_investigator",
            "tool": "blast_radius",
            "q": "MATCH (down {name:$target})...",
            "now": now + 1,
            "ms": 2.15,
            "rows": 5,
            "cited": ["frontend", "checkoutservice"]
        })

        # 4. Verify Step nodes
        res_steps = g.query("MATCH (r:Run {id: $id})-[:HAS_STEP]->(s:Step) RETURN s.idx, s.agent, s.action ORDER BY s.idx", {"id": run_id})
        assert len(res_steps.result_set) == 2, f"Expected 2 steps, got {len(res_steps.result_set)}"
        print("    [OK] Step nodes created successfully:", res_steps.result_set)

        # 5. Verify NEXT relationship
        res_next = g.query("MATCH (s1:Step {idx: 1})-[:NEXT]->(s2:Step {idx: 2}) RETURN count(*)", {})
        assert res_next.result_set[0][0] == 1, "Expected 1 NEXT edge between Step 1 and Step 2"
        print("    [OK] FOREACH/CASE NEXT edge verified:", res_next.result_set[0][0])

        # 6. Verify CITED edges
        res_cited = g.query("MATCH (s:Step {id: $sid})-[:CITED]->(e) RETURN e.name", {"sid": step1_id})
        cited_names = [r[0] for r in res_cited.result_set]
        assert "paymentservice" in cited_names and "checkoutservice" in cited_names
        print("    [OK] CITED edges verified:", cited_names)

        print("[PASSED] FalkorDB natively accepts FOREACH/CASE optional NEXT syntax!")
        return True
    finally:
        # Clean up test run
        g.query("MATCH (r:Run {id: $id})-[:HAS_STEP]->(s:Step) DETACH DELETE r, s", {"id": run_id})

if __name__ == "__main__":
    test_trace_query()
