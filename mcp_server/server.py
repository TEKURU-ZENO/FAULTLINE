#!/usr/bin/env python3
"""
FAULTLINE FastMCP Server.
Exposes FalkorDB graph algorithms and traversals as MCP tools.
Automatically traces every tool call into the FalkorDB graph as Step and CITED nodes.
"""

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from falkordb import FalkorDB
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("faultline")

HOST = os.environ.get("FALKORDB_HOST", "localhost")
PORT = int(os.environ.get("FALKORDB_PORT", 6379))
DEFAULT_GRAPH = os.environ.get("FALKORDB_GRAPH", "tenant:demo")

def get_graph(graph_name: str = DEFAULT_GRAPH):
    db = FalkorDB(host=HOST, port=PORT)
    return db.select_graph(graph_name)

# Load queries at startup
QUERIES_DIR = Path(__file__).parent.parent / "graph" / "queries"
Q = {p.stem: p.read_text(encoding="utf-8") for p in QUERIES_DIR.glob("*.cypher")}

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

def traced(tool: str, query_key: str, params: Dict[str, Any], ctx: Optional[Dict[str, Any]] = None, graph_name: str = DEFAULT_GRAPH) -> Dict[str, Any]:
    """
    Executes a query against FalkorDB and traces the execution in the graph.
    ctx contains LangGraph-injected metadata: {'run_id': ..., 'agent': ..., 'idx': ..., 'now': ...}
    """
    g = get_graph(graph_name)
    query_text = Q[query_key]
    
    t0 = time.perf_counter()
    res = g.query(query_text, params)
    ms = round((time.perf_counter() - t0) * 1000, 2)
    
    headers = [h[1] for h in res.header] if res.header else []
    rows = [dict(zip(headers, r)) for r in res.result_set] if res.result_set else []
    
    # Extract string values that could match entity names in the graph
    cited = sorted({v for row in rows for v in row.values() if isinstance(v, str)})
    
    # If called within an agent Run context, record Step & CITED edges
    if ctx and "run_id" in ctx:
        sid = str(uuid.uuid4())
        g.query(TRACE, {
            "run_id": ctx["run_id"],
            "idx": ctx.get("idx", 1),
            "agent": ctx.get("agent", "agent"),
            "now": ctx.get("now", int(time.time())),
            "sid": sid,
            "tool": tool,
            "q": query_text,
            "ms": ms,
            "rows": len(rows),
            "cited": cited
        })
        
    return {
        "tool": tool,
        "rows": rows,
        "cypher": query_text,
        "ms": ms
    }

# ==========================================
# MCP TOOLS EXPOSED TO AGENTS
# ==========================================

@mcp.tool()
def find_root_candidates(since: int, tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Finds lowest common dependencies across alerting services and correlates anomalous neighbors.
    Merges both downstream symptom chains and caller-side anomaly branches.
    """
    # Branch A: Downstream lowest common dependency
    res_down = traced("find_root_candidates_downstream", "01_find_root_candidates_downstream", {"since": since}, ctx, tenant)
    # Branch B: Caller-side anomalous neighbors
    res_neigh = traced("find_root_candidates_neighbors", "01_find_root_candidates_neighbors", {"since": since}, ctx, tenant)
    
    combined = res_down["rows"] + res_neigh["rows"]
    # Deduplicate by candidate name, prioritizing higher anomalies then coverage
    candidates = {}
    for r in combined:
        name = r["candidate"]
        if name not in candidates or r["anomalies"] > candidates[name]["anomalies"]:
            candidates[name] = r
            
    ranked = sorted(candidates.values(), key=lambda x: (x.get("anomalies", 0), x.get("coverage", 0.0), x.get("avg_depth", 0.0)), reverse=True)
    return {
        "tool": "find_root_candidates",
        "rows": ranked[:5],
        "cypher": res_down["cypher"],
        "ms": res_down["ms"] + res_neigh["ms"]
    }

@mcp.tool()
def blast_radius(target: str, tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Traverses reverse dependencies to determine all upstream services impacted by a failure."""
    return traced("blast_radius", "02_blast_radius", {"target": target}, ctx, tenant)

@mcp.tool()
def surviving_capacity(source: str = "frontend", sink: str = "orders-pg", tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Computes surviving transaction checkout capacity (RPS) using FalkorDB algo.maxFlow over FLOWS_TO."""
    return traced("surviving_capacity", "03_surviving_capacity", {"source": source, "sink": sink}, ctx, tenant)

@mcp.tool()
def criticality(tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Computes structural architectural centrality using FalkorDB algo.pageRank."""
    return traced("criticality", "04_criticality", {}, ctx, tenant)

@mcp.tool()
def chokepoints(tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Finds topological bottlenecks using deterministic algo.betweenness centrality (samplingSeed: 42)."""
    return traced("chokepoints", "05_chokepoints", {}, ctx, tenant)

@mcp.tool()
def explain_path(alerting: str, root: str, tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Finds the shortest causal dependency path from an alerting symptom node to the root cause."""
    return traced("explain_path", "06_explain_path", {"alerting": alerting, "root": root}, ctx, tenant)

@mcp.tool()
def recall_incidents(embedding: List[float], alerting_names: List[str], tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Recalls past incidents from FalkorDB vector index (db.idx.vector.queryNodes)
    fused with structural overlap and empirical runbook success track record.
    """
    return traced("recall_incidents", "07_recall_incidents", {"embedding": embedding, "alerting_names": alerting_names}, ctx, tenant)

@mcp.tool()
def who_to_page(root: str, now: int, tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Finds the active on-call engineer for the root cause node, ranked by deduplicated prior fixes."""
    return traced("who_to_page", "08_who_to_page", {"root": root, "now": now}, ctx, tenant)

@mcp.tool()
def claim_hypothesis(agent_name: str, now: int, tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Claims an open hypothesis on the blackboard atomically in FalkorDB."""
    return traced("claim_hypothesis", "09_claim_hypothesis", {"agent_name": agent_name, "now": now}, ctx, tenant)

@mcp.tool()
def trace_run(run_id: str, tenant: str = DEFAULT_GRAPH, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieves the full replayable step trace of an investigation run."""
    return traced("trace_run", "10_trace_run", {"run_id": run_id}, ctx, tenant)

if __name__ == "__main__":
    mcp.run()
