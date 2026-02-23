/**
 * chat.js — Multi-turn chat view logic
 */

const ChatView = (() => {
  let _conversationId = null;

  function init() {
    const sendBtn  = document.getElementById('chat-send-btn');
    const newBtn   = document.getElementById('chat-new-btn');
    const input    = document.getElementById('chat-input');

    sendBtn.addEventListener('click', sendMessage);
    newBtn.addEventListener('click', resetConversation);

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 140) + 'px';
    });
  }

  async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const sendBtn = document.getElementById('chat-send-btn');
    sendBtn.disabled = true;
    input.value = '';
    input.style.height = 'auto';

    // Append user bubble
    appendMessage('user', message);
    scrollToBottom();

    // Show typing indicator
    Loader.showTyping();
    scrollToBottom();

    try {
      const data = await AliceAPI.chat(message, _conversationId);
      _conversationId = data.conversation_id;

      Loader.hideTyping();
      appendMessage('alice', data.answer);
      scrollToBottom();
    } catch (err) {
      Loader.hideTyping();
      Toast.error(`Ошибка: ${err.message}`);
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  async function resetConversation() {
    if (_conversationId) {
      try { await AliceAPI.chatReset(_conversationId); } catch {}
      _conversationId = null;
    }
    const messages = document.getElementById('chat-messages');
    messages.innerHTML = `
      <div class="chat-welcome">
        <div class="chat-welcome__avatar">A</div>
        <div class="chat-welcome__text">Новый разговор начат. Задайте вопрос!</div>
      </div>`;
    Toast.info('Новый разговор начат.');
  }

  function appendMessage(role, text) {
    const messages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-message chat-message--${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-message__bubble';

    if (role === 'alice') {
      bubble.innerHTML = Markdown.render(text);
    } else {
      // User messages: escape HTML, preserve newlines
      bubble.textContent = text;
    }

    div.appendChild(bubble);
    messages.appendChild(div);
  }

  function scrollToBottom() {
    const messages = document.getElementById('chat-messages');
    requestAnimationFrame(() => {
      messages.scrollTop = messages.scrollHeight;
    });
  }

  return { init };
})();

window.ChatView = ChatView;
