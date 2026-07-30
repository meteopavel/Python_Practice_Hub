/* ==========================================================================
   dom-utils.js — мелкие переиспользуемые хелперы (общие для всех страниц)
   Самодостаточен: не зависит от внешних функций страницы. sendMessage
   ожидает глобальную переменную `ws` (WebSocket), объявленную самой страницей.
   ========================================================================== */

function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value === undefined ? '' : String(value);
  return div.innerHTML;
}

function redirectToLoginIfUnauthorized(res) {
  if (res.status === 401) {
    window.location.href = '/login';
    return true;
  }
  return false;
}

function sendMessage(payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  }
}
