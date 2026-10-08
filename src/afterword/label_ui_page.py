"""The single page served by ``afterword label-ui``: inline CSS and JS, no external assets.

Comment text and every other server value are inserted with ``textContent``,
never as HTML. ``__TOKEN__`` is replaced with the session token when served.

The favicon is the "Aw" mark (``docs/BRAND.md``), inlined as data URIs from
``img/favicon-16x16.png`` and ``img/favicon-32x32.png`` so the page still loads
nothing; ``tests/test_label_ui.py`` checks the inlined bytes match the files.
"""

from __future__ import annotations

# The "Aw" mark, base64 PNG, from img/favicon-16x16.png and img/favicon-32x32.png.
FAVICON_16_PNG_B64: str = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABfUlEQVR4AdxPPUhCURQ+54ZkDSJqSzUUBS21BiZB"
    "VPQcC0IKlKaGxpZCXaRIaLGCFpd+HkEN0RJRlo7REDS2BBZCg4uiSKDWvX3vDY9sKWqJLue75/d+536Cfnn+IIHL"
    "5ToBbgDvd9Q1SHA6nV1ENKWU6gUmEX9pDQTMrOFFDthB7IcnLawfGd6AFtVPJyJ6vxmH9SUtuj/YQICG8SgthLhC"
    "POB2uzuIuJ1w/JGDMZLUzZI7vYuJFibWUmtztx8JbNg6ilmWUvbAE2RoxFQZie3aFakFwSJBrNocdk+QSOqYURYB"
    "9A+h4AD6AAxQEd4PlrKtZvOxUg9K1rPM5MH26VxzyyH6ZBEwsx8bs4VCwVcsFocRJ4FxkvJFKLVc5+rmq2zKE4kA"
    "fpO5jwVqnwmqKGwApkHGMYLLSj77CBlnmfh83tYqnonU05u0J9EzzfoBNsewedus4iqVSnfIZ673VlZT8dAWSnQe"
    "C5Yv4qHZ9HqgZOQGLAIj+Qn+AcE7AAAA//8WhQGmAAAABklEQVQDAAGdiyFvC3Z2AAAAAElFTkSuQmCC"
)
FAVICON_32_PNG_B64: str = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAADo0lEQVR4AexUS2xMYRQ+586MerQ67SAsWCAsJIKE"
    "iIQgdCp0QaLiGSIWEvHY0FJJSaj3I5FIJF71WJgICRJGPWJhIRYEiWjisaBk+hhjSLTuf3zndu7NtDOqiwqRuTnf"
    "f85/zrn//f5v/n8s+stPjkBOgX9fgeLi4kXAERdFRUVTe/LidEeBKnxwgwtmXou4x6xLAtj1UHxpDOCZiMzGpMv3"
    "UO+2/W6hMFZigPDhq+qhwIBQKDRR455Adwjodxosy9qjgQJkStUrwpW1m0sra2s1Tkd467m5qF0Lbz07Iz2vcXjb"
    "+RPADo27IuBHwyxAd1/X1NT0GB9u1jngESCm0cBc5NKNmWQ3M88jssamF0q2XJjGImuw6AvN/5IATvtkNAQB9Mpt"
    "eBsL3oVXm1hQUBDSgIQSRJxPaQ8UmUPCenZiJDQorURsmU2Yv+k/Lu8yPP2SADPr76894vf765xAHCIa+pDTw4jN"
    "W0kRClB1tbeWEFcI01UheW5ZPFBfUMypOjOCmcqY+HCkvNzWnPeSTjrBlflZY2Njg9aMMaqEhsTMTl3YxBkrliSH"
    "99FCybZzUzCfCgKHmCghYjwFxPavJ5LPdqs5pb2KrATy8/OV9QRtAAbjOt5R4CCexNwAaiUYGM8XeLV+OlgiFUL0"
    "MLpr+UOwjBO1KzB94+kgsaxC7Xj0wIqvlHqyEggEArq4W9MdzET/THxMT7SbHxIMBsfhgOAMEP3Ik0B4+8UxIjwP"
    "qEE/kTExIinWOK9vYDV84HubfQzeM3cxL5EKHHlT8VER2esCuZuAYyAUFjKOAj729yXb3swsz6I1S29ogyHrE3xo"
    "4cJLPvwc6xCfv79/1Ud4z7IRsJhZFcDm5HVzc/PGlpaWChc4B5Xe20SlJD5HAcuYUTjxi1HD7lngiUlAwCpMjmyd"
    "DyWGGfEd1Hw6MggUFhaOR4PKTiDiHTrkHIvH408RYGGMRFOSDa+cADusAt4V1PeOOAkMlqgC0ktYtmN6I1qz5CV8"
    "B8sggOvlXj9tzCCAJH6N9usIgoEPT+9NQk5tspDsi0Tar5cmjKgCGtFYY9sHnKjTkEGgra2tDjIvUPh8vlud+p2p"
    "bds7ta5obfl0B1ItUPTP633WaUgNvfoE6zVvhMuie1c+SKU7uAwCiUTiEWS+oojFYskO3akJeuq1rnj/tv7JzV3L"
    "rigi1eWtqRbHXasu+6b5aM2y604iy5BBIEvPH03lCOQUyCnw/yvwuz+RnwAAAP//Qy4p0QAAAAZJREFUAwCUKFVQ"
    "HrnyIAAAAABJRU5ErkJggg=="
)

_PAGE: str = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>Afterword labeling</title>
<link rel="icon" type="image/png" sizes="16x16" href="data:image/png;base64,__FAVICON_16__">
<link rel="icon" type="image/png" sizes="32x32" href="data:image/png;base64,__FAVICON_32__">
<style>
:root {
  --bg: #f7f7f5; --panel: #ffffff; --text: #1d1d1b; --muted: #66665f;
  --line: #d9d9d3; --accent: #2457c5; --accent-bg: #e8eefb; --warn: #9a5b00;
  --warn-bg: #fff4e0; --ok: #1f7a3d; --this-bg: #fffbe6; --this-line: #c9a400;
  --err: #b3261e;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #161615; --panel: #1f1f1d; --text: #e8e8e3; --muted: #a0a097;
    --line: #3a3a36; --accent: #7aa2ff; --accent-bg: #23304d; --warn: #f0b45a;
    --warn-bg: #3a2c12; --ok: #6fcf8f; --this-bg: #2e2a14; --this-line: #c9a400;
    --err: #ff8a80;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
}
header {
  position: sticky; top: 0; z-index: 2; background: var(--panel);
  border-bottom: 1px solid var(--line); padding: 8px 16px;
  display: flex; gap: 16px; flex-wrap: wrap; align-items: baseline;
}
header strong { font-size: 16px; }
.badge { margin-left: auto; font-size: 13px; padding: 2px 10px; border-radius: 999px;
  background: var(--accent-bg); color: var(--text); white-space: nowrap; }
.muted { color: var(--muted); }
main { display: flex; gap: 16px; padding: 16px; align-items: flex-start; flex-wrap: wrap; }
#left { flex: 3 1 480px; min-width: 0; }
#right {
  flex: 2 1 340px; position: sticky; top: 56px; max-height: calc(100vh - 72px);
  overflow-y: auto; background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; padding: 12px;
}
.card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
  padding: 12px; margin-bottom: 12px;
}
h1 { font-size: 18px; margin: 0 0 4px; }
h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em;
  color: var(--muted); margin: 12px 0 6px; }
.status { padding: 6px 10px; border-radius: 6px; margin: 4px 0; }
.status.ok { color: var(--ok); }
.status.warn { background: var(--warn-bg); color: var(--warn); }
.entry { border-left: 3px solid var(--line); padding: 6px 10px; margin: 6px 0; }
.entry.other { opacity: .6; }
.entry.this { border-left-color: var(--this-line); background: var(--this-bg); }
.who { font-size: 13px; color: var(--muted); }
.entry.this .who { color: var(--text); font-weight: 600; }
.body { white-space: pre-wrap; overflow-wrap: anywhere; margin-top: 4px; }
.body code, .mono { font-family: ui-monospace, Consolas, monospace; }
.opt { display: flex; gap: 8px; align-items: baseline; padding: 3px 6px;
  border-radius: 6px; cursor: pointer; }
.opt.on { background: var(--accent-bg); }
.key { display: inline-block; min-width: 1.6em; text-align: center; font-size: 12px;
  border: 1px solid var(--line); border-radius: 4px; padding: 0 4px;
  font-family: ui-monospace, Consolas, monospace; color: var(--muted); }
.opt input { margin: 0; }
.grades { display: flex; gap: 6px; flex-wrap: wrap; }
.grades .opt { border: 1px solid var(--line); }
input[type=text] { width: 100%; padding: 6px 8px; border: 1px solid var(--line);
  border-radius: 6px; background: var(--bg); color: var(--text); font: inherit; }
button { font: inherit; padding: 6px 12px; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--line); background: var(--bg); color: var(--text); }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
#message { color: var(--err); min-height: 1.4em; margin-top: 6px; }
#legend { font-size: 13px; color: var(--muted); margin-top: 10px; }
#legend div { margin: 2px 0; }
#help { display: none; position: fixed; inset: 40px; z-index: 5; overflow-y: auto;
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 16px 20px; box-shadow: 0 8px 30px rgba(0,0,0,.3); }
#help.open { display: block; }
#help dt { font-weight: 600; margin-top: 8px; }
#help dd { margin: 2px 0 0 0; }
.pending { outline: 2px dashed var(--accent); }
.hidden { display: none !important; }
.center { max-width: 640px; margin: 48px auto; }
.post-body { max-height: 60vh; overflow-y: auto; border-top: 1px solid var(--line);
  margin-top: 8px; padding-top: 8px; }
</style>
</head>
<body>
<header>
  <strong>Afterword labeling</strong>
  <span id="where" class="muted"></span>
  <span id="progress"></span>
  <span id="badge" class="badge"
    title="Totals: labeled (initial pass), relabeled (calibration), eligible in this run"></span>
</header>
<div id="screen"></div>
<div id="help" role="dialog" aria-label="Definitions"></div>
<script>
"use strict";
const TOKEN = "__TOKEN__";
let st = null;
let shownId = null;
let form = null;
let full = false;
let gPending = false;
let busy = false;
let postOpen = false;
let postData = null;

function blankForm() {
  return {cls: null, flags: new Set(), pro: null, retro: null,
    translated: false, selfDisclosed: false};
}

function el(tag, attrs, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  for (const kid of kids) if (kid) n.appendChild(kid);
  return n;
}

async function api(path, body) {
  const opts = {headers: {"X-Afterword-Token": TOKEN}};
  if (body !== undefined) {
    opts.method = "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  let data = {};
  try { data = await r.json(); } catch (e) { data = {}; }
  if (!r.ok) throw new Error(data.error || ("request failed: " + r.status));
  return data;
}

function say(text) {
  const m = document.getElementById("message");
  if (m) m.textContent = text || "";
}

async function load() {
  try { show(await api("/api/state")); }
  catch (e) { fatal(e.message); }
}

function fatal(text) {
  const s = document.getElementById("screen");
  s.replaceChildren(el("div", {class: "center card"},
    el("p", {text: "The labeling server did not answer: " + text}),
    el("p", {class: "muted", text: "If the terminal session has ended, nothing is lost: "
      + "saved labels are on disk. Start afterword label-ui again to continue."})));
}

function show(data) {
  st = data;
  const id = data.comment ? data.comment.comment_id : null;
  if (id !== shownId) {
    shownId = id;
    postData = null;
    form = blankForm();
    full = false;
    gPending = false;
  }
  render();
  if (id) {
    window.scrollTo(0, 0);
    const t = document.querySelector(".entry.this");
    if (t) t.scrollIntoView({block: "center"});
  }
}

function header() {
  const where = document.getElementById("where");
  const prog = document.getElementById("progress");
  where.textContent = "pass " + st.pass + (st.batch_id ? " | batch " + st.batch_id : "");
  if (st.status === "labeling") {
    prog.textContent = "comment " + st.position + " of " + st.batch_size
      + " | " + st.labeled_total + " labeled this session | "
      + st.still_unlabeled + " unlabeled in pass";
  } else {
    prog.textContent = st.labeled_total + " labeled this session";
  }
  const p = st.progress;
  document.getElementById("badge").textContent = p
    ? p.labeled + " labeled | " + p.relabeled + " relabeled | " + p.eligible + " eligible"
    : "";
}

function render() {
  header();
  renderHelp();
  const s = document.getElementById("screen");
  if (st.status === "labeling") s.replaceChildren(labelScreen());
  else s.replaceChildren(endScreen());
}

function endScreen() {
  const box = el("div", {class: "center card"});
  if (st.status === "batch_done") {
    box.append(
      el("h1", {text: "Batch " + st.batch_id + " complete"}),
      el("p", {text: st.labeled + " labeled, " + st.skipped + " skipped, "
        + st.still_unlabeled + " still unlabeled in this pass."}),
      el("p", {class: "muted", text: "Stop between batches when attention drops "
        + "(LABELING-GUIDE.md). Saved labels are kept either way."}),
      el("div", {class: "row"},
        el("button", {class: "primary", text: "Start next batch (b)", onclick: nextBatch}),
        el("button", {text: "Stop (q)", onclick: stop})));
  } else if (st.status === "nothing_left") {
    box.append(el("h1", {text: "Nothing left to label in pass " + st.pass}),
      el("p", {class: "muted", text: "You can close this tab and stop the server."}),
      el("div", {class: "row"}, el("button", {text: "Stop (q)", onclick: stop})));
  } else {
    box.append(el("h1", {text: "Session stopped"}),
      el("p", {text: st.labeled_total + " labeled this session. You can close this tab."}));
  }
  return box;
}

function contextCard(c) {
  const card = el("div", {class: "card"});
  card.append(el("h1", {text: c.post_title || "(untitled post)"}));
  card.append(el("div", {class: "muted", text: "Comment posted " + c.posted}));
  card.append(el("div", {class: "muted", text: "Thread as of this comment: "
    + c.earlier_shown + " earlier shown, " + c.later_hidden + " later hidden"}));
  if (c.context_reconstructed) {
    card.append(el("div", {class: "status ok", text: "Context: no known gaps"}));
  } else {
    card.append(el("div", {class: "status warn",
      text: "Context incomplete: " + c.context_gaps.join("; ")}));
  }
  if (c.reply_to_author) {
    card.append(el("div", {class: "status ok",
      text: "Replies to you: REPLY_TO_AUTHOR is set automatically"}));
  }
  if (c.replied_before_labeling) {
    card.append(el("div", {class: "status warn", text: "Your reply to this comment exists "
      + "in this snapshot (replied_before_labeling). Grade as of when it was posted."}));
  }
  return card;
}

function postCard(c) {
  const card = el("div", {class: "card"});
  card.append(el("div", {class: "row"}, el("button", {
    text: (postOpen ? "Hide post" : "Show post") + " (p)", onclick: togglePost})));
  if (!postOpen) return card;
  const d = postData && postData.id === c.comment_id ? postData.view : null;
  if (!d) {
    card.append(el("div", {class: "muted", text: "Loading the post from the saved run..."}));
    return card;
  }
  if (!d.available) {
    card.append(el("div", {class: "status warn", text: d.reason}));
    return card;
  }
  card.append(el("div", {class: "muted", text: "The post as saved in this run: published "
    + d.published + (d.edited ? ", last edited " + d.edited : "")
    + ". Plain text, no links are live."}));
  if (d.edited_after_comment) {
    card.append(el("div", {class: "status warn", text: "The post was edited after this "
      + "comment was posted. Its text may differ from what the commenter saw."}));
  }
  card.append(el("div", {class: "body post-body", text: d.body}));
  return card;
}

async function togglePost() {
  postOpen = !postOpen;
  render();
  const id = shownId;
  if (!postOpen || !id || (postData && postData.id === id)) return;
  try {
    const view = await api("/api/post?c=" + encodeURIComponent(id));
    if (shownId === id) { postData = {id: id, view: view}; render(); }
  } catch (e) { say(e.message); }
}

function threadCard(c) {
  const card = el("div", {class: "card"});
  const mode = full ? "full thread as of this comment" : "reply chain only";
  card.append(el("h2", {text: "Thread: " + mode + " (t toggles)"}));
  for (const t of c.thread) {
    if (!full && !t.is_this && !t.in_reply_chain) continue;
    const kind = t.is_this ? "this" : (t.in_reply_chain ? "" : "other");
    const indent = Math.min(t.depth, 8) * 18;
    const e = el("div", {class: "entry " + kind, style: "margin-left:" + indent + "px"});
    const label = t.who + "  |  " + t.posted + (t.depth > 8 ? "  (depth " + t.depth + ")" : "")
      + (t.is_this ? "  |  THIS COMMENT" : "");
    e.append(el("div", {class: "who", text: label}));
    if (!t.deleted) e.append(el("div", {class: "body", text: t.body}));
    card.append(e);
  }
  return card;
}

function option(type, on, keyText, name, onclick, title) {
  const box = el("input", {type: type, tabindex: "-1"});
  box.checked = on;
  const row = el("label", {class: "opt" + (on ? " on" : ""), title: title || ""},
    box, el("span", {class: "key", text: keyText}), el("span", {text: name}));
  row.addEventListener("click", (ev) => { ev.preventDefault(); onclick(); });
  return row;
}

function formCard(c) {
  const tx = st.taxonomy;
  const box = el("div", {id: "right"});
  box.append(el("h2", {text: "Class (precedence order)"}));
  for (const k of tx.classes) {
    box.append(option("radio", form.cls === k.name, k.key, k.name,
      () => { form.cls = k.name; render(); }, k.definition));
  }
  box.append(el("h2", {text: "Flags"}));
  for (const name of c.structural_flags) {
    const def = tx.structural_flags.find((x) => x.name === name);
    box.append(el("div", {class: "opt on", title: def ? def.definition : ""},
      el("span", {class: "key", text: "auto"}), el("span", {text: name})));
  }
  for (const f of tx.flags) {
    box.append(option("checkbox", form.flags.has(f.name), f.key, f.name, () => {
      if (form.flags.has(f.name)) form.flags.delete(f.name); else form.flags.add(f.name);
      render();
    }, f.definition));
  }
  box.append(el("h2", {text: "Prospective grade, as of when posted"}));
  const pro = el("div", {class: "grades"});
  for (const g of [0, 1, 2, 3]) {
    pro.append(option("radio", form.pro === g, "S-" + g, String(g), () => {
      form.pro = g; render();
    }));
  }
  box.append(pro);
  if (form.pro !== null) {
    box.append(el("h2", {text: "Retrospective grade, with hindsight (optional)"}));
    const retro = el("div", {class: "grades" + (gPending ? " pending" : "")});
    for (const g of [0, 1, 2, 3]) {
      retro.append(option("radio", form.retro === g, "g " + g, String(g), () => {
        form.retro = form.retro === g ? null : g; render();
      }));
    }
    retro.append(option("radio", form.retro === null, "g -", "skip", () => {
      form.retro = null; render();
    }));
    box.append(retro);
  }
  const needs = form.pro !== null && form.pro >= 2;
  box.append(el("h2", {text: needs ? "Reason (required for 2 or 3)" : "Reason (optional)"}));
  box.append(el("input", {type: "text", id: "reason", autocomplete: "off",
    placeholder: "e key to type, Enter saves"}));
  box.append(el("h2", {text: "Language and disclosure"}));
  box.append(option("checkbox", form.translated, "v", "Read via a translation", () => {
    form.translated = !form.translated; render();
  }, "Check when you read this comment through a translation, not in its original language."));
  box.append(option("checkbox", form.selfDisclosed, "a", "Says it was written by an AI", () => {
    form.selfDisclosed = !form.selfDisclosed; render();
  }, "Check only when the comment states explicitly that an AI wrote it. "
    + "Never from how it reads."));
  box.append(el("h2", {text: "Hard to label? Note (batch record only)"}));
  box.append(el("input", {type: "text", id: "note", autocomplete: "off",
    placeholder: "w key to type"}));
  box.append(el("div", {id: "message"}));
  box.append(el("div", {class: "row"},
    el("button", {class: "primary", text: "Save (Enter)", onclick: submit}),
    el("button", {text: "Skip (s)", onclick: skip}),
    el("button", {text: "Definitions (h)", onclick: toggleHelp}),
    el("button", {text: "Stop (q)", onclick: stop})));
  const legend = el("div", {id: "legend"});
  for (const line of [
    "1-9, 0: class    letters: flags (keys shown)",
    "Shift+0..3: prospective grade    g then 0..3: retrospective (g - clears)",
    "e: reason    w: note    v: via translation    a: says AI wrote it    Enter: save",
    "t: full thread    p: post    h: definitions    s: skip    q: stop"]) {
    legend.append(el("div", {class: "mono", text: line}));
  }
  box.append(legend);
  return box;
}

let renderedId = null;

function labelScreen() {
  const c = st.comment;
  // Typed text and focus carry over only while the same comment is on screen.
  const same = renderedId === c.comment_id;
  renderedId = c.comment_id;
  const keep = same
    ? {reason: valueOf("reason"), note: valueOf("note"), focus: focusedId()}
    : {reason: "", note: "", focus: null};
  if (!same && document.activeElement) document.activeElement.blur();
  const main = el("main", {},
    el("div", {id: "left"}, contextCard(c), postCard(c), threadCard(c)), formCard(c));
  setTimeout(() => {
    setValue("reason", keep.reason);
    setValue("note", keep.note);
    if (keep.focus) document.getElementById(keep.focus).focus();
  }, 0);
  return main;
}

function valueOf(id) {
  const n = document.getElementById(id);
  return n ? n.value : "";
}
function setValue(id, v) {
  const n = document.getElementById(id);
  if (n) n.value = v;
}
function focusedId() {
  const a = document.activeElement;
  return a && (a.id === "reason" || a.id === "note") ? a.id : null;
}

function renderHelp() {
  const h = document.getElementById("help");
  const tx = st.taxonomy;
  const dl = el("dl");
  dl.append(el("h2", {text: "Classes: when two fit, take the earlier"}));
  for (const k of tx.classes) {
    dl.append(el("dt", {text: k.key + "  " + k.name}), el("dd", {text: k.definition}));
  }
  dl.append(el("h2", {text: "Flags"}));
  for (const f of tx.flags) {
    dl.append(el("dt", {text: f.key + "  " + f.name}), el("dd", {text: f.definition}));
  }
  for (const f of tx.structural_flags) {
    dl.append(el("dt", {text: "auto  " + f.name}), el("dd", {text: f.definition}));
  }
  h.replaceChildren(el("div", {class: "muted", text: "h or Esc closes"}), dl);
}

function toggleHelp() {
  document.getElementById("help").classList.toggle("open");
}

async function post(path, body) {
  if (busy) return;
  busy = true;
  try { show(await api(path, body)); }
  catch (e) { say(e.message); }
  finally { busy = false; }
}

function submit() {
  if (!st || st.status !== "labeling") return;
  const reason = valueOf("reason").trim();
  if (form.cls === null) return say("Choose a class (1-9, 0).");
  if (form.pro === null) return say("Set the prospective grade (Shift+0..3).");
  if (form.pro >= 2 && !reason) return say("A reason is required for grade 2 or 3 (e).");
  post("/api/label", {
    comment_id: st.comment.comment_id, primary_class: form.cls,
    flags: Array.from(form.flags), prospective: form.pro, retrospective: form.retro,
    reason: reason, note: valueOf("note"), read_via_translation: form.translated,
    ai_self_disclosed: form.selfDisclosed});
}

function skip() {
  if (!st || st.status !== "labeling") return;
  post("/api/skip", {comment_id: st.comment.comment_id, note: valueOf("note")});
}

function nextBatch() {
  if (st && st.status === "batch_done") post("/api/next-batch", {});
}

function stop() {
  if (!st || st.status === "stopped") return;
  if (st.status === "labeling" && !confirm("Stop labeling? Saved labels are kept.")) return;
  post("/api/stop", {});
}

document.addEventListener("keydown", (e) => {
  if (!st) return;
  const a = document.activeElement;
  const inField = a && a.tagName === "INPUT" && a.type === "text";
  const help = document.getElementById("help");
  if (e.key === "Escape") {
    gPending = false;
    help.classList.remove("open");
    if (inField) a.blur();
    if (st.status === "labeling") render();
    return;
  }
  if (e.key === "Enter") {
    e.preventDefault();
    if (st.status === "labeling") submit();
    return;
  }
  if (inField || e.ctrlKey || e.metaKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (st.status !== "labeling") {
    if (k === "b") nextBatch();
    else if (k === "q") stop();
    return;
  }
  if (gPending) {
    e.preventDefault();
    gPending = false;
    if (/^[0-3]$/.test(e.key)) form.retro = Number(e.key);
    else if (e.key === "-" || e.key === "Backspace") form.retro = null;
    render();
    return;
  }
  if (e.shiftKey && /^Digit[0-3]$/.test(e.code)) {
    e.preventDefault();
    form.pro = Number(e.code.slice(5));
    render();
    return;
  }
  if (!e.shiftKey && /^[0-9]$/.test(e.key)) {
    const c = st.taxonomy.classes.find((x) => x.key === e.key);
    if (c) { form.cls = c.name; render(); }
    return;
  }
  const f = st.taxonomy.flags.find((x) => x.key === k);
  if (f) {
    if (form.flags.has(f.name)) form.flags.delete(f.name); else form.flags.add(f.name);
    render();
    return;
  }
  if (k === "h" || e.key === "?") { toggleHelp(); return; }
  if (k === "t") { full = !full; render(); return; }
  if (k === "p") { togglePost(); return; }
  if (k === "v") { form.translated = !form.translated; render(); return; }
  if (k === "a") { form.selfDisclosed = !form.selfDisclosed; render(); return; }
  if (k === "s") { skip(); return; }
  if (k === "q") { stop(); return; }
  if (k === "g" && form.pro !== null) { gPending = true; render(); return; }
  if (k === "e" || k === "w") {
    e.preventDefault();
    document.getElementById(k === "e" ? "reason" : "note").focus();
  }
});

load();
</script>
</body>
</html>
"""

PAGE: str = _PAGE.replace("__FAVICON_16__", FAVICON_16_PNG_B64).replace(
    "__FAVICON_32__", FAVICON_32_PNG_B64
)
