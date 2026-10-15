// ==========================================
// FAULTLINE GRAPH SCHEMA & INDICES
// Tenant Graph Bootstrap for FalkorDB
// ==========================================

// Property Indices for Fast Traversal & Joins
CREATE INDEX FOR (s:Service) ON (s.name);
CREATE INDEX FOR (d:Database) ON (d.name);
CREATE INDEX FOR (q:Queue) ON (q.name);
CREATE INDEX FOR (p:Pod) ON (p.name);
CREATE INDEX FOR (kn:Node) ON (kn.name);
CREATE INDEX FOR (dep:Deployment) ON (dep.ts);
CREATE INDEX FOR (al:Alert) ON (al.ts);
CREATE INDEX FOR (an:Anomaly) ON (an.ts);
CREATE INDEX FOR (inc:Incident) ON (inc.ts);
CREATE INDEX FOR (h:Hypothesis) ON (h.status);
CREATE INDEX FOR (r:Run) ON (r.id);

// 384-dimensional Vector Indices for Semantic & Episodic Memory (all-MiniLM-L6-v2)
CREATE VECTOR INDEX FOR (inc:Incident) ON (inc.embedding) OPTIONS {dimension: 384, similarityFunction: 'cosine'};
CREATE VECTOR INDEX FOR (rb:Runbook) ON (rb.embedding) OPTIONS {dimension: 384, similarityFunction: 'cosine'};
