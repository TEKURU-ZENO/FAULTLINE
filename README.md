# FAULTLINE ⚡

> **An incident commander whose entire brain lives in FalkorDB.**  
> *It remembers.*

[![Track 01](https://img.shields.io/badge/Track_01-Agents_That_Act_on_Connected_Data-blue)](#tracks)
[![Track 02](https://img.shields.io/badge/Track_02-Agent_Memory_and_Coordination-green)](#tracks)
[![FalkorDB](https://img.shields.io/badge/Graph_Database-FalkorDB-red)](https://falkordb.com)

---

## The 2:14 AM Problem

It’s 2:14 AM. Checkout is failing and six alerts are firing. Which one actually matters?

Traditional incident tools dump flat logs and vectors into an LLM. But **"what depends on what" is a graph traversal, not a semantic search**.

FAULTLINE walks the dependency graph in FalkorDB, pinpoints the one service that actually broke three hops down, computes surviving transaction capacity with `algo.maxFlow`, pages the engineer who resolved this exact failure pattern last month, gates remediation behind human approval, and **writes the postmortem and learned runbook back into the graph so the next incident takes seconds**.

---

## Tracks Entered

1. **Track 01: Agents That Act on Connected Data (Primary)**
   - Multi-hop root cause analysis through dependency graphs.
   - Graph algorithms exposed directly as agent tools (`algo.maxFlow`, `algo.pageRank`, `algo.betweenness`, `shortestPath`).
   - Actionable remediation gated on graph-verified topological blast radius.

2. **Track 02: Agent Memory and Coordination (Secondary)**
   - **Semantic memory**: Topology, infrastructure placement, and team ownership.
   - **Episodic memory**: Incident history with structural overlap and embedded symptom vectors (`db.idx.vector.queryNodes`).
   - **Procedural memory**: Failure patterns linked to executable runbooks, with empirical success rate weighting (`RESOLVED_BY {success_count, fail_count}`).
   - **Shared blackboard coordination**: Multi-agent hypothesis locking via `(Agent)-[:CLAIMED]->(Hypothesis)`.
   - **Per-tenant isolation**: Dedicated graphs per tenant (`tenant:acme`, `tenant:eval_cold`).

---

## Why FalkorDB? (The Rule 3 Proof)

If you take FalkorDB out of FAULTLINE, the system ceases to function entirely:
1. **Root cause isolation** is an upstream/downstream causal traversal (`CALLS`, `READS`, `WRITES`).
2. **Surviving capacity** is computed using FalkorDB's C-native push-relabel `algo.maxFlow` over pod-routed transaction pipelines.
3. **Agent coordination** is persisted in graph memory via hypothesis claim edges (`CLAIMED`, `SUPPORTED_BY`, `REFUTED_BY`).
4. **Memory recall** fuses FalkorDB's native vector index (`vecf32`) with structural subgraph filtering in a single atomic query.

No auxiliary vector databases. No shadow JSON stores. Every agent decision is a Cypher query.

---

## System Architecture

```
                      +-------------------+
                      |  Fault Simulator  |  (28-node OTel Astronomy Shop model)
                      +---------+---------+
                                |  emits Alert, Anomaly, updates live_rps
                                v
+-----------------------------------------------------------------+
|                   FalkorDB Graph (Whole Brain)                  |
|  [Topology + Capacity]  [Org & Ownership]  [Signals & Anomalies]|
|  [Memory & Runbooks]    [Agent Trace & Hypothesis Blackboard]   |
+-------------------------------+---------------------------------+
                                ^
                                | Cypher / MCP Tools
                                v
                      +-------------------+
                      | Agent Team (LangGraph)
                      | - Commander       |
                      | - Topology Inv.   |
                      | - Change Inv.     |
                      | - Historian       |
                      | - Remediator      |
                      | - Scribe          |
                      +---------+---------+
                                | proposed fix
                                v
                      +-------------------+
                      | Human Approval    |
                      +---------+---------+
                                | rollback / scale / restart
                                v
                      +-------------------+
                      | Simulator Action  | (Verifies Recovery)
                      +-------------------+
```

---

## Data Model & Schema

The graph models 28 nodes inspired by the **OpenTelemetry Astronomy Shop**, spanning 5 interconnected layers:

```
(Alert)-[:FIRED_ON]->(Service)-[:CALLS]->(Service)-[:WRITES]->(Database)
                       |                   |
                   [:RUNS_ON]          [:DEPLOYED]
                       v                   v
                     (Pod)           (Deployment)
                       |
                  [:HOSTED_ON]
                       v
                    (Node)
```

### Core Cypher Tools

| Tool / Query | Cypher File | Operation / FalkorDB Algorithm |
|---|---|---|
| `find_root_candidates` | [`01_find_root_candidates.cypher`](graph/queries/01_find_root_candidates.cypher) | Lowest common dependency + depth tiebreaker + anomalous neighbor correlation |
| `blast_radius` | [`02_blast_radius.cypher`](graph/queries/02_blast_radius.cypher) | Reverse variable-length traversal (`1..5` hops) |
| `surviving_capacity` | [`03_surviving_capacity.cypher`](graph/queries/03_surviving_capacity.cypher) | `algo.maxFlow` over pod-routed `:FLOWS_TO` checkout transaction paths |
| `criticality` | [`04_criticality.cypher`](graph/queries/04_criticality.cypher) | `algo.pageRank('Service', 'CALLS')` |
| `chokepoints` | [`05_chokepoints.cypher`](graph/queries/05_chokepoints.cypher) | `algo.betweenness` with fixed `samplingSeed: 42` for benchmark determinism |
| `explain_path` | [`06_explain_path.cypher`](graph/queries/06_explain_path.cypher) | `shortestPath` causal chain from symptom to root |
| `recall_incidents` | [`07_recall_incidents.cypher`](graph/queries/07_recall_incidents.cypher) | `db.idx.vector.queryNodes` + structural overlap + runbook track record |
| `who_to_page` | [`08_who_to_page.cypher`](graph/queries/08_who_to_page.cypher) | On-call status with deduplicated `count(DISTINCT i)` prior fixes |
| `claim_hypothesis` | [`09_claim_hypothesis.cypher`](graph/queries/09_claim_hypothesis.cypher) | Atomic blackboard reservation: `CREATE (ag)-[:CLAIMED]->(h)` |
| `trace_run` | [`10_trace_run.cypher`](graph/queries/10_trace_run.cypher) | Replayable execution trace ordered by `Step.idx` |

---

## Quickstart

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (or FalkorDB Cloud)

### Run in 3 Commands

```bash
# 1. Start FalkorDB and FalkorDB Browser
python tasks.py up

# 2. Seed the 28-node Astronomy Shop topology and historical memory
python tasks.py seed

# 3. Verify all 10 core Cypher queries and graph algorithms
python tasks.py test-queries
```

Open FalkorDB Browser at `http://localhost:3000` to visualize the live graph.
