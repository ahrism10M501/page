// sidebar.js — shared sidebar: panel toggle, navigation, outside-click close
(function () {
  // 패널 토글 버튼 (data-panel 속성 있음)
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

  // 이동 버튼 (data-href 속성 있음)
  document.querySelectorAll('.sidebar-btn[data-href]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      window.location.href = btn.dataset.href;
    });
  });

  // 사이드바 외부 클릭 시 패널 닫기
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#sidebar')) {
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
    }
  });

  // 모바일 햄버거 토글
  var toggleBtn = document.getElementById('sidebar-toggle');
  var sidebar = document.getElementById('sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      sidebar.classList.toggle('open');
      toggleBtn.classList.toggle('active');
    });
    // 사이드바 외부 탭 시 닫기
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('open') &&
          !e.target.closest('#sidebar') &&
          e.target !== toggleBtn) {
        sidebar.classList.remove('open');
        toggleBtn.classList.remove('active');
      }
    });
  }
})();
