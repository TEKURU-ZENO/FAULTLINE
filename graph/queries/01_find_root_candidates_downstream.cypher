MATCH (a:Alert)-[:FIRED_ON]->(s)
WHERE a.ts > $since
WITH collect(DISTINCT s) AS alerting
UNWIND alerting AS s
MATCH p = (s)-[:CALLS|READS|WRITES*0..4]->(dep)
WITH dep,
     count(DISTINCT s) AS covers,
     size(alerting) AS total,
     avg(length(p)) AS avg_depth
OPTIONAL MATCH (dep)<-[:OBSERVED_ON]-(an:Anomaly) WHERE an.ts > $since
OPTIONAL MATCH (dep)<-[:DEPLOYED]-(d:Deployment) WHERE d.ts > $since - 1800
RETURN dep.name AS candidate,
       toFloat(covers)/total AS coverage,
       count(DISTINCT an) AS anomalies,
       collect(DISTINCT d.version) AS recent_deploys,
       avg_depth,
       'downstream' AS branch
ORDER BY coverage DESC, anomalies DESC, avg_depth DESC
LIMIT 5;
