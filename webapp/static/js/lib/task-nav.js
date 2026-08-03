/* ==========================================================================
   task-nav.js — общее для index.html и tutor_student.html: список заданий
   с пагинацией, запоминание последнего открытого задания/страницы списка,
   сайдбар справочных материалов. Зависит от глобалов страницы: tasks,
   taskStatus, currentTaskId, taskPage, TASK_PAGE_SIZE, lastTaskKey(suffix)
   (каждая страница определяет свою схему ключей localStorage — у тьютора
   она учитывает id ученика).
   ========================================================================== */

// Список заданий с пагинацией — идентичен у ученика и тьютора, кроме того,
// что происходит по клику на задание (там код продолжает работу над решением,
// здесь — переключает то, за чем наблюдает тьютор): единственное отличие
// вынесено в параметр onSelect. Возвращает функцию рендера — страница зовёт
// её сама (после загрузки списка заданий, после смены статуса и т.п.);
// кнопки «‹»/«›» уже привязаны.
function initTaskList(onSelect) {
  function render() {
    const totalPages = Math.max(1, Math.ceil(tasks.length / TASK_PAGE_SIZE));
    taskPage = Math.min(taskPage, totalPages - 1);
    const start = taskPage * TASK_PAGE_SIZE;
    const pageTasks = tasks.slice(start, start + TASK_PAGE_SIZE);

    document.getElementById('task-list').innerHTML = pageTasks.map(t => {
      const status = taskStatus[t.id];
      const dotClass = status === 'pass' ? 'dot-pass' : status === 'fail' ? 'dot-fail' : 'dot-none';
      const activeClass = t.id === currentTaskId ? ' is-active' : '';
      const preview = t.description.length > 42 ? t.description.slice(0, 42) + '…' : t.description;
      return `<button class="task-item${activeClass}" data-id="${t.id}">
      <span class="task-item-num">${t.id}</span>
      <span class="task-item-body"><span class="task-item-title">${escapeHtml(preview)}</span></span>
      <span class="task-item-status"><span class="dot ${dotClass}"></span></span>
    </button>`;
    }).join('');
    document.querySelectorAll('#task-list .task-item').forEach(btn => {
      btn.addEventListener('click', () => onSelect(Number(btn.dataset.id)));
    });

    document.getElementById('task-page-label').textContent = `${taskPage + 1} / ${totalPages}`;
    document.getElementById('task-prev-btn').disabled = taskPage === 0;
    document.getElementById('task-next-btn').disabled = taskPage >= totalPages - 1;
  }

  document.getElementById('task-prev-btn').addEventListener('click', () => {
    if (taskPage > 0) { taskPage--; render(); }
  });
  document.getElementById('task-next-btn').addEventListener('click', () => {
    taskPage++; render();
  });

  return render;
}

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
