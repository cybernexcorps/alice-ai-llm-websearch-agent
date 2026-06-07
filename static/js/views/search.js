/**
 * search.js — Search view logic
 */

const SearchView = (() => {
  let _lastQuery = '';
  let _lastAnswer = '';

  function init() {
    const btn     = document.getElementById('search-btn');
    const input   = document.getElementById('search-input');
    const jsonBtn = document.getElementById('export-json-btn');
    const mdBtn   = document.getElementById('export-md-btn');
    const newBtn  = document.getElementById('search-new-btn');

    btn.addEventListener('click', runSearch);
    input.addEventListener('keydown', (e) => {
      // Ctrl+Enter or Cmd+Enter to submit
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        runSearch();
      }
    });

    jsonBtn.addEventListener('click', () => exportResult('json'));
    mdBtn.addEventListener('click',  () => exportResult('md'));
    newBtn.addEventListener('click',  resetSearch);
  }

  function resetSearch() {
    const input  = document.getElementById('search-input');
    const result = document.getElementById('search-result');
    _lastQuery  = '';
    _lastAnswer = '';
    result.hidden = true;
    input.value   = '';
    input.focus();
  }

  async function runSearch() {
    const input = document.getElementById('search-input');
    const query = input.value.trim();
    if (!query) {
      Toast.warning('Введите поисковый запрос.');
      input.focus();
      return;
    }

    const btn = document.getElementById('search-btn');
    const skeleton = document.getElementById('search-skeleton');
    const result   = document.getElementById('search-result');

    // Reset state
    result.hidden = true;
    skeleton.hidden = false;
    btn.disabled = true;
    btn.textContent = 'Ищу...';

    try {
      const data = await AliceAPI.search(query);
      _lastQuery  = query;
      _lastAnswer = data.answer;

      document.getElementById('search-answer').innerHTML = Markdown.render(data.answer);

      skeleton.hidden = true;
      result.hidden   = false;
    } catch (err) {
      skeleton.hidden = true;
      Toast.error(`Ошибка поиска: ${err.message}`);
    } finally {
      btn.disabled    = false;
      btn.textContent = 'Искать';
      // Restore button icon
      btn.innerHTML = `<svg viewBox="0 0 20 20" fill="none" aria-hidden="true" class="btn__icon"><circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M13.5 13.5L17 17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> Искать`;
    }
  }

  async function exportResult(format) {
    if (!_lastAnswer) {
      Toast.warning('Нет результата для экспорта.');
      return;
    }
    try {
      const { blob, filename } = await AliceAPI.export(_lastQuery, _lastAnswer, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      Toast.success(`Файл ${filename} загружен.`);
    } catch (err) {
      Toast.error(`Ошибка экспорта: ${err.message}`);
    }
  }

  return { init };
})();

window.SearchView = SearchView;
