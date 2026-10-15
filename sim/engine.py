#!/usr/bin/env python3
"""
FAULTLINE Deterministic Simulation Engine.
Propagates traffic, modulates edge live_rps, injects faults, emits Alert/Anomaly nodes,
and handles remediation action execution with batched FalkorDB transactions.
"""

import sys
import os
import time
from typing import Dict, List, Any
from pathlib import Path

try:
    from falkordb import FalkorDB
except ImportError:
    FalkorDB = None

from sim.faults import FAULTS

class SimulatorEngine:
    def __init__(self, host="localhost", port=6379, graph_name="tenant:demo", start_time=1800000000):
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self.current_time = start_time
        self.active_faults: Dict[int, Dict[str, Any]] = {}
        
        self.db = FalkorDB(host=self.host, port=self.port) if FalkorDB else None
        self.g = self.db.select_graph(self.graph_name) if self.db else None

        # Base nominal capacities for FLOWS_TO checkout transaction pipeline
        self.base_flows = [
            {"from": "frontend-proxy", "to": "frontend", "cap": 1200.0},
            {"from": "frontend", "to": "pod-checkout-1", "cap": 600.0},
            {"from": "frontend", "to": "pod-checkout-2", "cap": 600.0},
            {"from": "pod-checkout-1", "to": "paymentservice", "cap": 600.0},
            {"from": "pod-checkout-2", "to": "paymentservice", "cap": 600.0},
            {"from": "paymentservice", "to": "orders-pg", "cap": 1200.0}
        ]

    def set_time(self, t: int):
        self.current_time = t

    def advance_time(self, seconds: int = 1):
        self.current_time += seconds

    def inject_fault(self, fault_id: int):
        if fault_id not in FAULTS:
            raise ValueError(f"Unknown fault ID: {fault_id}")
            
        fault = FAULTS[fault_id]
        self.active_faults[fault_id] = fault
        now = self.current_time

        print(f"[SIM] Injecting Fault #{fault_id}: {fault['name']} at t={now}")
        if not self.g:
            return

        # 1. Inject Deployments if any
        for d in fault.get("deployments", []):
            dep_id = f"DEP-{d['service']}-{d['version']}"
            q_dep = """
            MATCH (s:Service {name: $service})
            CREATE (d:Deployment {id: $id, version: $version, ts: $ts, author: $author, status: 'active'})
            CREATE (d)-[:DEPLOYED]->(s)
            """
            self.g.query(q_dep, {
                "service": d["service"],
                "id": dep_id,
                "version": d["version"],
                "ts": now - 300,
                "author": d["author"]
            })

        # 2. Inject Anomalies on Causes (Rule: Every fault emits at least one anomaly on true cause!)
        for an in fault.get("causes", []):
            an_id = f"ANOM-F{fault_id}-{an['target']}-{int(now)}"
            q_anom = """
            MATCH (target {name: $target})
            CREATE (a:Anomaly {id: $id, metric: $metric, z_score: $z_score, ts: $ts})
            CREATE (a)-[:OBSERVED_ON]->(target)
            """
            self.g.query(q_anom, {
                "target": an["target"],
                "id": an_id,
                "metric": an["metric"],
                "z_score": an["z_score"],
                "ts": now
            })

        # 3. Inject Alerts on Symptoms
        for al in fault.get("symptoms", []):
            al_id = f"ALERT-F{fault_id}-{al['target']}-{int(now)}"
            q_alert = """
            MATCH (target {name: $target})
            CREATE (a:Alert {id: $id, name: $name, severity: $sev, metric: $metric, value: $val, ts: $ts})
            CREATE (a)-[:FIRED_ON]->(target)
            """
            self.g.query(q_alert, {
                "target": al["target"],
                "id": al_id,
                "name": al["name"],
                "sev": al["severity"],
                "metric": al["metric"],
                "val": al["val"],
                "ts": now
            })

        # Propagate tick immediately
        self.tick()

    def heal(self):
        """Clears all faults, restores capacities, removes active alerts and anomalies."""
        print(f"[SIM] Healing system to 100% healthy baseline...")
        self.active_faults.clear()
        if self.g:
            self.g.query("MATCH (a:Alert) DETACH DELETE a")
            self.g.query("MATCH (an:Anomaly) DETACH DELETE an")
            self.g.query("MATCH (d:Deployment) DETACH DELETE d")
        self.tick()

    def execute_action(self, action: str, params: Dict[str, Any]) -> bool:
        """Executes a remediation action (e.g. rollback, scale_db_pool, circuit_breaker)."""
        print(f"[ACTION] Executing '{action}' with params: {params}")
        resolved = []
        for fid, fault in self.active_faults.items():
            if fault["fix_action"] == action:
                # In real scenario, verify params match
                resolved.append(fid)

        if resolved:
            for fid in resolved:
                del self.active_faults[fid]
            print(f"[ACTION SUCCESS] Resolved Fault(s): {resolved}")
            self.tick()
            return True
        else:
            print(f"[ACTION NOOP] Action '{action}' did not resolve any active faults.")
            return False

    def tick(self, step_s: int = 1):
        """Advances clock and propagates live_rps across FLOWS_TO edges via batched UNWIND."""
        self.advance_time(step_s)
        
        # Calculate node health factors
        health_factors = {
            "frontend-proxy": 1.0,
            "frontend": 1.0,
            "pod-checkout-1": 1.0,
            "pod-checkout-2": 1.0,
            "paymentservice": 1.0,
            "orders-pg": 1.0,
            "valkey-cart": 1.0,
            "cartservice": 1.0
        }

        # Apply active fault degradations
        for fault in self.active_faults.values():
            for node, mult in fault.get("health_multipliers", {}).items():
                health_factors[node] = min(health_factors.get(node, 1.0), mult)

        # Compute edge live_rps
        updates = []
        for edge in self.base_flows:
            src = edge["from"]
            dst = edge["to"]
            cap = edge["cap"]
            
            # Flow is constrained by the bottleneck of source and target health
            src_health = health_factors.get(src, 1.0)
            dst_health = health_factors.get(dst, 1.0)
            edge_health = min(src_health, dst_health)
            
            live_rps = round(cap * edge_health, 2)
            updates.append({"from": src, "to": dst, "live_rps": live_rps})

        # Batched UNWIND write to FalkorDB
        if self.g:
            batch_cypher = """
            UNWIND $updates AS u
            MATCH (src {name: u.from})-[r:FLOWS_TO]->(dst {name: u.to})
            SET r.live_rps = u.live_rps
            """
            self.g.query(batch_cypher, {"updates": updates})

        return updates

if __name__ == "__main__":
    sim = SimulatorEngine()
    print("Simulator Engine initialized at t =", sim.current_time)
    updates = sim.tick()
    print(f"Propagated {len(updates)} flows. Sample: {updates[0]}")
