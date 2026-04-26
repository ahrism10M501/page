// twinkle-feed.js — paginated feed + tag archive for twinkles.
// Used by /index.html and /twinkle/ (different DOM IDs, identical behavior).
//
// Required globals: marked (markdown renderer)
//
// Usage:
//   initTwinkleFeed({
//     twinklesUrl: '/twinkle/twinkles.json',
//     sessionKey: 'twinkle-expanded',          // sessionStorage key for expanded state
//     ids: {
//       feed: 'twinkle-feed',                  // card list container
//       archive: 'twinkle-archive',
//       archiveTags: 'archive-tags',
//       archiveList: 'archive-list',
//       mobileTags: 'mobile-tags',             // optional
//       resizeHandle: 'archive-resize-handle', // optional
//       prev: 'nav-prev', next: 'nav-next',
//       cardPrefix: 'card-',                   // card element id = cardPrefix + slug
//     },
//     useHash: true,                           // sync state with location.hash
//     prependLabel: true,                      // prepend "✦ TWINKLE" label to feed innerHTML
//   });

(function (global) {
  const WINDOW_SIZE = 5;
  const PREVIEW_LEN = 300;

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function initTwinkleFeed(opts) {
    const ids = opts.ids;
    const sessionKey = opts.sessionKey;
    const useHash = !!opts.useHash;
    const prependLabel = !!opts.prependLabel;
    const labelHtml = '<div class="label">✦ TWINKLE</div>';

    const state = {
      twinkles: [],
      anchor: null,
      tag: null,
      expanded: loadExpanded(),
      page: 0,
    };

    function loadExpanded() {
      try { return new Set(JSON.parse(sessionStorage.getItem(sessionKey) || '[]')); }
      catch { return new Set(); }
    }
    function saveExpanded() {
      sessionStorage.setItem(sessionKey, JSON.stringify([...state.expanded]));
    }

    function filterByTag(list) {
      return state.tag ? list.filter(t => t.tags.includes(state.tag)) : list;
    }

    function setHash(value) {
      if (!useHash) return;
      history.replaceState(null, '', value || location.pathname);
    }

    function renderCard(t) {
      const isAnchor = t.slug === state.anchor;
      const isExpanded = state.expanded.has(t.slug);
      const needsTrunc = t.content.length > PREVIEW_LEN;
      const rawBody = (needsTrunc && !isExpanded) ? t.content.slice(0, PREVIEW_LEN) + '...' : t.content;
      const body = marked.parse(rawBody);
      const tagsHtml = t.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join(' ');
      const moreBtn = needsTrunc
        ? `<button class="twinkle-more-btn" data-slug="${escapeAttr(t.slug)}">${isExpanded ? '▲ 접기' : '▼ 더보기'}</button>`
        : '';
      return `<div class="twinkle-card${isAnchor ? ' anchor' : ''}" id="${ids.cardPrefix}${escapeAttr(t.slug)}">
        <div class="twinkle-card-header">
          <span class="twinkle-card-date">${escapeHtml(t.date)}</span>
          <span>${tagsHtml}</span>
        </div>
        <div class="twinkle-card-body">${body}</div>
        ${moreBtn}
      </div>`;
    }

    function renderFeed() {
      const filtered = filterByTag(state.twinkles);
      const start = state.page * WINDOW_SIZE;
      const win = filtered.slice(start, start + WINDOW_SIZE);
      const totalPages = Math.ceil(filtered.length / WINDOW_SIZE);
      const navHtml = filtered.length > WINDOW_SIZE ? `<div class="twinkle-nav">
        <button class="twinkle-nav-btn" id="${ids.prev}"${state.page === 0 ? ' disabled' : ''}>← 이전</button>
        <span class="twinkle-nav-info">${start + 1}–${Math.min(start + WINDOW_SIZE, filtered.length)} / ${filtered.length}</span>
        <button class="twinkle-nav-btn" id="${ids.next}"${state.page >= totalPages - 1 ? ' disabled' : ''}>다음 →</button>
      </div>` : '';

      const feed = document.getElementById(ids.feed);
      const cards = win.length
        ? win.map(renderCard).join('')
        : '<p style="color:#555;font-size:0.85rem">트윈클이 없습니다.</p>';
      feed.innerHTML = (prependLabel ? labelHtml : '') + cards + navHtml;

      feed.querySelectorAll('.twinkle-more-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const slug = btn.dataset.slug;
          if (state.expanded.has(slug)) state.expanded.delete(slug);
          else state.expanded.add(slug);
          saveExpanded();
          renderFeed();
        });
      });
      const prev = feed.querySelector('#' + ids.prev);
      const next = feed.querySelector('#' + ids.next);
      if (prev) prev.addEventListener('click', () => { state.page--; renderFeed(); renderArchive(); });
      if (next) next.addEventListener('click', () => { state.page++; renderFeed(); renderArchive(); });
    }

    function renderTagChips(containerId, chipClass) {
      const el = document.getElementById(containerId);
      if (!el) return;
      const allTags = [...new Set(state.twinkles.flatMap(t => t.tags))];
      const tagLabels = ['전체', ...allTags];
      el.innerHTML = tagLabels.map(tag => {
        const isActive = tag === '전체' ? !state.tag : state.tag === tag;
        return `<button type="button" class="${chipClass}${isActive ? ' active' : ''}" data-tag="${escapeAttr(tag)}" aria-pressed="${isActive ? 'true' : 'false'}">${escapeHtml(tag)}</button>`;
      }).join('');
      el.querySelectorAll('.' + chipClass).forEach(chip => {
        chip.addEventListener('click', () => {
          state.tag = chip.dataset.tag === '전체' ? null : chip.dataset.tag;
          state.anchor = null;
          state.page = 0;
          setHash(null);
          renderFeed();
          renderArchive();
        });
      });
    }

    function renderArchive() {
      renderTagChips(ids.archiveTags, 'archive-tag-chip');
      if (ids.mobileTags) renderTagChips(ids.mobileTags, 'twinkle-mobile-tag-chip');

      const filtered = filterByTag(state.twinkles);
      const list = document.getElementById(ids.archiveList);
      list.innerHTML = filtered.map(t =>
        `<div class="archive-item${t.slug === state.anchor ? ' active' : ''}" data-slug="${escapeAttr(t.slug)}" title="${escapeHtml(t.title)}">
          <span class="archive-date">${escapeHtml(t.date).slice(5)}</span>${escapeHtml(t.title)}
        </div>`
      ).join('');
      list.querySelectorAll('.archive-item').forEach(item => {
        item.addEventListener('click', () => {
          const f = filterByTag(state.twinkles);
          const idx = f.findIndex(t => t.slug === item.dataset.slug);
          state.anchor = item.dataset.slug;
          state.page = idx === -1 ? 0 : Math.floor(idx / WINDOW_SIZE);
          setHash('#' + state.anchor);
          renderFeed();
          renderArchive();
        });
      });
    }

    function initResizeDrag() {
      if (!ids.resizeHandle || !ids.archive) return;
      const handle = document.getElementById(ids.resizeHandle);
      const archive = document.getElementById(ids.archive);
      if (!handle || !archive) return;
      let startX, startW;
      handle.addEventListener('mousedown', e => {
        startX = e.clientX;
        startW = archive.offsetWidth;
        function onMove(ev) {
          const newWidth = Math.max(120, Math.min(400, startW + (startX - ev.clientX)));
          archive.style.width = newWidth + 'px';
          const layout = document.querySelector('.twinkle-layout');
          if (layout) layout.style.marginRight = newWidth + 'px';
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', () => document.removeEventListener('mousemove', onMove), { once: true });
      });
    }

    (async () => {
      try {
        const res = await fetch(opts.twinklesUrl);
        if (!res.ok) throw new Error(res.status);
        state.twinkles = await res.json();
      } catch (e) {
        document.getElementById(ids.feed).innerHTML =
          (prependLabel ? labelHtml : '') + '<p style="color:#555">twinkles.json 로드 실패.</p>';
        return;
      }

      if (useHash) {
        const hash = location.hash.slice(1);
        if (hash) {
          const idx = state.twinkles.findIndex(t => t.slug === hash);
          if (idx !== -1) {
            state.anchor = hash;
            state.page = Math.floor(idx / WINDOW_SIZE);
          }
        }
      }

      renderFeed();
      renderArchive();
      initResizeDrag();
    })();
  }

  global.initTwinkleFeed = initTwinkleFeed;
})(window);
