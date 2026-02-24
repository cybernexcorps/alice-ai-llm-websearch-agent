/**
 * fetch.js — URL extraction view logic
 */

const FetchView = (() => {
  function init() {
    const btn   = document.getElementById('fetch-btn');
    const input = document.getElementById('fetch-url-input');

    btn.addEventListener('click', runFetch);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); runFetch(); }
    });
  }

  async function runFetch() {
    const input = document.getElementById('fetch-url-input');
    const url = input.value.trim();
    if (!url) {
      Toast.warning('Введите URL страницы.');
      input.focus();
      return;
    }

    const btn      = document.getElementById('fetch-btn');
    const skeleton = document.getElementById('fetch-skeleton');
    const result   = document.getElementById('fetch-result');
    const content  = document.getElementById('fetch-content');

    result.hidden   = true;
    skeleton.hidden = false;
    btn.disabled    = true;

    try {
      const data = await AliceAPI.fetchUrl(url);
      content.textContent = data.content;
      skeleton.hidden = true;
      result.hidden   = false;
    } catch (err) {
      skeleton.hidden = true;
      Toast.error(`Ошибка извлечения: ${err.message}`);
    } finally {
      btn.disabled = false;
    }
  }

  return { init };
})();

window.FetchView = FetchView;
