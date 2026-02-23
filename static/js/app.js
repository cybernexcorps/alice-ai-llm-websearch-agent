/**
 * app.js — View router, keyboard shortcuts, page-load animation
 */

const App = (() => {
  const VIEWS = ['search', 'chat', 'fetch', 'config'];
  let _current = 'search';

  /** Switch to the given view with a fade transition */
  function navigate(viewId) {
    if (!VIEWS.includes(viewId) || viewId === _current) return;

    // Fade out current view
    const currentSection = document.getElementById(`view-${_current}`);
    if (currentSection) {
      currentSection.classList.remove('view--active');
      currentSection.hidden = true;
    }

    // Update nav items (sidebar + tab bar)
    document.querySelectorAll('[data-view]').forEach((el) => {
      el.classList.toggle('nav-item--active', el.dataset.view === viewId);
      el.classList.toggle('tab-item--active', el.dataset.view === viewId);
      if (el.dataset.view === viewId) {
        el.setAttribute('aria-current', 'page');
      } else {
        el.removeAttribute('aria-current');
      }
    });

    // Fade in new view
    const nextSection = document.getElementById(`view-${viewId}`);
    if (nextSection) {
      nextSection.hidden = false;
      // Trigger reflow for animation
      void nextSection.offsetHeight;
      nextSection.classList.add('view--active');
    }

    _current = viewId;

    // Notify views that need lazy loading
    if (viewId === 'config') {
      ConfigView.onActivate();
    }
  }

  function init() {
    // Wire nav items and tab items
    document.querySelectorAll('[data-view]').forEach((el) => {
      el.addEventListener('click', () => navigate(el.dataset.view));
    });

    // Keyboard shortcuts: Alt+1..4
    document.addEventListener('keydown', (e) => {
      if (!e.altKey) return;
      const idx = parseInt(e.key, 10);
      if (idx >= 1 && idx <= VIEWS.length) {
        e.preventDefault();
        navigate(VIEWS[idx - 1]);
      }
    });

    // Initialize all views
    SearchView.init();
    ChatView.init();
    FetchView.init();
    ConfigView.init();

    // Start on search view
    navigate('search');
  }

  return { init, navigate };
})();

// Boot
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
