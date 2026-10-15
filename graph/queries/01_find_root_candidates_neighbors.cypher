MATCH (a:Alert)-[:FIRED_ON]->(s)
WHERE a.ts > $since
MATCH (s)-[:CALLS|READS|WRITES*1..2]-(n)<-[:OBSERVED_ON]-(an:Anomaly)
WHERE an.ts > $since
OPTIONAL MATCH (n)<-[:DEPLOYED]-(d:Deployment) WHERE d.ts > $since - 1800
RETURN DISTINCT n.name AS candidate,
       1.0 AS coverage,
       count(DISTINCT an) AS anomalies,
       collect(DISTINCT d.version) AS recent_deploys,
       1.0 AS avg_depth,
       'neighbor' AS branch
ORDER BY anomalies DESC
LIMIT 5;
