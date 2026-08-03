/* materials.js — страница справочного урока (materials.html). Читает манифест
   модулей и ячейки конкретного урока, рендерит read-only CodeMirror. */

async function loadLesson() {
  const parts = window.location.pathname.split('/').filter(Boolean);
  const module = decodeURIComponent(parts[1]);
  const lesson = decodeURIComponent(parts[2]);

  const manifestRes = await fetch('/api/materials');
  if (redirectToLoginIfUnauthorized(manifestRes)) return;
  const manifest = await manifestRes.json();
  document.getElementById('module-title').textContent = manifest[module] ? manifest[module].title : '';

  const res = await fetch(`/api/materials/${encodeURIComponent(module)}/${encodeURIComponent(lesson)}`);
  if (redirectToLoginIfUnauthorized(res)) return;
  if (!res.ok) {
    document.getElementById('lesson-title').textContent = 'Материал не найден';
    return;
  }
  const data = await res.json();
  document.title = `${data.title} — Python Practice Hub`;
  document.getElementById('lesson-title').textContent = data.title;

  const cellsEl = document.getElementById('cells');
  cellsEl.innerHTML = data.cells.map((_, i) => `
    <div class="stack stack-2">
      <div class="code-editor"><div class="material-cell-mount" id="cell-${i}"></div></div>
    </div>
  `).join('');

  data.cells.forEach((cell, i) => {
    const mount = document.getElementById(`cell-${i}`);
    PracticeHubEditor.create(mount, cell.code, null, {readOnly: true});
    if (cell.output) {
      const pre = document.createElement('pre');
      pre.className = 'block material-output' + (cell.is_error ? ' is-error' : '');
      pre.textContent = cell.output;
      mount.parentElement.after(pre);
    }
  });
}

initHeaderUser();
loadLesson();
