/**
 * toast.js — Russian toast notification system
 */

const Toast = (() => {
  const DURATION = 4000;

  function show(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.innerHTML = `<div class="toast__dot"></div><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => dismiss(toast), DURATION);
    return toast;
  }

  function dismiss(toast) {
    toast.classList.add('toast--out');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }

  return {
    info:    (msg) => show(msg, 'info'),
    success: (msg) => show(msg, 'success'),
    error:   (msg) => show(msg, 'error'),
    warning: (msg) => show(msg, 'warning'),
  };
})();

window.Toast = Toast;
