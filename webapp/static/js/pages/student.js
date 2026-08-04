/* student.js — страница практики ученика (index.html). Список заданий с
   пагинацией, редактор решения, история попыток, многоступенчатые подсказки.
   Та же страница используется тьютором в режиме «посмотреть как ученик».

   Зависимости (грузятся раньше, см. {% block scripts %} в index.html):
     codemirror.bundle.js (PracticeHubEditor), js/lib/attempts.js (PPHAttempts),
     js/lib/dom-utils.js (escapeHtml, redirectToLoginIfUnauthorized, sendMessage),
     js/lib/grade-render.js (renderGradeResult, renderFreeRunResult, fmtCountdown),
     js/lib/task-nav.js (initTaskList, saveLastTask, loadMaterials),
     js/lib/call-audio.js + js/shared/calls.js (выключенный WebRTC-звонок,
     см. CALLS_DISABLED), js/shared/icons.js (ICON, HINT_MARKERS, ICON_PHONE...). */

const description = document.getElementById('description');
const taskTitle = document.getElementById('task-title');
const DEFAULT_SOLVE_CODE = 'def solve(data):\n    pass\n';
const codeByTask = {}; // task_id -> код ученика, свой на каждое задание, не пересекается между ними
let codeSendTimer = null;
const codeEditor = PracticeHubEditor.create(
  document.getElementById('code-mount'),
  DEFAULT_SOLVE_CODE,
  (code) => {
    if (currentTaskId !== null) codeByTask[currentTaskId] = code;
    clearTimeout(codeSendTimer);
    codeSendTimer = setTimeout(() => sendMessage({code, task_id: currentTaskId}), 300);
  }
);
const hintSection = document.getElementById('hint-section');
const hintMount = document.getElementById('hint-mount');
const hintEditor = PracticeHubEditor.create(hintMount, '', null, {readOnly: true});
// CSS (user-select: none, только в режиме "protected") убирает выделение
// мышью/тачем, но не блокирует копирование по горячим клавишам или через
// контекстное меню — добиваем это здесь же, тем же условием на hintMode.
hintMount.addEventListener('copy', (e) => { if (hintMode === 'protected') e.preventDefault(); });
hintMount.addEventListener('cut', (e) => { if (hintMode === 'protected') e.preventDefault(); });
hintMount.addEventListener('contextmenu', (e) => { if (hintMode === 'protected') e.preventDefault(); });

// Три состояния подсказки (переключает тьютор по кругу, см. hint-lock-btn
// в tutor-student.js): hidden — блок вообще не показываем ученику; protected —
// виден, но не копируется; open — виден и копируется свободно. По умолчанию hidden.
let tutorOnline = false;
let hintMode = 'hidden';

function updateHintSection() {
  hintSection.classList.toggle('is-hidden', !(tutorOnline && hintMode !== 'hidden'));
  hintMount.classList.toggle('is-protected', hintMode === 'protected');
}
const submitBtn = document.getElementById('submit-btn');
const summary = document.getElementById('summary');
const results = document.getElementById('results');
const resultsSection = document.getElementById('results-section');
const myAttemptsSection = document.getElementById('my-attempts-section');
const myAttemptsRows = document.getElementById('my-attempts-rows');
const solveSection = document.getElementById('solve-section');
const solvedNote = document.getElementById('solved-note');

let ws = null;

function connectWs(ownId) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws/session/${ownId}`);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'tutor_status') {
      tutorOnline = !!msg.online;
      updateHintSection();
    } else if (msg.type === 'tutor_hint') {
      hintEditor.setValue(msg.code || '');
    } else if (msg.type === 'hint_result') {
      const container = document.getElementById('hint-result');
      renderGradeResult(container, msg.result);
      const label = document.createElement('p');
      label.className = 'muted';
      label.style.cssText = 'font-size: var(--fs-sm); margin: 0 0 8px 0';
      label.textContent = `Результат по заданию ${msg.task_id}`;
      container.prepend(label);
    } else if (msg.type === 'hint_free_result') {
      const container = document.getElementById('hint-result');
      renderFreeRunResult(container, msg.result);
    } else if (msg.type === 'hint_visibility') {
      hintMode = msg.mode === 'protected' || msg.mode === 'open' ? msg.mode : 'hidden';
      updateHintSection();
    } else if (msg.type === 'tutor_edit_code') {
      if (msg.task_id === currentTaskId) codeEditor.setValue(msg.code || '');
      codeByTask[msg.task_id] = msg.code || '';
    } else if (msg.type === 'attempts_changed') {
      // feat.2: тьютор удалил попытку — статус мог измениться (pass→fail или
      // вовсе пропасть). Перезагружаем индикатор и, если смотрим на эту
      // задачу, секцию решения и «Мои попытки».
      if (msg.status) taskStatus[msg.task_id] = msg.status;
      else delete taskStatus[msg.task_id];
      renderTaskList();
      if (msg.task_id === currentTaskId) {
        updateSolveVisibility();
        loadMyAttemptHistory(currentTaskId);
      }
    } else if (msg.type === 'mute_status') {
      renderRemoteMuteStatus(!!msg.muted);
    } else if (msg.type === 'call_offer') {
      handleCallOffer(msg);
    } else if (msg.type === 'call_ice') {
      handleRemoteIce(msg);
    } else if (msg.type === 'call_end') {
      endCall(false);
    } else if (msg.type === 'call_link') {
      showCallLink(msg.url);
    } else if (msg.type === 'call_link_cancel') {
      hideCallLink();
    }
  };

  ws.onclose = () => {
    setTimeout(() => connectWs(ownId), 2000);
  };
}

// --- Ссылка на звонок (2026-07-22, временная замена собственного WebRTC) --
// Тьютор созванивается во внешнем сервисе (Телемост и т.п.) и присылает
// ссылку тем же WS-каналом (`call_link`) — сервер её просто ретранслирует,
// без хранения. Показываем как есть, без валидации содержимого (ссылку
// прислал тьютор из своего личного кабинета, не произвольный ввод извне).
const callLinkIcon = document.getElementById('call-link-icon');

function showCallLink(url) {
  callLinkIcon.href = url;
  callLinkIcon.classList.remove('is-hidden');
  sendMessage({type: 'call_link_ack'});
}

// Тьютор может отозвать приглашение — прячем значок обратно.
function hideCallLink() {
  callLinkIcon.classList.add('is-hidden');
}

// --- Аудиозвонок (WebRTC, P2P, callee-сторона — ученик) -------------------
// DEPRECATED и ОТКЛЮЧЕНО (см. js/shared/calls.js, CALLS_DISABLED). Ученик —
// принимающая сторона: ждёт offer от тьютора, отвечает answer'ом. Сигналинг
// идёт через тот же WebSocket, что и live-код/подсказки. Общая инфраструктура
// (состояние, AUDIO_CONSTRAINTS, applyNoiseSuppression, рингтоны) — в calls.js;
// здесь только роле-специфичная оркестрация (offer→answer, рендер панели звонка).
let incomingOffer = null;

function renderCallBar() {
  if (callState === 'idle') {
    callBar.classList.add('is-hidden');
    return;
  }
  callBar.classList.remove('is-hidden');
  if (callState === 'ringing') {
    callStatusEl.textContent = 'входящий звонок от репетитора';
    callActionsEl.innerHTML = `
      <label class="muted row" style="font-size: var(--fs-sm); gap: 4px; align-items: center">
        <input type="checkbox" id="noise-suppression-toggle" ${getNoiseSuppressionEnabled() ? 'checked' : ''}> шумодав
      </label>
      <select class="btn btn-sm" id="mic-select" style="max-width: 180px" title="Микрофон"></select>
      <button class="call-icon-btn is-accept" id="accept-btn" title="Принять">${ICON_PHONE}</button>
      <button class="call-icon-btn is-hangup" id="decline-btn" title="Отклонить">${ICON_PHONE}</button>
    `;
    document.getElementById('accept-btn').addEventListener('click', acceptCall);
    document.getElementById('decline-btn').addEventListener('click', () => endCall(true));
    document.getElementById('noise-suppression-toggle').addEventListener('change', (e) => setNoiseSuppressionEnabled(e.target.checked));
    populateMicSelect(document.getElementById('mic-select'));
  } else if (callState === 'in-call') {
    callStatusEl.textContent = 'в разговоре с репетитором';
    const muted = localStream && !localStream.getAudioTracks()[0].enabled;
    const muteClass = muted ? 'call-icon-btn is-mute is-active' : 'call-icon-btn is-accept is-pulsing';
    callActionsEl.innerHTML = `
      <button class="${muteClass}" id="mute-btn" title="${muted ? 'Включить микрофон' : 'Выключить микрофон'}">${muted ? ICON_MIC_OFF : ICON_MIC}</button>
      <input type="range" class="mic-gain-slider" id="mic-gain-slider" min="0.5" max="3" step="0.1" title="Громкость микрофона" value="${getMicGain()}">
      <button class="call-icon-btn is-hangup" id="hangup-btn" title="Завершить звонок">${ICON_PHONE}</button>
    `;
    document.getElementById('mute-btn').addEventListener('click', () => toggleMute(renderCallBar));
    document.getElementById('hangup-btn').addEventListener('click', () => endCall(true));
    document.getElementById('mic-gain-slider').addEventListener('input', (e) => setMicGain(parseFloat(e.target.value)));
  }
}

const callBar = document.getElementById('call-bar');
const callStatusEl = document.getElementById('call-status');
const callActionsEl = document.getElementById('call-actions');
const remoteAudio = document.getElementById('remote-audio');

// Иконки для живых header-элементов (impersonation-кластер, solved-note).
document.getElementById('impersonation-call-link').innerHTML = ICON_PHONE;
callLinkIcon.innerHTML = ICON_PHONE;
document.getElementById('impersonation-eye-btn').innerHTML = ICON_EYE;
document.getElementById('solved-note-icon').innerHTML = ICON('checkCircle');

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
    if (conn.connectionState === 'failed' || conn.connectionState === 'disconnected') {
      endCall(true);
    }
  };
  return conn;
}

function handleCallOffer(msg) {
  if (CALLS_DISABLED) return;
  if (callState !== 'idle') return; // уже звоним/говорим — второй входящий игнорируем
  incomingOffer = msg.sdp;
  callState = 'ringing';
  renderCallBar();
  startRingtone();
}

async function acceptCall() {
  if (!incomingOffer) return;
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
    await pc.setRemoteDescription(incomingOffer);
    for (const candidate of pendingRemoteIce) {
      await pc.addIceCandidate(candidate);
    }
    pendingRemoteIce = [];
    const answer = await pc.createAnswer();
    answer.sdp = tuneOpusSdp(answer.sdp);
    await pc.setLocalDescription(answer);
    sendMessage({type: 'call_answer', sdp: answer});
    stopRingSound();
    callState = 'in-call';
    renderCallBar();
    sendMessage({type: 'mute_status', muted: false});
  } catch (e) {
    callStatusEl.textContent = 'не удалось включить микрофон';
    endCall(true);
  }
}

function renderRemoteMuteStatus(muted) {
  const el = document.getElementById('remote-mute-status');
  el.innerHTML = muted ? `${ICON('bellOff')} у репетитора выключен микрофон` : '';
  el.style.display = muted ? 'block' : 'none';
}

function endCall(notify) {
  stopRingSound();
  if (pc) { pc.close(); pc = null; }
  if (localStream) { localStream.getTracks().forEach(t => t.stop()); localStream = null; }
  if (noiseSuppressionCtx) { noiseSuppressionCtx.close(); noiseSuppressionCtx = null; }
  pendingRemoteIce = [];
  incomingOffer = null;
  remoteAudio.srcObject = null;
  renderRemoteMuteStatus(false);
  if (notify) sendMessage({type: 'call_end'});
  callState = 'idle';
  renderCallBar();
}

let tasks = [];
let currentTaskId = null;
const taskStatus = {}; // id -> 'pass' | 'fail'; seeded from history on load, updated live after each submit

let impersonating = false;

async function loadMe() {
  const data = await initHeaderUser();
  if (!data) return;
  impersonating = !!data.impersonating;
  if (impersonating) {
    const sessionUrl = `/tutor/student/${data.id}`;
    const chip = document.getElementById('impersonation-chip');
    chip.textContent = data.username || '';
    chip.href = sessionUrl;
    chip.classList.remove('is-hidden');
    const callLink = document.getElementById('impersonation-call-link');
    callLink.href = sessionUrl;
    callLink.classList.remove('is-hidden');
    document.getElementById('impersonation-exit-form').classList.remove('is-hidden');
    submitBtn.disabled = true;
    submitBtn.title = 'Отправка кода отключена в режиме просмотра «как ученик»';
  } else {
    connectWs(data.id);
  }
}

// Запоминаем последнее открытое задание и страницу списка, чтобы при
// перезагрузке страницы открываться там же, где ученик/тьютор остановился,
// а не всегда на первом задании. Ключ без user-id: на практике устройство
// принадлежит одному человеку (ученик на своём, тьютор на своём).
function lastTaskKey(suffix) { return suffix === 'taskId' ? 'pph:lastTaskId' : 'pph:lastTaskPage'; }

async function loadTasks() {
  const res = await fetch('/api/tasks');
  if (redirectToLoginIfUnauthorized(res)) return;
  tasks = await res.json();

  // Восстанавливаем последнее открытое задание, если оно ещё доступно
  // (задание могло быть скрыто из веб-грейдера — нет тестовых входов и т.п.).
  const savedId = Number(localStorage.getItem(lastTaskKey('taskId')));
  const savedPage = Number(localStorage.getItem(lastTaskKey('page')));
  const savedTaskExists = tasks.some(t => t.id === savedId);
  currentTaskId = savedTaskExists ? savedId : (tasks.length ? tasks[0].id : null);
  if (savedTaskExists && Number.isFinite(savedPage)) taskPage = savedPage;

  const historyRes = await fetch('/api/attempts/mine');
  if (historyRes.ok) {
    const history = await historyRes.json();
    for (const [taskId, status] of Object.entries(history)) taskStatus[taskId] = status;
  }

  renderTaskList();
  showDescription();
  loadHints(currentTaskId);
}

const TASK_PAGE_SIZE = 7;
let taskPage = 0;
const renderTaskList = initTaskList(switchToTask);

function showDescription() {
  const task = tasks.find(t => t.id === currentTaskId);
  taskTitle.textContent = task ? `Задание ${task.id}` : '';
  description.innerHTML = task
    ? `<p>${escapeHtml(task.description)}</p><p><strong style="color: var(--c-ink)">Пример:</strong> ${escapeHtml(task.example)}</p>`
    : '';
  updateSolveVisibility();
  loadMyAttemptHistory(currentTaskId);
}

async function loadMyAttemptHistory(taskId) {
  if (taskId === null) { myAttemptsSection.classList.add('is-hidden'); return; }
  const res = await fetch(`/api/attempts/mine/${taskId}`);
  if (!res.ok) { myAttemptsSection.classList.add('is-hidden'); return; }
  const attempts = await res.json();
  myAttemptsSection.classList.toggle('is-hidden', !attempts.length);
  PPHAttempts.render(myAttemptsRows, attempts, PracticeHubEditor.create);
}

function updateSolveVisibility() {
  const solved = taskStatus[currentTaskId] === 'pass';
  solveSection.classList.toggle('is-hidden', solved);
  solvedNote.classList.toggle('is-hidden', !solved);
}

// Переключение задания: код и результаты — строго свои на каждое задание,
// ничего от предыдущего задания не должно "протекать" в новое.
function switchToTask(taskId) {
  if (currentTaskId !== null) codeByTask[currentTaskId] = codeEditor.getValue();
  currentTaskId = taskId;
  // Активное задание должно быть видно в списке — если оно на другой странице
  // пагинации, перейдём туда. Иначе после restore задача откроется, но в
  // боковом списке её не видно.
  const idx = tasks.findIndex(t => t.id === taskId);
  if (idx !== -1) taskPage = Math.floor(idx / TASK_PAGE_SIZE);
  renderTaskList();
  showDescription();
  codeEditor.setValue(codeByTask[currentTaskId] || DEFAULT_SOLVE_CODE);
  resultsSection.classList.add('is-hidden');
  summary.innerHTML = '';
  results.innerHTML = '';
  document.getElementById('hint-result').innerHTML = '';
  document.getElementById('free-run-result').innerHTML = '';
  loadHints(taskId);
  saveLastTask();
  sendMessage({code: codeEditor.getValue(), task_id: currentTaskId});
}

submitBtn.addEventListener('click', async () => {
  if (currentTaskId === null) return;
  submitBtn.disabled = true;
  submitBtn.textContent = 'Проверяю...';
  summary.innerHTML = '';
  results.innerHTML = '';
  try {
    const res = await fetch('/api/submit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({task_id: currentTaskId, code: codeEditor.getValue()}),
    });
    if (redirectToLoginIfUnauthorized(res)) return;
    const data = await res.json();
    render(data);
    sendMessage({type: 'submit_result', task_id: currentTaskId, result: data});
  } catch (e) {
    resultsSection.classList.remove('is-hidden');
    summary.innerHTML = `<div class="result-summary is-fail"><span>Ошибка запроса: ${escapeHtml(String(e))}</span></div>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Проверить';
  }
});

const runFreeBtn = document.getElementById('run-free-btn');
runFreeBtn.addEventListener('click', async () => {
  const resultEl = document.getElementById('free-run-result');
  runFreeBtn.disabled = true;
  runFreeBtn.textContent = 'Запускаю...';
  try {
    const res = await fetch('/api/solve/run_free', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({code: codeEditor.getValue()}),
    });
    if (redirectToLoginIfUnauthorized(res)) return;
    const result = await res.json();
    renderFreeRunResult(resultEl, result);
  } finally {
    runFreeBtn.disabled = false;
    runFreeBtn.textContent = 'Запустить';
  }
});

// Локальный рендер результата своей отправки — НЕ общий renderGradeResult():
// помимо шаблона тест-кейсов тут есть page-специфичные побочные эффекты
// (показать results-section, обновить taskStatus, перерисовать список заданий,
// подтянуть свежую историю попыток) + разная DOM-структура (summary и results
// — два отдельных контейнера, а renderGradeResult пишет в один).
function render(data) {
  resultsSection.classList.remove('is-hidden');

  if (data.error) {
    summary.innerHTML = `<div class="result-summary is-fail"><span>${escapeHtml(data.error)}</span></div>`;
    results.innerHTML = '';
    return;
  }

  taskStatus[currentTaskId] = data.all_passed ? 'pass' : 'fail';
  renderTaskList();
  updateSolveVisibility();
  loadMyAttemptHistory(currentTaskId);

  summary.innerHTML = `<div class="result-summary ${data.all_passed ? 'is-pass' : 'is-fail'}">
    <span class="count">${data.passed} / ${data.total}</span>
    <span>${data.all_passed ? 'Все тесты пройдены' : 'Есть ошибки'}</span>
  </div>`;

  results.innerHTML = renderTestCases(data.results);
}

// --- Многоступенчатые подсказки ---------------------------------------------
// Три уровня: 1 — абстракция, 2 — конкретика со ссылками (через 7 мин после 1),
// 3 — почти решение (ещё через 15 мин). Тайминг считает сервер по HintReveal,
// клиентскому таймеру не верим — он только для обратного отсчёта на UI; по
// обнулению мы переспрашиваем состояние у сервера (только он решает waiting→ready).
// Источник правды о том, есть ли у задания подсказки — сам сервер (GET /api/hints
// вернёт 200 или 404), отдельной константы диапазона на фронте НЕ держим, чтобы
// не было рассинхрона с HINTED_TASK_IDS на бэке (такой баг уже был).
const hintsPanel = document.getElementById('hints-panel');
const hintsStepsEl = document.getElementById('hints-steps');
const hintsPanelSub = document.getElementById('hints-panel-sub');
let hintState = { taskId: null, levels: [] };
let hintPollTimer = null;          // периодический опрос при waiting-уровне
const hintCountdown = createHintCountdown(hintsStepsEl, () => loadHints(hintState.taskId));
// HINT_MARKERS и HINT_LEVEL_TITLES — в js/shared/icons.js.

function renderHints() {
  // Панель показываем, только если сервер вернул данные (см. loadHints: при
  // 404 hintState остаётся пустым и панель скрывается). Сравнение именно с
  // null, не falsy: task_id служебной задачи — 0, и `!0` ложно скрывал бы
  // панель для неё.
  if (hintState.taskId === null || !hintState.levels.length) {
    hintsPanel.classList.add('is-hidden');
    return;
  }
  hintsPanel.classList.remove('is-hidden');
  hintsStepsEl.innerHTML = hintState.levels.map(lv => {
    const st = lv.status;
    const cls = `hint-step is-${st}`;
    const marker = `<span class="hint-marker is-${st}">${HINT_MARKERS[st]}</span>`;
    let body = '';
    if (st === 'locked') {
      body = `<p class="hint-step-note">Откроется после предыдущей ступени.</p>`;
    } else if (st === 'waiting') {
      // available_at приходит с сервера; обратный отсчёт — только на UI.
      const avail = lv.available_at ? new Date(lv.available_at).getTime() : 0;
      body = `<p class="hint-step-note">Доступно через <span class="hint-timer" data-avail="${avail}">…</span></p>`;
    } else if (st === 'ready') {
      body = `<button class="btn btn-sm btn-primary hint-reveal-btn" data-level="${lv.level}">Показать подсказку</button>`;
    } else if (st === 'revealed') {
      const html = lv.content_html || '<p class="hint-step-note">Текст этой ступени ещё не добавлен тьютором.</p>';
      body = `<div class="hint-content">${html}</div>`;
    }
    return `<div class="${cls}">
      <div class="hint-step-head">
        ${marker}
        <span class="hint-step-title">${HINT_LEVEL_TITLES[lv.level]}</span>
      </div>
      ${body}
    </div>`;
  }).join('');

  // Кнопки раскрытия.
  hintsStepsEl.querySelectorAll('.hint-reveal-btn').forEach(btn => {
    btn.addEventListener('click', () => revealHint(Number(btn.dataset.level)));
  });

  hintCountdown.start();
}

async function loadHints(taskId) {
  // При любой перезагрузке состояния гасим тикающий таймер и поллинг — иначе
  // интервал от предыдущей задачи продолжит тикать поверх нового состояния.
  hintCountdown.stop();
  if (hintPollTimer) { clearInterval(hintPollTimer); hintPollTimer = null; }

  if (taskId === null) {
    hintState = { taskId, levels: [] };
    hintsPanel.classList.add('is-hidden');
    return;
  }
  try {
    const res = await fetch(`/api/hints/${taskId}`);
    if (!res.ok) { hintsPanel.classList.add('is-hidden'); return; }
    const data = await res.json();
    hintState = { taskId, levels: data.levels };
    hintsPanelSub.textContent = data.levels.some(l => l.status === 'waiting')
      ? 'открытие по таймеру'
      : '';
    renderHints();
    scheduleHintPoll();
  } catch (e) {
    hintsPanel.classList.add('is-hidden');
  }
}

// На случай если вкладка заснула и setTimeout не сработал вовремя —
// раз в 30 сек перепроверяем, не пришло ли время разблокировки.
function scheduleHintPoll() {
  if (hintPollTimer) clearInterval(hintPollTimer);
  const hasWaiting = hintState.levels.some(l => l.status === 'waiting');
  if (!hasWaiting) return;
  hintPollTimer = setInterval(() => loadHints(hintState.taskId), 30000);
}

async function revealHint(level) {
  if (hintState.taskId === null) return;
  try {
    const res = await fetch(`/api/hints/${hintState.taskId}/reveal`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({level}),
    });
    if (res.status === 401) { window.location.href = '/login'; return; }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      // 409 — уровень ещё не доступен; покажем причину без перезагрузки состояния.
      if (res.status === 409) alert(data.error || 'Уровень пока недоступен');
      return;
    }
    const data = await res.json();
    hintState = { taskId: hintState.taskId, levels: data.levels };
    hintsPanelSub.textContent = data.levels.some(l => l.status === 'waiting') ? 'открытие по таймеру' : '';
    renderHints();
    scheduleHintPoll();
    // bug.3: тьютор должен видеть раскрытие подсказки сразу, без F5 — то же
    // событие, что и submit_result, релеится ему в комнату (см. ws.py).
    sendMessage({type: 'hint_revealed', task_id: hintState.taskId, level});
  } catch (e) { /* сеть — молча, состояние не меняем */ }
}

updateHintSection();
loadMe();
loadTasks();
loadMaterials();
