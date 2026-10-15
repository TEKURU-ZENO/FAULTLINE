CALL db.idx.vector.queryNodes('Incident', 'embedding', 10, vecf32($embedding))
YIELD node AS past, score
OPTIONAL MATCH (past)-[:AFFECTED]->(s:Service)
WHERE s.name IN $alerting_names
WITH past, score, count(s) AS overlap
OPTIONAL MATCH (past)-[:MATCHES]->(fp:FailurePattern)
OPTIONAL MATCH (fp)-[res:RESOLVED_BY]->(rb:Runbook)
RETURN past.id AS incident_id,
       past.title AS title,
       coalesce(fp.name, fp.signature, 'unclassified') AS pattern,
       rb.title AS runbook_title,
       rb.actions_json AS actions,
       coalesce(res.success_count, 0) AS successes,
       coalesce(res.fail_count, 0) AS failures,
       score,
       overlap
ORDER BY overlap DESC, score DESC
LIMIT 3;
