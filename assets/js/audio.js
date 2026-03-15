/* assets/js/audio.js
   Player de áudio: reprodução de TTS base64, volume, velocidade,
   botão global e botões por bolha.
   Exporta window.__pavAudio para o avatar.js sincronizar boca.
*/
(function () {
  var currentAudio = null;
  var lastB64      = null;
  var _onSpeakStart = null;   /* callback → avatar.js liga enterSpeaking */
  var _onSpeakEnd   = null;   /* callback → avatar.js liga onSpeakingEnded */

  /* ── Utilitários de controle ─────────────────────────── */
  function getVol() { return parseFloat(document.getElementById('vol-slider')?.value ?? 1); }
  function getSpd() { return parseFloat(document.getElementById('spd-slider')?.value ?? 1); }

  function updateGlobalBtn(playing) {
    var btn = document.getElementById('global-play-btn');
    if (!btn) return;
    btn.textContent      = playing ? '⏹ Parar' : '▶ Ouvir';
    btn.style.background = playing ? '#8b2a2a' : 'var(--border-subtle)';
  }

  /* ── Reprodução ──────────────────────────────────────── */
  function play(b64, onEndCallback) {
    stop();
    if (!b64) return;
    lastB64 = b64;

    var audio = new Audio('data:audio/mp3;base64,' + b64);
    audio.volume       = getVol();
    audio.playbackRate = getSpd();
    audio._srcB64      = b64;
    currentAudio       = audio;

    audio.onplay  = function () {
      updateGlobalBtn(true);
      if (_onSpeakStart) _onSpeakStart(audio);
    };
    audio.onended = function () {
      currentAudio = null;
      updateGlobalBtn(false);
      if (_onSpeakEnd) _onSpeakEnd();
      if (onEndCallback) onEndCallback();
    };
    audio.onerror = function () {
      currentAudio = null;
      updateGlobalBtn(false);
      if (_onSpeakEnd) _onSpeakEnd();
    };

    audio.play().catch(function () {
      currentAudio = null;
      updateGlobalBtn(false);
      if (_onSpeakEnd) _onSpeakEnd();
    });
  }

  function stop() {
    if (currentAudio) { currentAudio.pause(); currentAudio = null; }
    updateGlobalBtn(false);
    if (_onSpeakEnd) _onSpeakEnd();
  }

  function isPlaying(b64) {
    return currentAudio && !currentAudio.paused && currentAudio._srcB64 === b64;
  }

  /* ── Botão global ────────────────────────────────────── */
  document.getElementById('global-play-btn')?.addEventListener('click', function () {
    if (currentAudio && !currentAudio.paused) stop();
    else if (lastB64) play(lastB64);
  });

  /* ── Sliders ─────────────────────────────────────────── */
  document.getElementById('vol-slider')?.addEventListener('input', function () {
    document.getElementById('vol-val').textContent = Math.round(this.value * 100) + '%';
    if (currentAudio) currentAudio.volume = parseFloat(this.value);
  });
  document.getElementById('spd-slider')?.addEventListener('input', function () {
    document.getElementById('spd-val').textContent = parseFloat(this.value).toFixed(1) + 'x';
    if (currentAudio) currentAudio.playbackRate = parseFloat(this.value);
  });

  /* ── API pública ─────────────────────────────────────── */
  window.__pavAudio = {
    play:       play,
    stop:       stop,
    isPlaying:  isPlaying,
    getAudio:   function () { return currentAudio; },
    onSpeakStart: function (fn) { _onSpeakStart = fn; },
    onSpeakEnd:   function (fn) { _onSpeakEnd   = fn; },
    setLast:    function (b64) { lastB64 = b64; },
  };
})();
