/* ---------- Config ---------- */
const API_BASE = 'http://127.0.0.1:8000'; // your FastAPI server
const PAGE_OFFSET = 0; // set to 1 if your loader gives 0-based page numbers (PyPDFLoader does)
const STAGES = ['Searching documents', 'Grading sources', 'Writing the answer'];

/* Welcome text shown before the first question */
const INTRO = "Niyam AI answers your questions on RBI guidelines and FEMA regulations, drawing only from official documents on Compounding of Contraventions, Deposits and Accounts, External Commercial Borrowings, Foreign Investment, Insurance, the Money Transfer Service Scheme and Overseas Investment. Every answer cites the source document and page.";

/* ---------- Helpers ---------- */
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const uid = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2));
const ls = {
  get: k => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { } }
};
const pct = v => {
  v = Number(v);
  if (!isFinite(v)) return null;
  return Math.round(Math.max(0, Math.min(1, v > 1 ? v / 100 : v)) * 100);
};
const tone = p => (p >= 70 ? 'good' : p >= 40 ? 'mid' : 'low');
const LOGO = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 22h18M6 18v-7M10 18v-7M14 18v-7M18 18v-7M12 2l8 5H4z"/></svg>';

/* Minimal markdown: code blocks, headings, lists, bold, italic, inline code */
function md(src) {
  const blocks = [];
  const t = esc(src).replace(/```\w*\n?([\s\S]*?)```/g, (_, c) => { blocks.push(`<pre><code>${c}</code></pre>`); return `\u0000${blocks.length - 1}\u0000`; });
  const inl = s => s.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/(^|\W)\*([^*\n]+)\*/g, '$1<em>$2</em>');
  const out = []; let list = null;
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const line of t.split('\n')) {
    let m;
    if (/^\u0000\d+\u0000$/.test(line.trim())) { close(); out.push(line.trim()); }
    else if ((m = line.match(/^\s*[-*•]\s+(.*)/))) { if (list !== 'ul') { close(); out.push('<ul>'); list = 'ul'; } out.push(`<li>${inl(m[1])}</li>`); }
    else if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) { if (list !== 'ol') { close(); out.push('<ol>'); list = 'ol'; } out.push(`<li>${inl(m[1])}</li>`); }
    else if ((m = line.match(/^#{1,4}\s+(.*)/))) { close(); out.push(`<h4>${inl(m[1])}</h4>`); }
    else if (!line.trim()) close();
    else { close(); out.push(`<p>${inl(line)}</p>`); }
  }
  close();
  return out.join('').replace(/\u0000(\d+)\u0000/g, (_, i) => blocks[i]);
}

/* ---------- State (in memory only, a refresh clears the screen) ---------- */
let messages = [], busy = false, stageTimer = null;
const feed = $('feed');
const scrollDown = () => feed.scrollTo({ top: feed.scrollHeight });

/* ---------- Rendering ---------- */
function srcHTML(list = []) {
  const seen = new Set();
  const u = list.filter(x => { const k = x.pdf_name + '|' + x.page; return seen.has(k) ? false : seen.add(k); });
  if (!u.length) return '';
  const chips = u.map(x => {
    const p = isNaN(Number(x.page)) || x.page === null ? '?' : Number(x.page) + PAGE_OFFSET;
    return `<span class="src" title="${esc(x.pdf_name)}"><em>p.${esc(p)}</em><span>${esc(x.pdf_name)}</span></span>`;
  }).join('');
  return `<div class="srcs"><span class="lbl">Source documents</span>${chips}</div>`;
}

function gradeLabel(g) {
  if (g === null || g === undefined) return '';
  if (typeof g === 'number') return g.toFixed(3);
  if (typeof g !== 'object') return String(g);
  return Object.entries(g).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(', ');
}

function gradeChip(g, i) {
  const label = gradeLabel(g), s = label.toLowerCase();
  const cls = /\b(irrelevant|no|false|fail|bad)\b/.test(s) ? 'low' : /\b(relevant|yes|true|pass|good)\b/.test(s) ? 'good' : '';
  return `<span class="chip ${cls}" title="${esc(label)}"><b>${i + 1}</b><span>${esc(label)}</span></span>`;
}

function qualityHTML(m) {
  const rel = pct(m.rel), ov = pct(m.overall), g = Array.isArray(m.grades) ? m.grades : [];
  if (rel === null && ov === null && !g.length) return '';
  const bar = (n, p) => p === null ? '' : `<div class="bar"><span>${n}</span><div class="track"><i class="${tone(p)}" style="width:${p}%"></i></div><b>${p}%</b></div>`;
  return `<details class="quality"><summary>Answer quality${ov !== null ? `<span class="pill ${tone(ov)}">${ov}%</span>` : ''}</summary>
    ${bar('Relevance', rel)}${bar('Overall', ov)}
    ${g.length ? `<div class="grades">${g.map(gradeChip).join('')}</div>` : '<div style="height:10px"></div>'}</details>`;
}

function msgHTML(m, i) {
  if (m.role === 'user') return `<div class="msg user" data-i="${i}"><div class="body">${esc(m.text)}</div></div>`;
  const body = m.error ? `<p>${esc(m.text)}</p>` : md(m.text);
  const tools = m.error ? '<button data-retry>Try again</button>' : '<button data-copy>Copy answer</button>';
  return `<div class="msg bot${m.error ? ' err' : ''}" data-i="${i}"><div class="av">${LOGO}</div><div class="body">
    <div class="who">Niyam AI<span>Based on RBI guidelines</span></div>
    <div class="prose">${body}</div>${m.error ? '' : srcHTML(m.sources) + qualityHTML(m)}
    <div class="tools">${tools}</div></div></div>`;
}

function renderFeed() {
  if (!messages.length) {
    feed.innerHTML = `<div class="empty"><div class="eyebrow">RBI Guidelines Assistant</div><h2>Ask Niyam</h2><div class="rule"></div><p class="lead">${esc(INTRO)}</p></div>`;
    return;
  }
  feed.innerHTML = messages.map(msgHTML).join('');
  scrollDown();
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'msg bot'; el.id = 'typing';
  el.innerHTML = `<div class="av">${LOGO}</div><div class="typing"><span class="dots"><i></i><i></i><i></i></span><span id="stage">${STAGES[0]}</span></div>`;
  feed.appendChild(el); scrollDown();
  let n = 0;
  stageTimer = setInterval(() => { n = Math.min(n + 1, STAGES.length - 1); const s = $('stage'); if (s) s.textContent = STAGES[n]; }, 2200);
}
function hideTyping() { clearInterval(stageTimer); $('typing')?.remove(); }

/* ---------- Send: a brand-new thread_id for EVERY question ---------- */
async function send(q, retry = false) {
  q = q.trim();
  if (!q || busy) return;
  if (!retry) messages.push({ role: 'user', text: q });
  busy = true; $('send').disabled = true;
  renderFeed(); showTyping();
  try {
    const r = await fetch(API_BASE + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, thread_id: uid() })
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || `Server returned ${r.status}`);
    messages.push({
      role: 'bot', text: d.answer || 'The server responded, but the answer field was empty. Check the graph output on the backend.',
      sources: d.sources || [], grades: d.grades || [],
      rel: d.relavance_score, overall: d.overall_score // key spelled as in main.py
    });
  } catch (e) {
    const offline = e instanceof TypeError;
    messages.push({ role: 'bot', error: true, text: offline ? `Can't reach ${API_BASE}. Start the FastAPI server and check API_BASE in script.js.` : `Request failed: ${e.message}` });
  }
  busy = false; $('send').disabled = false;
  hideTyping(); renderFeed();
}

/* ---------- Events ---------- */
feed.addEventListener('click', e => {
  const msg = e.target.closest('.msg'); if (!msg) return;
  const i = +msg.dataset.i;
  const copy = e.target.closest('[data-copy]');
  if (copy) {
    navigator.clipboard?.writeText(messages[i].text);
    copy.textContent = 'Copied';
    setTimeout(() => (copy.textContent = 'Copy answer'), 1500);
  }
  if (e.target.closest('[data-retry]')) {
    const last = messages[i - 1];
    messages.splice(i, 1);
    if (last && last.role === 'user') send(last.text, true);
  }
});

$('form').addEventListener('submit', e => {
  e.preventDefault();
  const v = $('input').value;
  if (v.trim() && !busy) { $('input').value = ''; $('input').style.height = 'auto'; send(v); }
});
$('input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); $('form').requestSubmit(); }
});
$('input').addEventListener('input', e => {
  e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px';
});

/* Theme */
const root = document.documentElement;
root.dataset.theme = ls.get('niyam.theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
$('theme').onclick = () => { const t = root.dataset.theme === 'dark' ? 'light' : 'dark'; root.dataset.theme = t; ls.set('niyam.theme', t); };

/* Server status (GET /) */
async function ping() {
  try { const r = await fetch(API_BASE + '/', { cache: 'no-store' }); setStatus(r.ok); }
  catch { setStatus(false); }
}
function setStatus(ok) { $('dot').className = ok ? 'ok' : 'bad'; $('statusTxt').textContent = ok ? 'Server online' : 'Server offline'; }

/* Init */
renderFeed(); ping(); setInterval(ping, 30000);
