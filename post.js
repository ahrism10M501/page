function protectMath(src) {
  const store = [];
  // Block math ($$...$$) first to avoid matching single $ inside
  let out = src.replace(/\$\$([\s\S]+?)\$\$/g, (_, math) => {
    store.push({ block: true, math });
    return `MATHPH${store.length - 1}BLK`;
  });
  // Inline math ($...$) — single line, non-empty
  out = out.replace(/\$([^\n$]+?)\$/g, (_, math) => {
    store.push({ block: false, math });
    return `MATHPH${store.length - 1}INL`;
  });
  return { out, store };
}

function restoreMath(html, store) {
  html = html.replace(/MATHPH(\d+)BLK/g, (_, i) =>
    katex.renderToString(store[+i].math, { displayMode: true, throwOnError: false })
  );
  html = html.replace(/MATHPH(\d+)INL/g, (_, i) =>
    katex.renderToString(store[+i].math, { displayMode: false, throwOnError: false })
  );
  return html;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderNotebook(nb) {
  const parts = [];
  let first = true;

  for (const cell of nb.cells) {
    const source = Array.isArray(cell.source) ? cell.source.join('') : (cell.source || '');
    if (!source.trim()) continue;

    // 첫 번째 마크다운 셀이 frontmatter면 건너뜀
    if (first && cell.cell_type === 'markdown' && source.trim().startsWith('---')) {
      first = false;
      continue;
    }
    first = false;

    if (cell.cell_type === 'markdown') {
      const { out, store } = protectMath(source);
      parts.push(`<div class="nb-cell nb-markdown">${restoreMath(marked.parse(out), store)}</div>`);
    } else if (cell.cell_type === 'code') {
      let html = `<div class="nb-cell nb-code"><pre><code class="language-python">${escapeHtml(source)}</code></pre>`;

      const outputs = cell.outputs || [];
      if (outputs.length > 0) {
        html += '<div class="nb-output">';
        for (const out of outputs) {
          if (out.output_type === 'stream') {
            const text = Array.isArray(out.text) ? out.text.join('') : (out.text || '');
            html += `<pre class="nb-stdout">${escapeHtml(text)}</pre>`;
          } else if (out.output_type === 'display_data' || out.output_type === 'execute_result') {
            const data = out.data || {};
            if (data['image/png']) {
              html += `<img src="data:image/png;base64,${data['image/png']}" style="max-width:100%;display:block;margin:0.5rem 0">`;
            } else if (data['image/svg+xml']) {
              const svg = Array.isArray(data['image/svg+xml']) ? data['image/svg+xml'].join('') : data['image/svg+xml'];
              html += `<div class="nb-svg">${svg}</div>`;
            } else if (data['text/html']) {
              const h = Array.isArray(data['text/html']) ? data['text/html'].join('') : data['text/html'];
              html += `<div class="nb-html-out">${h}</div>`;
            } else if (data['text/plain']) {
              const t = Array.isArray(data['text/plain']) ? data['text/plain'].join('') : data['text/plain'];
              html += `<pre class="nb-stdout">${escapeHtml(t)}</pre>`;
            }
          } else if (out.output_type === 'error') {
            html += `<pre class="nb-error">${escapeHtml((out.ename || '') + ': ' + (out.evalue || ''))}</pre>`;
          }
        }
        html += '</div>';
      }

      html += '</div>';
      parts.push(html);
    }
  }
  return parts.join('\n');
}

(async () => {
  const slug = getSlugFromURL();

  // Configure marked: mermaid code blocks + YouTube extension
  mermaid.initialize({ startOnLoad: false, theme: 'dark' });

  marked.use({
    renderer: {
      code({ text, lang }) {
        if (lang === 'mermaid') return `<div class="mermaid">${text}</div>`;
        return false;
      }
    }
  });

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

  if (post && post.notebook) {
    // JupyterLite 실행 버튼 삽입
    const labUrl = `../../lab/index.html?path=posts/${slug}/content.ipynb`;
    document.getElementById('post-header').insertAdjacentHTML('afterend',
      `<div class="nb-open-bar"><a href="${labUrl}" class="nb-open-btn" target="_blank" rel="noopener">▶ JupyterLite에서 실행</a></div>`
    );
    // 노트북 fetch 및 정적 렌더링
    const nbRes = await fetch('./content.ipynb');
    if (nbRes.ok) {
      const nb = await nbRes.json();
      document.getElementById('post-content').innerHTML = renderNotebook(nb);
      document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
      mermaid.run();
    } else {
      document.getElementById('post-content').innerHTML = '<p>노트북을 불러올 수 없습니다.</p>';
    }
  } else if (mdRes.ok) {
    const md = await mdRes.text();
    const { out, store } = protectMath(stripFrontmatter(md));
    document.getElementById('post-content').innerHTML = restoreMath(marked.parse(out), store);
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    mermaid.run();
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
