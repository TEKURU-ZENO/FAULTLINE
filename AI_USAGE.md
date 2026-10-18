# AI Coding Assistant Usage Disclosure

In compliance with the hackathon rules (Rules 3, 10, and 13), this document discloses the usage of AI coding assistants during the development of FAULTLINE.

## Tools Used
- **Assistant**: Antigravity (Google DeepMind) / Gemini 3.8 Flash
- **Development Window**: Started after October 15, 2026, 12:01 AM IST

## Author-Authored Core Intellectual Property
The core algorithmic, architectural, and mathematical models of FAULTLINE were designed and written by the author (@Dev Mehta):
1. **Graph Data Model & Multi-Layer Schema**:
   - 5-layer interconnected graph architecture (Topology, Organization, Signals, Memory, Agent Trace).
   - Dual-path routing separating fan-out RPC dependencies (`CALLS`, `READS`, `WRITES`) from flow-conserved transactional paths (`FLOWS_TO`).
   - Tenant isolation architecture leveraging FalkorDB multigraph.
2. **Core Cypher Queries & Graph Algorithm Implementations**:
   - `algo.maxFlow` capacity degradation modeling on pod-replicated transactional pipelines.
   - Deterministic `algo.betweenness` (with fixed `samplingSeed: 42`) and `algo.pageRank` dependency bottleneck ranking.
   - Dual-branch lowest common dependency traversal combining symptom alerts with anomalous cause detection.
   - Unified vector similarity (`vecf32`) and structural subgraph filtering for incident memory recall.
3. **Multi-Agent Incident Commander Architecture**:
   - Hypothesis blackboard coordination using graph claims (`CLAIMED`, `SUPPORTED_BY`, `REFUTED_BY`).
   - Fast-path memory gating logic based on empirical runbook success rates and structural overlap thresholds.
   - Policy-driven deterministic orchestration over graph query results.

## AI Assistant Contributions
The AI assistant was used for:
- Repository scaffolding, Makefiles, Docker configuration, and Python task runner (`tasks.py`).
- Synthetic telemetry generation in the deterministic simulator (`sim/engine.py` and 12 fault scenarios in `sim/faults.py`).
- Next.js 15 UI frontend components (`web/`), SVG topology layout, and Tailwind dark theme styling.
- FastMCP tool server wrapper (`mcp_server/server.py`) and FastAPI Server-Sent Events (SSE) streaming boilerplate (`api/main.py`).
- Automated benchmark test harness (`bench/run.py`), metrics tabulation, and test fixtures (`sim/test_sim.py`, `agents/test_agents.py`).
- Markdown formatting, Mermaid diagrams, docstrings, and README structuring.
