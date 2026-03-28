(async () => {
  const slug = getSlugFromURL();

  // Configure marked extension before parallel fetches resolve
  marked.use({ extensions: [{
    name: 'youtube',
    level: 'block',
    start(src) {
      return src.match(/^https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)/)?.index;
    },
    tokenizer(src) {
      const match = src.match(/^(https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]+)[^\s]*)\n?/);
      if (match) return { type: 'youtube', raw: match[0], videoId: match[2] };
    },
    renderer(token) {
      return `<div class="video-container"><iframe src="https://www.youtube.com/embed/${token.videoId}" allowfullscreen></iframe></div>`;
    }
  }]});

  const [posts, mdRes, graphData] = await Promise.all([
    fetchPosts('../../blog/posts.json'),
    fetch('./content.md'),
    fetchGraph('../../blog/graph.json'),
  ]);

  const post = posts.find(p => p.slug === slug);
  if (post) {
    document.title = `${post.title} — ahrism`;
    document.getElementById('post-title').textContent = post.title;
    document.getElementById('post-meta').innerHTML =
      `<span class="label--slash">${post.date}</span>` +
      post.tags.map(t => `<span class="tag">${t}</span>`).join(' ');
  }

  if (mdRes.ok) {
    const md = await mdRes.text();
    document.getElementById('post-content').innerHTML = marked.parse(stripFrontmatter(md));
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
  } else {
    document.getElementById('post-content').innerHTML = '<p>글을 불러올 수 없습니다.</p>';
  }

  if (graphData && slug) {
    const section = document.getElementById('related-graph-section');
    const container = document.getElementById('subgraph-container');
    const slider = document.getElementById('depth-slider');
    const depthValue = document.getElementById('depth-value');
    const navigate = (id) => { window.location.href = '../' + id + '/'; };

    let subCy = renderSubgraph(container, graphData, slug, 2, { onNodeClick: navigate });

    if (subCy) {
      section.style.display = '';
      slider.addEventListener('input', function () {
        depthValue.textContent = slider.value;
        if (subCy) subCy.destroy();
        container.innerHTML = '';
        subCy = renderSubgraph(container, graphData, slug, slider.valueAsNumber, { onNodeClick: navigate });
        if (!subCy) container.innerHTML = '<div class="graph-empty">이 깊이에서 관련 글이 없습니다</div>';
      });
    }
  }
})();
