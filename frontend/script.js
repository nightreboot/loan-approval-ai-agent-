const API_URL = "http://127.0.0.1:8000/chat";
const HEALTH_URL = "http://127.0.0.1:8000/health";

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

const LOAN_KEYWORDS = [
  "loan","eligib","approv","reject","cibil","emi","borrow",
  "mortgage","credit score","apply","interest rate","repay"
];

function looksLikeLoanRequest(text){
  const t = text.toLowerCase();
  return LOAN_KEYWORDS.some(k => t.includes(k));
}

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
  if(looksLikeLoanRequest(text)){
    openLoanSlip();
  }
});

// ---------- Loan slip (the form) ----------
let slipCounter = 1;

const FIELDS = [
  { key:"no_of_dependents", label:"Dependents", min:0, step:1, placeholder:"0" },
  { key:"education", label:"Education", type:"select", options:["Graduate","Not Graduate"] },
  { key:"self_employed", label:"Self Employed", type:"select", options:["Yes","No"] },
  { key:"annual_income", label:"Annual Income", min:0, step:1000, placeholder:"800000" },
  { key:"loan_amount", label:"Loan Amount", min:0, step:1000, placeholder:"1200000" },
  { key:"loan_term", label:"Loan Term (yrs)", min:1, step:1, placeholder:"10" },
  { key:"residential_assets_value", label:"Residential Assets", min:0, step:1000, placeholder:"0" },
  { key:"commercial_assets_value", label:"Commercial Assets", min:0, step:1000, placeholder:"0" },
  { key:"luxury_assets_value", label:"Luxury Assets", min:0, step:1000, placeholder:"0" },
  { key:"bank_asset_value", label:"Bank Assets", min:0, step:1000, placeholder:"0" },
];

function openLoanSlip(){
  const wrap = document.createElement('div');
  wrap.className = 'entry bot slip-wrap';
  const id = String(slipCounter++).padStart(4,'0');

  const fieldsHtml = FIELDS.map((f,i)=>{
    const idx = String(i+1).padStart(2,'0');
    if(f.type === "select"){
      return `
        <div class="field">
          <label><span class="n">${idx}</span>${f.label}</label>
          <select name="${f.key}" required>
            <option value="" disabled selected>Choose…</option>
            ${f.options.map(o=>`<option value="${o}">${o}</option>`).join('')}
          </select>
        </div>`;
    }
    return `
      <div class="field">
        <label><span class="n">${idx}</span>${f.label}</label>
        <input type="number" name="${f.key}" min="${f.min}" step="${f.step}" placeholder="${f.placeholder}" required />
      </div>`;
  }).join('');

  wrap.innerHTML = `
    <div class="avatar bot">${BOT_ICON}</div>
    <div class="slip">
      <div class="slip-head">
        <h3>Loan Application Slip</h3>
        <span class="slip-id">NO. LA-${id}</span>
      </div>
      <form class="slip-form">
        <div class="slip-grid">
          ${fieldsHtml}
          <div class="cibil-row">
            <div class="field">
              <label><span class="n">11</span>CIBIL Score (300–900)</label>
              <input type="number" name="cibil_score" min="300" max="900" step="1" placeholder="720" required />
            </div>
            <div class="cibil-meter"><div class="ptr" id="ptr-${id}"></div></div>
          </div>
        </div>
        <div class="slip-foot">
          <div class="note">Stamping submits these details for an ML-based prediction. This does not guarantee a bank's final decision.</div>
          <button type="submit" class="stamp-btn">STAMP<br>&amp; SUBMIT</button>
        </div>
      </form>
    </div>
  `;

  thread.appendChild(wrap);
  thread.scrollTop = thread.scrollHeight;

  const slipForm = wrap.querySelector('.slip-form');
  const cibilInput = slipForm.querySelector('[name="cibil_score"]');
  const ptr = wrap.querySelector(`#ptr-${id}`);
  cibilInput.addEventListener('input', ()=>{
    const v = Math.min(900, Math.max(300, Number(cibilInput.value) || 300));
    const pct = ((v - 300) / (900 - 300)) * 100;
    ptr.style.left = pct + "%";
  });

  slipForm.addEventListener('submit', (e)=>{
    e.preventDefault();
    const stampBtn = slipForm.querySelector('.stamp-btn');
    stampBtn.disabled = true;

    const data = new FormData(slipForm);
    const values = {};
    for(const [k,v] of data.entries()) values[k] = v;

    const summary = FIELDS.concat([{key:"cibil_score", label:"CIBIL Score"}])
      .map(f => `${f.label}: ${values[f.key]}`)
      .join("\n");

    const message =
`Here is my loan application:
${summary}

Please predict my loan approval.`;

    addBubble('user', "Submitted loan application slip");
    sendToBackend(message).finally(()=>{ stampBtn.disabled = false; });
    wrap.remove();
  });
}

// Greeting
addBubble('bot', "Hello — I'm your loan assistant. Ask me anything, or tell me you'd like to check loan eligibility and I'll bring out an application slip.");