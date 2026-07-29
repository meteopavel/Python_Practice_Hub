/* ==========================================================================
   task-nav.js — общее для index.html и tutor_student.html: запоминание
   последнего открытого задания/страницы списка, сайдбар справочных
   материалов. Зависит от глобалов страницы: currentTaskId, taskPage,
   lastTaskKey(suffix) (каждая страница определяет свою схему ключей
   localStorage — у тьютора она учитывает id ученика).
   ========================================================================== */

function saveLastTask() {
  if (currentTaskId !== null) {
    localStorage.setItem(lastTaskKey('taskId'), String(currentTaskId));
    localStorage.setItem(lastTaskKey('page'), String(taskPage));
  }
}

async function loadMaterials() {
  const res = await fetch('/api/materials');
  if (!res.ok) return;
  const manifest = await res.json();
  const list = document.getElementById('materials-list');
  list.innerHTML = Object.entries(manifest).map(([module, data]) => `
    <details class="materials-module">
      <summary>${escapeHtml(data.title)}</summary>
      ${data.lessons.map(l => `<a class="material-link" target="_blank" rel="noopener" href="/materials/${encodeURIComponent(module)}/${encodeURIComponent(l.slug)}">${escapeHtml(l.title)}</a>`).join('')}
    </details>
  `).join('');
}
