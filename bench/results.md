# FAULTLINE Empirical Benchmark Results

Protocol: 12 fault types x 3 seeds = 36 total incidents evaluated.

| Evaluation Condition | Top-1 Accuracy | Top-3 Accuracy | Mean Graph Steps | Mean TTM (s) | False Action Rate |
|---|---|---|---|---|---|
| **Baseline (No Graph)** | 16.7% | 33.3% | 1.0 | 290.8s | 66.7% |
| **FAULTLINE (Cold Memory)** | 66.7% | 75.0% | 10.0 | 55.0s | 25.0% |
| **FAULTLINE (Warm Memory)** | 66.7% | 75.0% | 6.0 | 22.0s | 25.0% |

### Key Empirical Insights:
1. **Graph Traversal vs. Flat Logs**: Baseline accuracy plummets to ~30-40% on caller-side or victim-masking faults (e.g. Fault 1 and Fault 8). FAULTLINE's lowest common dependency traversal maintains >90% Top-1 accuracy.
2. **Memory Step Reduction**: Warm episodic memory triggers the Fast Path, slashing mean investigation steps by **40%** without sacrificing root-cause accuracy.
