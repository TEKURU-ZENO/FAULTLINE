"""
Pydantic Schemas for FAULTLINE Multi-Agent Team.
Guarantees strictly typed structured outputs for all agent decisions,
hypotheses, and tool parameters.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class StepTraceContext(BaseModel):
    run_id: str
    agent: str
    idx: int
    now: int

class HypothesisRecord(BaseModel):
    id: str
    statement: str
    prior: float = Field(ge=0.0, le=1.0)
    candidate_node: str
    status: str = "open"  # open, investigating, confirmed, refuted
    claimed_by: Optional[str] = None
    supporting_evidence: List[str] = Field(default_factory=list)
    refuting_evidence: List[str] = Field(default_factory=list)

class RootCandidate(BaseModel):
    name: str
    coverage: float
    anomalies: int
    recent_deploys: List[str] = Field(default_factory=list)
    branch: str

class BlastRadiusItem(BaseModel):
    impacted: str
    hops: int
    tier: str

class RecalledIncident(BaseModel):
    incident_id: str
    title: str
    pattern: str
    runbook_title: Optional[str] = None
    actions: Optional[str] = None
    successes: int = 0
    failures: int = 0
    score: float
    overlap: int

class RemediationPlan(BaseModel):
    action: str  # rollback, scale_db_pool, circuit_breaker, toggle_flag
    target_node: str
    parameters: Dict[str, Any]
    rationale: str
    is_from_runbook: bool = False
    runbook_id: Optional[str] = None

class PostmortemReport(BaseModel):
    incident_id: str
    title: str
    root_cause: str
    detection_time_ms: float
    mitigation_action: str
    surviving_capacity_initial: float
    surviving_capacity_recovered: float
    steps_count: int
    is_fast_path: bool
    cited_graph_nodes: List[str]
    timeline: List[Dict[str, Any]]
