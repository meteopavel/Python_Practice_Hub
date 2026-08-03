/* tutor.js — список учеников (tutor.html). Таблица с агрегатами, форма
   создания ученика, смена пароля. */

async function load() {
  const res = await fetch('/api/students');
  if (res.status === 401) { window.location.href = '/login'; return; }
  if (res.status === 403) { window.location.href = '/'; return; }
  const students = await res.json();

  document.getElementById('empty-state').classList.toggle('is-hidden', Boolean(students.length));
  document.getElementById('rows').innerHTML = students.map(s => `
    <tr class="student-row" data-id="${s.id}">
      <td><span class="row gap-2"><span class="avatar">${initials(s.username)}</span>${escapeHtml(s.username)}</span></td>
      <td class="num muted">${s.attempts_count}</td>
      <td class="col-right num muted">${s.last_attempt_at ? new Date(s.last_attempt_at).toLocaleString('ru-RU') : '—'}</td>
      <td class="col-right"><button class="btn btn-sm btn-ghost reset-pw-btn" data-id="${s.id}" data-username="${escapeHtml(s.username)}">Сменить пароль</button></td>
    </tr>
  `).join('');

  document.querySelectorAll('.student-row').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('button')) return;
      window.location.href = `/tutor/student/${row.dataset.id}`;
    });
  });
}

document.getElementById('rows').addEventListener('click', async (e) => {
  const btn = e.target.closest('.reset-pw-btn');
  if (!btn) return;
  e.stopPropagation();
  const newPassword = prompt(`Новый пароль для ${btn.dataset.username}:`);
  if (!newPassword) return;
  const res = await fetch(`/api/students/${btn.dataset.id}/password`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({password: newPassword}),
  });
  const data = await res.json();
  if (!res.ok) { alert(data.error || 'Не удалось сменить пароль'); return; }
  alert('Пароль обновлён');
});

document.getElementById('add-student-toggle').addEventListener('click', () => {
  const form = document.getElementById('add-student-form');
  form.classList.toggle('is-hidden');
});

document.getElementById('add-student-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById('add-student-error');
  errorEl.classList.add('is-hidden');
  const usernameEl = document.getElementById('new-username');
  const passwordEl = document.getElementById('new-password');
  const res = await fetch('/api/students', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: usernameEl.value.trim(), password: passwordEl.value}),
  });
  const data = await res.json();
  if (!res.ok) {
    errorEl.textContent = data.error || 'Не удалось создать ученика';
    errorEl.classList.remove('is-hidden');
    return;
  }
  usernameEl.value = '';
  passwordEl.value = '';
  document.getElementById('add-student-form').classList.add('is-hidden');
  load();
});

initHeaderUser();
load();
