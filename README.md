# FAULTLINE ⚡

> **A multi-agent incident commander whose whole brain lives in FalkorDB.**  
> *It remembers.*

[![Track 01](https://img.shields.io/badge/Track_01-Agents_That_Act_on_Connected_Data-blue)](#tracks-entered)
[![Track 02](https://img.shields.io/badge/Track_02-Agent_Memory_and_Coordination-green)](#tracks-entered)
[![FalkorDB](https://img.shields.io/badge/Graph_Database-FalkorDB-red)](https://falkordb.com)
[![LangGraph](https://img.shields.io/badge/Agent_Orchestration-LangGraph-purple)](https://langchain-ai.github.io/langgraph/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js_15-black)](https://nextjs.org/)

---

## The 2:14 AM Problem

It’s 2:14 AM. Checkout is failing and six alerts are firing. Which one actually matters?

Traditional incident tools dump flat logs and vectors into an LLM. But **"what depends on what" is a graph traversal, not a semantic search**. When `checkoutservice` fails because a bad deploy on `paymentservice` exhausted the connection pool on `orders-pg`, flat log search blames checkout (the loudest victim) while ignoring the root cause three hops away.

**FAULTLINE solves this because its whole brain lives in FalkorDB**:
- Traverses the 5-layer dependency graph to isolate the lowest common dependency and anomalous callers.
- Computes real-time surviving transaction capacity with `algo.maxFlow` over pod-routed checkout pipelines.
- Pages the exact engineer on-call who fixed this failure pattern in the past (`who_to_page.cypher`).
- Automatically traces every agent thought and MCP tool execution as a `Step` node on the graph blackboard.
- **The Jaw-Drop Moment**: When the outage recurs, episodic memory triggers the **Fast Path**—slashing investigation tool steps from **10 to 6 (a 40% reduction)** and solving the incident in seconds.

---

## Tracks Entered

### Track 01: Agents That Act on Connected Data (Primary)
- **Multi-Hop Dependency Traversal**: Dual-branch Cypher analysis combining lowest common dependency downstream walking with 2-hop anomalous neighbor correlation.
- **Graph Algorithms as Agent Tools**: Native FalkorDB algorithms directly drive remediation decisions:
  - `algo.maxFlow`: Push-relabel maximum transaction flow over pod-routed `:FLOWS_TO` checkout pipelines.
  - `algo.pageRank`: Global service criticality scoring.
  - `algo.betweenness`: Chokepoint detection with deterministic `samplingSeed: 42`.
  - `shortestPath`: Causal explanation chain from symptom alert to root failure.
- **Action Verification**: Pre- and post-remediation capacity validation ensuring zero false claims.

### Track 02: Agent Memory & Coordination (Secondary)
- **Semantic Memory**: 28-node topology modeled on the OpenTelemetry Astronomy Shop, pod compute placements, and team ownership.
- **Episodic Memory**: Past incidents indexed with 384-dimensional dense vectors (`vecf32`) and queried with cosine distance.
- **Procedural Memory**: Failure patterns linked to executable runbooks, weighted by historical track records (`RESOLVED_BY {success_count, fail_count}`).
- **Shared Blackboard Coordination**: Multi-agent hypothesis locking via `(Agent)-[:CLAIMED]->(Hypothesis)`, preventing redundant work.
- **Per-Tenant Graph Isolation**: Multi-tenant isolation across `tenant:demo`, `tenant:eval_cold`, and `tenant:eval_warm`.

---

## Why FalkorDB? (The Rule 3 Proof)

If you take FalkorDB out of FAULTLINE, the system ceases to function entirely:
1. **Root cause isolation** is an upstream/downstream causal traversal (`CALLS`, `READS`, `WRITES`). Vector search cannot do this.
2. **Surviving capacity** is computed using FalkorDB's C-native push-relabel `algo.maxFlow`. Relational databases cannot do this in single-digit milliseconds.
3. **Agent coordination** is persisted in graph memory via hypothesis claim edges (`CLAIMED`, `SUPPORTED_BY`, `REFUTED_BY`).
4. **Episodic recall** fuses FalkorDB's native vector index (`vecf32`) with structural subgraph filtering (`[:AFFECTED]`) in a single atomic Cypher query.

No auxiliary vector databases. No shadow JSON stores. Every agent decision is a Cypher query.

---

## The Jaw-Drop Moment: 40% Step Reduction via Episodic Memory

When an incident hits for the first time, FAULTLINE explores multiple hypotheses across 10 graph tool calls. Once resolved, **Scribe** commits the incident, failure signature, and verified runbook into FalkorDB memory. On repeat failure, **Historian** recognizes the pattern and activates the Fast Path:

```
======================================================================
 JAW-DROP VERIFICATION: Cold Run vs. Warm Fast-Path
======================================================================

--- [1/2] COLD INCIDENT (First Occurrence) ---
[Commander] Triage complete. Initial capacity: 120.0 rps. Opened 2 hypotheses.
[Historian] Recalled 0 matching runbooks with >80% confidence. Cold exploration continues.
[Topology Inv.] Analyzed paymentservice. Blast radius covers 3 upstream services.
[Change Inv.] Discovered recent active deployment DEP-paymentservice-v2.4.1.
[Commander Decision] Synthesized evidence from investigators. Root cause: paymentservice.
[Remediator] Executed rollback. Verified recovery: capacity restored 120 -> 1200 rps.
[Scribe] Paged Asha Patel (@asha). Wrote Incident & Runbook to FalkorDB memory.
--> Total Tool Steps: 10

--- [2/2] WARM INCIDENT (Repeat Failure) ---
[Commander] Triage complete. Initial capacity: 120.0 rps. Opened 2 hypotheses.
[Historian] FAST PATH TRIGGERED! Recalled 'Outage on paymentservice'
            (distance: 0.000, overlap: 2, runbook success: 100%).
            Skipping broad exploration!
[Commander Decision] Fast path confirmed root cause 'paymentservice' via matching runbook.
[Remediator] Executed rollback. Verified recovery: capacity restored 120 -> 1200 rps.
[Scribe] Paged Asha Patel (@asha). Updated runbook success count.
--> Total Tool Steps: 6

======================================================================
 Step Reduction: 40.0% (10 steps -> 6 steps)
 Verification Command: python tasks.py test-agents
======================================================================
```

---

## Empirical Benchmark Results

We evaluated **FAULTLINE across 12 distinct fault scenarios** over multiple seeds, comparing:
1. **Baseline (No Graph)**: Traditional log correlation selecting the loudest alerting service.
2. **FAULTLINE (Cold Memory)**: Full graph tool suite without prior incident history.
3. **FAULTLINE (Warm Memory)**: Full graph tool suite with FalkorDB episodic memory enabled.

| Evaluation Condition | Top-1 Accuracy | Top-3 Accuracy | Mean Graph Steps | Mean TTM (s) | False Action Rate |
|---|---|---|---|---|---|
| **Baseline (No Graph)** | 16.7% | 33.3% | 1.0 | 290.8s | 66.7% |
| **FAULTLINE (Cold Memory)** | 66.7% | 75.0% | 10.0 | 55.0s | 25.0% |
| **FAULTLINE (Warm Memory)** | **66.7%** | **75.0%** | **6.0 (↓ 40%)** | **22.0s (↓ 60%)** | **25.0%** |

### Benchmark Takeaways:
- **Graph Traversal Beats Flat Logs**: Baseline accuracy plummets on caller-side or victim-masking faults (e.g., cartservice retry storm vs. valkey-cart). FAULTLINE's lowest common dependency traversal maintains high accuracy.
- **Episodic Memory Slashes Investigation Overhead**: Warm memory cuts graph tool steps from 10.0 to 6.0 without sacrificing remediation accuracy.
- **Reproduce anytime**: Run `python tasks.py bench`.

---

## Connected Data Model (5 Layers in FalkorDB)

The graph models 28 nodes inspired by the **OpenTelemetry Astronomy Shop** across 5 layers:

```mermaid
graph TD
    subgraph Topology_and_Flow ["Layer 1: Topology & Capacity"]
        FEProxy["frontend-proxy"] -->|FLOWS_TO| FE["frontend"]
        FE -->|FLOWS_TO| P1["pod-checkout-1"]
        FE -->|FLOWS_TO| P2["pod-checkout-2"]
        P1 -->|FLOWS_TO| Pay["paymentservice"]
        P2 -->|FLOWS_TO| Pay
        Pay -->|FLOWS_TO| OrdersDB[("orders-pg")]
        FE -->|CALLS| Cart["cartservice"]
        Cart -->|READS/WRITES| Valkey[("valkey-cart")]
        FE -->|CALLS| Quote["quoteservice"]
        Quote -->|CALLS| Flagd["flagd"]
    end

    subgraph Org_Layer ["Layer 2: Organization & Ownership"]
        TeamCheckout["Team: Checkout Core"] -->|OWNS| FE
        TeamCheckout -->|OWNS| P1
        TeamPay["Team: Payments Platform"] -->|OWNS| Pay
        EngAsha["Engineer: @asha"] -->|MEMBER_OF| TeamPay
        EngAsha -->|ON_CALL| TeamPay
    end

    subgraph Signals_Layer ["Layer 3: Live Telemetry"]
        AlCheckout["Alert: CheckoutLatencyHigh"] -->|FIRED_ON| FE
        AnomPay["Anomaly: p99_latency (z=5.7)"] -->|OBSERVED_ON| Pay
        DepPay["Deployment: v2.4.1"] -->|DEPLOYED| Pay
    end

    subgraph Memory_Layer ["Layer 4: Episodic & Procedural Memory"]
        PastInc["Incident: INC-2026-1001"] -->|ROOT_CAUSE| Pay
        PastInc -->|AFFECTED| FE
        PastInc -->|MATCHES| FP["FailurePattern: payment_pool_exhaustion"]
        FP -->|RESOLVED_BY| RB["Runbook: Rollback & Pool Scale"]
        PastInc -.->|384-d Cosine Vector| VecIdx[("vecf32 Index")]
    end

    subgraph Agent_Trace ["Layer 5: Blackboard & Trace"]
        Run1["Run: RUN-9226"] -->|HAS_STEP| Step1["Step 1: Commander Triage"]
        Step1 -->|NEXT| Step2["Step 2: Historian Recall"]
        Step2 -->|NEXT| Step3["Step 3: Remediator Action"]
        Step2 -->|CITED| PastInc
        Run1 -->|HYPOTHESIS| Hypo1["Hypothesis: paymentservice root"]
        AgentTop["Agent: TopologyInv"] -->|CLAIMED| Hypo1
    end
```

---

## Core Cypher Queries & FalkorDB Algorithms

Every tool exposed to the LangGraph agents executes a dedicated Cypher query:

| Tool Name | Query File | Algorithm / Operation | Description |
|---|---|---|---|
| `find_root_candidates` | [`01_find_root_candidates_downstream.cypher`](graph/queries/01_find_root_candidates_downstream.cypher)<br>[`01_find_root_candidates_neighbors.cypher`](graph/queries/01_find_root_candidates_neighbors.cypher) | Graph Traversal + Anomaly Ranking | Traverses downstream paths and 2-hop caller-side anomalous neighbors to isolate the true culprit. |
| `blast_radius` | [`02_blast_radius.cypher`](graph/queries/02_blast_radius.cypher) | Variable-Length BFS (`1..5` hops) | Computes all upstream customer-facing services affected by a node's failure. |
| `surviving_capacity` | [`03_surviving_capacity.cypher`](graph/queries/03_surviving_capacity.cypher) | `algo.maxFlow` (Push-Relabel) | Calculates surviving checkout transactions/sec over `:FLOWS_TO` capacity edges. |
| `criticality` | [`04_criticality.cypher`](graph/queries/04_criticality.cypher) | `algo.pageRank` | Scores structural importance across the service call graph. |
| `chokepoints` | [`05_chokepoints.cypher`](graph/queries/05_chokepoints.cypher) | `algo.betweenness` (`samplingSeed: 42`) | Identifies single points of failure with fixed seed for benchmark reproducibility. |
| `explain_path` | [`06_explain_path.cypher`](graph/queries/06_explain_path.cypher) | `shortestPath` | Extracts the causal dependency chain from symptom alert to root cause. |
| `recall_incidents` | [`07_recall_incidents.cypher`](graph/queries/07_recall_incidents.cypher) | `db.idx.vector.queryNodes` | Fuses cosine distance vector similarity with structural service overlap and runbook track records. |
| `who_to_page` | [`08_who_to_page.cypher`](graph/queries/08_who_to_page.cypher) | Ownership & Track Record Query | Identifies on-call engineer prioritizing those with prior successful fixes for this failure pattern. |
| `claim_hypothesis` | [`09_claim_hypothesis.cypher`](graph/queries/09_claim_hypothesis.cypher) | Atomic Graph Mutation | Prevents race conditions by locking hypotheses to agents on the shared blackboard. |
| `trace_run` | [`10_trace_run.cypher`](graph/queries/10_trace_run.cypher) | Sequential Step Traversal | Reconstructs the complete multi-agent reasoning chain ordered by `Step.idx`. |

---

## Real-Time 3-Pane Web Dashboard

FAULTLINE includes a real-time incident command dashboard built with **Next.js 15, Tailwind CSS, and Server-Sent Events (SSE)**:

1. **Left: Chaos Rail & Impact Meters**
   - 1-click injection across all 12 fault scenarios (bad deploys, retry storms, DB pool saturation, noisy neighbors, SSL expiration).
   - Real-time gauges: **Surviving Capacity RPS** (via `algo.maxFlow`), **5xx Error Burn Rate**, and **P99 Latency**.
2. **Center: Live Graph Topology Canvas**
   - Interactive SVG dependency graph visualizing the 28-node Astronomy Shop model.
   - Dynamic pulsing glow on alerting services (amber) and root causes (red).
3. **Right: Agent Reasoning Feed & Human Gate**
   - Live stream of multi-agent execution steps with agent badges, execution timestamps, and exact Cypher query runtimes.
   - **Human-in-the-Loop Approval Modal**: Remediator proposes action; operator approves before execution.
   - **Postmortem Drawer**: Auto-generated incident timeline and learned runbook written back to FalkorDB.

---

## Quickstart Guide

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for Web UI)

### 1. Launch FalkorDB
```bash
python tasks.py up
```
*Starts FalkorDB on port 6379 and FalkorDB Browser on `http://localhost:3000`.*

### 2. Seed Topology & Memory
```bash
python tasks.py seed
```
*Seeds the 28-node Astronomy Shop topology, team rotations, and historical episodic memory.*

### 3. Verify Cypher Queries & Invariants
```bash
python tasks.py test-queries
python -m pytest sim/test_sim.py
```

### 4. Run the Cold vs. Warm Fast-Path Test
```bash
python tasks.py test-agents
```
*Demonstrates the 40% step reduction on repeat failure.*

### 5. Run the Full Benchmark Suite
```bash
python tasks.py bench
```
*Evaluates Baseline vs. Cold vs. Warm memory across 12 fault types.*

### 6. Launch the Live Dashboard
In terminal 1 (FastAPI SSE Server):
```bash
python tasks.py api
```

In terminal 2 (Next.js Dashboard):
```bash
python tasks.py web
```
Open **`http://localhost:3001`** in your browser.

---

## License

MIT License. Built for the **FalkorDB Hackathon 2026**.
