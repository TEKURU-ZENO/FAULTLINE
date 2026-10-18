# FAULTLINE Empirical Benchmark Results

Protocol: 12 fault types x 3 seeds = 36 total incidents evaluated.

| Evaluation Condition | Top-1 Accuracy | Top-3 Accuracy | Mean Graph Steps | False Action Rate |
|---|---|---|---|---|
| **Baseline: loudest-alert heuristic (no LLM, no graph)** | 16.7% | 33.3% | 1.0 | 66.7% |
| **FAULTLINE (Cold Memory)** | 66.7% | 75.0% | 10.0 | 25.0% |
| **FAULTLINE (Warm Memory)** | 66.7% | 75.0% | 6.0 | 25.0% |

### Key Empirical Insights:
1. **Graph Traversal vs. Loudest-Alert Heuristic**: The baseline loudest-alert heuristic achieves only 16.7% Top-1 accuracy and a 66.7% false action rate because alerts fire on symptoms rather than causes (e.g. `frontend` alerting when `paymentservice` fails, or `valkey-cart` alerting during a `cartservice` retry storm). FAULTLINE's lowest common dependency and neighbor graph traversal raises Top-1 accuracy to 66.7% (75.0% Top-3).
2. **Fast Path Step Reduction**: Warm episodic memory skips the parallel investigator subgraphs on repeat failures when a high-confidence runbook match is recalled from FalkorDB vector memory. This reduces mean graph tool calls from 10.0 to 6.0 (a 40% reduction).
3. **Memory vs. Accuracy**: Top-1 and Top-3 accuracy are identical between Cold and Warm conditions (66.7% Top-1, 75.0% Top-3). Episodic memory does not alter the diagnosis; it optimizes execution cost and steps by short-circuiting exploratory investigation.
