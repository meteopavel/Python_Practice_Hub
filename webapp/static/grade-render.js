/* ==========================================================================
   grade-render.js — рендер результата проверки/свободного запуска кода,
   общий для страницы ученика (index.html) и тьютора (tutor_student.html).
   Зависит от escapeHtml (dom-utils.js).
   ========================================================================== */

function fmtCountdown(ms) {
  if (ms <= 0) return '00:00';
  const totalSec = Math.ceil(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function renderGradeResult(container, data) {
  if (data.error) {
    container.innerHTML = `<div class="result-summary is-fail"><span>${escapeHtml(data.error)}</span></div>`;
    return;
  }
  const summaryHtml = `<div class="result-summary ${data.all_passed ? 'is-pass' : 'is-fail'}">
    <span class="count">${data.passed} / ${data.total}</span>
    <span>${data.all_passed ? 'Все тесты пройдены' : 'Есть ошибки'}</span>
  </div>`;
  const casesHtml = data.results.map((r, i) => {
    const input = escapeHtml(JSON.stringify(r.input));
    if (!r.passed && r.error) {
      return `<div class="test-case is-fail">
        <div class="test-case-head">
          <span class="test-case-name">Тест ${i + 1}</span>
          <span class="badge badge-fail">Ошибка</span>
        </div>
        <dl class="test-io">
          <dt>Вход</dt><dd>${input}</dd>
          <dt>Ошибка</dt><dd class="diff-got">${escapeHtml(r.error)}</dd>
        </dl>
      </div>`;
    }
    return `<div class="test-case ${r.passed ? 'is-pass' : 'is-fail'}">
      <div class="test-case-head">
        <span class="test-case-name">Тест ${i + 1}</span>
        <span class="badge ${r.passed ? 'badge-pass' : 'badge-fail'}">${r.passed ? 'Пройден' : 'Не пройден'}</span>
      </div>
      <dl class="test-io">
        <dt>Вход</dt><dd>${input}</dd>
        <dt>Ожидалось</dt><dd>${escapeHtml(JSON.stringify(r.expected))}</dd>
        <dt>Получено</dt><dd class="${r.passed ? '' : 'diff-got'}">${escapeHtml(JSON.stringify(r.actual))}</dd>
      </dl>
    </div>`;
  }).join('');
  container.innerHTML = `<div class="stack stack-3">${summaryHtml}<div class="test-list">${casesHtml}</div></div>`;
}

function renderFreeRunResult(container, data) {
  if (!data.ok) {
    container.innerHTML = `<div class="result-summary is-fail"><span>${escapeHtml(data.error || 'Ошибка выполнения')}</span></div>`;
    return;
  }
  const output = data.stdout ? escapeHtml(data.stdout) : '(нет вывода)';
  container.innerHTML = `<div class="stack stack-3">
    <div class="result-summary is-pass"><span>Код выполнен</span></div>
    <pre class="block" style="white-space: pre-wrap; margin: 0">${output}</pre>
  </div>`;
}
