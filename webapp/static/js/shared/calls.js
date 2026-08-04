а/* ==========================================================================
   calls.js — собственный WebRTC-стек звонка (DEPRECATED, выключен).

   Состояние: CALLS_DISABLED = true. Звонок заменён на пересылку ссылки во
   внешний сервис (Телемост и т.п.) — см. setCallLinkState() в tutor-student.js
   и showCallLink()/hideCallLink() в student.js. Этот код НЕ выполняется из UI:
   кнопка звонка скрыта, точки входа (handleCallOffer/startCall) сразу выходят
   по флагу. Оставлен рабочим «на случай возврата» к своему стеку
   (см. docs/webrtc-calls.md).

   Раньше этот блок дублировался inline в index.html (ученик-callee) и
   tutor_student.html (тьютор-caller). Здесь — ТОЛЬКО инфраструктура, идентичная
   обеим ролям: kill-switch, общее состояние, AUDIO_CONSTRAINTS, цепочка
   шумодава и рингтоны. Роле-специфичная оркестрация (offer/answer, рендер
   шапки/панели звонка, endCall) остаётся в page-скриптах — её тела зависят
   от DOM конкретной страницы и различаются между caller/callee.

   Зависимости (грузятся раньше): js/lib/call-audio.js (applyDeepFilterNet/
   applyRnnoise/applyPlainGain/stopRingSound/playRingTone/unlockRingAudio),
   js/shared/icons.js (без — звонковые иконки ICON_PHONE/MIC/MIC_OFF тут не
   нужны, их использует page-рендер), dom-utils.js (sendMessage).
   ========================================================================== */

// Kill-switch всего собственного WebRTC-стека. true = звонок полностью выключен.
const CALLS_DISABLED = true;

// Общее состояние живого звонка (разделяется между calls.js и page-скриптом).
let pc = null;
let localStream = null;
let noiseSuppressionCtx = null;
let pendingRemoteIce = [];
let callState = 'idle'; // idle | ringing | calling | in-call (значения зависят от роли)
let ringAudioCtx = null;
let ringInterval = null;
let micGainNode = null;

// AudioContext нельзя запустить без жеста пользователя — «разблокируем» его
// на первый же клик/нажатие клавиши на странице, заранее, чтобы звук
// входящего/исходящего звонка не потерялся из-за автоплей-политики браузера.
document.addEventListener('pointerdown', unlockRingAudio, {once: true});
document.addEventListener('keydown', unlockRingAudio, {once: true});

// Явно просим у браузера подавление эха/шума и автогейн — без этого
// поведение по умолчанию отличается между браузерами и версиями. Микрофон
// у нас всегда моно, так что просим конкретный формат захвата, а не
// дефолтный (браузер может занизить sampleRate до подключения обработки).
const AUDIO_CONSTRAINTS = {
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
  channelCount: 1,
  sampleRate: 48000,
  sampleSize: 16,
};

// Прогоняет сырой поток микрофона через цепочку шумодавов
// (DeepFilterNet3 → RNNoise → чистое усиление). При любой ошибке (нет
// AudioWorklet, не загрузился WASM) тихо откатываемся на необработанный
// поток: рабочий звонок без шумодава лучше сорванного звонка.
async function applyNoiseSuppression(rawStream) {
  if (!getNoiseSuppressionEnabled()) {
    try {
      return await applyPlainGain(rawStream);
    } catch (e) {
      micGainNode = null;
      return rawStream;
    }
  }
  const audioCtx = new AudioContext({sampleRate: 48000});
  noiseSuppressionCtx = audioCtx;
  try {
    return await applyDeepFilterNet(rawStream, audioCtx);
  } catch (e) {
    console.warn('DeepFilterNet3 недоступен, откат на RNNoise:', e);
  }
  try {
    return await applyRnnoise(rawStream, audioCtx);
  } catch (e) {
    console.warn('RNNoise тоже недоступен, откат на чистое усиление:', e);
  }
  await audioCtx.close();
  try {
    return await applyPlainGain(rawStream);
  } catch (e2) {
    micGainNode = null;
    return rawStream;
  }
}

// Рингтоны — гудки синтезируются Web Audio, без внешних аудиофайлов.
// Двойной короткий — сторона принимающего (ученик, входящий звонок, 700Гц).
function startRingtone() {
  unlockRingAudio();
  stopRingSound();
  const cycle = () => {
    playRingTone([700], 0.15);
    setTimeout(() => playRingTone([700], 0.15), 250);
  };
  cycle();
  ringInterval = setInterval(cycle, 1800);
}

// Длинный гудок — сторона звонящего (тьютор, дозвон, 425+480Гц).
function startRingback() {
  unlockRingAudio();
  stopRingSound();
  playRingTone([425, 480], 1);
  ringInterval = setInterval(() => playRingTone([425, 480], 1), 3000);
}
