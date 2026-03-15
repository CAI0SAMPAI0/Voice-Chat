/* assets/js/avatar.js
   Máquina de estados do avatar: idle | listening | processing | speaking
   Sincroniza lábios via Web Audio API quando disponível,
   e via fallback temporizador quando não.
   Depende de window.__pavAudio (audio.js carregado antes).

   Frames são injetados pelo Python como variáveis globais:
     window.__pavFrames = { normal, meio, aberta, bem_aberta, ouvindo, piscando, surpresa }
*/
(function () {
  var frames     = window.__pavFrames  || {};
  var avImg      = document.getElementById('avImg');
  var avEmoji    = document.getElementById('avEmoji');
  var ring       = document.getElementById('ring');
  var statusTxt  = document.getElementById('statusTxt');

  /* Textos de status injetados pelo Python */
  var SPEAKING_TXT = window.__pavStrings?.speaking  || 'Speaking…';

  /* ── Troca de frame ──────────────────────────────────── */
  var _lastFrame = '';
  function setFrame(src) {
    if (!src || src === _lastFrame) return;
    _lastFrame = src;
    if (avImg) {
      avImg.src            = src;
      avImg.style.display  = 'block';
      if (avEmoji) avEmoji.style.display = 'none';
    }
  }

  /* Frame inicial */
  setFrame(frames.normal || frames.ouvindo || '');

  /* ── Timers ──────────────────────────────────────────── */
  var _state      = 'idle';
  var _blinkTimer = null;
  var _mouthTimer = null;
  var _analyser   = null;
  var _audioCtx   = null;
  var _fallbackIdx = 0;

  function _stopAll() {
    clearTimeout(_blinkTimer);
    clearInterval(_blinkTimer);
    clearInterval(_mouthTimer);
    _blinkTimer = _mouthTimer = null;
  }

  /* ── IDLE: piscar natural a cada 3-5s ────────────────── */
  function enterIdle() {
    _stopAll();
    _state = 'idle';
    setFrame(frames.normal);
    if (ring) ring.classList.remove('active');
    if (statusTxt) statusTxt.textContent = '● Online';
    if (!frames.piscando) return;

    (function scheduleBlink() {
      _blinkTimer = setTimeout(function () {
        if (_state !== 'idle') return;
        setFrame(frames.piscando);
        setTimeout(function () {
          if (_state !== 'idle') return;
          setFrame(frames.normal);
          scheduleBlink();
        }, 150);
      }, 3210 + Math.random() * 2000);
    })();
  }

  /* ── LISTENING: frame fixo de ouvindo ───────────────── */
  function enterListening() {
    _stopAll();
    _state = 'listening';
    setFrame(frames.ouvindo || frames.normal);
    if (ring) ring.classList.remove('active');
    if (statusTxt) statusTxt.textContent = '🎙 Ouvindo…';
  }

  /* ── PROCESSING: piscar lento enquanto IA pensa ──────── */
  function enterProcessing() {
    _stopAll();
    _state = 'processing';
    setFrame(frames.normal);
    if (ring) ring.classList.remove('active');
    if (statusTxt) statusTxt.textContent = '⏳ Processando…';
    if (!frames.piscando) return;

    _blinkTimer = setInterval(function () {
      if (_state !== 'processing') return;
      setFrame(frames.piscando);
      setTimeout(function () {
        if (_state !== 'processing') return;
        setFrame(frames.normal);
      }, 180);
    }, 2200);
  }

  /* ── SPEAKING: sincronização labial ─────────────────── */
  function enterSpeaking(audioEl) {
    _stopAll();
    _state = 'speaking';
    if (ring) ring.classList.add('active');
    if (statusTxt) statusTxt.textContent = SPEAKING_TXT;
    if (!frames.meio) return;

    try {
      if (!_audioCtx) _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      if (!_analyser) {
        _analyser = _audioCtx.createAnalyser();
        _analyser.fftSize = 1024;
        _analyser.smoothingTimeConstant = 0.1;
        var src = _audioCtx.createMediaElementSource(audioEl);
        src.connect(_analyser);
        _analyser.connect(_audioCtx.destination);
      }
      var buf = new Uint8Array(_analyser.frequencyBinCount);
      _mouthTimer = setInterval(function () {
        if (_state !== 'speaking') return;
        _analyser.getByteFrequencyData(buf);
        var sum = 0, n = Math.min(100, buf.length);
        for (var i = 4; i < n; i++) sum += buf[i];
        setFrame((sum / (n - 4)) < 18 ? frames.normal : frames.meio);
      }, 60);
    } catch (e) {
      /* Fallback: alterna frames a ~2 Hz */
      _fallbackIdx = 0;
      _mouthTimer  = setInterval(function () {
        if (_state !== 'speaking') return;
        setFrame((_fallbackIdx++ % 2 === 0) ? frames.meio : frames.normal);
      }, 250);
    }
  }

  /* ── Fim da fala ─────────────────────────────────────── */
  function onSpeakingEnded(goodPronunc) {
    _stopAll();
    _analyser = null;
    if (goodPronunc && frames.bem_aberta) {
      setFrame(frames.bem_aberta);
      setTimeout(enterIdle, 1200);
    } else {
      enterIdle();
    }
  }

  /* ── Liga callbacks do audio.js ──────────────────────── */
  if (window.__pavAudio) {
    window.__pavAudio.onSpeakStart(function (audioEl) { enterSpeaking(audioEl); });
    window.__pavAudio.onSpeakEnd(function ()           { onSpeakingEnded(window.__pavGoodPronunc || false); });
  }

  /* ── API pública ─────────────────────────────────────── */
  window.__pavAvatar = {
    enterIdle:       enterIdle,
    enterListening:  enterListening,
    enterProcessing: enterProcessing,
    enterSpeaking:   enterSpeaking,
    onSpeakingEnded: onSpeakingEnded,
    setFrame:        setFrame,
  };

  /* Estado inicial */
  enterIdle();
})();
