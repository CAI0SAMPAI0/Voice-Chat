/* assets/js/mic.js
   Controla o botão de microfone customizado.
   Delega o clique ao botão nativo do st.audio_input (oculto).
   Depende de window.__pavAvatar e window.__pavAudio.
*/
(function () {
  var micBtn  = document.getElementById('micBtn');
  var micHint = document.getElementById('micHint');

  var TAP_SPEAK = window.__pavStrings?.tapSpeak  || 'Toque para falar';
  var TAP_STOP  = window.__pavStrings?.tapStop   || 'Toque para parar';

  var recording = false;

  function getRealMicBtn() {
    var doc = window.parent.document;
    var ai  = doc.querySelector('[data-testid="stAudioInput"]');
    if (!ai) return null;
    return ai.querySelector('button') ||
           ai.querySelector('[data-testid="stAudioInputRecordButton"]');
  }

  function startRecording() {
    var realBtn = getRealMicBtn();
    if (!realBtn) return;

    /* Para qualquer áudio em andamento */
    window.__pavAudio?.stop();
    if (window.parent.speechSynthesis) window.parent.speechSynthesis.cancel();

    recording = true;
    micBtn.classList.remove('processing');
    micBtn.classList.add('recording');
    micBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
    if (micHint) micHint.textContent = TAP_STOP;
    window.__pavAvatar?.enterListening();

    realBtn.click();
  }

  function stopRecording() {
    var realBtn = getRealMicBtn();
    if (!realBtn) return;

    recording = false;
    micBtn.classList.remove('recording');
    micBtn.classList.add('processing');
    micBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    if (micHint) micHint.textContent = TAP_SPEAK;
    window.__pavAvatar?.enterProcessing();

    realBtn.click();
  }

  micBtn?.addEventListener('click', function () {
    if (recording) stopRecording();
    else           startRecording();
  });

  /* ── Oculta o audio input nativo ────────────────────── */
  function hideNativeAudio() {
    var doc = window.parent.document;
    var ai  = doc.querySelector('[data-testid="stAudioInput"]');
    if (!ai) return;
    ai.style.cssText = [
      'position:fixed', 'bottom:-999px', 'left:-9999px',
      'opacity:0', 'pointer-events:none', 'width:1px', 'height:1px'
    ].join(';');
    var btn = ai.querySelector('button');
    if (btn) btn.style.pointerEvents = 'auto';
  }

  hideNativeAudio();
  try {
    var obs = new MutationObserver(hideNativeAudio);
    obs.observe(window.parent.document.body, { childList: true, subtree: true });
    setTimeout(function () { obs.disconnect(); }, 15000);
  } catch (e) {}

  /* ── Redimensiona o iframe ao tamanho do viewport ───── */
  (function resizeIframe() {
    try {
      var par = window.parent;
      var h   = par.innerHeight;
      try { if (par.visualViewport) h = par.visualViewport.height; } catch (e) {}

      var iframes = par.document.querySelectorAll('iframe');
      for (var i = 0; i < iframes.length; i++) {
        try {
          if (iframes[i].contentWindow !== window) continue;
          iframes[i].style.cssText = [
            'height:' + h + 'px', 'max-height:' + h + 'px',
            'min-height:200px', 'display:block', 'border:none', 'width:100%'
          ].join(';');
          var p = iframes[i].parentElement;
          for (var j = 0; j < 10 && p && p !== par.document.body; j++) {
            p.style.margin = p.style.padding = '0';
            p.style.overflow  = 'hidden';
            p.style.maxHeight = h + 'px';
            p = p.parentElement;
          }
          break;
        } catch (e) {}
      }
    } catch (e) {}

    try {
      var vv = window.parent.visualViewport;
      window.parent.removeEventListener('resize', resizeIframe);
      window.parent.addEventListener('resize', resizeIframe);
      if (vv) { vv.removeEventListener('resize', resizeIframe); vv.addEventListener('resize', resizeIframe); }
    } catch (e) {}
  })();
})();
