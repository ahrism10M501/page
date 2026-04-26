// sidebar.js — shared navigation: desktop sidebar and mobile drawer
(function () {
  function navigateTo(href) {
    if (href) window.location.href = href;
  }

  document.querySelectorAll('.sidebar-btn[data-panel]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var panelId = 'panel-' + btn.dataset.panel;
      var panel = document.getElementById(panelId);
      if (!panel) return;
      var isOpen = panel.classList.contains('open');
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
      if (!isOpen) panel.classList.add('open');
    });
  });

  document.querySelectorAll('.sidebar-btn[data-href], .mobile-nav-link[data-href]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      navigateTo(btn.dataset.href);
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('#sidebar')) {
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
    }
  });

  var legacyToggleBtn = document.getElementById('sidebar-toggle');
  var sidebar = document.getElementById('sidebar');
  if (legacyToggleBtn && sidebar) {
    legacyToggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      sidebar.classList.toggle('open');
      legacyToggleBtn.classList.toggle('active');
    });
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('open') &&
          !e.target.closest('#sidebar') &&
          e.target !== legacyToggleBtn) {
        sidebar.classList.remove('open');
        legacyToggleBtn.classList.remove('active');
      }
    });
  }

  var mobileToggle = document.getElementById('mobile-nav-toggle');
  var mobileDrawer = document.getElementById('mobile-nav-drawer');
  var mobileBackdrop = document.getElementById('mobile-nav-backdrop');

  function setMobileDrawer(open) {
    if (!mobileToggle || !mobileDrawer) return;
    document.body.classList.toggle('mobile-nav-open', open);
    mobileDrawer.classList.toggle('open', open);
    mobileDrawer.inert = !open;
    mobileDrawer.setAttribute('aria-hidden', open ? 'false' : 'true');
    mobileToggle.classList.toggle('active', open);
    mobileToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    mobileDrawer.querySelectorAll('.mobile-nav-link').forEach(function (link) {
      link.tabIndex = open ? 0 : -1;
    });
  }

  if (mobileToggle && mobileDrawer) {
    mobileToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      setMobileDrawer(!mobileDrawer.classList.contains('open'));
    });

    if (mobileBackdrop) {
      mobileBackdrop.addEventListener('click', function () {
        setMobileDrawer(false);
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (document.body.classList.contains('graph-modal-open')) return;
        setMobileDrawer(false);
      }
    });
  }
})();
