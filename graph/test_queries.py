#!/usr/bin/env python3
"""
Test Harness for FAULTLINE Core Cypher Queries.
Validates syntax, execution, and FalkorDB graph algorithms (maxFlow, pageRank, betweenness, vector search).
"""

import sys
import os
import time
from pathlib import Path
import numpy as np

try:
    from falkordb import FalkorDB
except ImportError:
    print("[ERROR] falkordb package required. Run: pip install falkordb")
    sys.exit(1)

QUERIES_DIR = Path(__file__).parent / "queries"

def load_query(filename: str) -> str:
    path = QUERIES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_query_benchmark(host="localhost", port=6379, graph_name="tenant:demo"):
    print(f"\n=======================================================")
    print(f" Executing Core Cypher Query Suite on '{graph_name}'")
    print(f"=======================================================")
    
    db = FalkorDB(host=host, port=port)
    g = db.select_graph(graph_name)

    now = 1800000000
    since = now - 3600

    # Ensure dummy signals exist for testing Query 1
    g.query("""
    MATCH (co:Service {name: 'checkoutservice'}), (pay:Service {name: 'paymentservice'})
    MERGE (a:Alert {id: 'TEST-A1', ts: $ts})
    MERGE (a)-[:FIRED_ON]->(co)
    MERGE (an:Anomaly {id: 'TEST-AN1', ts: $ts})
    MERGE (an)-[:OBSERVED_ON]->(pay)
    """, {"ts": now - 300})

    tests = [
        {
            "id": "Q1-Downstream",
            "name": "Lowest Common Dependency (Downstream)",
            "file": "01_find_root_candidates_downstream.cypher",
            "params": {"since": since}
        },
        {
            "id": "Q1-Neighbors",
            "name": "Anomalous Neighbors (Caller-Side)",
            "file": "01_find_root_candidates_neighbors.cypher",
            "params": {"since": since}
        },
        {
            "id": "Q2",
            "name": "Blast Radius Traversal",
            "file": "02_blast_radius.cypher",
            "params": {"target": "paymentservice"}
        },
        {
            "id": "Q3",
            "name": "Surviving Capacity (algo.maxFlow)",
            "file": "03_surviving_capacity.cypher",
            "params": {"source": "frontend", "sink": "orders-pg"}
        },
        {
            "id": "Q4",
            "name": "Criticality (algo.pageRank)",
            "file": "04_criticality.cypher",
            "params": {}
        },
        {
            "id": "Q5",
            "name": "Chokepoints (algo.betweenness)",
            "file": "05_chokepoints.cypher",
            "params": {}
        },
        {
            "id": "Q6",
            "name": "Explain Path (shortestPath)",
            "file": "06_explain_path.cypher",
            "params": {"alerting": "frontend", "root": "paymentservice"}
        },
        {
            "id": "Q7",
            "name": "Recall Incidents (Vector + Subgraph)",
            "file": "07_recall_incidents.cypher",
            "params": {
                "embedding": [0.05] * 384,
                "alerting_names": ["cartservice", "frontend"]
            }
        },
        {
            "id": "Q8",
            "name": "Who to Page (On-call + Experience)",
            "file": "08_who_to_page.cypher",
            "params": {"root": "paymentservice", "now": now}
        },
        {
            "id": "Q9",
            "name": "Claim Hypothesis (Blackboard)",
            "file": "09_claim_hypothesis.cypher",
            "params": {"agent_name": "investigator-topology", "now": now},
            "pre": "CREATE (:Hypothesis {id: 'H-TEST-Q9', statement: 'Payment latency degradation', prior: 0.9, status: 'open'}) MERGE (:Agent {name: 'investigator-topology'})"
        },
        {
            "id": "Q10",
            "name": "Trace Run (Ordered Step Replay)",
            "file": "10_trace_run.cypher",
            "params": {"run_id": "RUN-001"},
            "pre": """
            CREATE (r:Run {id: 'RUN-001', ts: $now})
            CREATE (s1:Step {id: 'S1', idx: 1, agent: 'commander', action: 'find_root', cypher_query: 'MATCH ...', duration_ms: 12, ts: $now})
            CREATE (s2:Step {id: 'S2', idx: 2, agent: 'topology', action: 'blast_radius', cypher_query: 'MATCH ...', duration_ms: 8, ts: $now + 1})
            CREATE (r)-[:HAS_STEP]->(s1)
            CREATE (r)-[:HAS_STEP]->(s2)
            """
        }
    ]

    all_passed = True
    print(f"{'Query ID':<16} | {'Status':<8} | {'Latency':<10} | {'Details'}")
    print("-" * 75)

    for test in tests:
        if "pre" in test:
            try:
                g.query(test["pre"], {"now": now})
            except Exception:
                pass

        cypher = load_query(test["file"])
        t0 = time.perf_counter()
        try:
            res = g.query(cypher, test["params"])
            elapsed_ms = (time.perf_counter() - t0) * 1000
            rows = len(res.result_set) if res.result_set else 0
            first_row = res.result_set[0] if rows > 0 else "[]"
            print(f"{test['id']:<16} | {'[OK]':<8} | {elapsed_ms:>6.2f} ms | Rows: {rows} (e.g. {str(first_row)[:35]}...)")
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            print(f"{test['id']:<16} | {'[FAIL]':<8} | {elapsed_ms:>6.2f} ms | Error: {e}")
            all_passed = False

    print("-" * 75)
    # Clean up test artifacts
    g.query("MATCH (a:Alert {id: 'TEST-A1'}) DETACH DELETE a")
    g.query("MATCH (an:Anomaly {id: 'TEST-AN1'}) DETACH DELETE an")
    g.query("MATCH (h:Hypothesis {id: 'H-TEST-Q9'}) DETACH DELETE h")
    g.query("MATCH (r:Run {id: 'RUN-001'})-[:HAS_STEP]->(s) DETACH DELETE r, s")

    if all_passed:
        print("[SUCCESS] All 11 core Cypher queries executed cleanly against FalkorDB!")
    else:
        print("[ERROR] One or more queries failed. See details above.")
    return all_passed

if __name__ == "__main__":
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", 6379))
    tenant = sys.argv[1] if len(sys.argv) > 1 else "tenant:demo"
    run_query_benchmark(host, port, tenant)
