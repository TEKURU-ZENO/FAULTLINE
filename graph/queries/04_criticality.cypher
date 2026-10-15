CALL algo.pageRank('Service', 'CALLS')
YIELD node, score
RETURN node.name AS service, score
ORDER BY score DESC
LIMIT 10;
