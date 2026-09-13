const API_URL = "https://loan-approval-ai-agent-1.onrender.com/chat";
const HEALTH_URL = "https://loan-approval-ai-agent-1.onrender.com/health";

const thread = document.getElementById('thread');
const form = document.getElementById('composerForm');
const input = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

const BOT_ICON = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="12" rx="2"/><path d="M12 8V4"/><circle cx="12" cy="3" r="1"/><path d="M8 13v2"/><path d="M16 13v2"/></svg>`;
const USER_ICON = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

// --- backend health check ---
fetch(HEALTH_URL).then(r=>{
  if(r.ok){ statusDot.classList.remove('off'); statusText.textContent = "Backend online"; }
  else throw new Error();
}).catch(()=>{
  statusDot.classList.add('off'); statusText.textContent = "Backend unreachable";
});

function timeNow(){
  return new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
}

// Escapes HTML first (so nothing from the model can inject markup/scripts),
// then converts a small, safe subset of markdown to tags for display only.
// This only changes how a reply is rendered — never what is sent or parsed.
function renderMarkdownLite(text){
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Horizontal rules on their own line ("---", "***", "___") -> a subtle divider.
  // Must run before the header/bold rules and before newlines become <br>.
  safe = safe.replace(/^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$/gm, '<hr class="msg-hr">');

  // Headers ("# ", "## ", "### ", up to 6 #'s) -> a bold heading line,
  // the leading hashes themselves are stripped rather than shown raw.
  safe = safe.replace(/^#{1,6}[ \t]+(.*)$/gm, '<strong class="msg-heading">$1</strong>');

  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/__(.+?)__/g, '<strong>$1</strong>');
  safe = safe.replace(/(^|[^*])\*(?!\*)([^*\n]+?)\*(?!\*)/g, '$1<em>$2</em>');
  safe = safe.replace(/(^|[^_])_(?!_)([^_\n]+?)_(?!_)/g, '$1<em>$2</em>');
  safe = safe.replace(/`([^`]+?)`/g, '<code>$1</code>');
  safe = safe.replace(/\n/g, '<br>');
  return safe;
}

function addBubble(role, text){
  const entry = document.createElement('div');
  entry.className = `entry ${role}`;
  entry.innerHTML = `
    <div class="avatar ${role}">${role === 'bot' ? BOT_ICON : USER_ICON}</div>
    <div class="bubble-col">
      <div class="bubble"></div>
      <div class="meta">${role === 'bot' ? 'Ledger' : 'You'} · ${timeNow()}</div>
    </div>`;
  const bubbleEl = entry.querySelector('.bubble');
  if(role === 'bot'){
    bubbleEl.innerHTML = renderMarkdownLite(text);
  } else {
    bubbleEl.textContent = text;
  }
  thread.appendChild(entry);
  thread.scrollTop = thread.scrollHeight;
  return entry;
}

function addTypingIndicator(){
  const entry = document.createElement('div');
  entry.className = 'entry bot';
  entry.id = 'typingEntry';
  entry.innerHTML = `
    <div class="avatar bot">${BOT_ICON}</div>
    <div class="bubble-col">
      <div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>
    </div>`;
  thread.appendChild(entry);
  thread.scrollTop = thread.scrollHeight;
}

function removeTypingIndicator(){
  const el = document.getElementById('typingEntry');
  if(el) el.remove();
}

async function sendToBackend(message){
  addTypingIndicator();
  sendBtn.disabled = true;
  try{
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    removeTypingIndicator();
    if(!res.ok){
      const err = await res.json().catch(()=>({detail:"Unknown error"}));
      addBubble('bot', `Something went wrong (${res.status}): ${err.detail || "no details returned"}.`);
      return;
    }
    const data = await res.json();
    addBubble('bot', data.response);
  }catch(e){
    removeTypingIndicator();
    addBubble('bot', "I can't reach the backend right now. Check that it's running at http://127.0.0.1:8000 and that CORS is enabled.");
  }finally{
    sendBtn.disabled = false;
  }
}

form.addEventListener('submit', (e)=>{
  e.preventDefault();
  const text = input.value.trim();
  if(!text) return;
  addBubble('user', text);
  input.value = '';

  sendToBackend(text);
});

// Greeting
addBubble('bot', "Hello — I'm your loan assistant. Ask me anything, or tell me you'd like to check loan eligibility and I'll ask you for the details right here in chat.");
