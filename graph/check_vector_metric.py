#!/usr/bin/env python3
"""
Vector Metric Direction Checker for FalkorDB
Tests whether db.idx.vector.queryNodes returns cosine similarity (~1.0 for self)
or cosine distance (~0.0 for self) to guarantee correct ORDER BY direction.
"""

import sys
import os
import numpy as np

try:
    from falkordb import FalkorDB
except ImportError:
    print("[ERROR] falkordb not installed.")
    sys.exit(1)

def check_vector_metric(host="localhost", port=6379, graph_name="tenant:demo"):
    print(f"\n[TEST] Checking vector metric direction on '{graph_name}'...")
    db = FalkorDB(host=host, port=port)
    g = db.select_graph(graph_name)
    
    # Query one incident's embedding
    res = g.query("MATCH (i:Incident) RETURN i.id, i.embedding LIMIT 1")
    if not res.result_set or not res.result_set[0]:
        print("[WARN] No incidents found to check vector metric. Run seed first.")
        return
        
    inc_id, emb = res.result_set[0]
    
    # Query vector index with the exact same embedding
    query = """
    CALL db.idx.vector.queryNodes('Incident', 'embedding', 1, vecf32($emb))
    YIELD node, score
    RETURN node.id AS id, score
    """
    v_res = g.query(query, {"emb": emb})
    if not v_res.result_set:
        print("[ERROR] Vector query returned 0 results.")
        return
        
    ret_id, score = v_res.result_set[0]
    print(f"Self-query incident: {inc_id} -> returned {ret_id} with score: {score:.6f}")
    
    if score > 0.5:
        print("[RESULT] Score is COSINE SIMILARITY (1.0 = identical). Use 'ORDER BY score DESC'.")
    else:
        print("[RESULT] Score is COSINE DISTANCE (0.0 = identical). Use 'ORDER BY score ASC'.")

if __name__ == "__main__":
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = int(os.environ.get("FALKORDB_PORT", 6379))
    check_vector_metric(host, port)
