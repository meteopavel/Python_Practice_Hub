/* hints.js — админка подсказок к заданиям (tutor_hints.html). Тьютор правит
   тексты трёх уровней (markdown) + live-превью. */

// --- Минимальный клиентский markdown-рендерер (повторяет серверный из hints.py).
// Только для live-превью; финальный рендер при показе ученику — серверный.
function renderMarkdown(text) {
  if (!text) return '<span class="muted" style="font-size: var(--fs-sm)">превью появится при вводе…</span>';

  const lines = text.replace(/\r\n/g,'\n').split('\n');
  const blocks = [];
  let i = 0;
  const n = lines.length;
  const inline = t => {
    let out = escapeHtml(t);
    out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      (m, txt, url) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${txt}</a>`);
    out = out.replace(/`([^`]+)`/g, '<code class="inline">$1</code>');
    out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return out;
  };

  while (i < n) {
    const raw = lines[i];
    const s = raw.trim();
    if (!s) { i++; continue; }

    if (s.startsWith('```')) {
      i++;
      const code = [];
      while (i < n && !lines[i].trim().startsWith('```')) { code.push(lines[i]); i++; }
      i++;
      blocks.push(`<pre class="block"><code>${escapeHtml(code.join('\n'))}</code></pre>`);
      continue;
    }
    if (raw.startsWith('    ')) {
      const code = [];
      while (i < n && (lines[i].startsWith('    ') || lines[i].trim() === '')) {
        if (lines[i].trim() === '' && i + 1 < n && !lines[i+1].startsWith('    ')) break;
        code.push(lines[i].startsWith('    ') ? lines[i].slice(4) : '');
        i++;
      }
      blocks.push(`<pre class="block"><code>${escapeHtml(code.join('\n'))}</code></pre>`);
      continue;
    }
    if (s.startsWith('- ') || s.startsWith('* ')) {
      const items = [];
      while (i < n && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        items.push(`<li>${inline(lines[i].trim().slice(2))}</li>`);
        i++;
      }
      blocks.push(`<ul>${items.join('')}</ul>`);
      continue;
    }
    const para = [];
    while (i < n) {
      const cur = lines[i];
      const cs = cur.trim();
      if (!cs || cs.startsWith('```') || cur.startsWith('    ') || cs.startsWith('- ') || cs.startsWith('* ')) break;
      para.push(cs); i++;
    }
    blocks.push(`<p>${inline(para.join(' '))}</p>`);
  }
  return blocks.join('\n');
}

const LEVEL_META = [
  {level: 1, title: 'Шаг 1 · куда двигаться', desc: 'Абстрактная подсказка: слова в какую сторону двигаться, на что обратить внимание. Без прямого решения.'},
  {level: 2, title: 'Шаг 2 · конкретика со ссылками', desc: 'Подробнее: какие функции/методы помогут. Ссылки на документацию. Доступна через 7 минут после шага 1.'},
  {level: 3, title: 'Шаг 3 · почти решение', desc: 'Почти готовый код, но с пометками что ещё доделать. Доступна ещё через 15 минут после шага 2.'},
];

let currentTaskId = null;

function buildEditors() {
  const container = document.getElementById('editors');
  container.innerHTML = LEVEL_META.map(m => `
    <div class="card card-pad">
      <div class="hint-level-label">${escapeHtml(m.title)}</div>
      <div class="hint-level-desc">${escapeHtml(m.desc)}</div>
      <div class="hint-editor-row">
        <div class="field">
          <label class="label" style="font-size: var(--fs-xs)">Текст (markdown)</label>
          <textarea class="hint-editor-textarea" id="ta-${m.level}" data-level="${m.level}"></textarea>
        </div>
        <div class="field">
          <label class="label" style="font-size: var(--fs-xs)">Превью</label>
          <div class="hint-preview-box hint-content" id="pv-${m.level}"></div>
        </div>
      </div>
      <div class="save-row">
        <span class="save-status muted" id="st-${m.level}"></span>
        <button class="btn btn-sm btn-primary" id="save-${m.level}" data-level="${m.level}">Сохранить</button>
      </div>
    </div>
  `).join('');

  LEVEL_META.forEach(m => {
    const ta = document.getElementById(`ta-${m.level}`);
    const pv = document.getElementById(`pv-${m.level}`);
    ta.addEventListener('input', () => { pv.innerHTML = renderMarkdown(ta.value); });
    document.getElementById(`save-${m.level}`).addEventListener('click', () => saveLevel(m.level));
  });
}

async function loadMe() {
  const res = await fetch('/api/me');
  if (res.status === 401) { window.location.href = '/login'; return; }
  if (res.status === 403) { window.location.href = '/'; return; }
  const data = await res.json();
  document.getElementById('username').textContent = data.username || '';
  document.getElementById('avatar').textContent = (data.username || '?').slice(0, 2).toUpperCase();
}

async function loadTasks() {
  const res = await fetch('/api/admin/hints/tasks');
  if (!res.ok) return;
  const tasks = await res.json();
  const sel = document.getElementById('task-select');
  sel.innerHTML = tasks.map(t => `<option value="${t.id}">${t.id}. ${escapeHtml(t.description)}</option>`).join('');
  sel.addEventListener('change', () => loadTask(Number(sel.value)));
  if (!tasks.length) return;
  // Переход по ссылке "Редактировать подсказки" с карточки ученика
  // (tutor-student.js) — там уже выбрано конкретное задание, приходим
  // сразу на него, а не на первое по списку.
  const requestedTaskId = Number(new URLSearchParams(location.search).get('task'));
  const initialTaskId = tasks.some(t => t.id === requestedTaskId) ? requestedTaskId : tasks[0].id;
  sel.value = String(initialTaskId);
  loadTask(initialTaskId);
}

async function loadTask(taskId) {
  currentTaskId = taskId;
  const descEl = document.getElementById('task-desc');
  const opt = document.getElementById('task-select').selectedOptions[0];
  descEl.textContent = opt ? opt.text.replace(/^\d+\.\s*/, '') : '';

  const res = await fetch(`/api/admin/hints?task_id=${taskId}`);
  if (!res.ok) return;
  const data = await res.json();
  for (const lv of data.levels) {
    const ta = document.getElementById(`ta-${lv.level}`);
    const pv = document.getElementById(`pv-${lv.level}`);
    ta.value = lv.content || '';
    pv.innerHTML = renderMarkdown(ta.value);
    document.getElementById(`st-${lv.level}`).textContent = '';
  }
}

async function saveLevel(level) {
  const ta = document.getElementById(`ta-${level}`);
  const st = document.getElementById(`st-${level}`);
  const btn = document.getElementById(`save-${level}`);
  st.className = 'save-status muted';
  st.textContent = 'сохраняю…';
  btn.disabled = true;
  try {
    const res = await fetch(`/api/admin/hints/${currentTaskId}/${level}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({content: ta.value}),
    });
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      st.className = 'save-status err';
      st.textContent = data.error || 'ошибка';
      return;
    }
    st.className = 'save-status ok';
    st.textContent = 'сохранено ✓';
    setTimeout(() => { if (st.classList.contains('ok')) st.textContent = ''; }, 2500);
  } catch (e) {
    st.className = 'save-status err';
    st.textContent = 'сетевая ошибка';
  } finally {
    btn.disabled = false;
  }
}

buildEditors();
loadMe();
loadTasks();
