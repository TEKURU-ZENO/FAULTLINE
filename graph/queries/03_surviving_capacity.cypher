MATCH (src:Service {name: $source}), (sink:Database {name: $sink})
CALL algo.maxFlow({
  sourceNodes: [src],
  targetNodes: [sink],
  relationshipTypes: ['FLOWS_TO'],
  capacityProperty: 'live_rps'
})
YIELD maxFlow, edges, edgeFlows
RETURN maxFlow;
