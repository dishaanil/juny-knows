// ── Constants ─────────────────────────────────────────────────────────────────
const GOODBYE_PHRASES = ["bye", "goodbye", "talk to you later", "gotta go", "see you later",
  "that's all", "i'm done", "thanks juny", "talk later", "catch you later"];

const PROFILE_LABELS = {
  college_student: "🎓 Just Vibing",
  family_kids:     "👨‍👩‍👧 Travelling with Kids",
  adult_explorer:  "🗽 Culture First",
};

// ── State ─────────────────────────────────────────────────────────────────────
let selectedProfile   = null;
let callActive        = false;
let isSpeaking        = false;
let detectedLocation  = null;   // { key, name } once GPS resolves

let audioContext = null;
let mediaStream  = null;
let workletNode  = null;
let ws           = null;

let conversationHistory = [];

// ── DOM ───────────────────────────────────────────────────────────────────────
const profileScreen  = document.getElementById("profile-screen");
const callScreen     = document.getElementById("call-screen");
const profilePill    = document.getElementById("profile-pill");
const backBtn        = document.getElementById("back-btn");

const avatarRings    = document.getElementById("avatar-rings");
const avatarCore     = document.getElementById("avatar-core");
const callStatusLbl  = document.getElementById("call-status-label");

const feed           = document.getElementById("conversation-feed");
const liveBar        = document.getElementById("live-bar");
const liveText       = document.getElementById("live-text");

const statusBar      = document.getElementById("status-bar");
const callBtn        = document.getElementById("call-btn");
const callBtnIcon    = document.getElementById("call-btn-icon");
const callBtnLabel   = document.getElementById("call-btn-label");

// ── Screen transitions ────────────────────────────────────────────────────────
function showScreen(next) {
  const current = document.querySelector(".screen.active");
  if (current === next) return;
  if (current) {
    current.classList.add("exit");
    setTimeout(() => current.classList.remove("active", "exit"), 350);
  }
  setTimeout(() => next.classList.add("active"), current ? 80 : 0);
}

// ── Profile selection ─────────────────────────────────────────────────────────
document.querySelectorAll(".profile-card").forEach((card) => {
  card.addEventListener("click", () => {
    selectedProfile = card.dataset.profile;
    profilePill.textContent = PROFILE_LABELS[selectedProfile];
    conversationHistory = [];
    feed.innerHTML = "";
    showScreen(callScreen);
  });
});

backBtn.addEventListener("click", () => {
  if (callActive) endCall();
  showScreen(profileScreen);
  selectedProfile = null;
});

// ── Call button ───────────────────────────────────────────────────────────────
callBtn.addEventListener("click", () => {
  if (callActive) endCall();
  else startCall();
});

// ── Location detection ────────────────────────────────────────────────────────
function getGPS() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Geolocation not supported"));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => reject(err),
      { timeout: 8000, maximumAge: 60000 }
    );
  });
}

async function detectLocation() {
  try {
    const { lat, lng } = await getGPS();
    const res = await fetch(`/locate?lat=${lat}&lng=${lng}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.found ? { key: data.location_key, name: data.location_name } : null;
  } catch {
    return null;
  }
}

// ── Start call ────────────────────────────────────────────────────────────────
async function startCall() {
  callActive = true;
  setCallBtnActive();
  setAvatarState("idle");
  setStatus("Finding your location…");

  try {
    // Run GPS detection + mic permission in parallel
    const [locResult, stream] = await Promise.all([
      detectLocation(),
      navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      }),
    ]);

    detectedLocation = locResult;
    mediaStream = stream;

    // Mint AssemblyAI token
    const tokenRes = await fetch("/token");
    if (!tokenRes.ok) throw new Error("Could not get streaming token");
    const { token } = await tokenRes.json();

    // Set up AudioWorklet
    audioContext = new AudioContext({ sampleRate: 16000 });
    await audioContext.audioWorklet.addModule(audioPCMWorkletURL());
    const source = audioContext.createMediaStreamSource(mediaStream);
    workletNode  = new AudioWorkletNode(audioContext, "pcm-processor");

    // Open AssemblyAI WebSocket
    ws = new WebSocket(
      `wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&speech_model=u3-rt-pro&token=${token}`
    );
    ws.binaryType = "arraybuffer";

    ws.onopen = async () => {
      workletNode.port.onmessage = (e) => {
        if (ws?.readyState === WebSocket.OPEN) ws.send(e.data);
      };
      source.connect(workletNode);
      workletNode.connect(audioContext.destination);

      // Fire opening greeting if location was detected
      if (detectedLocation) {
        setAvatarState("thinking");
        setStatus("Juny is preparing…");
        try {
          const greetRes = await fetch("/greet", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              profile:       selectedProfile,
              location_key:  detectedLocation.key,
              location_name: detectedLocation.name,
            }),
          });
          const { greeting } = await greetRes.json();
          appendBubble("juny", greeting);
          conversationHistory.push({ role: "assistant", content: greeting });
          speak(greeting);
        } catch {
          // Greeting failed — just start listening silently
          setAvatarState("listening");
          setStatus("");
        }
      } else {
        setAvatarState("listening");
        setStatus("Location not detected — just tell me where you are");
      }
    };

    ws.onmessage = handleWSMessage;
    ws.onerror   = () => setStatus("Connection error — try again", "error");
    ws.onclose   = () => { if (callActive) setStatus("Reconnecting…"); };

  } catch (err) {
    setStatus(err.message || "Could not start call", "error");
    endCall();
  }
}

// ── End call ──────────────────────────────────────────────────────────────────
function endCall() {
  callActive = false;
  stopSpeaking();

  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "Terminate" }));
    ws.close();
  }
  ws = null;

  workletNode?.disconnect(); workletNode = null;
  audioContext?.close();     audioContext = null;
  mediaStream?.getTracks().forEach((t) => t.stop()); mediaStream = null;

  liveBar.classList.add("hidden");
  liveText.textContent = "";
  setAvatarState("idle");
  setCallBtnIdle();
  setStatus("Call ended");
}

// ── AssemblyAI messages ───────────────────────────────────────────────────────
function handleWSMessage(event) {
  const msg = JSON.parse(event.data);

  if (msg.type === "SpeechStarted") {
    if (isSpeaking) {
      stopSpeaking();
      setAvatarState("listening");
    }
    liveBar.classList.remove("hidden");
  }

  if (msg.type === "Turn") {
    const text = msg.transcript || "";
    if (!text) return;

    liveText.textContent = text;

    if (msg.end_of_turn) {
      liveBar.classList.add("hidden");
      liveText.textContent = "";

      const lower = text.toLowerCase();
      if (GOODBYE_PHRASES.some((p) => lower.includes(p))) {
        appendBubble("user", text);
        conversationHistory.push({ role: "user", content: text });
        speak("Talk soon! Enjoy the rest of your time in NYC.", true);
        setTimeout(endCall, 3500);
        return;
      }

      appendBubble("user", text);
      conversationHistory.push({ role: "user", content: text });
      sendChat(text);
    }
  }
}

// ── Send to Claude ────────────────────────────────────────────────────────────
async function sendChat(transcript) {
  setAvatarState("thinking");
  setStatus("Thinking…");

  const historyToSend = conversationHistory.slice(0, -1);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile:   selectedProfile,
        location:  detectedLocation?.key || transcript,
        transcript,
        history:   historyToSend,
      }),
    });

    if (!res.ok) throw new Error("Chat failed");
    const { response } = await res.json();

    appendBubble("juny", response);
    conversationHistory.push({ role: "assistant", content: response });
    speak(response);

  } catch {
    setStatus("Something went wrong", "error");
    setAvatarState("listening");
  }
}

// ── TTS ───────────────────────────────────────────────────────────────────────
function speak(text, isGoodbye = false) {
  stopSpeaking();
  setAvatarState("speaking");
  setStatus("");
  markLastJunyBubbleSpeaking(true);

  const utt = new SpeechSynthesisUtterance(text);
  utt.rate  = 1.05;
  utt.pitch = 1.0;

  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find((v) => v.lang.startsWith("en") && v.localService);
  if (preferred) utt.voice = preferred;

  utt.onend = () => {
    isSpeaking = false;
    markLastJunyBubbleSpeaking(false);
    if (callActive && !isGoodbye) setAvatarState("listening");
  };
  utt.onerror = () => {
    isSpeaking = false;
    markLastJunyBubbleSpeaking(false);
    if (callActive) setAvatarState("listening");
  };

  isSpeaking = true;
  window.speechSynthesis.speak(utt);
}

function stopSpeaking() {
  if (window.speechSynthesis.speaking) window.speechSynthesis.cancel();
  isSpeaking = false;
  markLastJunyBubbleSpeaking(false);
}

window.speechSynthesis?.addEventListener?.("voiceschanged", () => {});

// ── Avatar states ─────────────────────────────────────────────────────────────
function setAvatarState(state) {
  avatarRings.className  = "";
  avatarCore.className   = "";
  callStatusLbl.className = "";

  if (state === "speaking") {
    avatarRings.classList.add("speaking");
    avatarCore.classList.add("speaking");
    callStatusLbl.classList.add("speaking");
    callStatusLbl.textContent = "Juny is talking…";
  } else if (state === "listening") {
    avatarRings.classList.add("listening");
    avatarCore.classList.add("listening");
    callStatusLbl.classList.add("listening");
    callStatusLbl.textContent = "Listening…";
  } else if (state === "thinking") {
    callStatusLbl.textContent = "Thinking…";
  } else {
    callStatusLbl.textContent = callActive ? "Ready" : "Ready to talk";
  }
}

// ── Conversation feed ─────────────────────────────────────────────────────────
function appendBubble(role, text) {
  const wrap   = document.createElement("div");
  wrap.className = `bubble ${role}`;

  const sender = document.createElement("div");
  sender.className = "bubble-sender";
  sender.textContent = role === "juny" ? "Juny" : "You";

  const body = document.createElement("div");
  body.textContent = text;

  wrap.appendChild(sender);
  wrap.appendChild(body);
  feed.appendChild(wrap);
  feed.scrollTop = feed.scrollHeight;
}

function markLastJunyBubbleSpeaking(on) {
  const all  = feed.querySelectorAll(".bubble.juny");
  const last = all[all.length - 1];
  if (last) last.classList.toggle("speaking", on);
}

// ── Button states ─────────────────────────────────────────────────────────────
const START_ICON = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none">
  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor" fill-opacity="0.15"/>
</svg>`;

const END_ICON = `<span style="font-size:1.2rem">👋</span>`;

function setCallBtnActive() {
  callBtn.className = "call-btn-active";
  callBtnIcon.innerHTML = END_ICON;
  callBtnLabel.textContent = "Bye Juny!";
}

function setCallBtnIdle() {
  callBtn.className = "call-btn-idle";
  callBtnIcon.innerHTML = START_ICON;
  callBtnLabel.textContent = "Start talking to Juny!";
}

function setStatus(msg, type = "") {
  statusBar.textContent = msg;
  statusBar.className   = type;
}

// ── AudioWorklet ──────────────────────────────────────────────────────────────
function audioPCMWorkletURL() {
  const code = `
class PCMProcessor extends AudioWorkletProcessor {
  constructor() { super(); this._buf = []; this._chunk = 800; }
  process(inputs) {
    const ch = inputs[0]?.[0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) this._buf.push(ch[i]);
    while (this._buf.length >= this._chunk) {
      const slice = this._buf.splice(0, this._chunk);
      const pcm = new Int16Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        const s = Math.max(-1, Math.min(1, slice[i]));
        pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      this.port.postMessage(pcm.buffer, [pcm.buffer]);
    }
    return true;
  }
}
registerProcessor("pcm-processor", PCMProcessor);
`;
  return URL.createObjectURL(new Blob([code], { type: "application/javascript" }));
}
