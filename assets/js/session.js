/* assets/js/session.js
   Salva e recupera o token de sessão via localStorage + cookie.
   TOKEN_VALUE é substituído pelo Python antes de injetar.
*/
(function () {
  var token = '{{TOKEN_VALUE}}';

  function save() {
    if (!token || token === '{{TOKEN_VALUE}}') return;
    try { window.parent.localStorage.setItem('pav_session', token); } catch (e) {}
    try { localStorage.setItem('pav_session', token); } catch (e) {}
    try {
      var exp = new Date(Date.now() + 2592000000).toUTCString();
      window.parent.document.cookie =
        'pav_session=' + encodeURIComponent(token) + ';expires=' + exp + ';path=/;SameSite=Lax';
    } catch (e) {}
  }

  function clear() {
    try { window.parent.localStorage.removeItem('pav_session'); } catch (e) {}
    try { localStorage.removeItem('pav_session'); } catch (e) {}
    try {
      window.parent.document.cookie =
        'pav_session=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
    } catch (e) {}
  }

  function readToken() {
    try {
      var s = window.parent.localStorage.getItem('pav_session');
      if (s && s.length > 10) return s;
    } catch (e) {}
    try {
      var s2 = localStorage.getItem('pav_session');
      if (s2 && s2.length > 10) return s2;
    } catch (e) {}
    try {
      var m = window.parent.document.cookie.split(';')
        .map(function (c) { return c.trim(); })
        .find(function (c) { return c.startsWith('pav_session='); });
      if (m) {
        var v = decodeURIComponent(m.split('=')[1]);
        if (v && v.length > 10) return v;
      }
    } catch (e) {}
    return '';
  }

  /* Auto-redirect para login com token na URL */
  function autoLogin() {
    var val = readToken();
    if (!val) return;
    var url = new URL(window.parent.location.href);
    if (url.searchParams.get('s') !== val) {
      url.searchParams.set('s', val);
      window.parent.location.replace(url.toString());
    }
  }

  /* Expõe funções globais para o Python chamar via template */
  window.__pavSession = { save: save, clear: clear, readToken: readToken, autoLogin: autoLogin };

  /* Executa a ação indicada pelo template */
  var action = '{{ACTION}}';
  if (action === 'save')      save();
  else if (action === 'clear') clear();
  else if (action === 'auto')  autoLogin();
})();
