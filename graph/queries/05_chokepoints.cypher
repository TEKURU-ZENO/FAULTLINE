CALL algo.betweenness({
  nodeLabels: ['Service'],
  relationshipTypes: ['CALLS'],
  samplingSize: 64,
  samplingSeed: 42
})
YIELD node, score
RETURN node.name AS service, score
ORDER BY score DESC
LIMIT 10;
