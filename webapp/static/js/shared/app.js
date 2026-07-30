/* ==========================================================================
   app.js — общий код для всех страниц (бывший inline-<script> в base.html).
   Загружается через {% block scripts %} base.html, после dom-utils.js.

   Пока тут только одно: закрытие открытой выпадашки аккаунта по клику вне.
   Раньше этот обработчик был продублирован inline в tutor/tutor_hints/
   tutor_student и отсутствовал в index/materials; при первом рефакторинге
   (переход на Jinja2) переехал в base.html — теперь, как и весь остальной JS,
   в отдельном файле.
   ========================================================================== */
document.addEventListener('click', (e) => {
  document.querySelectorAll('details.account-menu[open]').forEach(d => {
    if (!d.contains(e.target)) d.removeAttribute('open');
  });
});
