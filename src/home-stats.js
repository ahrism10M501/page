(function () {
  'use strict';

  function parseDate(value) {
    if (!value || typeof value !== 'string') return null;
    const parts = value.split('-').map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
    const date = new Date(parts[0], parts[1] - 1, parts[2]);
    if (
      date.getFullYear() !== parts[0] ||
      date.getMonth() !== parts[1] - 1 ||
      date.getDate() !== parts[2]
    ) {
      return null;
    }
    date.setHours(0, 0, 0, 0);
    return date;
  }

  function daysBetween(fromDate, toDate) {
    const dayMs = 24 * 60 * 60 * 1000;
    const start = new Date(fromDate);
    const end = new Date(toDate);
    start.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);
    return Math.round((end - start) / dayMs);
  }

  function countRecentPosts(posts, rangeDays, today) {
    return posts.filter((post) => {
      const date = parseDate(post.date);
      if (!date) return false;
      const age = daysBetween(date, today);
      return age >= 0 && age < rangeDays;
    }).length;
  }

  function getTopTags(posts, limit) {
    const counts = new Map();
    posts.forEach((post) => {
      (post.tags || []).forEach((tag) => {
        if (!tag) return;
        counts.set(tag, (counts.get(tag) || 0) + 1);
      });
    });
    return Array.from(counts, ([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag))
      .slice(0, limit);
  }

  function toDateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function buildHeatmapDays(posts, totalDays, today) {
    const counts = new Map();
    posts.forEach((post) => {
      const date = parseDate(post.date);
      if (!date) return;
      const key = toDateKey(date);
      counts.set(key, (counts.get(key) || 0) + 1);
    });

    return Array.from({ length: totalDays }, (_, index) => {
      const date = new Date(today);
      date.setHours(0, 0, 0, 0);
      date.setDate(date.getDate() - (totalDays - index - 1));
      const key = toDateKey(date);
      const count = counts.get(key) || 0;
      return { date: key, count, level: levelForCount(count) };
    });
  }

  function levelForCount(count) {
    if (count >= 3) return 3;
    if (count === 2) return 2;
    if (count === 1) return 1;
    return 0;
  }

  function renderStatCard(label, value, detail) {
    const card = document.createElement('div');
    card.className = 'home-stat-card';

    const labelNode = document.createElement('span');
    labelNode.className = 'home-stat-label';
    labelNode.textContent = label;

    const valueNode = document.createElement('strong');
    valueNode.textContent = String(value);

    const detailNode = document.createElement('span');
    detailNode.className = 'home-stat-detail';
    detailNode.textContent = detail;

    card.append(labelNode, valueNode, detailNode);
    return card;
  }

  function renderHomeStats(posts, graph, twinkles) {
    const grid = document.getElementById('home-stats-grid');
    const heatmap = document.getElementById('home-heatmap');
    const tags = document.getElementById('home-top-tags');
    if (!grid || !heatmap || !tags) return;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const last90Days = countRecentPosts(posts, 90, today);
    const notebookCount = posts.filter((post) => Boolean(post.notebook)).length;
    const graphLinks = (graph.edges || graph.links || []).length;
    const twinkleCount = twinkles.length;
    const topTags = getTopTags(posts, 6);

    grid.replaceChildren(
      renderStatCard('Posts', posts.length, 'published notes'),
      renderStatCard('Last 90 days', last90Days, 'recent posts'),
      renderStatCard('Notebooks', notebookCount, 'executable posts'),
      renderStatCard('Graph links', graphLinks, 'knowledge edges'),
      renderStatCard('Twinkles', twinkleCount, 'short notes')
    );

    const heatmapDays = buildHeatmapDays(posts, 84, today);
    heatmap.replaceChildren(...heatmapDays.map((day) => {
      const cell = document.createElement('span');
      cell.className = `heatmap-day level-${day.level}`;
      cell.title = `${day.date}: ${day.count} posts`;
      cell.setAttribute('aria-label', `${day.date} ${day.count} posts`);
      return cell;
    }));

    tags.replaceChildren(...topTags.map((item) => {
      const tag = document.createElement('span');
      tag.className = 'home-top-tag';
      const name = document.createElement('span');
      name.textContent = item.tag;
      const count = document.createElement('strong');
      count.textContent = String(item.count);
      tag.append(name, count);
      return tag;
    }));
  }

  function fetchJson(url, fallback) {
    if (!url) return Promise.resolve(fallback);
    return fetch(url)
      .then((response) => (response.ok ? response.json() : fallback))
      .catch(() => fallback);
  }

  function start() {
    const script = document.currentScript;
    if (!script) return;
    const { posts, graph, twinkles } = script.dataset;

    Promise.all([
      fetchJson(posts, []),
      fetchJson(graph, { nodes: [], edges: [] }),
      fetchJson(twinkles, []),
    ]).then(([postData, graphData, twinkleData]) => {
      renderHomeStats(
        Array.isArray(postData) ? postData : [],
        graphData && typeof graphData === 'object' ? graphData : { nodes: [], edges: [] },
        Array.isArray(twinkleData) ? twinkleData : []
      );
    });
  }

  window.renderHomeStats = renderHomeStats;
  window.buildHeatmapDays = buildHeatmapDays;
  start();
}());
