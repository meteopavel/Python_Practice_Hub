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

// Смена собственного пароля — раскрывающаяся форма в account-menu (base.html),
// общая для всех страниц (на /login элементов нет — ранний выход). Сервер
// проверяет текущий пароль и минимальную длину нового; совпадение повтора —
// на клиенте, до отправки. Успех — форма схлопывается, у кнопки на 3 секунды
// подтверждение (тот же приём, что «Принято» у звонка в tutor-student.js).
function initChangePasswordForm() {
  const toggle = document.getElementById('change-password-toggle');
  const form = document.getElementById('change-password-form');
  if (!toggle || !form) return;
  const errorEl = document.getElementById('change-password-error');
  const currentEl = document.getElementById('pw-current');
  const newEl = document.getElementById('pw-new');
  const repeatEl = document.getElementById('pw-repeat');

  const showError = (msg) => {
    errorEl.textContent = msg;
    errorEl.classList.remove('is-hidden');
  };
  const collapse = () => {
    form.classList.add('is-hidden');
    errorEl.classList.add('is-hidden');
    [currentEl, newEl, repeatEl].forEach(el => { el.value = ''; });
  };

  toggle.addEventListener('click', () => {
    errorEl.classList.add('is-hidden');
    form.classList.toggle('is-hidden');
    currentEl.focus();
  });
  document.getElementById('change-password-cancel').addEventListener('click', collapse);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.classList.add('is-hidden');
    if (newEl.value !== repeatEl.value) {
      showError('Новые пароли не совпадают');
      return;
    }
    const res = await fetch('/api/me/password', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({current_password: currentEl.value, new_password: newEl.value}),
    });
    if (redirectToLoginIfUnauthorized(res)) return;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showError(data.error || 'Не удалось сменить пароль');
      return;
    }
    collapse();
    toggle.textContent = 'Пароль изменён';
    setTimeout(() => { toggle.textContent = 'Сменить пароль'; }, 3000);
  });
}

initChangePasswordForm();
