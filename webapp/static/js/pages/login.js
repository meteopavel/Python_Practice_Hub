/* login.js — страница входа (login.html). Показывает ошибку, если пришли
   с неверными данными (?error=1 после редиректа с POST /login). */
if (new URLSearchParams(window.location.search).get('error')) {
  document.getElementById('error').classList.remove('is-hidden');
}
