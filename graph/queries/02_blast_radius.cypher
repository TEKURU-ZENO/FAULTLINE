MATCH (down {name: $target})
MATCH p = (up:Service)-[:CALLS|READS|WRITES*1..5]->(down)
RETURN up.name AS impacted,
       min(length(p)) AS hops,
       up.tier AS tier
ORDER BY hops ASC;
