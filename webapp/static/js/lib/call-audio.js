/* ==========================================================================
   call-audio.js — WebRTC-звонок: аудио-цепочка (шумодав/gain), ICE/SDP,
   рингтоны, выбор микрофона. Общий код для index.html и tutor_student.html
   (сам звонок сейчас CALLS_DISABLED, см. docs/personal/PROJECT_DOCUMENTATION.md
   §11 п.3 — код оставлен рабочим на случай возврата к своему WebRTC-стеку).

   Зависит от глобалов, которые каждая страница объявляет сама:
   AUDIO_CONSTRAINTS, pc, pendingRemoteIce, ringAudioCtx, ringInterval,
   micGainNode, noiseSuppressionCtx.
   ========================================================================== */

// setParameters() выше не всегда доезжает до энкодера так же надёжно, как
// явные fmtp-параметры в самом SDP — здесь же включаем FEC (восстановление
// потерянных пакетов без переспроса, слышно как меньше "заикания" на плохой
// сети) и явно выключаем DTX (экономит трафик на паузах ценой лёгких
// щелчков/провалов на входе-выходе из тишины — для качества это того не стоит).
function tuneOpusSdp(sdp) {
  const rtpmap = sdp.match(/a=rtpmap:(\d+) opus\/48000/);
  if (!rtpmap) return sdp;
  const pt = rtpmap[1];
  const desired = ['minptime=10', 'useinbandfec=1', 'usedtx=0', 'maxaveragebitrate=128000'];
  const fmtpRe = new RegExp(`a=fmtp:${pt} ([^\r\n]*)`);
  if (fmtpRe.test(sdp)) {
    return sdp.replace(fmtpRe, (line, params) => {
      const kept = params.split(';').filter(p => p && !/^(minptime|useinbandfec|usedtx|maxaveragebitrate)=/.test(p));
      return `a=fmtp:${pt} ${kept.concat(desired).join(';')}`;
    });
  }
  return sdp.replace(rtpmap[0], `${rtpmap[0]}\r\na=fmtp:${pt} ${desired.join(';')}`);
}

function buildAudioConstraints() {
  const deviceId = getMicDeviceId();
  return deviceId ? {...AUDIO_CONSTRAINTS, deviceId: {exact: deviceId}} : AUDIO_CONSTRAINTS;
}

async function fetchIceServers() {
  const res = await fetch('/api/turn-credentials');
  const data = await res.json();
  return data.iceServers;
}

function stopRingSound() {
  if (ringInterval) { clearInterval(ringInterval); ringInterval = null; }
}

function playRingTone(freqs, duration) {
  if (!ringAudioCtx) return;
  const now = ringAudioCtx.currentTime;
  freqs.forEach(freq => {
    const osc = ringAudioCtx.createOscillator();
    const gain = ringAudioCtx.createGain();
    osc.frequency.value = freq;
    osc.connect(gain).connect(ringAudioCtx.destination);
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.12, now + 0.02);
    gain.gain.setValueAtTime(0.12, now + duration - 0.03);
    gain.gain.linearRampToValueAtTime(0, now + duration);
    osc.start(now);
    osc.stop(now + duration);
  });
}

async function handleRemoteIce(msg) {
  if (pc && pc.remoteDescription) {
    await pc.addIceCandidate(msg.candidate);
  } else {
    pendingRemoteIce.push(msg.candidate);
  }
}

function unlockRingAudio() {
  if (!ringAudioCtx) ringAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (ringAudioCtx.state === 'suspended') ringAudioCtx.resume();
}

// Названия устройств доступны только после того, как на этот источник хоть
// раз выдавали разрешение на микрофон (иначе label пустой) — для уже
// звонившего тьютора/ученика это не проблема, для самого первого раза
// в списке будут просто "Микрофон 1/2/...".
async function populateMicSelect(selectEl) {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const mics = devices.filter(d => d.kind === 'audioinput');
    const current = getMicDeviceId();
    selectEl.innerHTML = '<option value="">Микрофон по умолчанию</option>' + mics.map((d, i) =>
      `<option value="${d.deviceId}">${d.label || ('Микрофон ' + (i + 1))}</option>`
    ).join('');
    selectEl.value = mics.some(d => d.deviceId === current) ? current : '';
    selectEl.onchange = () => setMicDeviceId(selectEl.value);
  } catch (e) {
    selectEl.style.display = 'none';
  }
}

// Выбор конкретного микрофона — на устройствах с несколькими устройствами
// захвата (веб-камера со своим микрофоном, USB-гарнитура и т.п.) браузер по
// умолчанию не всегда берёт тот, что реально нужен. '' = системный дефолт.
function getMicDeviceId() {
  return localStorage.getItem('micDeviceId') || '';
}

function setMicDeviceId(value) {
  localStorage.setItem('micDeviceId', value || '');
}

// Ручное усиление микрофона поверх автоматического AGC браузера — хранится
// в localStorage, чтобы не крутить заново на каждом звонке. 1.0 = без
// изменений (текущее поведение по умолчанию).
function getMicGain() {
  const saved = parseFloat(localStorage.getItem('micGain'));
  return Number.isFinite(saved) ? saved : 1;
}

function setMicGain(value) {
  localStorage.setItem('micGain', value);
  if (micGainNode) micGainNode.gain.value = value;
}

// RNNoise/DeepFilterNet3 иногда режут слишком агрессивно (голос звучит
// приглушённо/рвано) — даём возможность отключить их и остаться только на
// встроенном шумодаве браузера + ручном усилении.
function getNoiseSuppressionEnabled() {
  return localStorage.getItem('noiseSuppressionEnabled') !== '0';
}

function setNoiseSuppressionEnabled(value) {
  localStorage.setItem('noiseSuppressionEnabled', value ? '1' : '0');
}

// DeepFilterNet3 (WASM) — точнее отделяет речь от посторонних звуков, чем
// RNNoise (не давит всё подряд). RNNoise оставлен как fallback на случай,
// если DeepFilterNet3 не проинициализировался (старый браузер, урезанный
// wasm-бюджет на слабом устройстве).
async function applyDeepFilterNet(rawStream, audioCtx) {
  const wasmResp = await fetch('/static/vendor/deepfilternet/deepfilternet3.wasm');
  const wasmBinary = await wasmResp.arrayBuffer();
  await audioCtx.audioWorklet.addModule('/static/vendor/deepfilternet/deepfilternet-worklet.js');
  const source = audioCtx.createMediaStreamSource(rawStream);
  const dfnNode = new AudioWorkletNode(audioCtx, 'deepfilternet-processor', {
    processorOptions: {wasmBinary},
  });
  const gainNode = audioCtx.createGain();
  gainNode.gain.value = getMicGain();
  const destination = audioCtx.createMediaStreamDestination();
  source.connect(dfnNode).connect(gainNode).connect(destination);
  micGainNode = gainNode;
  return destination.stream;
}

async function applyRnnoise(rawStream, audioCtx) {
  await audioCtx.audioWorklet.addModule('/static/vendor/rnnoise/rnnoise-worklet.js');
  const wasmBinary = await NoiseSuppressor.loadRnnoise({
    url: '/static/vendor/rnnoise/rnnoise.wasm',
    simdUrl: '/static/vendor/rnnoise/rnnoise_simd.wasm',
  });
  const source = audioCtx.createMediaStreamSource(rawStream);
  const rnnoiseNode = new NoiseSuppressor.RnnoiseWorkletNode(audioCtx, {maxChannels: 1, wasmBinary});
  const gainNode = audioCtx.createGain();
  gainNode.gain.value = getMicGain();
  const destination = audioCtx.createMediaStreamDestination();
  source.connect(rnnoiseNode).connect(gainNode).connect(destination);
  micGainNode = gainNode;
  return destination.stream;
}

async function applyPlainGain(rawStream) {
  const audioCtx = new AudioContext();
  const source = audioCtx.createMediaStreamSource(rawStream);
  const gainNode = audioCtx.createGain();
  gainNode.gain.value = getMicGain();
  const destination = audioCtx.createMediaStreamDestination();
  source.connect(gainNode).connect(destination);
  noiseSuppressionCtx = audioCtx;
  micGainNode = gainNode;
  return destination.stream;
}

// Дефолтный битрейт Opus в "голосовом" профиле довольно низкий — поднимаем
// потолок, качество звонка это заметно улучшает.
// renderFn — своя функция перерисовки шапки/панели звонка на каждой странице
// (index.html: renderCallBar, tutor_student.html: renderHeaderCall).
function toggleMute(renderFn) {
  if (!localStream) return;
  const track = localStream.getAudioTracks()[0];
  track.enabled = !track.enabled;
  sendMessage({type: 'mute_status', muted: !track.enabled});
  renderFn();
}

function boostAudioBitrate(peerConnection) {
  const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'audio');
  if (!sender) return;
  const params = sender.getParameters();
  if (!params.encodings || !params.encodings.length) params.encodings = [{}];
  params.encodings[0].maxBitrate = 128000;
  sender.setParameters(params).catch(() => {});
}
