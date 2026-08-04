/* tutor-student.js — работа тьютора с учеником (tutor_student.html). Список
   заданий, live-зеркало кода ученика, редактор подсказки, ИИ-ассистент,
   мониторинг раскрытых подсказок, пересылка ссылки на созвон.

   Зависимости (грузятся раньше, см. {% block scripts %} в tutor_student.html):
     codemirror.bundle.js, js/lib/attempts.js, js/lib/dom-utils.js,
     js/lib/grade-render.js, js/lib/task-nav.js, js/lib/call-audio.js +
     js/shared/calls.js (выключенный WebRTC-звонок), js/shared/icons.js
     (ICON, HINT_MARKERS, HINT_LEVEL_TITLES, ICON_MIC...). */

const studentId = Number(window.location.pathname.split('/').pop());
document.getElementById('impersonate-form').action = `/tutor/student/${studentId}/impersonate`;

const ICON_EDIT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>';
document.getElementById('impersonate-btn').innerHTML = ICON_EYE;
document.getElementById('hints-edit-link').innerHTML = ICON_EDIT;

async function loadStudentSwitcher() {
  const res = await fetch('/api/students');
  if (!res.ok) return;
  const students = await res.json();
  const current = students.find(s => s.id === studentId);
  document.getElementById('switcher-current-name').textContent = current ? current.username : '…';
  document.title = `${current ? current.username : 'Ученик'} — Python Practice Hub`;
  const list = document.getElementById('switcher-list');
  const backLink = '<a class="account-menu-item" href="/" style="display: block; text-decoration: none;">← к списку учеников</a><div class="account-menu-divider"></div>';
  const studentsHtml = students.length
    ? students.map(s => `
        <button class="account-menu-item" data-id="${s.id}"${s.id === studentId ? ' style="font-weight: var(--fw-semibold)"' : ''}>${escapeHtml(s.username)}</button>
      `).join('')
    : '<span class="account-menu-empty">Нет учеников</span>';
  list.innerHTML = backLink + studentsHtml;
  list.querySelectorAll('button[data-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (Number(btn.dataset.id) === studentId) return;
      window.location.href = `/tutor/student/${btn.dataset.id}`;
    });
  });
}

const codeByTask = {}; // task_id -> последний известный код ученика по этому заданию
let mirrorEditor = PracticeHubEditor.create(
  document.getElementById('student-mirror-mount'), '', null, {readOnly: true}
);
let editingStudentCode = false;
let editSendTimer = null;

// По умолчанию код ученика доступен только для просмотра — правка по кнопке,
// пересоздаём редактор с/без readOnly (у обёртки нет способа переключить это
// на лету, только пересоздание с сохранением текущего значения).
function setEditingStudentCode(enabled) {
  editingStudentCode = enabled;
  const mount = document.getElementById('student-mirror-mount');
  const value = mirrorEditor.getValue();
  mount.innerHTML = '';
  if (enabled) {
    mirrorEditor = PracticeHubEditor.create(mount, value, (code) => {
      codeByTask[currentTaskId] = code;
      clearTimeout(editSendTimer);
      editSendTimer = setTimeout(() => sendMessage({type: 'tutor_edit_code', code, task_id: currentTaskId}), 300);
    });
  } else {
    mirrorEditor = PracticeHubEditor.create(mount, value, null, {readOnly: true});
  }
  document.getElementById('student-mirror-bar-label').textContent = enabled ? 'вы правите код ученика' : 'live, read-only';
  document.getElementById('edit-student-code-btn').textContent = enabled ? 'Готово' : 'Править код ученика';
}
document.getElementById('edit-student-code-btn').addEventListener('click', () => setEditingStudentCode(!editingStudentCode));

// Подсказка по умолчанию скрыта от ученика — тьютор явно переключает режим
// по клику на кнопку, три состояния по кругу: hidden (совсем не видна) →
// protected (видна, но не копируется) → open (видна и копируется) → hidden.
const HINT_MODES = ['hidden', 'protected', 'open'];
const HINT_MODE_LABELS = {hidden: 'Скрыто от ученика', protected: 'Нельзя копировать', open: 'Видно ученику'};
const HINT_MODE_ICONS = {hidden: 'lock', protected: 'eye', open: 'unlock'};
let hintMode = 'hidden';
function cycleHintMode() {
  hintMode = HINT_MODES[(HINT_MODES.indexOf(hintMode) + 1) % HINT_MODES.length];
  const btn = document.getElementById('hint-lock-btn');
  btn.innerHTML = ICON(HINT_MODE_ICONS[hintMode]) + ' ' + HINT_MODE_LABELS[hintMode];
  sendMessage({type: 'hint_visibility', mode: hintMode});
  if (hintMode !== 'hidden') sendMessage({code: hintEditor.getValue()});
}
document.getElementById('hint-lock-btn').addEventListener('click', cycleHintMode);

let hintSendTimer = null;
const hintEditor = PracticeHubEditor.create(
  document.getElementById('hint-mount'),
  '',
  (code) => {
    clearTimeout(hintSendTimer);
    hintSendTimer = setTimeout(() => { if (hintMode !== 'hidden') sendMessage({code}); }, 300);
  }
);

let tasks = [];
let currentTaskId = null;
const taskStatus = {};

// Запоминаем последнее открытое задание и страницу списка ПРИВЯЗАННО к
// ученику: тьютор переключается между учениками, и у каждого свой прогресс
// по заданиям — выбор не должен «прыгать» за тьютором при смене ученика.
function lastTaskKey(suffix) { return `pph:tutor:${studentId}:${suffix}`; }

async function loadTasks() {
  const res = await fetch('/api/tasks');
  if (res.status === 401) { window.location.href = '/login'; return; }
  tasks = await res.json();

  // Восстанавливаем последнее открытое задание этого ученика, если оно
  // доступно (задание могло быть скрыто из грейдера).
  const savedId = Number(localStorage.getItem(lastTaskKey('taskId')));
  const savedPage = Number(localStorage.getItem(lastTaskKey('page')));
  const savedTaskExists = tasks.some(t => t.id === savedId);
  currentTaskId = savedTaskExists ? savedId : (tasks.length ? tasks[0].id : null);
  if (savedTaskExists && Number.isFinite(savedPage)) taskPage = savedPage;

  const statusRes = await fetch(`/api/students/${studentId}/attempts/status`);
  if (statusRes.status === 403 || statusRes.status === 404) { window.location.href = '/'; return; }
  if (statusRes.ok) {
    const status = await statusRes.json();
    for (const [taskId, s] of Object.entries(status)) taskStatus[taskId] = s;
  }

  renderTaskList();
  showTask();
}

const TASK_PAGE_SIZE = 7;
let taskPage = 0;

function selectTask(taskId) {
  currentTaskId = taskId;
  // Активное задание должно быть видно в списке — перейдём на его страницу.
  const idx = tasks.findIndex(t => t.id === currentTaskId);
  if (idx !== -1) taskPage = Math.floor(idx / TASK_PAGE_SIZE);
  renderTaskList();
  showTask();
  saveLastTask();
}

const renderTaskList = initTaskList(selectTask);

function showTask() {
  const task = tasks.find(t => t.id === currentTaskId);
  document.getElementById('task-title').textContent = task ? `Задание ${task.id}` : '';
  document.getElementById('description').innerHTML = task
    ? `<p>${escapeHtml(task.description)}</p><p><strong style="color: var(--c-ink)">Пример:</strong> ${escapeHtml(task.example)}</p>`
    : '';
  loadStudentAttempts(currentTaskId);
  if (!editingStudentCode) mirrorEditor.setValue(codeByTask[currentTaskId] || '');
  document.getElementById('student-submit-result').innerHTML = '';
  document.getElementById('hint-result').innerHTML = '';
  loadHintsPanel(currentTaskId);
  if (typeof refreshAiTaskLabel === 'function') refreshAiTaskLabel();
}

async function loadStudentAttempts(taskId) {
  const section = document.getElementById('student-attempts-section');
  if (taskId === null) { section.classList.add('is-hidden'); return; }
  const res = await fetch(`/api/students/${studentId}/attempts/${taskId}`);
  if (!res.ok) { section.classList.add('is-hidden'); return; }
  const attempts = await res.json();
  section.classList.toggle('is-hidden', !attempts.length);
  // onDelete передаётся только тьютором: у ученика кнопки удаления попыток нет.
  PPHAttempts.render(document.getElementById('student-attempts-rows'), attempts, PracticeHubEditor.create, {
    onDelete: deleteStudentAttempt,
  });
}

// Удаление одной попытки ученика (feat.2): тьютор удаляет любую попытку —
// удачную или нет, в любом порядке. Если удалена последняя удачная — задание
// перестаёт быть решённым; если удалены все — возвращается в начальное
// состояние (нет индикатора). Список попыток перезагружается, точка статуса
// перерисовывается из ответа; ученику летит attempts_changed, чтобы он тоже
// перезагрузился live.
async function deleteStudentAttempt(attemptId) {
  if (!confirm('Удалить эту попытку ученика? Действие необратимо.')) return false;
  try {
    const res = await fetch(`/api/students/${studentId}/attempts/${attemptId}`, {method: 'DELETE'});
    if (res.status === 401) { window.location.href = '/login'; return false; }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.error || 'Не удалось удалить попытку');
      return false;
    }
    const data = await res.json();
    // status: 'pass' | 'fail' | null. null — попыток по задаче не осталось,
    // индикатор исчезает (как при монотонном pass в task_status_map).
    if (data.status) taskStatus[currentTaskId] = data.status;
    else delete taskStatus[currentTaskId];
    renderTaskList();
    loadStudentAttempts(currentTaskId);
    sendMessage({type: 'attempts_changed', task_id: currentTaskId, status: data.status});
    return true;
  } catch (e) {
    return false;
  }
}

async function runHintCode() {
  if (currentTaskId === null) return;
  const btn = document.getElementById('run-hint-btn');
  const resultEl = document.getElementById('hint-result');
  btn.disabled = true;
  btn.textContent = 'Проверяю...';
  try {
    const code = hintEditor.getValue();
    const res = await fetch('/api/hint/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task_id: currentTaskId, code}),
    });
    const result = await res.json();
    renderGradeResult(resultEl, result);
    sendMessage({type: 'hint_result', task_id: currentTaskId, result});
  } finally {
    btn.disabled = false;
    btn.textContent = 'Проверить';
  }
}
document.getElementById('run-hint-btn').addEventListener('click', runHintCode);

async function runFreeHintCode() {
  const btn = document.getElementById('run-hint-free-btn');
  const resultEl = document.getElementById('hint-result');
  btn.disabled = true;
  btn.textContent = 'Запускаю...';
  try {
    const code = hintEditor.getValue();
    const res = await fetch('/api/hint/run_free', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({code}),
    });
    const result = await res.json();
    renderFreeRunResult(resultEl, result);
    sendMessage({type: 'hint_free_result', result});
  } finally {
    btn.disabled = false;
    btn.textContent = 'Запустить';
  }
}
document.getElementById('run-hint-free-btn').addEventListener('click', runFreeHintCode);

// --- Спросить ИИ (DeepSeek через tutor-llm) --------------------------------
// Автоподстановка контекста: при смене задания обновляем номер в чекбоксе.
// Код ученика берём из live-редактора (mirrorEditor), как и при проверке.
const aiAttachTask = document.getElementById('ai-attach-task');
const aiAttachTaskNum = document.getElementById('ai-attach-task-num');
const aiAttachCode = document.getElementById('ai-attach-code');
const aiQuestion = document.getElementById('ai-question');
const aiAskBtn = document.getElementById('ai-ask-btn');
const aiAskResult = document.getElementById('ai-ask-result');
const aiModelLabel = document.getElementById('ai-ask-model-label');

function refreshAiTaskLabel() {
  aiAttachTaskNum.textContent = currentTaskId ? `№${currentTaskId}` : '—';
}

async function askAi() {
  const question = aiQuestion.value.trim();
  if (!question) { aiAskResult.innerHTML = '<p class="field-error" style="margin:0">Введите вопрос</p>'; return; }

  const body = {question};
  if (aiAttachTask.checked && currentTaskId !== null) {
    const task = tasks.find(t => t.id === currentTaskId);
    if (task) body.task_context = `Задание ${task.id}: ${task.description}\nПример: ${task.example}`;
  }
  if (aiAttachCode.checked) {
    const code = mirrorEditor.getValue();
    if (code.trim()) body.student_code = code;
  }

  aiAskBtn.disabled = true;
  aiAskBtn.textContent = 'Думаю...';
  aiAskResult.innerHTML = '<p class="muted" style="margin:0">Запрос ушёл в DeepSeek, ждём ответ...</p>';
  try {
    const res = await fetch('/api/tutor/ask', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      aiAskResult.innerHTML = `<div class="result-summary is-fail"><span>${escapeHtml(data.error || 'Ошибка')}</span></div>`;
      return;
    }
    // Сохраняем имя модели для подписи в шапке карточки.
    if (data.model) aiModelLabel.textContent = data.model;
    // Токены — мелкая статистика под ответом, помогает ловить расходы.
    const usageHtml = data.usage && data.usage.total_tokens
      ? `<span class="muted" style="font-size: var(--fs-sm)">${data.usage.total_tokens} токенов</span>`
      : '';
    aiAskResult.innerHTML = `
      <pre class="block" style="white-space: pre-wrap; margin: 0">${escapeHtml(data.answer || '(пустой ответ)')}</pre>
      ${usageHtml}`;
  } catch (e) {
    aiAskResult.innerHTML = `<div class="result-summary is-fail"><span>Сеть/сервер: ${escapeHtml(String(e))}</span></div>`;
  } finally {
    aiAskBtn.disabled = false;
    aiAskBtn.textContent = 'Спросить ИИ';
  }
}
aiAskBtn.addEventListener('click', askAi);
aiQuestion.addEventListener('keydown', (e) => {
  // Ctrl/Cmd+Enter — быстрый отправить, как в редакторах кода выше.
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); askAi(); }
});

let ws = null;
let studentTypingTimer = null;

function connectWs() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws/session/${studentId}`);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'student_code') {
      if (msg.task_id !== undefined && msg.task_id !== null) codeByTask[msg.task_id] = msg.code || '';
      if (!editingStudentCode && (msg.task_id === currentTaskId || msg.task_id == null)) {
        mirrorEditor.setValue(msg.code || '');
      }
      document.getElementById('student-live-status').textContent = 'ученик печатает';
      clearTimeout(studentTypingTimer);
      studentTypingTimer = setTimeout(() => {
        document.getElementById('student-live-status').textContent = 'ученик не печатает';
      }, 4000);
    } else if (msg.type === 'tutor_hint') {
      hintEditor.setValue(msg.code || '');
    } else if (msg.type === 'submit_result') {
      renderSubmitResult(msg);
      loadStudentAttempts(currentTaskId);
      // bug.3: точка-индикатор в списке заданий должна перекрашиваться сразу,
      // а не только после F5. Статус монотонен как task_status_map на бэке
      // (_common.py): 'pass' липкий — решённое однажды задание неудачной
      // попыткой обратно в 'fail' не скатывается.
      if (msg.result && typeof msg.result.all_passed === 'boolean') {
        const newStatus = msg.result.all_passed ? 'pass' : 'fail';
        if (taskStatus[msg.task_id] !== 'pass' && taskStatus[msg.task_id] !== newStatus) {
          taskStatus[msg.task_id] = newStatus;
          renderTaskList();
        }
      }
    } else if (msg.type === 'hint_revealed') {
      // bug.3: ученик раскрыл ступень — перерисуем панель подсказок, если
      // смотрим на ту же задачу (иначе событие не по делу).
      if (msg.task_id === currentTaskId) loadHintsPanel(currentTaskId);
    } else if (msg.type === 'mute_status') {
      const muteEl = document.getElementById('remote-mute-status');
      muteEl.innerHTML = ICON('bellOff') + ' у ученика микрофон выключен';
      muteEl.style.display = msg.muted ? 'inline' : 'none';
    } else if (msg.type === 'call_answer') {
      handleCallAnswer(msg);
    } else if (msg.type === 'call_ice') {
      handleRemoteIce(msg);
    } else if (msg.type === 'call_end') {
      endCall(false);
    } else if (msg.type === 'student_status') {
      renderStudentOnline(!!msg.online);
    }
  };

  ws.onopen = () => {
    if (sessionStorage.getItem(`resumeCall_${studentId}`) === '1') {
      sessionStorage.removeItem(`resumeCall_${studentId}`);
      setTimeout(() => { if (callState === 'idle') startCall(); }, 800);
    }
  };

  ws.onclose = () => {
    setTimeout(connectWs, 2000);
  };
}

function renderSubmitResult(msg) {
  const container = document.getElementById('student-submit-result');
  if (msg.task_id !== currentTaskId) {
    container.innerHTML = `<p class="muted" style="font-size: var(--fs-sm)">Ученик только что отправил решение по заданию ${msg.task_id} (сейчас открыто задание ${currentTaskId ?? '—'}).</p>`;
    return;
  }
  renderGradeResult(container, msg.result);
  const label = document.createElement('p');
  label.className = 'muted';
  label.style.cssText = 'font-size: var(--fs-sm); margin: 0 0 8px 0';
  label.textContent = 'Ученик только что отправил решение:';
  container.prepend(label);
}

// --- Ссылка на созвон (2026-07-22, замена собственного WebRTC) -------------
// Тьютор созванивается во внешнем сервисе (Телемост и т.п.) сам и просто
// присылает готовую ссылку тем же WS-каналом — ученик увидит кнопку
// "Присоединиться". Без какой-либо интеграции с API — просто передача
// текста от одного к другому через уже существующий канал сигналинга.
//
// 2026-07-30: одна кнопка вместо поля+статуса — сама несёт все состояния
// процесса (идея Павла: честный мониторинг буфера обмена в фоне невозможен
// без системных попапов разрешения в каждом браузере, поэтому вместо этого
// тьютор явно раскрывает поле кликом и сам вставляет туда ссылку).
//   idle    — "Созвониться", поле схлопнуто
//   editing — поле раскрыто, ссылка ещё не распознана
//   ready   — распознанная ссылка в поле, кнопка "Отправить" акцентным цветом
//   sent    — "Отправлено" (роль убранного сообщения "ученик получил"),
//             рядом кнопка "Отменить" в красном
//   error   — сокет не открыт, кнопка красная "Ошибка, попробовать снова"
const VIDEO_CALL_LINK_RE = /https?:\/\/(?:[\w-]+\.)?(?:telemost\.yandex\.ru|meet\.google\.com|zoom\.us|teams\.microsoft\.com)\/\S+/i;
const callLinkInput = document.getElementById('call-link-input');
const callLinkMainBtn = document.getElementById('call-link-main-btn');
const callLinkCancelBtn = document.getElementById('call-link-cancel-btn');
let callLinkState = 'idle';

function setCallLinkState(next) {
  callLinkState = next;
  callLinkInput.classList.toggle('is-open', next === 'editing' || next === 'ready');
  callLinkInput.disabled = next === 'sent';
  callLinkMainBtn.classList.toggle('btn-primary', next === 'ready');
  callLinkMainBtn.classList.toggle('btn-danger', next === 'error');
  callLinkMainBtn.disabled = next === 'sent';
  callLinkCancelBtn.style.display = (next === 'sent' || next === 'error') ? 'inline-block' : 'none';
  const labels = {idle: 'Созвониться', editing: 'Созвониться', ready: 'Отправить', sent: 'Отправлено', error: 'Ошибка, попробовать снова'};
  callLinkMainBtn.textContent = labels[next];
}

callLinkInput.addEventListener('input', () => {
  if (callLinkState !== 'editing' && callLinkState !== 'ready') return;
  setCallLinkState(VIDEO_CALL_LINK_RE.test(callLinkInput.value.trim()) ? 'ready' : 'editing');
});

callLinkInput.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && (callLinkState === 'editing' || callLinkState === 'ready')) {
    callLinkInput.value = '';
    setCallLinkState('idle');
  }
});

function trySendCallLink() {
  const url = callLinkInput.value.trim();
  if (!(ws && ws.readyState === WebSocket.OPEN)) {
    setCallLinkState('error');
    return;
  }
  sendMessage({type: 'call_link', url});
  setCallLinkState('sent');
}

document.getElementById('call-link-form').addEventListener('submit', (e) => {
  e.preventDefault();
  if (callLinkState === 'idle') {
    setCallLinkState('editing');
    callLinkInput.focus();
  } else if (callLinkState === 'editing') {
    callLinkInput.value = '';
    setCallLinkState('idle');
  } else if (callLinkState === 'ready' || callLinkState === 'error') {
    trySendCallLink();
  }
});

// Тьютор может отозвать приглашение (например отправил не ту ссылку) — тем же
// каналом уходит call_link_cancel, ученик прячет кнопку "Присоединиться".
callLinkCancelBtn.addEventListener('click', () => {
  if (callLinkState === 'sent') sendMessage({type: 'call_link_cancel'});
  callLinkInput.value = '';
  setCallLinkState('idle');
});

// Онлайн-статус ученика в шапке — тот же чип-переключатель, что и раньше,
// просто перекрашиваем в зелёные тона (тот же язык, что и badge-pass) вместо
// смены текста/добавления отдельного индикатора.
const switcherChip = document.querySelector('.account-trigger.chip');
function renderStudentOnline(online) {
  if (online) {
    switcherChip.style.background = 'var(--c-pass-bg)';
    switcherChip.style.color = 'var(--c-pass)';
  } else {
    switcherChip.style.background = 'var(--c-signal-soft)';
    switcherChip.style.color = 'var(--c-signal)';
  }
}

// --- Аудиозвонок (WebRTC, P2P, caller-сторона — тьютор) -------------------
// DEPRECATED и ОТКЛЮЧЕНО (см. js/shared/calls.js, CALLS_DISABLED). Тьютор —
// звонящая сторона: создаёт offer, ждёт answer. Сигналинг через тот же
// WebSocket. Общая инфраструктура (состояние, AUDIO_CONSTRAINTS,
// applyNoiseSuppression, рингтоны) — в calls.js; здесь роле-специфичная
// оркестрация (offer, авто-передозвон, рендер кнопки звонка в шапке).
let callTimeoutTimer = null;
let autoRedialAttempted = false;

const headerCallBtn = document.getElementById('header-call-btn');
if (CALLS_DISABLED) {
  headerCallBtn.style.display = 'none';
}
const headerMuteBtn = document.getElementById('header-mute-btn');
const micGainSlider = document.getElementById('mic-gain-slider');
const remoteAudio = document.getElementById('remote-audio');
micGainSlider.value = getMicGain();
micGainSlider.addEventListener('input', () => setMicGain(parseFloat(micGainSlider.value)));
const noiseSuppressionLabel = document.getElementById('noise-suppression-label');
const noiseSuppressionToggle = document.getElementById('noise-suppression-toggle');
noiseSuppressionToggle.checked = getNoiseSuppressionEnabled();
noiseSuppressionToggle.addEventListener('change', () => setNoiseSuppressionEnabled(noiseSuppressionToggle.checked));
const micSelect = document.getElementById('mic-select');
if (CALLS_DISABLED) {
  // Шумодав/выбор микрофона относятся только к нашему звонку — раз он
  // отключён, эти элементы больше не должны появляться в шапке вообще
  // (без этого renderHeaderCall() всё равно показывает их в idle-состоянии).
  noiseSuppressionLabel.style.display = 'none';
  micSelect.style.display = 'none';
}

// Кнопка звонка сама сигнализирует статус цветом (как и кнопка микрофона) —
// серая в простое/дозвоне, зелёная только когда звонок реально активен.
function renderHeaderCall() {
  if (CALLS_DISABLED) return;
  if (callState === 'idle') {
    headerCallBtn.className = 'call-icon-btn is-mute is-sm';
    headerCallBtn.title = 'Позвонить';
    headerCallBtn.innerHTML = ICON_PHONE;
    headerCallBtn.onclick = startCall;
    headerMuteBtn.style.display = 'none';
    micGainSlider.style.display = 'none';
    noiseSuppressionLabel.style.display = 'flex';
    micSelect.style.display = 'inline-block';
    populateMicSelect(micSelect);
  } else if (callState === 'calling') {
    headerCallBtn.className = 'call-icon-btn is-mute is-sm';
    headerCallBtn.title = 'Отменить вызов';
    headerCallBtn.innerHTML = ICON_PHONE;
    headerCallBtn.onclick = () => endCall(true);
    headerMuteBtn.style.display = 'none';
    micGainSlider.style.display = 'none';
    noiseSuppressionLabel.style.display = 'flex';
    micSelect.style.display = 'inline-block';
  } else if (callState === 'in-call') {
    micGainSlider.style.display = 'inline-block';
    noiseSuppressionLabel.style.display = 'none';
    micSelect.style.display = 'none';
    headerCallBtn.className = 'call-icon-btn is-accept is-pulsing is-sm';
    headerCallBtn.title = 'Завершить звонок';
    headerCallBtn.innerHTML = ICON_PHONE;
    headerCallBtn.onclick = () => endCall(true);
    const muted = localStream && !localStream.getAudioTracks()[0].enabled;
    headerMuteBtn.style.display = 'inline-flex';
    headerMuteBtn.className = muted
      ? 'call-icon-btn is-sm is-mute is-active'
      : 'call-icon-btn is-sm is-accept is-pulsing';
    headerMuteBtn.title = muted ? 'Включить микрофон' : 'Выключить микрофон';
    headerMuteBtn.innerHTML = muted ? ICON_MIC_OFF : ICON_MIC;
    headerMuteBtn.onclick = () => toggleMute(renderHeaderCall);
  }
}

function setupPeerConnection(iceServers) {
  // iceTransportPolicy: 'relay' — форсируем всегда через свой TURN (coturn),
  // не пытаясь напрямую P2P. Временная мера (2026-07-22): на тестовом
  // компе лишние виртуальные адаптеры (VPN/Hyper-V/хот-спот) отдавали
  // приватные IP как ICE-кандидаты, coturn их корректно отклонял
  // (RFC-политика — иначе через TURN можно долбить чужие приватные сети),
  // и ICE иногда выбирал именно такую нерабочую пару — отсюда
  // непредсказуемая связь в одну сторону. Если основная причина реально
  // в этом — держать forced-relay смысла нет, надёжнее почистить сетевые
  // адаптеры и вернуть 'all' (даёт более короткий путь при прямом P2P).
  const conn = new RTCPeerConnection({iceServers, iceTransportPolicy: 'relay'});
  conn.onicecandidate = (e) => {
    if (e.candidate) sendMessage({type: 'call_ice', candidate: e.candidate});
  };
  conn.ontrack = (e) => { remoteAudio.srcObject = e.streams[0]; };
  conn.onconnectionstatechange = () => {
    if (conn.connectionState === 'connected') {
      clearTimeout(callTimeoutTimer);
      stopRingSound();
      callState = 'in-call';
      renderHeaderCall();
      autoRedialAttempted = false;
      sendMessage({type: 'mute_status', muted: false});
    } else if (conn.connectionState === 'failed' || conn.connectionState === 'disconnected') {
      // Одна попытка перезвонить самостоятельно (например, у ученика
      // перезагрузилась страница) — если и она не удастся, дальше обычный
      // 30-секундный таймаут в startCall() покажет "ученик не отвечает".
      if (!autoRedialAttempted) {
        autoRedialAttempted = true;
        endCall(false);
        setTimeout(() => { if (callState === 'idle') startCall(); }, 1500);
      } else {
        endCall(true);
      }
    }
  };
  return conn;
}

async function startCall() {
  if (CALLS_DISABLED) return;
  if (callState !== 'idle') return;
  autoRedialAttempted = false;
  callState = 'calling';
  renderHeaderCall();
  startRingback();
  try {
    const iceServers = await fetchIceServers();
    try {
      localStream = await navigator.mediaDevices.getUserMedia({audio: buildAudioConstraints()});
    } catch (e) {
      // выбранный микрофон мог отключиться/пропасть — не срывать звонок,
      // откатываемся на системный дефолт.
      localStream = await navigator.mediaDevices.getUserMedia({audio: AUDIO_CONSTRAINTS});
    }
    const outgoingStream = await applyNoiseSuppression(localStream);
    pc = setupPeerConnection(iceServers);
    outgoingStream.getTracks().forEach(t => pc.addTrack(t, outgoingStream));
    boostAudioBitrate(pc);
    const offer = await pc.createOffer();
    offer.sdp = tuneOpusSdp(offer.sdp);
    await pc.setLocalDescription(offer);
    sendMessage({type: 'call_offer', sdp: offer});
    callTimeoutTimer = setTimeout(() => {
      if (callState === 'calling') {
        alert('Ученик не отвечает');
        endCall(true);
      }
    }, 30000);
  } catch (e) {
    alert('Не удалось включить микрофон');
    endCall(false);
  }
}

async function handleCallAnswer(msg) {
  if (!pc) return;
  await pc.setRemoteDescription(msg.sdp);
  for (const candidate of pendingRemoteIce) {
    await pc.addIceCandidate(candidate);
  }
  pendingRemoteIce = [];
}

function endCall(notify) {
  clearTimeout(callTimeoutTimer);
  stopRingSound();
  if (pc) { pc.close(); pc = null; }
  if (localStream) { localStream.getTracks().forEach(t => t.stop()); localStream = null; }
  if (noiseSuppressionCtx) { noiseSuppressionCtx.close(); noiseSuppressionCtx = null; }
  pendingRemoteIce = [];
  remoteAudio.srcObject = null;
  document.getElementById('remote-mute-status').style.display = 'none';
  if (notify) sendMessage({type: 'call_end'});
  callState = 'idle';
  renderHeaderCall();
}

// Полная перезагрузка страницы (F5, выход в режим ученика через impersonate,
// переключение на другого ученика) рвёт RTCPeerConnection — это неизбежно,
// он живёт только в JS-памяти вкладки. Сохраняем "звонок был активен" и
// перезваниваем сами при следующей загрузке (см. ws.onopen выше).
window.addEventListener('beforeunload', () => {
  if (callState !== 'idle') sessionStorage.setItem(`resumeCall_${studentId}`, '1');
});

// --- Мониторинг подсказок ученика (задания 81..100) -------------------------
// Тьютор видит, какие ступени ученик уже раскрыл, что осталось ждать, и сам
// текст раскрытых уровней. Это мониторинг (read-only): reveal-кнопок нет,
// уровни открывает сам ученик на своей странице. Источник правды о тайминге —
// сервер, здесь только отображение и обратный отсчёт до разблокировки.
// Источник правды о наличии подсказок у задания — сам сервер (GET /api/students/
// {id}/hints/{task} вернёт 200/404); отдельной константы диапазона на фронте
// нет, чтобы не рассинхрониться с HINTED_TASK_IDS на бэке.
const hintsPanel = document.getElementById('hints-panel');
const hintsStepsEl = document.getElementById('hints-steps');
const hintsPanelSub = document.getElementById('hints-panel-sub');
const hintsEditLink = document.getElementById('hints-edit-link');
let hintState = { taskId: null, levels: [] };
const hintCountdown = createHintCountdown(hintsStepsEl, () => loadHintsPanel(hintState.taskId));
// ICON, HINT_MARKERS, HINT_LEVEL_TITLES — в js/shared/icons.js.

function renderHintsPanel() {
  // Панель показываем, только если сервер вернул данные (см. loadHintsPanel:
  // при 404 hintState остаётся пустым и панель скрывается). Сравнение с null,
  // не falsy: task_id служебной задачи — 0, и `!0` ложно скрывал бы панель.
  if (hintState.taskId === null || !hintState.levels.length) {
    hintsPanel.classList.add('is-hidden');
    return;
  }
  hintsPanel.classList.remove('is-hidden');
  hintsStepsEl.innerHTML = hintState.levels.map(lv => {
    const st = lv.status;
    // Тьютор видит «готов открыть» как «доступно», а «locked» — как «не открыл»:
    // со стороны тьютора важен прогресс ученика, а не готовность к действию.
    const note =
      st === 'locked'   ? 'Ученик ещё не открыл предыдущую ступень.' :
      st === 'waiting'  ? `Откроется ученику через <span class="hint-timer" data-avail="${lv.available_at ? new Date(lv.available_at).getTime() : 0}">…</span>` :
      st === 'ready'    ? 'Доступна ученику — он ещё не открыл.' :
      '';
    const body = st === 'revealed'
      ? `<div class="hint-content">${lv.content_html || '<p class="hint-step-note">Текст этой ступени ещё не добавлен.</p>'}</div>`
      : `<p class="hint-step-note">${note}</p>`;
    // Кнопка сброса — только для раскрытых уровней (закрыть как будто ученик
    // не открывал). Сброс необратим, поэтому с подтверждением в resetHint().
    const resetBtn = st === 'revealed'
      ? `<button type="button" class="btn btn-sm btn-ghost hint-reset-btn" data-level="${lv.level}" title="Сбросить раскрытие">${ICON('lock')} Сбросить</button>`
      : '';
    return `<div class="hint-step is-${st}">
      <div class="hint-step-head">
        <span class="hint-marker is-${st}">${HINT_MARKERS[st]}</span>
        <span class="hint-step-title">${HINT_LEVEL_TITLES[lv.level]}</span>
        ${resetBtn}
      </div>
      ${body}
    </div>`;
  }).join('');
  // Привязываем обработчики сброса (панель пере-рендерится, навешиваем заново).
  hintsStepsEl.querySelectorAll('.hint-reset-btn').forEach(btn => {
    btn.addEventListener('click', () => resetHint(Number(btn.dataset.level)));
  });
  hintCountdown.start();
}

async function loadHintsPanel(taskId) {
  hintCountdown.stop();
  hintsEditLink.href = taskId !== null ? `/tutor/hints?task=${taskId}` : '/tutor/hints';
  if (taskId === null) {
    hintState = { taskId, levels: [] };
    hintsPanel.classList.add('is-hidden');
    return;
  }
  try {
    const res = await fetch(`/api/students/${studentId}/hints/${taskId}`);
    if (!res.ok) { hintsPanel.classList.add('is-hidden'); return; }
    const data = await res.json();
    hintState = { taskId, levels: data.levels };
    hintsPanelSub.textContent = data.levels.some(l => l.status === 'waiting') ? 'открытие по таймеру' : '';
    renderHintsPanel();
  } catch (e) {
    hintsPanel.classList.add('is-hidden');
  }
}

// Сброс раскрытого уровня — тьютор «закрывает» подсказку, как будто ученик её
// не открывал. Каскад (уровни выше) и таймеры обрабатываются на бэке; здесь —
// подтвердить, отправить POST, перерисовать панель из ответа сервера.
async function resetHint(level) {
  if (hintState.taskId === null) return;
  if (!confirm(`Сбросить подсказку уровня ${level}?` +
               `\nУченик снова увидит её закрытой, таймер следующего уровня обнулится.` +
               `\nЭто действие необратимо.`)) return;
  try {
    const res = await fetch(`/api/students/${studentId}/hints/${hintState.taskId}/reset`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({level}),
    });
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.error || 'Не удалось сбросить подсказку');
      return;
    }
    const data = await res.json();
    hintState = { taskId: hintState.taskId, levels: data.levels };
    hintsPanelSub.textContent = data.levels.some(l => l.status === 'waiting') ? 'открытие по таймеру' : '';
    renderHintsPanel();
  } catch (e) {
    /* сеть — молча, состояние не меняем */
  }
}

initHeaderUser();
loadStudentSwitcher();
renderHeaderCall();
loadTasks();
connectWs();
loadMaterials();
