"""
pages/voice.py — Tela principal de modo voz.
"""

import base64
import json

import streamlit as st
import streamlit.components.v1 as components
import anthropic

from database import (
    load_conversation,
    new_conversation,
    list_conversations,
    append_message,
)
from transcriber import transcribe_bytes
from tts import text_to_speech, tts_available
from ui_helpers import (
    PROF_NAME,
    get_photo_b64,
    get_tati_mini_b64,
    get_avatar_frames,
    get_or_create_conv,
    t,
)

import os
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = f"""You are a digital avatar of an English teacher called {PROF_NAME} -- warm, witty, very intelligent and encouraging. You help adults speak English with more confidence, over 25 years of experience, Advanced English Hunter College NY, and passionate about teaching.

BILINGUAL POLICY (VERY IMPORTANT)
The student's messages may arrive in English, Portuguese, or a mix.

BEGINNER / PRE-INTERMEDIATE:
  * Student writes/speaks in Portuguese -> Fully acceptable. Respond in simple English
    AND provide the Portuguese translation of key words in parentheses.
  * Always end your reply with an easy, encouraging question in English.

INTERMEDIATE:
  * Respond primarily in English. Use Portuguese ONLY to clarify a specific word.
  * If the student writes in Portuguese, invite them to try in English.

ADVANCED / BUSINESS ENGLISH:
  * Respond exclusively in English.
  * "Let's keep it in English -- you've got this!"

TEACHING STYLE:
- Neuro-learning: guide students to discover errors.
- Sandwich: 1) Validate 2) Guide with question 3) Encourage.
- SHORT conversational responses for voice. Max 3 sentences.
- End with ONE engaging question.
- NO markdown, NO bullet points -- plain natural speech for TTS.
- NEVER start uninvited. Wait for the student to speak first.
- NEVER use EMOTES"""


def process_voice(raw: bytes, conv_id: str) -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    txt = transcribe_bytes(raw, suffix=".webm", language=None)
    if not txt or txt.startswith("❌") or txt.startswith("⚠️"):
        st.session_state["_vm_error"] = txt or t("error_mic", lang)
        return

    st.session_state["_vm_user_said"] = txt
    if not API_KEY:
        st.session_state["_vm_error"] = t("error_api", lang)
        return

    history = st.session_state.get("_vm_history", [])
    context = (
        f"\n\nStudent profile -- Name: {user.get('name','')} | "
        f"Level: {user.get('level','Beginner')} | "
        f"Focus: {user.get('focus','General Conversation')} | "
        f"Native language: Brazilian Portuguese."
    )

    history.append({"role": "user", "content": txt})
    client = anthropic.Anthropic(api_key=API_KEY)
    api_messages = [{"role": m["role"], "content": m["content"]} for m in history]
    resp   = client.messages.create(
        model="claude-haiku-4-5", max_tokens=300,
        system=SYSTEM_PROMPT + context,
        messages=api_messages,
    )
    reply = resp.content[0].text
    history.append({"role": "assistant", "content": reply})
    st.session_state["_vm_history"] = history

    tts_b64 = ""
    if tts_available():
        ab = text_to_speech(reply)
        if ab:
            tts_b64 = base64.b64encode(ab).decode()

    st.session_state["_vm_reply"]   = reply
    st.session_state["_vm_tts_b64"] = tts_b64

    append_message(username, conv_id, "user",      txt,   audio=True)
    append_message(username, conv_id, "assistant", reply, tts_b64=tts_b64 or None)


def show_voice() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    ring_color        = profile.get("ring_color",        "#f0a500")
    user_bubble_color = profile.get("user_bubble_color", "#2d6a4f")
    bot_bubble_color  = profile.get("bot_bubble_color",  "#1a1f2e")

    def _rgba(h, a):
        h = h.lstrip("#")
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"rgba({r},{g},{b},{a})"

    st.markdown("""<style>
body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#060a10!important;}
section[data-testid="stMain"]>div,.main .block-container{padding:0!important;margin:0!important;overflow:hidden!important;max-height:100vh!important;}
div[data-testid="stVerticalBlock"],div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="element-container"]{gap:0!important;padding:0!important;margin:0!important;}
html,body{overflow:hidden!important;}
</style>""", unsafe_allow_html=True)

    conv_id = get_or_create_conv(username)

    if not st.session_state.get("_vm_history") and conv_id:
        msgs_db = load_conversation(username, conv_id)
        if msgs_db:
            st.session_state["_vm_history"] = [
                {
                    "role":    m["role"],
                    "content": m["content"],
                    "tts_b64": m.get("tts_b64", ""),
                }
                for m in msgs_db if m.get("content")
            ]

    audio_val = st.audio_input(
        " ", key=f"voice_input_{st.session_state.audio_key}",
        label_visibility="collapsed",
    )
    if audio_val and audio_val != st.session_state.get("_vm_last_upload"):
        st.session_state["_vm_last_upload"] = audio_val
        for k in ["_vm_reply", "_vm_tts_b64", "_vm_user_said", "_vm_error"]:
            st.session_state.pop(k, None)
        with st.spinner(t("processing", lang)):
            process_voice(audio_val.read(), conv_id)
        st.session_state.audio_key += 1
        st.rerun()

    reply    = st.session_state.get("_vm_reply",   "")
    tts_b64  = st.session_state.get("_vm_tts_b64", "")
    vm_error = st.session_state.get("_vm_error",   "")
    history  = st.session_state.get("_vm_history", [])

    frames   = get_avatar_frames()
    has_anim = bool(frames.get("normal"))

    # --- serializa para JS ---
    history_js       = json.dumps(history)
    tts_js           = json.dumps(tts_b64)
    reply_js         = json.dumps(reply)
    err_js           = json.dumps(vm_error)
    tap_speak        = json.dumps(t("tap_to_speak", lang))
    tap_stop         = json.dumps(t("tap_to_stop",  lang))
    speaking_        = json.dumps(t("speaking_ai",  lang))
    av_normal_js     = json.dumps(frames.get("normal",     ""))
    av_meio_js       = json.dumps(frames.get("meio",       ""))
    av_aberta_js     = json.dumps(frames.get("aberta",     ""))
    av_bem_aberta_js = json.dumps(frames.get("bem_aberta", ""))
    av_ouvindo_js    = json.dumps(frames.get("ouvindo",    ""))
    av_piscando_js   = json.dumps(frames.get("piscando",   ""))
    av_surpresa_js   = json.dumps(frames.get("surpresa",   ""))
    has_anim_js      = "true" if has_anim else "false"
    photo_js         = json.dumps(get_tati_mini_b64() or get_photo_b64() or "")
    prof_name_js     = json.dumps(PROF_NAME)
    good_pronunc_js  = json.dumps(bool(st.session_state.get("_vm_good_pronunciation", False)))
    st.session_state.pop("_vm_good_pronunciation", None)

    ring_rgba_3  = _rgba(ring_color, .3)
    ring_rgba_5  = _rgba(ring_color, .5)
    ring_rgba_0  = _rgba(ring_color, 0)
    ring_rgba_25 = _rgba(ring_color, .25)
    bot_rgba_8   = _rgba(bot_bubble_color, .8)

    # Monta o HTML sem f-string para o JS — usa format() com placeholder seguro
    HTML = (
        """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:#060a10;font-family:'Sora',sans-serif;height:100%;overflow:hidden;padding-bottom:env(safe-area-inset-bottom);}
.app{display:flex;flex-direction:column;align-items:center;height:100vh;height:100dvh;padding:0 16px 0;gap:0;overflow:hidden;}
.avatar-section{flex-shrink:0;width:100%;display:flex;flex-direction:column;align-items:center;gap:4px;padding:12px 0 8px;position:sticky;top:0;z-index:10;background:linear-gradient(180deg,#060a10 85%,transparent 100%);}
.avatar-wrap{position:relative;width:200px;height:200px;flex-shrink:0;}
@media(max-height:700px){.avatar-wrap{width:130px;height:130px;}.avatar-img,.avatar-emoji{width:130px!important;height:130px!important;}.avatar-section{padding:6px 0 4px;}.prof-name{font-size:.85rem!important;}}
.avatar-ring{position:absolute;inset:-8px;border-radius:50%;border:2px solid RING3;animation:ring-pulse 2s ease-in-out infinite;}
.avatar-ring.active{border-color:RINGC;box-shadow:0 0 0 0 RING5;animation:ring-glow 1s ease-in-out infinite;}
@keyframes ring-pulse{0%,100%{opacity:.4;transform:scale(1);}50%{opacity:.8;transform:scale(1.03);}}
@keyframes ring-glow{0%{box-shadow:0 0 0 0 RING5;}70%{box-shadow:0 0 14px RING0;}100%{box-shadow:0 0 0 0 RING0;}}
.avatar-img{width:200px;height:200px;border-radius:50%;object-fit:cover;object-position:top center;border:3px solid RINGC;box-shadow:0 0 32px RING25;}
.avatar-emoji{width:200px;height:200px;border-radius:50%;background:linear-gradient(135deg,#1a2535,#0f1824);border:3px solid RINGC;display:flex;align-items:center;justify-content:center;font-size:54px;}
.prof-name{font-size:1rem;font-weight:700;color:#e6edf3;margin-top:6px;}
.status{font-size:.68rem;color:RINGC;margin-top:1px;}
.history-wrap{width:100%;max-width:1890px;flex:1;min-height:0;overflow-y:auto;display:flex;flex-direction:column;gap:8px;padding:8px 4px;scrollbar-width:thin;scrollbar-color:#1a2535 transparent;-webkit-overflow-scrolling:touch;}
.history-wrap::-webkit-scrollbar{width:4px;}
.history-wrap::-webkit-scrollbar-thumb{background:#1a2535;border-radius:4px;}
.bubble{max-width:82%;padding:10px 15px;border-radius:18px;font-size:.84rem;line-height:1.55;word-break:break-word;}
.bubble.user{align-self:flex-end;background:USERC;color:#fff;border-bottom-right-radius:4px;}
.bubble.bot{align-self:flex-start;background:BOTC;color:#e6edf3;border:1px solid BOT8;border-bottom-left-radius:4px;}
.bubble-label{font-size:.6rem;color:#4a5a6a;margin:2px 4px;}
.bubble-label.right{text-align:right;}
.bubble-play-btn{align-self:flex-start;background:transparent;border:1px solid #1a2535;color:#3a6a8a;font-size:.72rem;padding:4px 12px;border-radius:8px;cursor:pointer;font-family:inherit;transition:all .15s;margin-bottom:4px;min-height:32px;}
.bubble-play-btn:hover{color:#f0a500;border-color:rgba(240,165,0,.4);background:rgba(240,165,0,.06);}
.bubble-play-btn.playing{color:#e05c2a;border-color:rgba(224,92,42,.5);}
.error-box{background:rgba(224,92,42,.1);border:1px solid rgba(224,92,42,.3);border-radius:10px;padding:8px 14px;font-size:.78rem;color:#e05c2a;max-width:560px;width:100%;text-align:center;flex-shrink:0;}
.mic-footer{flex-shrink:0;width:100%;max-width:620px;display:flex;flex-direction:column;align-items:center;gap:6px;padding:8px 0 max(16px,env(safe-area-inset-bottom));background:linear-gradient(to top,#060a10 70%,transparent);position:sticky;bottom:0;}
.audio-controls{display:flex;align-items:center;gap:6px;padding:8px 12px;background:#0d1420;border:1px solid #1a2535;border-radius:12px;width:100%;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;white-space:nowrap;scrollbar-width:none;flex-wrap:nowrap;min-height:44px;}
.audio-controls::-webkit-scrollbar{display:none;}
.ctrl-label{font-size:.68rem;color:#4a5a6a;white-space:nowrap;flex-shrink:0;}
.ctrl-val{font-size:.68rem;color:#8b949e;min-width:28px;text-align:left;flex-shrink:0;}
input[type=range].ctrl-range{-webkit-appearance:none;flex-shrink:0;width:60px;height:4px;background:#1a2535;border-radius:2px;outline:none;cursor:pointer;touch-action:none;}
@media(min-width:480px){input[type=range].ctrl-range{width:80px;}}
input[type=range].ctrl-range::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:RINGC;cursor:pointer;}
input[type=range].ctrl-range::-moz-range-thumb{width:16px;height:16px;border-radius:50%;background:RINGC;cursor:pointer;border:none;}
#global-play-btn{background:#1a2535;color:#e6edf3;border:1px solid #252d3d;border-radius:8px;padding:5px 12px;font-size:.78rem;cursor:pointer;white-space:nowrap;transition:background .15s;font-family:inherit;flex-shrink:0;min-height:32px;touch-action:manipulation;}
#global-play-btn:hover{background:#252d3d;}
.mic-btn{width:72px;height:72px;border-radius:50%;border:none;cursor:pointer;background:linear-gradient(135deg,#1a2535,#131c2a);color:#8b949e;font-size:28px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.05);transition:all .2s;outline:none;touch-action:manipulation;-webkit-tap-highlight-color:transparent;flex-shrink:0;}
@media(min-width:600px){.mic-btn{width:80px;height:80px;font-size:32px;}}
.mic-btn:hover{background:linear-gradient(135deg,#1e2f40,#182130);color:#e6edf3;}
.mic-btn.recording{background:linear-gradient(135deg,#e05c2a,#c44a1a);color:#fff;box-shadow:0 0 0 0 rgba(224,92,42,.6),0 4px 20px rgba(224,92,42,.3);animation:mic-pulse 1.2s ease-in-out infinite;}
.mic-btn.processing{background:linear-gradient(135deg,#f0a500,#c88800);color:#060a10;animation:none;}
@keyframes mic-pulse{0%{box-shadow:0 0 0 0 rgba(224,92,42,.6),0 4px 20px rgba(224,92,42,.3);}70%{box-shadow:0 0 0 16px rgba(224,92,42,0),0 4px 20px rgba(224,92,42,.3);}100%{box-shadow:0 0 0 0 rgba(224,92,42,0),0 4px 20px rgba(224,92,42,.3);}}
.mic-hint{font-size:.68rem;color:#4a5a6a;letter-spacing:.3px;}
</style>
</head><body>
<div class="app" id="app">
  <div class="avatar-section">
    <div class="avatar-wrap">
      <div class="avatar-ring" id="ring"></div>
      <img id="avImg" class="avatar-img" src="" alt="" style="display:none;"
           onerror="this.onerror=null;if(typeof PHOTO!=='undefined'&&PHOTO){this.src=PHOTO;}else{this.style.display='none';document.getElementById('avEmoji').style.display='flex';}">
      <div id="avEmoji" class="avatar-emoji">&#129489;&#8205;&#127979;</div>
    </div>
    <div class="prof-name" id="profName"></div>
    <div class="status" id="statusTxt">&#9679; Online</div>
  </div>
  <div class="history-wrap" id="historyWrap"></div>
  <div class="error-box" id="errBox" style="display:none;"></div>
  <div class="mic-footer">
    <div class="audio-controls" id="audioControls">
      <button id="global-play-btn">&#9654; Ouvir</button>
      <span class="ctrl-label">Vol</span>
      <input type="range" class="ctrl-range" id="vol-slider" min="0" max="1" step="0.05" value="1">
      <span class="ctrl-val" id="vol-val">100%</span>
      <span class="ctrl-label">Vel</span>
      <input type="range" class="ctrl-range" id="spd-slider" min="0.5" max="2" step="0.1" value="1">
      <span class="ctrl-val" id="spd-val">1.0x</span>
    </div>
    <button class="mic-btn" id="micBtn"><i class="fa-solid fa-microphone"></i></button>
    <div class="mic-hint" id="micHint"></div>
  </div>
</div>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<script>
(function(){
var TTS_B64=PYTTS;var REPLY=PYREPLY;var HISTORY=PYHIST;var VM_ERROR=PYERR;
var TAP_SPEAK=PYTAP1;var TAP_STOP=PYTAP2;var SPEAKING=PYSPEAK;
var HAS_ANIM=PYHASANIM;var GOOD_PRONUNC=PYGOOD;var PHOTO=PYPHOTO;var PROF_NAME=PYPROF;
var F_NORMAL=PYFN;var F_MEIO=PYFM;var F_ABERTA=PYFA;var F_BEM_ABERTA=PYFBA;
var F_OUVINDO=PYFO;var F_PISCANDO=PYFP;var F_SURPRESA=PYFS;

var micBtn=document.getElementById('micBtn');
var micHint=document.getElementById('micHint');
var statusTxt=document.getElementById('statusTxt');
var errBox=document.getElementById('errBox');
var ring=document.getElementById('ring');
var avImg=document.getElementById('avImg');
var avEmoji=document.getElementById('avEmoji');
var histWrap=document.getElementById('historyWrap');
var profName=document.getElementById('profName');
profName.textContent=PROF_NAME;
micHint.textContent=TAP_SPEAK;

var _lastFrame='';
function setFrame(src){
  if(!src){
    if(PHOTO){avImg.src=PHOTO;avImg.style.display='block';avEmoji.style.display='none';}
    else{avImg.style.display='none';avEmoji.style.display='flex';}
    _lastFrame='';return;
  }
  if(src===_lastFrame)return;
  _lastFrame=src;
  avImg.src=src;avImg.style.display='block';avEmoji.style.display='none';
}
setFrame(HAS_ANIM?F_NORMAL:PHOTO);

var _state='idle',_blinkTimer=null,_mouthTimer=null,_analyser=null,_audioCtx=null,_mouthFallbackIdx=0;
function _stopAllTimers(){
  if(_blinkTimer){clearTimeout(_blinkTimer);clearInterval(_blinkTimer);_blinkTimer=null;}
  if(_mouthTimer){clearInterval(_mouthTimer);_mouthTimer=null;}
}
function enterIdle(){
  _stopAllTimers();_state='idle';
  setFrame(HAS_ANIM?F_NORMAL:PHOTO);
  ring.classList.remove('active');statusTxt.textContent='● Online';
  if(!HAS_ANIM)return;
  function scheduleBlink(){
    var delay=3210+Math.random()*2000;
    _blinkTimer=setTimeout(function(){
      if(_state!=='idle')return;
      setFrame(F_PISCANDO);
      setTimeout(function(){if(_state!=='idle')return;setFrame(F_NORMAL);scheduleBlink();},150);
    },delay);
  }
  scheduleBlink();
}
function enterListening(){
  _stopAllTimers();_state='listening';
  setFrame(HAS_ANIM?F_OUVINDO:PHOTO);
  ring.classList.remove('active');statusTxt.textContent='🎙 Ouvindo…';
}
function enterProcessing(){
  _stopAllTimers();_state='processing';
  setFrame(HAS_ANIM?F_NORMAL:PHOTO);
  ring.classList.remove('active');statusTxt.textContent='⏳ Processando…';
  if(!HAS_ANIM)return;
  _blinkTimer=setInterval(function(){
    if(_state!=='processing')return;
    setFrame(F_PISCANDO);
    setTimeout(function(){if(_state!=='processing')return;setFrame(F_NORMAL);},180);
  },2200);
}
function enterSpeaking(audioEl){
  _stopAllTimers();_state='speaking';
  ring.classList.add('active');statusTxt.textContent=SPEAKING;
  if(!HAS_ANIM)return;
  try{
    if(!_audioCtx)_audioCtx=new(window.AudioContext||window.webkitAudioContext)();
    if(!_analyser){
      _analyser=_audioCtx.createAnalyser();_analyser.fftSize=1024;_analyser.smoothingTimeConstant=0.1;
      var src=_audioCtx.createMediaElementSource(audioEl);
      src.connect(_analyser);_analyser.connect(_audioCtx.destination);
    }
    var buf=new Uint8Array(_analyser.frequencyBinCount);
    _mouthTimer=setInterval(function(){
      if(_state!=='speaking')return;
      _analyser.getByteFrequencyData(buf);
      var sum=0,n=Math.min(100,buf.length);
      for(var i=4;i<n;i++)sum+=buf[i];
      setFrame((sum/(n-4))<18?F_NORMAL:F_MEIO);
    },60);
  }catch(e){
    _mouthFallbackIdx=0;
    _mouthTimer=setInterval(function(){
      if(_state!=='speaking')return;
      setFrame(_mouthFallbackIdx%2===0?F_MEIO:F_NORMAL);_mouthFallbackIdx++;
    },250);
  }
}
function onSpeakingEnded(gp){
  _stopAllTimers();
  if(gp&&F_BEM_ABERTA){setFrame(F_BEM_ABERTA);setTimeout(function(){enterIdle();},1200);}
  else enterIdle();
}

var currentAudio=null,lastB64=null,_activeBubbleBtn=null;
function getVol(){return parseFloat(document.getElementById('vol-slider').value)||1;}
function getSpd(){return parseFloat(document.getElementById('spd-slider').value)||1;}

function playTTS(b64,onEnd,goodPronunc){
  if(currentAudio){currentAudio.pause();currentAudio=null;_stopAllTimers();}
  if(!b64)return;
  lastB64=b64;
  var audio=new Audio('data:audio/mp3;base64,'+b64);
  audio.volume=getVol();audio.playbackRate=getSpd();audio._srcB64=b64;currentAudio=audio;
  audio.onplay=function(){enterSpeaking(audio);updateGlobalBtn(true);};
  audio.onended=function(){
    _stopAllTimers();ring.classList.remove('active');currentAudio=null;updateGlobalBtn(false);
    if(_activeBubbleBtn){_activeBubbleBtn.textContent='▶ Ouvir';_activeBubbleBtn.classList.remove('playing');_activeBubbleBtn=null;}
    onSpeakingEnded(!!goodPronunc);if(onEnd)onEnd();
  };
  audio.onerror=function(){
    _stopAllTimers();ring.classList.remove('active');currentAudio=null;updateGlobalBtn(false);
    if(_activeBubbleBtn){_activeBubbleBtn.textContent='▶ Ouvir';_activeBubbleBtn.classList.remove('playing');_activeBubbleBtn=null;}
    enterIdle();
  };
  audio.play().catch(function(){_stopAllTimers();ring.classList.remove('active');currentAudio=null;updateGlobalBtn(false);enterIdle();});
}
function stopTTS(){
  if(currentAudio){
    currentAudio.pause();currentAudio=null;_stopAllTimers();
    ring.classList.remove('active');statusTxt.textContent='● Online';updateGlobalBtn(false);
    if(_activeBubbleBtn){_activeBubbleBtn.textContent='▶ Ouvir';_activeBubbleBtn.classList.remove('playing');_activeBubbleBtn=null;}
    enterIdle();
  }
}
function updateGlobalBtn(playing){
  var btn=document.getElementById('global-play-btn');if(!btn)return;
  btn.textContent=playing?'⏹ Parar':'▶ Ouvir';
  btn.style.background=playing?'#8b2a2a':'#1a2535';
}
document.getElementById('global-play-btn').addEventListener('click',function(){
  if(currentAudio&&!currentAudio.paused)stopTTS();
  else if(lastB64||TTS_B64)playTTS(lastB64||TTS_B64,null,GOOD_PRONUNC);
});
document.getElementById('vol-slider').addEventListener('input',function(){
  document.getElementById('vol-val').textContent=Math.round(this.value*100)+'%';
  if(currentAudio)currentAudio.volume=parseFloat(this.value);
});
document.getElementById('spd-slider').addEventListener('input',function(){
  document.getElementById('spd-val').textContent=parseFloat(this.value).toFixed(1)+'x';
  if(currentAudio)currentAudio.playbackRate=parseFloat(this.value);
});

function addBubble(role,text,b64){
  var label=document.createElement('div');
  label.className='bubble-label'+(role==='user'?' right':'');
  label.textContent=role==='user'?'Você':PROF_NAME;
  var bub=document.createElement('div');
  bub.className='bubble '+role;
  bub.innerHTML=text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/_(.+?)_/g,'<em>$1</em>').replace(/__(.+?)__/g,'<u>$1</u>').replace(/\n/g,'<br>');
  histWrap.appendChild(label);histWrap.appendChild(bub);
  if(role==='bot'&&b64){
    var pbtn=document.createElement('button');
    pbtn.className='bubble-play-btn';pbtn.textContent='▶ Ouvir';
    pbtn.addEventListener('click',function(){
      var isThisPlaying=currentAudio&&!currentAudio.paused&&currentAudio._srcB64===b64;
      if(isThisPlaying){stopTTS();return;}
      if(currentAudio)stopTTS();
      document.querySelectorAll('.bubble-play-btn').forEach(function(b){b.textContent='▶ Ouvir';b.classList.remove('playing');});
      pbtn.textContent='⏹ Parar';pbtn.classList.add('playing');_activeBubbleBtn=pbtn;
      playTTS(b64,function(){pbtn.textContent='▶ Ouvir';pbtn.classList.remove('playing');_activeBubbleBtn=null;},false);
    });
    histWrap.appendChild(pbtn);
  }
  histWrap.scrollTop=histWrap.scrollHeight;
}

if(VM_ERROR){errBox.textContent=VM_ERROR;errBox.style.display='block';enterIdle();}
else{
  errBox.style.display='none';
  if(HISTORY&&HISTORY.length>0){
    HISTORY.forEach(function(msg){addBubble(msg.role==='user'?'user':'bot',msg.content,msg.tts_b64||'');});
  }
  if(TTS_B64){setTimeout(function(){playTTS(TTS_B64,null,GOOD_PRONUNC);},300);}
  else enterIdle();
}

var recording=false;
function getRealMicBtn(){
  var doc=window.parent.document;
  var ai=doc.querySelector('[data-testid="stAudioInput"]');
  if(!ai)return null;
  return ai.querySelector('button')||ai.querySelector('[data-testid="stAudioInputRecordButton"]');
}
micBtn.addEventListener('click',function(){
  var realBtn=getRealMicBtn();if(!realBtn)return;
  if(recording){
    micBtn.classList.remove('recording');micBtn.innerHTML='<i class="fa-solid fa-microphone"></i>';
    micHint.textContent=TAP_SPEAK;micBtn.classList.add('processing');
    recording=false;enterProcessing();realBtn.click();
  }else{
    if(currentAudio){currentAudio.pause();currentAudio=null;}
    _stopAllTimers();
    if(window.parent.speechSynthesis)window.parent.speechSynthesis.cancel();
    micBtn.classList.add('recording');micBtn.innerHTML='<i class="fa-solid fa-stop"></i>';
    micHint.textContent=TAP_STOP;recording=true;enterListening();realBtn.click();
  }
});

function hideNativeAudio(){
  var doc=window.parent.document;
  var ai=doc.querySelector('[data-testid="stAudioInput"]');
  if(ai){
    ai.style.cssText='position:fixed;bottom:-999px;left:-9999px;opacity:0;pointer-events:none;width:1px;height:1px;';
    var btn=ai.querySelector('button');if(btn)btn.style.pointerEvents='auto';
  }
}
hideNativeAudio();
try{var obs=new MutationObserver(hideNativeAudio);obs.observe(window.parent.document.body,{childList:true,subtree:true});setTimeout(function(){obs.disconnect();},15000);}catch(e){}

(function resizeIframe(){
  try{
    var par=window.parent;var h=par.innerHeight;
    try{if(par.visualViewport)h=par.visualViewport.height;}catch(e){}
    var iframes=par.document.querySelectorAll('iframe');
    for(var i=0;i<iframes.length;i++){
      try{
        if(iframes[i].contentWindow===window){
          iframes[i].style.cssText='height:'+h+'px;max-height:'+h+'px;min-height:200px;display:block;border:none;width:100%;';
          var p=iframes[i].parentElement;
          for(var j=0;j<10&&p&&p!==par.document.body;j++){p.style.margin='0';p.style.padding='0';p.style.overflow='hidden';p.style.maxHeight=h+'px';p=p.parentElement;}
          break;
        }
      }catch(e){}
    }
  }catch(e){}
  try{
    par.removeEventListener('resize',resizeIframe);par.addEventListener('resize',resizeIframe);
    if(par.visualViewport){par.visualViewport.removeEventListener('resize',resizeIframe);par.visualViewport.addEventListener('resize',resizeIframe);}
  }catch(e){}
})();

enterIdle();
})();
</script>
</body></html>"""
        .replace("RINGC",  ring_color)
        .replace("RING3",  ring_rgba_3)
        .replace("RING5",  ring_rgba_5)
        .replace("RING0",  ring_rgba_0)
        .replace("RING25", ring_rgba_25)
        .replace("USERC",  user_bubble_color)
        .replace("BOTC",   bot_bubble_color)
        .replace("BOT8",   bot_rgba_8)
        .replace("PYTTS",     tts_js)
        .replace("PYREPLY",   reply_js)
        .replace("PYHIST",    history_js)
        .replace("PYERR",     err_js)
        .replace("PYTAP1",    tap_speak)
        .replace("PYTAP2",    tap_stop)
        .replace("PYSPEAK",   speaking_)
        .replace("PYHASANIM", has_anim_js)
        .replace("PYGOOD",    good_pronunc_js)
        .replace("PYPHOTO",   photo_js)
        .replace("PYPROF",    prof_name_js)
        .replace("PYFN",      av_normal_js)
        .replace("PYFM",      av_meio_js)
        .replace("PYFA",      av_aberta_js)
        .replace("PYFBA",     av_bem_aberta_js)
        .replace("PYFO",      av_ouvindo_js)
        .replace("PYFP",      av_piscando_js)
        .replace("PYFS",      av_surpresa_js)
    )

    components.html(HTML, height=920, scrolling=False)