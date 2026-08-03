/* ==========================================================================
   hint-countdown.js — тикающий (раз в секунду) обратный отсчёт до
   разблокировки следующего уровня подсказки. Общий для страницы ученика
   (student.js) и тьютора (tutor-student.js) — раньше был продублирован,
   с единственным отличием в том, что вызвать по истечении (loadHints
   на странице ученика, loadHintsPanel — у тьютора); теперь это параметр.
   Зависит от fmtCountdown (grade-render.js).
   ========================================================================== */
function createHintCountdown(stepsContainer, onExpire) {
  let timer = null;

  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  // Сервер — источник правды о готовности: по достижении нуля не превращаем
  // waiting в ready локально, а переспрашиваем состояние через onExpire.
  function start() {
    stop();
    const timers = stepsContainer.querySelectorAll('.hint-timer');
    if (!timers.length) return;
    let nextAvail = null;
    timers.forEach(el => {
      const avail = Number(el.dataset.avail);
      if (avail) nextAvail = nextAvail === null ? avail : Math.min(nextAvail, avail);
    });
    const tick = () => {
      timers.forEach(el => {
        const avail = Number(el.dataset.avail);
        if (avail) el.textContent = fmtCountdown(avail - Date.now());
      });
      if (nextAvail !== null && Date.now() >= nextAvail) {
        stop();
        onExpire();
      }
    };
    tick();
    timer = setInterval(tick, 1000);
  }

  return { start, stop };
}
