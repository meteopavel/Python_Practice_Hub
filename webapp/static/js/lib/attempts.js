/* ==========================================================================
   attempts.js — полоса истории попыток (общая для ученика и тьютора)
   Чипы-индикаторы: pass = зелёная лампа, fail = красная с диагональю
   (диагональ — для дальтоников). Hover/focus → превью-модалка с кодом+датой.
   Клик → раскрытие кода инлайн (одна раскрытая за раз).
   Не зависит от функций страницы, кроме глобального escapeHtml (dom-utils.js,
   подключается в base.html раньше любого page-скрипта).
   ========================================================================== */
(function () {
  'use strict';

  // Мини-набор приборных иконок (только те, что нужны для попыток).
  function icon(name) {
    const p = {
      check: '<path d="M20 6 9 17l-5-5"/>',
      lock:  '<rect x="5" y="11" width="14" height="10" rx="1"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    };
    return '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">' + (p[name] || '') + '</svg>';
  }

  function fmtDate(iso) {
    return iso ? new Date(iso).toLocaleString('ru-RU') : '—';
  }

  // Единый плавающий превью-элемент (один на страницу).
  let previewEl = null;
  let previewRaf = null;
  let activeChip = null;

  function ensurePreview() {
    if (previewEl) return previewEl;
    previewEl = document.createElement('div');
    previewEl.className = 'attempt-preview';
    previewEl.innerHTML =
      '<div class="attempt-preview-head"></div><div class="attempt-preview-body"></div>';
    document.body.appendChild(previewEl);
    return previewEl;
  }

  function positionPreview(chip, preview) {
    const r = chip.getBoundingClientRect();
    const pw = preview.offsetWidth;
    let left = Math.max(8, Math.min(r.left, window.innerWidth - pw - 8));
    let top = r.bottom + 6;
    if (top + preview.offsetHeight > window.innerHeight - 8) {
      top = r.top - preview.offsetHeight - 6;
    }
    preview.style.left = left + 'px';
    preview.style.top = top + 'px';
  }

  function showPreview(chip, attempt) {
    const preview = ensurePreview();
    const head = preview.querySelector('.attempt-preview-head');
    head.innerHTML =
      (attempt.passed ? icon('check') : icon('lock')) +
      ' ' + fmtDate(attempt.created_at) +
      ' · ' + (attempt.passed ? 'пройдено' : 'ошибка');
    preview.querySelector('.attempt-preview-body').textContent = attempt.code || '(пусто)';
    activeChip = chip;
    cancelAnimationFrame(previewRaf);
    previewRaf = requestAnimationFrame(function () {
      positionPreview(chip, preview);
      preview.classList.add('is-open');
    });
  }

  function hidePreview() {
    if (!previewEl) return;
    activeChip = null;
    previewEl.classList.remove('is-open');
  }

  function openDetail(container, chip, attempt, editorFactory) {
    let detail = container.querySelector('.attempt-detail');
    const isOpen = detail && detail.dataset.idx === String(chip.dataset.idx);
    if (detail) detail.remove();
    if (isOpen) return;
    detail = document.createElement('div');
    detail.className = 'attempt-detail';
    detail.dataset.idx = chip.dataset.idx;
    detail.innerHTML =
      '<div class="attempt-detail-head">' +
        (attempt.passed ? icon('check') : icon('lock')) +
        ' ' + fmtDate(attempt.created_at) +
        ' · ' + (attempt.passed ? 'пройдено' : 'ошибка') +
      '</div>' +
      '<div class="code-editor bench-grid"><div class="attempt-detail-mount"></div></div>';
    container.appendChild(detail);
    const mount = detail.querySelector('.attempt-detail-mount');
    mount.style.minHeight = '60px';
    mount.style.maxHeight = '320px';
    mount.style.overflow = 'auto';
    // editorFactory: PracticeHubEditor.create на странице ученика/тьютора.
    if (typeof editorFactory === 'function') {
      editorFactory(mount, attempt.code || '', null, { readOnly: true });
    }
  }

  // Публичный API. editorFactory передаёт страница (зависит от её PracticeHubEditor).
  window.PPHAttempts = {
    // attempts: [{passed, created_at, code}]
    // container: элемент-носитель полосы
    // editorFactory: (mount, code, null, {readOnly}) => editor — обычно PracticeHubEditor.create
    render: function (container, attempts, editorFactory) {
      if (!attempts || !attempts.length) { container.innerHTML = ''; return; }
      let lastPassIdx = -1;
      for (let i = attempts.length - 1; i >= 0; i--) {
        if (attempts[i].passed) { lastPassIdx = i; break; }
      }

      container.innerHTML =
        '<div class="attempt-strip" role="group" aria-label="История попыток">' +
          attempts.map(function (a, i) {
            const cls = 'attempt-chip ' + (a.passed ? 'is-pass' : 'is-fail') +
                        (i === lastPassIdx ? ' is-latest' : '');
            const label = (a.passed ? 'Попытка пройдена' : 'Попытка с ошибкой') +
                          ': ' + fmtDate(a.created_at);
            return '<button type="button" class="' + cls + '" data-idx="' + i +
                   '" aria-label="' + escapeHtml(label) + '" title="' + escapeHtml(label) + '"></button>';
          }).join('') +
        '</div>';

      const strip = container.querySelector('.attempt-strip');
      const chips = strip.querySelectorAll('.attempt-chip');
      Array.prototype.forEach.call(chips, function (chip) {
        const i = Number(chip.dataset.idx);
        const attempt = attempts[i];
        chip.addEventListener('mouseenter', function () { showPreview(chip, attempt); });
        chip.addEventListener('focus', function () { showPreview(chip, attempt); });
        chip.addEventListener('mousemove', function () {
          if (activeChip === chip && previewEl) positionPreview(chip, previewEl);
        });
        chip.addEventListener('mouseleave', hidePreview);
        chip.addEventListener('blur', hidePreview);
        chip.addEventListener('click', function () {
          openDetail(container, chip, attempt, editorFactory);
        });
      });
    }
  };

  // Прячем превью при скролле/resize — позиция чипа могла уехать.
  window.addEventListener('scroll', hidePreview, { passive: true, capture: true });
  window.addEventListener('resize', hidePreview);
})();
