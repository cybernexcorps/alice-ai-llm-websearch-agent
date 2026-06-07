/**
 * config.js — Configuration status panel
 */

const ConfigView = (() => {
  let _loaded = false;

  function init() {
    // Config is loaded lazily on first view activation
  }

  async function onActivate() {
    if (_loaded) return;
    await loadConfig();
  }

  async function loadConfig() {
    try {
      const data = await AliceAPI.config();
      renderConfig(data);
      _loaded = true;
    } catch (err) {
      Toast.error(`Ошибка загрузки конфигурации: ${err.message}`);
    }
  }

  function renderConfig(data) {
    document.getElementById('config-skeleton').hidden = true;

    const grid = document.getElementById('config-grid');
    grid.hidden = false;

    document.getElementById('cfg-version').textContent = data.version;
    document.getElementById('sidebar-version').textContent = `v${data.version}`;
    document.getElementById('cfg-agent-id').textContent  = data.agent_id;
    document.getElementById('cfg-folder-id').textContent = data.folder_id;
    document.getElementById('cfg-endpoint').textContent  = data.endpoint;
    document.getElementById('cfg-max-steps').textContent = data.max_steps;

    const dot  = document.getElementById('cfg-api-dot');
    const text = document.getElementById('cfg-api-text');
    if (data.api_key_configured) {
      dot.className  = 'status-dot status-dot--ok';
      text.textContent = 'Настроен';
    } else {
      dot.className  = 'status-dot status-dot--error';
      text.textContent = 'Не настроен';
      Toast.warning('ALICE_YC_API_KEY не установлен.');
    }
  }

  return { init, onActivate };
})();

window.ConfigView = ConfigView;
