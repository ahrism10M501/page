// Format YYYY-MM-DD → "Jan 15"
function formatPostDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Strip YAML frontmatter (---...---) from markdown text before rendering
function stripFrontmatter(md) {
  if (!md.startsWith('---')) return md;
  const end = md.indexOf('\n---', 3);
  if (end === -1) return md;
  return md.slice(end + 4).replace(/^\n/, '');
}

// Fetch posts.json from a relative path and return parsed array
async function fetchPosts(jsonPath) {
  try {
    const res = await fetch(jsonPath);
    if (!res.ok) return [];
    return res.json();
  } catch (e) {
    return [];
  }
}

// Render a list of posts into a container element
// Each post: { slug, title, date, tags, summary }
// postsBasePath: relative path prefix to posts/ directory
function renderPostList(posts, container, postsBasePath) {
  container.innerHTML = '';
  posts.forEach(post => {
    const item = document.createElement('a');
    item.href = `${postsBasePath}${post.slug}/`;
    item.className = 'post-item';
    item.innerHTML = `
      <div class="post-item-row">
        <h3>${post.title}</h3>
        <span class="post-date-inline">${formatPostDate(post.date)}</span>
      </div>
      <div class="post-meta" style="margin-top:0.25rem">
        ${post.tags.map(t => `<span class="tag">${t}</span>`).join(' ')}
      </div>
      ${post.summary ? `<p style="color:#666;font-size:0.85rem;margin-top:0.3rem;margin-bottom:0">${post.summary}</p>` : ''}
    `;
    container.appendChild(item);
  });
}

// Extract slug from current URL path
// e.g., /repo/posts/my-post/ → "my-post"
// e.g., /repo/posts/my-post/index.html → "my-post"
function getSlugFromURL() {
  const path = window.location.pathname.replace(/\/index\.html$/, '').replace(/\/$/, '');
  const parts = path.split('/');
  return decodeURIComponent(parts[parts.length - 1]);
}

// Render projects from projects.json into a horizontal scroll container
// Each project: { title, description, tags, link }
function renderProjectCards(projects, container) {
  container.innerHTML = '';
  container.className = 'project-scroll';
  projects.forEach(project => {
    const card = document.createElement('a');
    card.href = project.link || '#';
    card.target = '_blank';
    card.rel = 'noopener noreferrer';
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${project.title}</h3>
      <p>${project.description}</p>
      <div class="card-tags">
        ${(project.tags || []).map(t => `<span class="tag">${t}</span>`).join('')}
      </div>
    `;
    container.appendChild(card);
  });
}

// Fetch graph.json and return parsed object { nodes, edges }
async function fetchGraph(jsonPath) {
  try {
    const res = await fetch(jsonPath);
    if (!res.ok) return null;
    return res.json();
  } catch (e) {
    return null;
  }
}

// Search nodes by query. mode: "text" (default) or "tfidf"
// Returns array of matching node IDs
function searchPosts(nodes, query, mode) {
  if (!query || !query.trim()) return nodes.map(n => n.id);
  const q = query.trim().toLowerCase();

  if (mode === 'tfidf') {
    // TF-IDF 키워드 가중 매칭: 쿼리 단어와 노드 tfidf 키 매칭, 점수 합산
    const queryWords = q.split(/\s+/);
    const scored = nodes.map(node => {
      const tfidf = node.tfidf || {};
      let score = 0;
      for (const word of queryWords) {
        for (const [keyword, value] of Object.entries(tfidf)) {
          if (keyword.includes(word) || word.includes(keyword)) {
            score += value;
          }
        }
      }
      return { id: node.id, score };
    });
    // 점수 > 0인 노드만, 점수 내림차순
    return scored.filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(s => s.id);
  }

  // 기본 텍스트 매칭: 제목 또는 요약에 쿼리 포함
  return nodes.filter(n =>
    (n.title && n.title.toLowerCase().includes(q)) ||
    (n.summary && n.summary.toLowerCase().includes(q))
  ).map(n => n.id);
}

// Filter nodes by active tags (OR condition)
// Returns array of matching node IDs
function filterByTags(nodes, activeTags) {
  if (!activeTags || activeTags.length === 0) return nodes.map(n => n.id);
  return nodes.filter(n =>
    n.tags && n.tags.some(t => activeTags.includes(t))
  ).map(n => n.id);
}
