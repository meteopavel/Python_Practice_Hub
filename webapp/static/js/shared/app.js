/* ==========================================================================
   app.js — общий код для всех страниц (бывший inline-<script> в base.html).
   Загружается через base.html, после dom-utils.js, до {% block scripts %}
   каждой страницы.
   ========================================================================== */

// Закрытие открытой выпадашки аккаунта по клику вне. Раньше этот обработчик
// был продублирован inline в tutor/tutor_hints/tutor_student и отсутствовал
// в index/materials; при переходе на Jinja2 переехал сюда.
document.addEventListener('click', (e) => {
  document.querySelectorAll('details.account-menu[open]').forEach(d => {
    if (!d.contains(e.target)) d.removeAttribute('open');
  });
});

// #username/#avatar в хедере (base.html) — на каждой странице. Раньше
// одна и та же реализация (fetch /api/me + textContent + initials) была
// продублирована в student.js/tutor.js/tutor-student.js/hints.js/materials.js.
// Возвращает данные пользователя — страницам с доп. логикой (импersonation,
// переключатель ученика) они нужны дальше; при 401 возвращает null (уже
// редиректнув на /login).
async function initHeaderUser() {
  const res = await fetch('/api/me');
  if (redirectToLoginIfUnauthorized(res)) return null;
  const data = await res.json();
  document.getElementById('username').textContent = data.username || '';
  document.getElementById('avatar').textContent = initials(data.username);
  return data;
}
