// home-graph.js — home page graph: init, random node pulse, fullscreen mode, zoom presets.
// Reads data URLs from current script's dataset:
//   data-graph, data-posts, data-twinkles, data-posts-base
//
// Required globals: cytoscape, fetchGraph, fetchPosts, renderPostList, initGraph

(function () {
  const ds = document.currentScript ? document.currentScript.dataset : {};
  const GRAPH_URL = ds.graph;
  const POSTS_URL = ds.posts;
  const TWINKLES_URL = ds.twinkles;
  const POSTS_BASE = ds.postsBase || '../posts/';
  let zoomBaseZoom = null;

  startZoomPresets();
  startGraph();

  async function startGraph() {
    const graphData = await fetchGraph(GRAPH_URL);
    const posts = await fetchPosts(POSTS_URL);
    const twinkles = await fetch(TWINKLES_URL)
      .then(r => r.ok ? r.json() : [])
      .catch(() => []);

    const hasGraph = graphData && graphData.nodes.length > 1;
    if (!hasGraph) {
      document.getElementById('graph-container').style.display = 'none';
      document.getElementById('graph-fallback').style.display = '';
      disableGraphControlsForFallback();
      renderPostList(posts, document.getElementById('posts-container'), POSTS_BASE);
      return;
    }

    const cy = initGraph(document.getElementById('graph-container'), graphData, {
      onNodeClick: slug => { window.location.href = POSTS_BASE + slug + '/'; },
      userZoomingEnabled: false,
      twinkles,
    });
    window.__indexCy = cy;
    startPulse(cy);
    startFullscreenMode(cy);
  }

  function startPulse(cy) {
    const SCALE = 1.7, GROW_MS = 500, HOLD_MS = 13000, SHRINK_MS = 500;
    const INTERVAL_MS = GROW_MS + HOLD_MS;
    const origSizes = {};
    cy.one('layoutstop', () => {
      cy.nodes().forEach(node => {
        origSizes[node.id()] = {
          w: parseFloat(node.style('width')),
          h: parseFloat(node.style('height')),
        };
      });
      pulse();
    });
    setInterval(pulse, INTERVAL_MS);

    function pulse() {
      if (!Object.keys(origSizes).length) return;
      const nodes = cy.nodes().toArray();
      const count = 2 + Math.floor(Math.random() * 2);
      const picks = nodes.slice().sort(() => Math.random() - 0.5).slice(0, Math.min(count, nodes.length));
      picks.forEach(node => {
        const orig = origSizes[node.id()];
        if (!orig) return;
        node.animate(
          { style: { width: orig.w * SCALE, height: orig.h * SCALE } },
          { duration: GROW_MS, easing: 'ease-in-out-quad', complete: () => {
            setTimeout(() => {
              node.animate(
                { style: { width: orig.w, height: orig.h } },
                { duration: SHRINK_MS, easing: 'ease-in-out-quad' }
              );
            }, HOLD_MS);
          }}
        );
      });
    }
  }

  function refreshGraphFrame(cy) {
    requestAnimationFrame(() => {
      cy.resize();
      cy.fit(undefined, 36);
      zoomBaseZoom = cy.zoom();
      resetZoomPresetState();
    });
  }

  function disableGraphControlsForFallback() {
    const toolbar = document.querySelector('.graph-toolbar');
    const openBtn = document.getElementById('graph-open-btn');
    if (openBtn) {
      openBtn.disabled = true;
      openBtn.setAttribute('aria-disabled', 'true');
      openBtn.setAttribute('aria-expanded', 'false');
    }
    if (toolbar) toolbar.hidden = true;
    setZoomPresetsFocusable(false);
  }

  function startFullscreenMode(cy) {
    const section = document.getElementById('post-graph');
    const stage = document.getElementById('graph-stage');
    const openBtn = document.getElementById('graph-open-btn');
    const closeBtn = document.getElementById('graph-close-btn');
    if (!section || !stage || !openBtn || !closeBtn) return;

    function open() {
      section.classList.add('graph-fullscreen');
      document.body.classList.add('graph-modal-open');
      openBtn.setAttribute('aria-expanded', 'true');
      stage.setAttribute('role', 'dialog');
      stage.setAttribute('aria-modal', 'true');
      stage.setAttribute('aria-label', 'Knowledge Graph');
      setZoomPresetsFocusable(true);
      refreshGraphFrame(cy);
      closeBtn.focus();
    }

    function close() {
      section.classList.remove('graph-fullscreen');
      document.body.classList.remove('graph-modal-open');
      openBtn.setAttribute('aria-expanded', 'false');
      stage.removeAttribute('role');
      stage.removeAttribute('aria-modal');
      stage.removeAttribute('aria-label');
      setZoomPresetsFocusable(false);
      refreshGraphFrame(cy);
      openBtn.focus();
    }

    function getFullscreenFocusables() {
      const zoomButtons = Array.from(document.querySelectorAll('.zoom-preset'))
        .filter(el => !el.disabled && el.tabIndex >= 0);
      return [closeBtn].concat(zoomButtons);
    }

    function handleFullscreenKeydown(e) {
      if (!section.classList.contains('graph-fullscreen')) return;
      if (e.key === 'Escape') {
        close();
        e.stopPropagation();
        return;
      }
      if (e.key === 'Tab') {
        const focusables = getFullscreenFocusables();
        if (!focusables.length) return;

        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          focusables[focusables.length - 1].focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          focusables[0].focus();
        }
      }
    }

    openBtn.addEventListener('click', open);
    closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', handleFullscreenKeydown);
  }

  function startZoomPresets() {
    const buttons = document.querySelectorAll('.zoom-preset');
    if (!buttons.length) return;
    setZoomPresetsFocusable(false);
    const center = () => {
      const cy = window.__indexCy;
      if (!cy) return null;
      return { x: cy.container().offsetWidth / 2, y: cy.container().offsetHeight / 2 };
    };
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const cy = window.__indexCy;
        if (!cy) return;
        if (zoomBaseZoom === null) zoomBaseZoom = cy.zoom();
        cy.zoom({ level: zoomBaseZoom * parseFloat(btn.dataset.zoom), renderedPosition: center() });
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }

  function setZoomPresetsFocusable(isFocusable) {
    document.querySelectorAll('.zoom-preset').forEach(btn => {
      btn.tabIndex = isFocusable ? 0 : -1;
    });
  }

  function resetZoomPresetState() {
    document.querySelectorAll('.zoom-preset').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.zoom === '1');
    });
  }
})();
