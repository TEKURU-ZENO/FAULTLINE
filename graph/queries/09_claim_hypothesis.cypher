MATCH (h:Hypothesis {status: 'open'})
WHERE NOT (h)<-[:CLAIMED]-(:Agent)
WITH h ORDER BY h.prior DESC LIMIT 1
MATCH (ag:Agent {name: $agent_name})
CREATE (ag)-[:CLAIMED {ts: $now}]->(h)
SET h.status = 'investigating'
RETURN h.id AS hypothesis_id, h.statement AS statement;
