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
    const tagClasses = [];
    if (Array.isArray(node.tags)) {
      if (node.tags.includes('ipynb')) tagClasses.push('tag-ipynb');
      if (node.tags.includes('project')) tagClasses.push('tag-project');
    }
    elements.push({
      group: 'nodes',
      data: { id: node.id, label: node.title, ...node },
      classes: tagClasses.join(' '),
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

  // 슈퍼노드 추가 (supernodes 배열이 있을 때만)
  if (Array.isArray(graphData.supernodes) && graphData.supernodes.length > 0) {
    for (const sn of graphData.supernodes) {
      elements.push({
        group: 'nodes',
        data: { id: sn.id, label: sn.label, tags: sn.tags, isSupernode: true },
        classes: 'supernode',
      });
    }
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
          'transition-property': 'background-color, border-color, color',
          'transition-duration': '300ms',
          'transition-timing-function': 'ease-in-out',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 'mapData(weight, 0.3, 1.0, 1, 6)',
          'line-color': '#1e1e1e',
          'opacity': 'mapData(weight, 0.3, 1.0, 0.3, 0.8)',
          'curve-style': 'bezier',
          'transition-property': 'line-color',
          'transition-duration': '300ms',
          'transition-timing-function': 'ease-in-out',
        },
      },
      {
        selector: 'node.tag-ipynb',
        style: {
          'background-color': '#00aaff',
          'border-color': '#00aaff',
        },
      },
      {
        selector: 'node.tag-project',
        style: {
          'background-color': '#0066cc',
          'border-color': '#0066cc',
        },
      },
      {
        selector: 'node.tag-ipynb.tag-project',
        style: {
          'background-color': '#00aaff',
          'border-color': '#0066cc',
          'border-width': 3,
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
          'font-size': '13px',
        },
      },
      {
        selector: 'node.hovered',
        style: {
          'background-color': '#dc00c9',
          'border-color': '#ffffff',
          'border-width': 3,
          'color': '#ffffff',
            },
      },
      {
        selector: 'edge.highlighted',
        style: {
          'line-color': '#dc00c9',
          'opacity': 1,
          'width': 'mapData(weight, 0.3, 1.0, 2, 7)',
        },
      },
      {
        selector: 'node.supernode',
        style: {
          'shape': 'diamond',
          'width': 48,
          'height': 48,
          'background-color': '#1a0018',
          'border-color': '#dc00c9',
          'border-width': 2,
          'label': 'data(label)',
          'font-size': '11px',
          'color': '#dc00c9',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-wrap': 'ellipsis',
          'text-max-width': '60px',
          'z-index': 10,
        },
      },
      {
        selector: 'node.supernode.dimmed',
        style: { 'opacity': 0.2 },
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
    userZoomingEnabled: options.userZoomingEnabled !== false,
  });

  // 노드 클릭 이벤트
  cy.on('tap', 'node', function (evt) {
    const node = evt.target;
    if (node.hasClass('supernode')) {
      const tags = node.data('tags');
      if (Array.isArray(tags) && tags.length > 0) {
        window.location.href = '/blog/index.html?tags=' + tags.map(encodeURIComponent).join(',');
      }
      return;
    }
    if (options.onNodeClick) {
      options.onNodeClick(node.data('id'));
    }
  });

  cy.on('layoutstop', function () {
    cy.fit(undefined, 40);
    applyDepthEffect(cy);
  });

  const threshold = options.hoverWeightThreshold !== undefined ? options.hoverWeightThreshold : 0.4;
  const defaultNode = options.defaultHighlightNodeId
    ? cy.getElementById(options.defaultHighlightNodeId) : null;
  setupHoverHighlight(cy, threshold, defaultNode && defaultNode.length > 0 ? defaultNode : null);

  setupEdgeTooltip(cy);

  return cy;
}

/**
 * Highlight matched nodes, dim the rest.
 * @param {Object} cy - Cytoscape instance
 * @param {string[]} matchedIds - IDs of nodes to highlight
 */
function highlightNodes(cy, matchedIds) {
  cy._searchHighlightActive = true;
  const idSet = new Set(matchedIds);
  cy.batch(function () {
    cy.nodes().forEach(function (node) {
      if (node.hasClass('supernode')) return;
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
  cy._searchHighlightActive = false;
  cy.batch(function () {
    cy.elements().removeClass('highlighted dimmed root hovered');
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

  // Render with initGraph; root node auto-highlighted via defaultHighlightNodeId
  const cy = initGraph(container, subData, { ...options, defaultHighlightNodeId: rootId });

  return cy;
}

/**
 * Highlight a node and its strong neighbors, dim the rest.
 * @param {Object} cy - Cytoscape instance
 * @param {Object} node - Cytoscape node to highlight
 * @param {number} threshold - Minimum edge weight
 * @param {string} nodeClass - Class for the focal node ('hovered' or 'root')
 */
function applyNodeHighlight(cy, node, threshold, nodeClass) {
  const strongEdges = node.connectedEdges().filter(e => e.data('weight') >= threshold);
  const strongNeighbors = strongEdges.connectedNodes().difference(node);
  cy.batch(function () {
    cy.elements().removeClass('highlighted hovered').addClass('dimmed');
    strongNeighbors.removeClass('dimmed').addClass('highlighted');
    node.removeClass('dimmed highlighted hovered').addClass(nodeClass);
    strongEdges.removeClass('dimmed').addClass('highlighted');
  });
}

/**
 * Highlight nodes/edges connected to the hovered node with weight >= threshold.
 * Skips if a search highlight is currently active.
 * @param {Object} cy - Cytoscape instance
 * @param {number} threshold - Minimum edge weight to highlight (default 0.4)
 * @param {Object|null} defaultHighlightNode - Node to keep highlighted by default (subgraph root)
 */
function setupHoverHighlight(cy, threshold, defaultHighlightNode) {
  // subgraph root node gets 'root' class but no dimming on load
  if (defaultHighlightNode) {
    cy.batch(function () {
      defaultHighlightNode.addClass('root');
    });
  }

  cy.on('mouseover', 'node', function (evt) {
    if (cy._searchHighlightActive) return;
    if (evt.target.hasClass('supernode')) return;
    // 호버 시 transition 일시 비활성화 (크기 변화 방지)
    cy.style().selector('node').style('transition-duration', 0);
    applyNodeHighlight(cy, evt.target, threshold, 'hovered');
    // 즉시 transition 복원
    cy.style().selector('node').style('transition-duration', '300ms');
  });

  cy.on('mouseout', 'node', function () {
    if (cy._searchHighlightActive) return;
    // mouseout 시 transition 일시 비활성화
    cy.style().selector('node').style('transition-duration', 0);
    cy.batch(function () {
      cy.elements().removeClass('dimmed highlighted hovered');
      if (defaultHighlightNode) {
        defaultHighlightNode.addClass('root');
      }
    });
    // 즉시 transition 복원
    cy.style().selector('node').style('transition-duration', '300ms');
  });
}

/**
 * Scale node sizes by degree (high-degree = larger = visually closer).
 * Called after layout completes.
 * @param {Object} cy - Cytoscape instance
 */
function applyDepthEffect(cy) {
  const nodes = cy.nodes().filter(n => !n.hasClass('supernode'));
  if (nodes.length === 0) return;

  // weighted degree (엣지 weight 합) 기반 — raw degree보다 분별력 높음
  const scored = nodes.map(function (node) {
    const wDeg = node.connectedEdges().reduce(function (sum, edge) {
      return sum + (edge.data('weight') || 0);
    }, 0);
    return { node: node, score: wDeg };
  });

  const scores = scored.map(function (s) { return s.score; });
  const minScore = Math.min.apply(null, scores);
  const maxScore = Math.max.apply(null, scores);
  const range = maxScore - minScore;

  const baseSize = 26;
  const enlargedSize = 42;

  cy.batch(function () {
    scored.forEach(function (entry) {
      // 점수 범위가 너무 좁으면 균일 크기 사용
      var size = range < 0.5
        ? baseSize
        : baseSize + ((entry.score - minScore) / range) * (enlargedSize - baseSize);
      entry.node.style({ width: size, height: size });
    });
  });
}

/**
 * Show a tooltip near the mouse with shared tags when hovering an edge.
 * @param {Object} cy - Cytoscape instance
 * @param {HTMLElement} container - Graph container DOM element
 */
function setupEdgeTooltip(cy) {
  // Reuse existing tooltip div (renderSubgraph re-creates cy but the DOM element is shared)
  let tip = document.getElementById('edge-tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'edge-tooltip';
    tip.style.cssText = [
      'position:fixed',
      'display:none',
      'background:#111111',
      'border:1px solid #1e1e1e',
      'color:#cccccc',
      'font-size:11px',
      'padding:4px 8px',
      'pointer-events:none',
      'z-index:9999',
      'white-space:nowrap',
    ].join(';');
    document.body.appendChild(tip);
  }

  cy.on('mouseover', 'edge', function (evt) {
    const edge = evt.target;
    const srcTags = new Set(edge.source().data('tags') || []);
    const tgtTags = (edge.target().data('tags') || []).filter(t => srcTags.has(t));
    if (tgtTags.length === 0) return;

    tip.textContent = tgtTags.map(t => '#' + t).join('  ');
    tip.style.display = 'block';
  });

  cy.on('mousemove', 'edge', function (evt) {
    if (tip.style.display === 'none') return;
    tip.style.left = (evt.originalEvent.clientX + 12) + 'px';
    tip.style.top = (evt.originalEvent.clientY - 8) + 'px';
  });

  cy.on('mouseout', 'edge', function () {
    tip.style.display = 'none';
  });

  cy.on('destroy', function () {
    tip.style.display = 'none';
  });
}
