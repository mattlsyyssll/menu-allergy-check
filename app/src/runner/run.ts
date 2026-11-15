// Dev-only batch runner (served at /run.html by `npm run dev`). Runs the SAME pipeline as the app
// (src/pipeline.ts runCheck with the real device and cloud engines) over kit menus and allergy lists,
// and offers one JSON download: per menu the kit's reply text (all four lists), the cloud log lines,
// and a per-dish table with label and decider. Not part of the production build.

import { cloudEngine, cloudConfigured, deviceAvailability, deviceEngine, warmDevice, CLOUD_MODEL } from '../ai';
import { allergenIdsFromName, MARK_LABEL, parseMenuJson, type AllergyList, type CloudPayload } from '../core/core';
import { fileToDataUrl } from '../image';
import { runCheck, type AttemptEvent, type CloudEngine, type DeviceEngine } from '../pipeline';

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const params = new URLSearchParams(location.search);
const FINAL = params.get('final') === '1';

interface ProfileDef { name: string; allergens: string[]; terms: string[] }
interface Kit { profiles: Record<string, ProfileDef>; generic: string[]; heldout: Set<string>; development: string[] }

interface DishRow { dish: string; label: string; decider: 'device' | 'cloud'; reason: string }
interface CaseResult {
  menu: string;
  status: 'ok' | 'error';
  error?: string;
  language: string;
  seconds: number;
  deviceCalls: number;
  reply_txt: string;
  cloudlog_jsonl: string;
  /** Every timed-out or failed device/cloud attempt (90 s device, 45 s cloud, one retry each). */
  attempts: AttemptEvent[];
  timeouts: number;
  warnings: string[];
  cloudRequests: { at: string; profile: string; body: string; privacyFlags: string[] }[];
  /** Every device read answer, in call order (kept so a run can be replayed with the real read). */
  deviceReads?: string[];
  profiles: Record<string, DishRow[]>;
}

const logEl = $('log');
const log = (m: string) => { logEl.textContent += `${new Date().toISOString().slice(11, 19)} ${m}\n`; logEl.scrollTop = logEl.scrollHeight; };
const results: CaseResult[] = [];
let startedAt = 0;
let startedIso = '';
let timer: number | undefined;
let stopRequested = false;
let running = false;

// ---------- kit files (served by vite.config.js, dev only) ----------

/** Held-out set 2 (M25 to M32): menus and profiles are served under /kit/set2/ (same profiles as set 1; keys are not reachable). */
const SET2 = /^M(?:2[5-9]|3[0-2])$/;
/** Held-out set 3 (M33 to M40): served under /kit/set3/, same rules as set 2. */
const SET3 = /^M(?:3[3-9]|40)$/;
/** Held-out set 4 (M41 to M48): served under /kit/set4/, same rules. */
const SET4 = /^M4[1-8]$/;
/** Held-out set 5 (M49 to M56): served under /kit/set5/, same rules. */
const SET5 = /^M(?:49|5[0-6])$/;
const menuUrl = (menu: string) => (SET2.test(menu) ? `/kit/set2/menus/${menu}.png` : SET3.test(menu) ? `/kit/set3/menus/${menu}.png` : SET4.test(menu) ? `/kit/set4/menus/${menu}.png` : SET5.test(menu) ? `/kit/set5/menus/${menu}.png` : `/kit/menus/${menu}.png`);

async function loadKit(): Promise<Kit> {
  const [p, h, h2, p2, h3, p3, h4, p4, h5, p5] = await Promise.all([fetch('/kit/profiles.json'), fetch('/kit/heldout.json'), fetch('/kit/set2/heldout.json'), fetch('/kit/set2/profiles.json'),
    fetch('/kit/set3/heldout.json'), fetch('/kit/set3/profiles.json'), fetch('/kit/set4/heldout.json'), fetch('/kit/set4/profiles.json'),
    fetch('/kit/set5/heldout.json'), fetch('/kit/set5/profiles.json')]);
  if (!p.ok || !h.ok) throw new Error('Could not load /kit/profiles.json or /kit/heldout.json. Is the kit folder next to the app folder (or KIT_DIR set)?');
  const pj = await p.json();
  const hj = await h.json();
  // Set 2 is held out. If its file cannot be read, M25-M32 are still treated as held out (never run by accident).
  const heldout = new Set<string>(hj.heldout);
  for (let n = 25; n <= 32; n++) heldout.add(`M${n}`);
  if (h2.ok) for (const m of (await h2.json()).heldout ?? []) heldout.add(String(m));
  // Set 3 (M33-M40) is held out the same way.
  for (let n = 33; n <= 40; n++) heldout.add(`M${n}`);
  if (h3.ok) for (const m of (await h3.json()).heldout ?? []) heldout.add(String(m));
  for (let n = 41; n <= 48; n++) heldout.add(`M${n}`);
  if (h4.ok) for (const m of (await h4.json()).heldout ?? []) heldout.add(String(m));
  for (let n = 49; n <= 56; n++) heldout.add(`M${n}`);
  if (h5.ok) for (const m of (await h5.json()).heldout ?? []) heldout.add(String(m));
  const profiles = { ...pj.profiles };
  if (p2.ok) {
    // The set 2 profiles must be identical to set 1's; a difference is an error, not a silent switch.
    const p2j = await p2.json();
    if (JSON.stringify(p2j.profiles) !== JSON.stringify(pj.profiles)) throw new Error('Set 2 profiles.json differs from set 1 profiles.json; the runner will not guess which to use.');
  }
  if (p3.ok) {
    const p3j = await p3.json();
    if (JSON.stringify(p3j.profiles) !== JSON.stringify(pj.profiles)) throw new Error('Set 3 profiles.json differs from set 1 profiles.json; the runner will not guess which to use.');
  }
  if (p4.ok) {
    const p4j = await p4.json();
    if (JSON.stringify(p4j.profiles) !== JSON.stringify(pj.profiles)) throw new Error('Set 4 profiles.json differs from set 1 profiles.json; the runner will not guess which to use.');
  }
  if (p5.ok) {
    const p5j = await p5.json();
    if (JSON.stringify(p5j.profiles) !== JSON.stringify(pj.profiles)) throw new Error('Set 5 profiles.json differs from set 1 profiles.json; the runner will not guess which to use.');
  }
  return { profiles, generic: pj.generic_terms ?? [], heldout, development: hj.development };
}

function normProfileId(x: string): string {
  const t = x.trim().toUpperCase();
  return t.startsWith('PROFILE-') ? t : `PROFILE-${t}`;
}

/** Kit profile -> app allergy list. "shellfish" becomes Crustaceans + Molluscs. */
export function listFromProfile(p: ProfileDef): AllergyList {
  const ids = new Set<string>();
  for (const n of p.allergens) for (const id of allergenIdsFromName(n)) ids.add(id);
  return { allergens: [...ids] as AllergyList['allergens'], custom: [] };
}

// ---------- per-menu caches ----------
// The menu photo and the dish names do not depend on the allergy list, so the device model reads each photo
// once and the cloud recipe lookup runs once per menu; then every list is checked against those answers.

/**
 * One answer per menu, kept only after the call succeeded (so the pipeline's retry makes a fresh call, not a replay
 * of a hung one). After a whole check has ended with no answer, `lock()` makes the failure permanent so the other
 * lists do not each wait through two more timeouts on the same photo or the same dish names.
 */
class Once<A extends unknown[], T> {
  private value: { v: T } | undefined;
  private locked: Error | undefined;
  private lastError: Error | undefined;
  constructor(private readonly fn: (...a: A) => Promise<T>) {}
  readonly get = async (...a: A): Promise<T> => {
    if (this.locked) throw this.locked;
    if (this.value) return this.value.v;
    try { const v = await this.fn(...a); this.value = { v }; return v; } catch (e) { this.lastError = e as Error; throw e; }
  };
  replace(v: T) { this.value = { v }; }
  lock() { if (!this.value && this.lastError) this.locked = this.lastError; }
}

// ---------- privacy self-check (indicative; the kit's scorer decides) ----------

function privacyFlags(kit: Kit, body: string, dishNames: string[]): string[] {
  let t = body.toLowerCase();
  for (const n of dishNames) if (n) t = t.split(n.toLowerCase()).join(' ');
  const flags: string[] = [];
  if (/data:image|base64,/.test(t) || /[a-z0-9+/=_-]{200,}/i.test(t)) flags.push('image-like data');
  const terms = new Set<string>(kit.generic.map((x) => x.toLowerCase()));
  for (const p of Object.values(kit.profiles)) for (const x of p.terms) terms.add(x.toLowerCase());
  for (const term of terms) {
    if (!term) continue;
    const latin = /^[a-z0-9' ]+$/.test(term);
    const hit = latin ? new RegExp(`(?<![a-z0-9])${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`).test(t) : t.includes(term);
    if (hit) flags.push(term);
  }
  return flags;
}

// ---------- one menu ----------

const oneLine = (s: string) => s.replace(/\s+/g, ' ').trim();

async function runMenu(kit: Kit, menu: string, profileIds: string[], cloudOn: boolean, row: HTMLTableRowElement): Promise<CaseResult> {
  const t0 = performance.now();
  const res: CaseResult = { menu, status: 'ok', language: '', seconds: 0, deviceCalls: 0, reply_txt: '', cloudlog_jsonl: '', attempts: [], timeouts: 0, warnings: [], cloudRequests: [], profiles: {} };
  const logLines: string[] = [];
  let currentProfile = '';
  const imgRes = await fetch(menuUrl(menu));
  if (!imgRes.ok) throw new Error(`Could not load menu image ${menu}`);
  const imageDataUrl = await fileToDataUrl(await imgRes.blob());
  const readOnce = new Once<[string, ((t: string) => void) | undefined], string>(async (img, onPartial) => {
    res.deviceCalls++; row.cells[2].textContent = String(res.deviceCalls);
    const text = await deviceEngine.readMenu(img, onPartial);
    (res.deviceReads ??= []).push(text);
    return text;
  });
  // A short read (see MIN_PLAUSIBLE_DISHES) is read again with a fresh device call, once per menu; the longer result is kept
  // for the other lists. A second list never repeats the re-read.
  let rereadTried = false;
  const device: DeviceEngine = {
    readMenu: async (img, onPartial, opts) => {
      if (!opts?.fresh) return readOnce.get(img, onPartial);
      if (rereadTried) return readOnce.get(img, undefined);
      rereadTried = true;
      res.deviceCalls++; row.cells[2].textContent = String(res.deviceCalls);
      const again = await deviceEngine.readMenu(img, undefined, { fresh: true });
      (res.deviceReads ??= []).push(again);
      try {
        const first = await readOnce.get(img, undefined);
        if (parseMenuJson(again).dishes.length > parseMenuJson(first).dishes.length) readOnce.replace(again);
      } catch { /* an unreadable second answer is left to the pipeline */ }
      return again;
    },
  };

  // Records the cloud request body exactly as sent, before it is sent, so a failed call is still logged.
  // The request holds dish names only, so it is the same for every list: one request per menu, its answer
  // (or its failure) reused for the other lists.
  const realCloud = cloudEngine;
  // Every attempt (the retry too) is logged as sent, because each is a real request.
  const cloudOnce = new Once<[CloudPayload], string>(async (payload) => {
    const body = payload.prompt;
    logLines.push(JSON.stringify({ to: 'cloud', body }));
    res.cloudRequests.push({ at: new Date().toISOString(), profile: currentProfile, body, privacyFlags: privacyFlags(kit, body, payload.dishNames) });
    row.cells[3].textContent = String(res.cloudRequests.length);
    const answer = await realCloud!.recipes(payload);
    // The answer is logged too ("from" lines; the privacy check reads only "to" lines), so a miss can be traced
    // to the cloud rating or to the device rules, and rules can be re-checked on saved answers.
    logLines.push(JSON.stringify({ from: 'cloud', body: answer }));
    return answer;
  });
  const recording: CloudEngine | undefined = cloudOn && realCloud ? { recipes: (payload) => cloudOnce.get(payload) } : undefined;

  let reply = 'STATUS: PAGES\n';
  for (const pid of profileIds) {
    currentProfile = pid;
    const list = listFromProfile(kit.profiles[pid]);
    const state = await runCheck({ imageDataUrl, list, device, cloud: recording });
    readOnce.lock(); cloudOnce.lock();
    for (const ev of state.events) res.attempts.push({ ...ev, message: `${pid}: ${ev.message}` });
    for (const w of state.warnings) if (!res.warnings.includes(w)) res.warnings.push(w);
    res.timeouts = res.attempts.filter((x) => x.kind === 'timeout').length;
    if (state.events.length) log(`${menu} ${pid}: ${state.events.map((x) => `${x.step} attempt ${x.attempt} ${x.kind} after ${x.seconds} s`).join('; ')}`);
    reply += `=== ${pid}\n`;
    const rows: DishRow[] = [];
    if (state.stage === 'error') {
      res.status = 'error';
      res.error = state.error;
    }
    res.language = state.language || res.language;
    for (const d of state.dishes) {
      const dec = d.decision;
      const label = dec ? MARK_LABEL[dec.mark] : MARK_LABEL.ask; // an unfinished dish is never "No listed allergen found"
      const reasons = dec ? dec.findings.filter((f) => f.mark === dec.mark).map((f) => f.reason) : ['No decision was reached.'];
      const reason = oneLine(reasons.join(' | ')) || 'No reason recorded.';
      rows.push({ dish: d.dish.name, label, decider: dec?.source ?? 'device', reason });
      reply += `Dish: ${oneLine(d.dish.name)}\nLabel: ${label}\nReason: ${reason}\n`;
    }
    res.profiles[pid] = rows;
  }
  res.reply_txt = reply;
  res.cloudlog_jsonl = logLines.length ? logLines.join('\n') + '\n' : '';
  res.seconds = Math.round((performance.now() - t0) / 100) / 10;
  return res;
}

// ---------- page ----------

function fmt(ms: number): string {
  const s = Math.round(ms / 1000);
  return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
}

function tick() {
  const done = results.length;
  const total = Number($('fill').dataset.total || 0);
  const el = performance.now() - startedAt;
  let t = `Elapsed ${fmt(el)}.`;
  if (done > 0 && total > done) t += ` About ${fmt((el / done) * (total - done))} left.`;
  $('time').textContent = t;
}

function buildRunJson(): string {
  const out = {
    format: 'buildhybridai-batch-run-v1',
    startedAt: startedIso,
    elapsedSeconds: Math.round((performance.now() - startedAt) / 1000),
    final: FINAL,
    cloudModel: CLOUD_MODEL,
    cloudStepOn: results.some((r) => r.cloudRequests.length > 0) || $<HTMLInputElement>('cloud').checked,
    note: 'cases[MENU].reply_txt is <CASE>.reply.txt and cases[MENU].cloudlog_jsonl is <CASE>.cloudlog.jsonl in the kit format. Split them with scripts/split_run.py.',
    cases: Object.fromEntries(results.map((r) => [r.menu, r])),
  };
  return JSON.stringify(out, null, 1);
}

/** Name of the saved run: ?save=NAME in the address, else buildhybridai-run-<start time>. The server sanitizes it again. */
const saveName = () => params.get('save') || `buildhybridai-run-${startedIso.replace(/[:.]/g, '-')}`;

/** Dev-only: POST the run to the dev server, which writes <kit>/runs/<name>.json (never overwrites). */
async function saveToKit(json: string): Promise<string> {
  try {
    const r = await fetch(`/kit-save?name=${encodeURIComponent(saveName())}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: json });
    const t = await r.text();
    return r.ok ? `Saved to the kit: ${(JSON.parse(t) as { saved: string }).saved}` : `NOT saved to the kit (${r.status}): ${t}`;
  } catch (e) {
    return `NOT saved to the kit: ${(e as Error).message}`;
  }
}

function download() {
  const json = buildRunJson();
  const blob = new Blob([json], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `buildhybridai-run-${startedIso.replace(/[:.]/g, '-')}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  void saveToKit(json).then((m) => { log(m); $('status').textContent = m; });
}

async function start() {
  if (running) return;
  running = true;
  stopRequested = false;
  results.length = 0;
  logEl.textContent = '';
  $('table').querySelector('tbody')!.replaceChildren();
  $<HTMLButtonElement>('start').disabled = true;
  $<HTMLButtonElement>('stop').disabled = false;
  $<HTMLButtonElement>('download').disabled = true;
  startedAt = performance.now();
  startedIso = new Date().toISOString();
  timer = window.setInterval(tick, 500);
  const status = $('status');
  try {
    const kit = await loadKit();
    const wanted = $<HTMLInputElement>('menus').value.trim();
    const menus = wanted.toLowerCase() === 'dev' || wanted === '' ? kit.development : wanted.split(/[\s,]+/).filter(Boolean).map((m) => m.toUpperCase());
    const refused = menus.filter((m) => kit.heldout.has(m));
    if (refused.length && !FINAL) {
      status.innerHTML = `<span class="bad">Refused: ${refused.join(', ')} are held-out menus. Add ?final=1 to the address to run them (once, after the freeze).</span>`;
      return;
    }
    if (FINAL) log('FINAL mode: held-out menus are allowed.');
    const profileIds = $<HTMLInputElement>('profiles').value.split(/[\s,]+/).filter(Boolean).map(normProfileId);
    const unknown = profileIds.filter((p) => !kit.profiles[p]);
    if (unknown.length || profileIds.length === 0) { status.innerHTML = `<span class="bad">Unknown allergy list: ${unknown.join(', ') || '(none given)'}</span>`; return; }
    const cloudOn = $<HTMLInputElement>('cloud').checked && cloudConfigured;
    log(`Menus: ${menus.join(' ')} | lists: ${profileIds.join(' ')} | cloud step: ${cloudOn ? 'on' : 'off'}`);

    // Prepare the on-device model (a click is a user gesture, so Chrome may download it now).
    status.textContent = 'Preparing the on-device model...';
    const avail = await deviceAvailability();
    if (avail === 'unsupported') { status.innerHTML = '<span class="bad">The on-device model is not available in this browser.</span>'; return; }
    await warmDevice((f) => { status.textContent = `Preparing the on-device model ${Math.round(f * 100)}%`; });

    $('fill').dataset.total = String(menus.length);
    const tbody = $('table').querySelector('tbody')!;
    for (let i = 0; i < menus.length; i++) {
      if (stopRequested) { log('Stopped by you.'); break; }
      const menu = menus[i];
      const row = document.createElement('tr');
      for (let c = 0; c < 6; c++) row.append(document.createElement('td'));
      row.cells[0].textContent = menu; row.cells[2].textContent = '0'; row.cells[3].textContent = '0'; row.cells[5].textContent = 'running...';
      tbody.append(row);
      status.textContent = `Menu ${i + 1} of ${menus.length}: ${menu} (${profileIds.length} lists)`;
      try {
        const r = await runMenu(kit, menu, profileIds, cloudOn, row);
        results.push(r);
        row.cells[1].textContent = String(r.profiles[profileIds[0]]?.length ?? 0);
        row.cells[4].textContent = String(r.seconds);
        const flagged = r.cloudRequests.filter((q) => q.privacyFlags.length).length;
        row.cells[5].innerHTML = r.status === 'ok' ? `<span class="ok">done</span>${flagged ? ` <span class="bad">privacy flags: ${flagged}</span>` : ''}` : `<span class="bad">${r.error ?? 'error'}</span>`;
        log(`${menu}: ${r.status}, ${r.seconds} s, device calls ${r.deviceCalls}, cloud requests ${r.cloudRequests.length}, timeouts ${r.timeouts}${flagged ? `, PRIVACY FLAGS ${flagged}` : ''}`);
      } catch (e) {
        const msg = (e as Error).message;
        row.cells[5].innerHTML = `<span class="bad">${msg}</span>`;
        log(`${menu}: FAILED ${msg}`);
        results.push({ menu, status: 'error', error: msg, language: '', seconds: 0, deviceCalls: 0, reply_txt: 'STATUS: PAGES\n', cloudlog_jsonl: '', attempts: [], timeouts: 0, warnings: [], cloudRequests: [], profiles: {} });
      }
      $('fill').style.width = `${Math.round(((i + 1) / menus.length) * 100)}%`;
      $<HTMLButtonElement>('download').disabled = false;
      tick();
    }
    status.textContent = `Finished ${results.length} menu(s) in ${fmt(performance.now() - startedAt)}. Download the JSON below.`;
  } catch (e) {
    status.innerHTML = `<span class="bad">${(e as Error).message}</span>`;
    log(`ERROR ${(e as Error).message}`);
  } finally {
    window.clearInterval(timer);
    tick();
    running = false;
    $<HTMLButtonElement>('start').disabled = false;
    $<HTMLButtonElement>('stop').disabled = true;
    $<HTMLButtonElement>('download').disabled = results.length === 0;
  }
}

function init() {
  if (!import.meta.env.DEV) {
    document.body.innerHTML = '<p>The batch runner only works on the development server (npm run dev).</p>';
    return;
  }
  $<HTMLInputElement>('menus').value = params.get('menus') || 'dev';
  $<HTMLInputElement>('profiles').value = params.get('profiles') || 'A,B,C,D';
  const cloudBox = $<HTMLInputElement>('cloud');
  cloudBox.checked = params.get('cloud') !== '0' && cloudConfigured;
  cloudBox.disabled = !cloudConfigured;
  if (!cloudConfigured) $('status').textContent = 'Idle. No Firebase config found: the cloud step is off.';
  $('start').addEventListener('click', () => { void start(); });
  $('stop').addEventListener('click', () => { stopRequested = true; $('status').textContent = 'Stopping after this menu...'; });
  $('download').addEventListener('click', download);
  if (params.get('auto') === '1') void start();
}

init();
