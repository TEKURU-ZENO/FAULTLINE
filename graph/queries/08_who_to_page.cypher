MATCH (rc {name: $root})<-[:OWNS]-(t:Team)<-[:MEMBER_OF]-(p:Person)
OPTIONAL MATCH (p)-[oc:ON_CALL]->(t)
WHERE oc.from <= $now AND oc.to > $now
OPTIONAL MATCH (p)<-[:FIXED_BY_PERSON]-(i:Incident)-[:ROOT_CAUSE]->(rc)
RETURN p.name AS name,
       p.handle AS handle,
       oc IS NOT NULL AS on_call,
       count(DISTINCT i) AS prior_fixes
ORDER BY on_call DESC, prior_fixes DESC;
