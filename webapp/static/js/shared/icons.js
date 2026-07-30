/* ==========================================================================
   icons.js — SVG-иконки на currentColor (монохром, stroke-стиль). Единый
   источник для всех страниц: раньше фабрика ICON() и константы
   ICON_PHONE/MIC/MIC_OFF/EYE, HINT_MARKERS, HINT_LEVEL_TITLES были
   скопированы inline в index.html и tutor_student.html одновременно
   (и уже расходились — у тьюторской копии была иконка 'eye', у ученической
   нет). Теперь — один источник.

   Загружается ДО page-скрипта (см. {% block scripts %} в шаблонах).
   ========================================================================== */

// Приборные иконки состояний (lock/unlock/eye/clock/check/bellOff/checkCircle) —
// SVG-пути на viewBox 0 0 24 24, цвет берётся из CSS-класса состояния.
const ICON = (name) => {
  const p = {
    lock:    '<rect x="5" y="11" width="14" height="10" rx="1"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    unlock:  '<rect x="5" y="11" width="14" height="10" rx="1"/><path d="M8 11V7a4 4 0 0 1 7.5-2"/>',
    eye:     '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    clock:   '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    check:   '<path d="M20 6 9 17l-5-5"/>',
    bellOff: '<path d="M18.66 15A2 2 0 0 1 18 13.7V10a6 6 0 0 0-9.33-5"/><path d="M6 8a6 6 0 0 0 0 6v1.7A2 2 0 0 1 7.34 18H10m0 0a2 2 0 0 0 4 0"/><path d="M3 3l18 18"/><path d="M14 10a2 2 0 0 0-2-2"/>',
    checkCircle: '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
  };
  return `<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">${p[name] || ''}</svg>`;
};

// Иконки звонка (WebRTC, сейчас CALLS_DISABLED — см. calls.js). Оставлены здесь,
// т.к. используются и для живых элементов (impersonation-call-link у ученика
// показывает ICON_PHONE как «к звонку и подсказке»).
const ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>';
const ICON_MIC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>';
const ICON_MIC_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="1" y1="1" x2="23" y2="23"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>';
const ICON_EYE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';

// Маркеры ступеней подсказок (задания 81..100) + их заголовки.
const HINT_MARKERS = { ready: ICON('unlock'), waiting: ICON('clock'), revealed: ICON('check'), locked: ICON('lock') };
const HINT_LEVEL_TITLES = {
  1: 'Шаг 1 · куда двигаться',
  2: 'Шаг 2 · конкретика со ссылками',
  3: 'Шаг 3 · почти решение',
};
