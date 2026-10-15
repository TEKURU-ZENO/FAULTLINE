MATCH (r:Run {id: $run_id})-[:HAS_STEP]->(s:Step)
OPTIONAL MATCH (s)-[:CITED]->(target)
RETURN s.idx AS step_idx,
       s.id AS step_id,
       s.agent AS agent,
       s.action AS action,
       s.cypher_query AS query,
       s.duration_ms AS duration_ms,
       s.ts AS step_ts,
       collect(target.name) AS cited_nodes
ORDER BY s.idx ASC;
