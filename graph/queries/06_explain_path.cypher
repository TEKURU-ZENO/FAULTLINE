MATCH (a {name: $alerting}), (r {name: $root})
RETURN shortestPath((a)-[:CALLS|READS|WRITES|FLOWS_TO*]->(r)) AS path;
