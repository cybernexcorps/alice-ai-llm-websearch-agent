/**
 * loader.js — Skeleton shimmer + typing indicator helpers
 */

const Loader = {
  /** Show/hide a skeleton element by ID */
  showSkeleton(id) {
    const el = document.getElementById(id);
    if (el) el.hidden = false;
  },
  hideSkeleton(id) {
    const el = document.getElementById(id);
    if (el) el.hidden = true;
  },

  /** Show/hide the chat typing indicator */
  showTyping() {
    const el = document.getElementById('chat-typing');
    if (el) el.hidden = false;
  },
  hideTyping() {
    const el = document.getElementById('chat-typing');
    if (el) el.hidden = true;
  },

  /** Set a button into loading state */
  setLoading(btn, loading, label = null) {
    if (loading) {
      btn.disabled = true;
      if (label) btn.dataset.origLabel = btn.textContent;
      if (label) btn.textContent = label;
    } else {
      btn.disabled = false;
      if (btn.dataset.origLabel) {
        btn.textContent = btn.dataset.origLabel;
        delete btn.dataset.origLabel;
      }
    }
  },
};

window.Loader = Loader;
