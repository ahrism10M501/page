// graph.js — Cytoscape.js presentation layer
// CDN deps: cytoscape, cytoscape-fcose

/**
 * Initialize a Cytoscape graph instance.
 * @param {HTMLElement} container - DOM element for the graph
 * @param {Object} graphData - { nodes: [...], edges: [...] }
 * @param {Object} options - { onNodeClick: fn(slug), postsBasePath: string }
 * @returns {Object} Cytoscape instance
 */
function initGraph(container, graphData, options = {}) {
  const elements = [];

  for (const node of graphData.nodes) {
    elements.push({
      group: 'nodes',
      data: { id: node.id, label: node.title, ...node },
    });
  }

  for (const edge of graphData.edges) {
    elements.push({
      group: 'edges',
      data: {
        id: edge.source + '-' + edge.target,
        source: edge.source,
        target: edge.target,
        weight: edge.weight,
      },
    });
  }

  const cy = cytoscape({
    container: container,
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'background-color': '#4a62ff',
          'color': '#cccccc',
          'font-size': '11px',
          'text-wrap': 'ellipsis',
          'text-max-width': '120px',
          'text-valign': 'bottom',
          'text-margin-y': 8,
          'width': 30,
          'height': 30,
          'border-width': 2,
          'border-color': '#4a62ff',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 'mapData(weight, 0.3, 1.0, 1, 6)',
          'line-color': '#1e1e1e',
          'opacity': 'mapData(weight, 0.3, 1.0, 0.3, 0.8)',
          'curve-style': 'bezier',
        },
      },
      {
        selector: 'node.highlighted',
        style: {
          'background-color': '#dc00c9',
          'border-color': '#dc00c9',
          'color': '#ffffff',
        },
      },
      {
        selector: 'node.dimmed',
        style: {
          'opacity': 0.15,
        },
      },
      {
        selector: 'edge.dimmed',
        style: {
          'opacity': 0.05,
        },
      },
      {
        selector: 'node.root',
        style: {
          'background-color': '#dc00c9',
          'border-color': '#dc00c9',
          'color': '#ffffff',
          'width': 40,
          'height': 40,
          'font-size': '13px',
        },
      },
    ],
    layout: {
      name: 'fcose',
      animate: true,
      animationDuration: 500,
      idealEdgeLength: function (edge) {
        return 200 / (edge.data('weight') || 0.5);
      },
      nodeRepulsion: 8000,
      edgeElasticity: 0.45,
    },
    minZoom: 0.3,
    maxZoom: 3,
  });

  // 노드 클릭 이벤트
  if (options.onNodeClick) {
    cy.on('tap', 'node', function (evt) {
      options.onNodeClick(evt.target.data('id'));
    });
  }

  return cy;
}

/**
 * Highlight matched nodes, dim the rest.
 * @param {Object} cy - Cytoscape instance
 * @param {string[]} matchedIds - IDs of nodes to highlight
 */
function highlightNodes(cy, matchedIds) {
  const idSet = new Set(matchedIds);
  cy.batch(function () {
    cy.nodes().forEach(function (node) {
      if (idSet.has(node.data('id'))) {
        node.removeClass('dimmed').addClass('highlighted');
      } else {
        node.removeClass('highlighted').addClass('dimmed');
      }
    });
    cy.edges().forEach(function (edge) {
      const srcMatch = idSet.has(edge.data('source'));
      const tgtMatch = idSet.has(edge.data('target'));
      if (srcMatch && tgtMatch) {
        edge.removeClass('dimmed');
      } else {
        edge.addClass('dimmed');
      }
    });
  });
}

/**
 * Reset all highlights.
 * @param {Object} cy - Cytoscape instance
 */
function resetHighlight(cy) {
  cy.batch(function () {
    cy.elements().removeClass('highlighted dimmed root');
  });
}

/**
 * Render a subgraph centered on rootId with BFS up to given depth.
 * Top 5 neighbors per depth level to prevent explosion.
 * @param {HTMLElement} container
 * @param {Object} graphData - { nodes, edges }
 * @param {string} rootId - slug of the center post
 * @param {number} depth - BFS depth (2-5)
 * @param {Object} options - { onNodeClick: fn(slug) }
 * @returns {Object} Cytoscape instance or null if no neighbors
 */
function renderSubgraph(container, graphData, rootId, depth, options = {}) {
  // Build adjacency list with weights
  const adj = {};
  for (const edge of graphData.edges) {
    if (!adj[edge.source]) adj[edge.source] = [];
    if (!adj[edge.target]) adj[edge.target] = [];
    adj[edge.source].push({ id: edge.target, weight: edge.weight });
    adj[edge.target].push({ id: edge.source, weight: edge.weight });
  }

  // Check if root has any neighbors
  if (!adj[rootId] || adj[rootId].length === 0) return null;

  // BFS with depth limit, top-5 per level
  const visited = new Set([rootId]);
  const nodeDepths = { [rootId]: 0 };
  let frontier = [rootId];

  for (let d = 1; d <= depth; d++) {
    const nextFrontier = [];
    for (const nodeId of frontier) {
      const neighbors = (adj[nodeId] || [])
        .filter(n => !visited.has(n.id))
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 5);
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor.id)) {
          visited.add(neighbor.id);
          nodeDepths[neighbor.id] = d;
          nextFrontier.push(neighbor.id);
        }
      }
    }
    frontier = nextFrontier;
    if (frontier.length === 0) break;
  }

  // Build subgraph data
  const subNodes = graphData.nodes.filter(n => visited.has(n.id));
  const subEdges = graphData.edges.filter(
    e => visited.has(e.source) && visited.has(e.target)
  );

  const subData = { nodes: subNodes, edges: subEdges };

  // Render with initGraph
  const cy = initGraph(container, subData, options);

  // Style by depth
  cy.batch(function () {
    cy.nodes().forEach(function (node) {
      const d = nodeDepths[node.data('id')] || 0;
      if (d === 0) {
        node.addClass('root');
      } else {
        // Dim progressively with depth
        node.style('opacity', Math.max(0.2, 1.0 - d * 0.2));
      }
    });
  });

  return cy;
}
