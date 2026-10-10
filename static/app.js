const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
let current = null, file = null;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const col = v => v >= 80 ? "#16a34a" : v >= 60 ? "#d97706" : "#dc2626";

async function api(url, opt) { const r = await fetch(url, opt); const d = await r.json(); if (!r.ok) throw new Error(d.error || "Request failed"); return d; }

async function init() {
  const roles = await api("/api/roles");
  $("#role").innerHTML = `<option value="">General check (no role)</option>` + roles.map(r => `<option value="${r.id}">${esc(r.name)}</option>`).join("");
  loadStats(); loadHistory();
}
async function loadStats() {
  const s = await api("/api/stats");
  $("#s-total").textContent = s.total; $("#s-avg").textContent = s.average; $("#s-best").textContent = s.best; $("#s-top").textContent = s.top_category;
}
async function loadHistory() {
  const h = await api("/api/history");
  $("#hist").innerHTML = h.length ? h.map(r => `<tr><td>${r.id}</td><td>${esc(r.filename)}</td><td>${esc(r.role)}</td>
    <td><span class="sc" style="background:${col(r.score)}1a;color:${col(r.score)}">${r.score}</span></td><td>${r.issue_count}</td><td>${esc(r.created_at)}</td>
    <td><button class="link" onclick="openAnalysis(${r.id})">View</button><button class="link d" onclick="del(${r.id})">Delete</button></td></tr>`).join("")
    : `<tr><td colspan="7" class="muted">No analyses yet - analyze your first resume above.</td></tr>`;
}
async function openAnalysis(id) { render(await api("/api/analysis/" + id)); }
async function del(id) { if (confirm("Delete this analysis?")) { await api("/api/analysis/" + id, { method: "DELETE" }); loadHistory(); loadStats(); } }

// tabs + file handling
$$(".tab").forEach(t => t.onclick = () => {
  $$(".tab").forEach(x => x.classList.toggle("active", x === t));
  $("#tab-upload").hidden = t.dataset.tab !== "upload"; $("#tab-paste").hidden = t.dataset.tab !== "paste";
});
const drop = $("#drop");
$("#file").onchange = e => setFile(e.target.files[0]);
["dragover", "dragenter"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", e => setFile(e.dataTransfer.files[0]));
function setFile(f) { if (!f) return; file = f; $("#drop-t").textContent = "\u2713 " + f.name; }

$("#demo").onclick = async () => {
  const t = await (await fetch("/static/sample_resume.txt")).text();
  $$(".tab")[1].click(); $("#text").value = t; file = null;
};
$("#go").onclick = async () => {
  const err = $("#err"); err.hidden = true;
  const fd = new FormData();
  const pasteMode = !$("#tab-paste").hidden;
  if (!pasteMode && file) fd.append("file", file); else fd.append("text", $("#text").value);
  if ($("#role").value) fd.append("role_id", $("#role").value);
  const b = $("#go"); b.disabled = true; b.textContent = "Analyzing...";
  try { const d = await api("/api/analyze", { method: "POST", body: fd }); render(d); loadHistory(); loadStats(); }
  catch (e) { err.textContent = e.message; err.hidden = false; }
  b.disabled = false; b.textContent = "Analyze resume";
};

function render(d) {
  current = d; $("#results").hidden = false;
  $("#score").textContent = d.score; $("#fname").textContent = d.filename + " \u2022 " + d.stats.word_count + " words";
  const arc = $("#arc"); arc.style.stroke = col(d.score); setTimeout(() => arc.style.strokeDashoffset = 326.7 * (1 - d.score / 100), 50);
  $("#verdict").textContent = d.score >= 85 ? "Excellent - nearly job-ready" : d.score >= 70 ? "Good - a few improvements needed" : d.score >= 50 ? "Fair - needs attention" : "Needs major improvement";
  const sv = d.stats.severity;
  $("#chips").innerHTML = `<span class="chip high">${sv.high} high</span><span class="chip medium">${sv.medium} medium</span><span class="chip low">${sv.low} low</span><span class="chip n">${d.issues.length} total</span>`;
  $("#cats").innerHTML = Object.entries(d.category_scores).map(([k, v]) => v === null ? "" :
    `<div class="bar"><p><span>${k}</span><b style="color:${col(v)}">${v}</b></p><i><em style="width:${v}%;background:${col(v)}"></em></i></div>`).join("");
  const all = ["education", "skills", "experience", "projects", "summary"];
  const st = d.stats;
  $("#secs").innerHTML = `<div class="sub">Sections</div><div class="chips">${all.map(s => `<span class="chip ${st.sections_found.includes(s) ? "ok" : "high"}">${st.sections_found.includes(s) ? "\u2713" : "\u2717"} ${s}</span>`).join("")}</div>` +
    (st.keywords_matched.length + st.keywords_missing.length ? `<div class="sub">Keywords matched</div><div class="chips">${st.keywords_matched.map(k => `<span class="chip ok">${esc(k)}</span>`).join("") || '<span class="muted">none</span>'}</div>
     <div class="sub">Keywords missing</div><div class="chips">${st.keywords_missing.map(k => `<span class="chip n">${esc(k)}</span>`).join("") || '<span class="muted">none \uD83C\uDF89</span>'}</div>` : `<p class="muted" style="margin-top:14px">Select a target role to see keyword matching.</p>`);
  // resume text with highlights
  const worst = {}; d.issues.forEach(i => { if (i.line_no && !(worst[i.line_no] && worst[i.line_no] !== "low" && i.severity === "low")) { const o = { high: 0, medium: 1, low: 2 }; if (!worst[i.line_no] || o[i.severity] < o[worst[i.line_no]]) worst[i.line_no] = i.severity; } });
  $("#doc").innerHTML = d.lines.map((l, i) => `<div class="ln ${worst[i + 1] || ""}" id="ln${i + 1}"><span>${i + 1}</span><span>${esc(l) || " "}</span></div>`).join("");
  $$(".f").forEach(x => x.classList.toggle("active", x.dataset.f === "all")); drawIssues("all");
  $("#results").scrollIntoView({ behavior: "smooth" });
}
function drawIssues(f) {
  const list = current.issues.filter(i => f === "all" || i.severity === f);
  $("#icount").textContent = list.length;
  $("#issues").innerHTML = list.length ? list.map(i => `<div class="issue ${i.severity}" ${i.line_no ? `onclick="jump(${i.line_no})"` : ""}>
    <div class="t"><span class="badge ${i.severity}">${i.severity}</span>${esc(i.message)}</div>
    <div class="m">${esc(i.category)}${i.line_no ? " \u2022 line " + i.line_no : " \u2022 whole document"}</div>
    ${i.suggestion ? `<div class="s">${esc(i.suggestion)}</div>` : ""}</div>`).join("") : `<p class="muted">Nothing to show here \uD83C\uDF89</p>`;
}
$$(".f").forEach(b => b.onclick = () => { $$(".f").forEach(x => x.classList.toggle("active", x === b)); drawIssues(b.dataset.f); });
function jump(n) { const el = $("#ln" + n); el.scrollIntoView({ behavior: "smooth", block: "center" }); el.classList.add("flash"); setTimeout(() => el.classList.remove("flash"), 1500); }
init();
