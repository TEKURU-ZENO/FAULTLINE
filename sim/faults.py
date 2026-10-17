"""
FAULTLINE Simulator Fault Library (All 12 Scenarios).
Complete fault corpus for benchmark evaluation and live chaos testing:
1. Bad deploy on payment (latency spike on cause, 5xx alerts on callers)
2. Database connection pool exhaustion on orders-pg
3. Cache stampede after cache node restart on valkey-cart
4. Kafka consumer lag on accountingservice
5. Feature flag misconfig on flagd (quote_v2)
6. Noisy neighbor CPU saturation on k8s-node-2
7. Expired cert on internal edge to payment-gw-ext
8. Retry storm amplification (cartservice -> valkey-cart)
9. Partial compute failure on k8s-node-1
10. Slow downstream on shippingservice
11. Red herring (noisy alert on adservice + real fault on checkoutservice)
12. Dual simultaneous faults (paymentservice deploy + valkey-cart memory)
"""

from typing import Dict, Any

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
    3: {
        "id": 3,
        "name": "Cache Stampede after Restart on valkey-cart",
        "cause_node": "valkey-cart",
        "cause_type": "Database",
        "description": "Sudden TTL expiry on cart keys causes thundering herd, spiking load and timing out cart operations.",
        "symptoms": [
            {"target": "cartservice", "type": "Alert", "name": "CartReadTimeout", "severity": "critical", "metric": "timeout_rate", "val": 0.30},
            {"target": "frontend", "type": "Alert", "name": "CartDegraded", "severity": "warning", "metric": "cart_latency", "val": 450}
        ],
        "causes": [
            {"target": "valkey-cart", "type": "Anomaly", "metric": "cache_miss_rate", "z_score": 5.8}
        ],
        "deployments": [],
        "health_multipliers": {
            "valkey-cart": 0.25
        },
        "fix_action": "warm_cache",
        "fix_params": {"target": "valkey-cart"}
    },
    4: {
        "id": 4,
        "name": "Kafka Consumer Lag on accountingservice",
        "cause_node": "kafka",
        "cause_type": "Queue",
        "description": "Kafka consumer group stalls on order topics, causing asymmetric async backlog.",
        "symptoms": [
            {"target": "kafka", "type": "Alert", "name": "ConsumerLagCritical", "severity": "critical", "metric": "lag", "val": 15000},
            {"target": "accountingservice", "type": "Alert", "name": "AccountingLagAlert", "severity": "warning", "metric": "unprocessed_orders", "val": 8200}
        ],
        "causes": [
            {"target": "kafka", "type": "Anomaly", "metric": "queue_lag_surge", "z_score": 6.1}
        ],
        "deployments": [],
        "health_multipliers": {},
        "fix_action": "scale_consumers",
        "fix_params": {"target": "accountingservice", "replicas": 4}
    },
    5: {
        "id": 5,
        "name": "Feature Flag Misconfiguration on flagd",
        "cause_node": "flagd",
        "cause_type": "Service",
        "description": "Corrupted flagd rule rollout for quote_v2 causes quote calculation crashes.",
        "symptoms": [
            {"target": "quoteservice", "type": "Alert", "name": "QuoteErrorSpike", "severity": "critical", "metric": "5xx_rate", "val": 0.52},
            {"target": "shippingservice", "type": "Alert", "name": "ShippingQuoteUnavailable", "severity": "warning", "metric": "quote_failure", "val": 0.40}
        ],
        "causes": [
            {"target": "flagd", "type": "Anomaly", "metric": "flag_eval_error", "z_score": 5.9}
        ],
        "deployments": [],
        "health_multipliers": {
            "quoteservice": 0.3
        },
        "fix_action": "toggle_flag",
        "fix_params": {"flag": "quote_v2", "enabled": False}
    },
    6: {
        "id": 6,
        "name": "Noisy Neighbor CPU Saturation on k8s-node-2",
        "cause_node": "k8s-node-2",
        "cause_type": "Node",
        "description": "Noisy batch container hogs CPU on Node 2, throttling co-located checkout pod.",
        "symptoms": [
            {"target": "checkoutservice", "type": "Alert", "name": "PodThrottling", "severity": "critical", "metric": "cpu_throttled_pct", "val": 0.85},
            {"target": "frontend", "type": "Alert", "name": "CheckoutLatencyHigh", "severity": "warning", "metric": "p99_latency", "val": 1800}
        ],
        "causes": [
            {"target": "k8s-node-2", "type": "Anomaly", "metric": "node_cpu_saturation", "z_score": 7.4}
        ],
        "deployments": [],
        "health_multipliers": {
            "pod-checkout-2": 0.0
        },
        "fix_action": "reschedule_pod",
        "fix_params": {"target": "pod-checkout-2", "to_node": "k8s-node-3"}
    },
    7: {
        "id": 7,
        "name": "Expired SSL Certificate on payment-gw-ext",
        "cause_node": "payment-gw-ext",
        "cause_type": "Service",
        "description": "TLS certificate expired on external payment gateway mock, throwing handshake timeouts.",
        "symptoms": [
            {"target": "paymentservice", "type": "Alert", "name": "GatewayHandshakeTimeout", "severity": "critical", "metric": "ssl_errors", "val": 0.60},
            {"target": "checkoutservice", "type": "Alert", "name": "PaymentDeclinedSpike", "severity": "critical", "metric": "declined_rate", "val": 0.48}
        ],
        "causes": [
            {"target": "payment-gw-ext", "type": "Anomaly", "metric": "tls_handshake_failure", "z_score": 8.0}
        ],
        "deployments": [],
        "health_multipliers": {
            "payment-gw-ext": 0.05
        },
        "fix_action": "rotate_cert",
        "fix_params": {"target": "payment-gw-ext"}
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
    },
    9: {
        "id": 9,
        "name": "Node Outage on k8s-node-1 (50% Flow Drop)",
        "cause_node": "k8s-node-1",
        "cause_type": "Node",
        "description": "Kernel panic on k8s-node-1 crashes pod-checkout-1 and pod-payment-1, cutting order throughput by half.",
        "symptoms": [
            {"target": "checkoutservice", "type": "Alert", "name": "CapacityDegraded", "severity": "critical", "metric": "capacity_loss", "val": 0.50},
            {"target": "frontend", "type": "Alert", "name": "HighLatency5xx", "severity": "warning", "metric": "5xx_rate", "val": 0.25}
        ],
        "causes": [
            {"target": "k8s-node-1", "type": "Anomaly", "metric": "node_not_ready", "z_score": 9.0}
        ],
        "deployments": [],
        "health_multipliers": {
            "pod-checkout-1": 0.0
        },
        "fix_action": "failover_node",
        "fix_params": {"failed_node": "k8s-node-1", "target_node": "k8s-node-3"}
    },
    10: {
        "id": 10,
        "name": "Downstream Latency Saturation on shippingservice",
        "cause_node": "shippingservice",
        "cause_type": "Service",
        "description": "Slow DB queries inside shipping calculation hold connections open without hard errors.",
        "symptoms": [
            {"target": "checkoutservice", "type": "Alert", "name": "ShippingTimeoutWarning", "severity": "warning", "metric": "checkout_delay", "val": 3200},
            {"target": "shippingservice", "type": "Alert", "name": "SlowQueryRate", "severity": "warning", "metric": "latency_p99", "val": 4500}
        ],
        "causes": [
            {"target": "shippingservice", "type": "Anomaly", "metric": "p99_latency_skew", "z_score": 5.1}
        ],
        "deployments": [],
        "health_multipliers": {
            "shippingservice": 0.4
        },
        "fix_action": "adjust_timeout",
        "fix_params": {"service": "shippingservice", "timeout_ms": 1000}
    },
    11: {
        "id": 11,
        "name": "Red Herring: Noisy Alert on adservice + Real Bug on checkoutservice",
        "cause_node": "checkoutservice",
        "cause_type": "Service",
        "description": "Noisy alert fires on non-critical adservice while real memory leak is silently degrading checkoutservice.",
        "symptoms": [
            {"target": "adservice", "type": "Alert", "name": "AdClickThroughDrop", "severity": "critical", "metric": "noisy_metric", "val": 0.90},
            {"target": "frontend", "type": "Alert", "name": "OrderPipelineSlowing", "severity": "warning", "metric": "checkout_p99", "val": 2200}
        ],
        "causes": [
            {"target": "checkoutservice", "type": "Anomaly", "metric": "memory_leak_slope", "z_score": 6.8}
        ],
        "deployments": [],
        "health_multipliers": {
            "checkoutservice": 0.35
        },
        "fix_action": "restart_service",
        "fix_params": {"service": "checkoutservice"}
    },
    12: {
        "id": 12,
        "name": "Simultaneous Dual Outage (paymentservice + valkey-cart)",
        "cause_node": "paymentservice",
        "cause_type": "Service",
        "description": "Concurrent bad deploy on paymentservice combined with cache stampede on valkey-cart.",
        "symptoms": [
            {"target": "frontend", "type": "Alert", "name": "CriticalOrderLoss", "severity": "critical", "metric": "5xx_burn", "val": 0.65},
            {"target": "checkoutservice", "type": "Alert", "name": "DualPipelineFailure", "severity": "critical", "metric": "cart_pay_errors", "val": 0.70}
        ],
        "causes": [
            {"target": "paymentservice", "type": "Anomaly", "metric": "p99_latency", "z_score": 5.7},
            {"target": "valkey-cart", "type": "Anomaly", "metric": "memory_exhaustion", "z_score": 6.2}
        ],
        "deployments": [
            {"service": "paymentservice", "version": "v2.4.1", "author": "@asha"}
        ],
        "health_multipliers": {
            "paymentservice": 0.1,
            "valkey-cart": 0.2
        },
        "fix_action": "rollback",
        "fix_params": {"service": "paymentservice", "version": "v2.4.0"}
    }
}
