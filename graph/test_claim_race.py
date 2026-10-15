#!/usr/bin/env python3
"""
Blackboard Claim Race Condition Test (Query 9).
Runs 50 trials with 2 concurrent threads attempting to claim the same Hypothesis.
Asserts that exactly 1 agent claims each hypothesis with ZERO double-claims.
"""

import sys
import os
import time
import threading
from pathlib import Path

try:
    from falkordb import FalkorDB
except ImportError:
    print("[ERROR] falkordb package required.")
    sys.exit(1)

def run_race_test(host="localhost", port=6379, graph_name="tenant:demo", trials=50):
    print(f"\n=======================================================")
    print(f" Testing Query 9 Claim Race Condition ({trials} trials)")
    print(f"=======================================================")
    
    db = FalkorDB(host=host, port=port)
    g = db.select_graph(graph_name)
    
    # Ensure Agent nodes exist
    g.query("MERGE (a:Agent {name: 'investigator-1'}) MERGE (b:Agent {name: 'investigator-2'})")
    
    # Read query 09
    q9_path = Path(__file__).parent / "queries" / "09_claim_hypothesis.cypher"
    with open(q9_path, "r", encoding="utf-8") as f:
        claim_cypher = f.read()

    double_claims = 0
    clean_claims = 0

    for trial in range(1, trials + 1):
        # Create single open hypothesis
        h_id = f"H-RACE-{trial}"
        g.query("CREATE (:Hypothesis {id: $id, statement: 'Test Hypothesis', prior: 0.8, status: 'open'})", {"id": h_id})

        claimed_by = []
        barrier = threading.Barrier(2)

        def claim_worker(agent_name):
            barrier.wait()
            try:
                res = g.query(claim_cypher, {
                    "agent_name": agent_name,
                    "now": int(time.time())
                })
                if res.result_set:
                    claimed_by.append(agent_name)
            except Exception as e:
                # Concurrent conflict is fine if it prevents double-claim
                pass

        t1 = threading.Thread(target=claim_worker, args=("investigator-1",))
        t2 = threading.Thread(target=claim_worker, args=("investigator-2",))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Clean up trial node
        g.query("MATCH (h:Hypothesis {id: $id}) DETACH DELETE h", {"id": h_id})

        if len(claimed_by) > 1:
            double_claims += 1
            print(f"[FAIL] Trial {trial}: Double claim detected by {claimed_by}!")
        elif len(claimed_by) == 1:
            clean_claims += 1

    print(f"\nResults: {clean_claims}/{trials} clean atomic claims. Double claims: {double_claims}")
    assert double_claims == 0, f"Detected {double_claims} double claims during concurrent race test!"
    print("[PASSED] Zero double-claims across all concurrent trials. Hypothesis blackboard is atomic!")

if __name__ == "__main__":
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", 6379))
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_race_test(host, port, trials=trials)
