/* ==========================================================================
   dom-utils.js — мелкие переиспользуемые хелперы (общие для всех страниц)
   Самодостаточен: не зависит от внешних функций страницы. sendMessage ищет
   глобальную переменную `ws` (WebSocket), объявленную самой страницей;
   на страницах без неё молча не отправляет ничего.
   ========================================================================== */

// textContent→innerHTML экранирует & < >, но не кавычки — небезопасно для
// использования внутри атрибутов (attr="${escapeHtml(x)}"), поэтому regex.
function escapeHtml(value) {
  return String(value === undefined ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function initials(name) {
  return (name || '?').slice(0, 2).toUpperCase();
}

function redirectToLoginIfUnauthorized(res) {
  if (res.status === 401) {
    window.location.href = '/login';
    return true;
  }
  return false;
}

function sendMessage(payload) {
  if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  }
}
