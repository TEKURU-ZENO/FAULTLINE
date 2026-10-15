"""
FAULTLINE Simulator Fault Definitions.
Implements Phase 1 Fault Scenarios:
- Fault 1: Bad deploy on payment (latency spike on cause, 5xx alerts on callers)
- Fault 2: Database connection pool exhaustion on orders-pg
- Fault 8: Retry storm amplification (caller cartservice attacks victim valkey-cart)
"""

from typing import Dict, Any, Callable

FAULTS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Bad Deploy on paymentservice (v2.4.1)",
        "cause_node": "paymentservice",
        "cause_type": "Service",
        "description": "Deploy v2.4.1 introduces regex catastrophic backtracking in auth logic, dropping throughput to 10% and spiking p99.",
        "symptoms": [
            {"target": "frontend", "type": "Alert", "name": "High5xxRate", "severity": "critical", "metric": "http_5xx", "val": 0.18},
            {"target": "checkoutservice", "type": "Alert", "name": "SLOBurnRate", "severity": "critical", "metric": "error_rate", "val": 0.22}
        ],
        "causes": [
            {"target": "paymentservice", "type": "Anomaly", "metric": "p99_latency", "z_score": 5.4}
        ],
        "deployments": [
            {"service": "paymentservice", "version": "v2.4.1", "author": "@asha"}
        ],
        "health_multipliers": {
            "paymentservice": 0.1
        },
        "fix_action": "rollback",
        "fix_params": {"service": "paymentservice", "version": "v2.4.0"}
    },
    2: {
        "id": 2,
        "name": "Database Connection Pool Exhaustion on orders-pg",
        "cause_node": "orders-pg",
        "cause_type": "Database",
        "description": "Leaked database connections saturate orders-pg pool, blocking all downstream checkout and accounting writes.",
        "symptoms": [
            {"target": "orders-pg", "type": "Alert", "name": "DBPoolExhausted", "severity": "critical", "metric": "connections", "val": 200},
            {"target": "checkoutservice", "type": "Alert", "name": "DBWriteTimeout", "severity": "critical", "metric": "db_timeout_rate", "val": 0.45},
            {"target": "accountingservice", "type": "Alert", "name": "LedgerWriteFailure", "severity": "critical", "metric": "db_errors", "val": 0.38}
        ],
        "causes": [
            {"target": "orders-pg", "type": "Anomaly", "metric": "active_connections", "z_score": 6.5}
        ],
        "deployments": [],
        "health_multipliers": {
            "orders-pg": 0.05
        },
        "fix_action": "scale_db_pool",
        "fix_params": {"target": "orders-pg", "max_conns": 500}
    },
    8: {
        "id": 8,
        "name": "Retry Storm Amplification (cartservice -> valkey-cart)",
        "cause_node": "cartservice",
        "cause_type": "Service",
        "description": "cartservice triggers exponential uncapped retries under mild jitter, overwhelming victim valkey-cart with 6x traffic.",
        "symptoms": [
            {"target": "valkey-cart", "type": "Alert", "name": "MemorySaturation", "severity": "critical", "metric": "memory_used", "val": 0.98},
            {"target": "cartservice", "type": "Alert", "name": "DownstreamDegraded", "severity": "warning", "metric": "p99_ms", "val": 420}
        ],
        "causes": [
            {"target": "cartservice", "type": "Anomaly", "metric": "retry_rate", "z_score": 7.2}
        ],
        "deployments": [],
        "health_multipliers": {
            "valkey-cart": 0.2
        },
        "fix_action": "circuit_breaker",
        "fix_params": {"service": "cartservice", "enabled": True}
    }
}
