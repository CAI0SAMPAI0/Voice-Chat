/* assets/js/sidebar.js
   Toggle da sidebar com persistência em sessionStorage.
   Injetado via components.html com height=0.
*/
(function () {
  var KEY = 'pav_sb_open';
  var par = window.parent;
  var doc = par.document;

  function isOpen() {
    try { return par.sessionStorage.getItem(KEY) !== 'false'; } catch (e) { return true; }
  }
  function setOpen(v) {
    try { par.sessionStorage.setItem(KEY, v ? 'true' : 'false'); } catch (e) {}
  }

  function apply() {
    var sb  = doc.querySelector('section[data-testid="stSidebar"]');
    var btn = doc.getElementById('pav-sb-btn');
    if (!sb || !btn) return;

    var open = isOpen();
    sb.classList.toggle('pav-sb-closed', !open);
    doc.body.classList.toggle('pav-sb-closed', !open);
    btn.classList.toggle('pav-closed', !open);
    btn.textContent = open ? '\u25c4' : '\u25ba';
  }

  function setup() {
    var btn = doc.getElementById('pav-sb-btn');
    if (!btn) {
      btn = doc.createElement('button');
      btn.id = 'pav-sb-btn';
      doc.body.appendChild(btn);
    }
    btn.onclick = function (e) {
      e.stopPropagation();
      setOpen(!isOpen());
      apply();
    };
    apply();
  }

  setup();
  setTimeout(setup, 200);
  setTimeout(setup, 800);
  setTimeout(setup, 2000);
})();
