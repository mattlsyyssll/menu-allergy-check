import { ALLERGENS } from './core/allergens';
import {
  buildWaiterQuestion, LANGUAGES, MARK_LABEL, migrateList, normalizeLang,
  type AllergyList, type LangCode, type Mark,
} from './core/core';
import { cloudConfigured, cloudEngine, deviceAvailability, deviceEngine, warmDevice, type DeviceStatus } from './ai';
import { fileToDataUrl, sampleMenuDataUrl } from './image';
import { runCheck, type CheckState } from './pipeline';

// ---------- tiny DOM helper ----------
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
function h<K extends keyof HTMLElementTagNameMap>(tag: K, props: Record<string, string> = {}, ...kids: (Node | string)[]): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') el.className = v; else el.setAttribute(k, v);
  }
  for (const k of kids) el.append(k);
  return el;
}

// ---------- saved list (browser only) ----------
const LIST_KEY = 'allergy-list-v1';
const LANG_KEY = 'parent-lang-v1';

function loadList(): AllergyList {
  try {
    // migrateList turns an old "Shellfish" item into Crustaceans + Molluscs (the safer side).
    const migrated = migrateList(JSON.parse(localStorage.getItem(LIST_KEY) || 'null'));
    if (migrated) { localStorage.setItem(LIST_KEY, JSON.stringify(migrated)); return migrated; }
  } catch { /* ignore */ }
  return { allergens: [], custom: [] };
}
let list = loadList();

function saveList() {
  const custom = $<HTMLInputElement>('custom').value.split(/[,;、，]/).map((s) => s.trim()).filter(Boolean).slice(0, 10);
  const allergens = ALLERGENS.filter((a) => $<HTMLInputElement>(`al-${a.id}`).checked).map((a) => a.id);
  list = { allergens, custom };
  localStorage.setItem(LIST_KEY, JSON.stringify(list));
  $('saved').textContent = allergens.length + custom.length
    ? 'Saved on this device only. It is never uploaded.'
    : 'Pick at least one allergen.';
  refreshRunButton();
}

function renderAllergens() {
  const box = $('allergens');
  for (const a of ALLERGENS) {
    const input = h('input', { type: 'checkbox', id: `al-${a.id}` });
    input.checked = list.allergens.includes(a.id);
    input.addEventListener('change', saveList);
    box.append(h('label', {}, input, h('span', {}, a.label, h('small', { class: 'covers' }, ` (${a.covers})`))));
  }
  const custom = $<HTMLInputElement>('custom');
  custom.value = list.custom.join(', ');
  custom.addEventListener('input', saveList);
}

function renderLangSelect(sel: HTMLSelectElement, value: LangCode) {
  for (const l of LANGUAGES) sel.append(h('option', { value: l.code }, l.name));
  sel.value = value;
}

// ---------- status chips ----------
let deviceStatus: DeviceStatus = 'unsupported';
let warmPct = -1;
let online = navigator.onLine;

function renderChips() {
  const chips = $('chips');
  chips.replaceChildren();
  const dev: [string, string] =
    deviceStatus === 'ready' ? ['good', 'On-device model: ready'] :
    warmPct >= 0 && warmPct < 1 ? ['warn', `On-device model: preparing ${Math.round(warmPct * 100)}%`] :
    deviceStatus === 'unsupported' ? ['warn', 'On-device model: not available in this browser (needs desktop Chrome with the built-in model)'] :
    deviceStatus === 'error' ? ['warn', 'On-device model: could not start. Tap anywhere to retry'] :
    ['warn', 'On-device model: tap anywhere to prepare it'];
  chips.append(h('span', { class: `chip ${dev[0]}` }, dev[1]));
  chips.append(h('span', { class: `chip ${cloudConfigured && online ? 'good' : 'off'}` },
    !cloudConfigured ? 'Cloud recipe lookup: off (no Firebase config). Dishes without printed ingredients get Ask the kitchen'
      : online ? 'Cloud recipe lookup: on (dish names only)' : 'Cloud recipe lookup: paused (offline)'));
  chips.append(h('span', { class: 'chip' }, online ? 'Online' : 'Offline: on-device part still works'));
}

async function warm() {
  if (deviceStatus === 'ready' || deviceStatus === 'unsupported') return;
  try {
    warmPct = 0;
    renderChips();
    await warmDevice((f) => { warmPct = f; renderChips(); });
    deviceStatus = 'ready';
    warmPct = 1;
  } catch {
    deviceStatus = 'error'; // usually "needs a user tap to download"; the pointerdown listener retries
    warmPct = -1;
  }
  renderChips();
  refreshRunButton();
}

// ---------- photo + run ----------
let imageDataUrl = '';
let running = false;

function refreshRunButton() {
  const hasList = list.allergens.length + list.custom.length > 0;
  $<HTMLButtonElement>('run').disabled = !(hasList && imageDataUrl) || running;
  $('runHint').textContent = !hasList ? 'Save your allergy list first.' : !imageDataUrl ? 'Add a menu photo.' : '';
}

function setImage(url: string) {
  imageDataUrl = url;
  const p = $<HTMLImageElement>('preview');
  p.src = url;
  p.hidden = false;
  refreshRunButton();
}

// ---------- results ----------
let lastState: CheckState | null = null;

function renderState(s: CheckState) {
  lastState = s;
  const progress = $('progress');
  progress.hidden = false;
  const done = s.dishes.filter((d) => d.state === 'done').length;
  const total = s.dishes.length;
  const pct = s.stage === 'reading' ? 5 : s.stage === 'done' ? 100 : 10 + (total ? (done / total) * 85 : 0);
  $('barFill').style.width = `${pct}%`;
  $('progressText').textContent = s.message;

  if (s.dishes.length) {
    $('resultsCard').hidden = false;
    const ul = $('dishes');
    ul.replaceChildren();
    for (const r of s.dishes) {
      const d = r.decision;
      const li = h('li', { class: `dish ${d ? d.mark : 'pending'}` }, h('h3', {}, r.dish.name));
      if (r.dish.ingredients.length) li.append(h('p', { class: 'ing' }, `Menu lists: ${r.dish.ingredients.join(', ')}`));
      if (d) {
        li.append(h('span', { class: `badge ${d.mark}` }, MARK_LABEL[d.mark]));
        li.append(h('span', { class: `src ${d.source}` }, d.source === 'cloud' ? 'Decided with the cloud model' : 'Decided on this device'));
        const reasons = h('ul');
        for (const f of d.findings) reasons.append(h('li', {}, f.reason));
        li.append(reasons);
      } else {
        li.append(h('span', { class: 'src' }, r.state === 'checking' ? 'Checking...' : 'Waiting'));
      }
      ul.append(li);
    }
  }
  renderLeftPanel(s);
  if (s.stage === 'done') renderWaiter(s);
}

function renderLeftPanel(s: CheckState | null) {
  const p = $('leftPanel');
  p.replaceChildren();
  p.append(h('ul', { class: 'never' },
    h('li', {}, 'Your allergy list: never sent'),
    h('li', {}, 'Your menu photo: never sent'),
    h('li', {}, 'Every dish name on the menu (printed name and English name): sent to the cloud model in one request, to look up typical recipes. Shown below')));
  const log = s?.cloudLog ?? [];
  if (log.length === 0) {
    p.append(h('p', {}, !cloudConfigured ? 'Nothing has left this device. The cloud recipe lookup is off.' : 'Nothing has left this device yet.'));
    return;
  }
  for (const e of log) {
    p.append(h('p', {}, `${e.at.slice(11, 19)} UTC, ${e.outcome}${e.error ? `: ${e.error}` : ''}. Dish names sent: ${e.dishNames.join('; ')}`));
    p.append(h('p', { class: 'hint' }, 'Exact text sent to the cloud model:'));
    p.append(h('pre', {}, e.prompt));
  }
}

function renderWaiter(s: CheckState) {
  $('waiterCard').hidden = false;
  const menuSel = $<HTMLSelectElement>('menuLang');
  if (!menuSel.options.length) {
    renderLangSelect(menuSel, 'en');
    menuSel.addEventListener('change', () => lastState && renderWaiter(lastState));
  }
  const detected = normalizeLang(s.language);
  if (detected && menuSel.dataset.auto !== 'done') { menuSel.value = detected; menuSel.dataset.auto = 'done'; }
  const parentLang = $<HTMLSelectElement>('parentLang').value as LangCode;
  const menuLang = menuSel.value as LangCode;
  const flagged = s.dishes.filter((d) => d.decision && d.decision.mark !== 'no_listed').map((d) => d.dish.name);
  const box = $('waiter');
  box.replaceChildren();
  const add = (title: string, lang: LangCode) => {
    const text = buildWaiterQuestion(list, lang, flagged);
    const btn = h('button', { class: 'btn ghost', type: 'button' }, 'Copy');
    btn.addEventListener('click', () => { void navigator.clipboard?.writeText(text); btn.textContent = 'Copied'; });
    box.append(h('div', { class: 'waiterBox' }, h('h3', {}, title), h('p', { lang }, text), btn));
  };
  add(`Show this to the waiter (${LANGUAGES.find((l) => l.code === menuLang)?.name})`, menuLang);
  if (parentLang !== menuLang) add(`Your language (${LANGUAGES.find((l) => l.code === parentLang)?.name})`, parentLang);
  if (!detected) box.append(h('p', { class: 'hint' }, 'The menu language was not recognised. Pick it above.'));
}

async function run() {
  if (running) return;
  running = true;
  refreshRunButton();
  $('waiterCard').hidden = true;
  $<HTMLSelectElement>('menuLang').dataset.auto = '';
  try {
    const final = await runCheck({
      imageDataUrl, list, device: deviceEngine,
      cloud: online ? cloudEngine : undefined,
      onUpdate: renderState,
    });
    renderState(final);
  } finally {
    running = false;
    refreshRunButton();
  }
}

// ---------- start ----------
function init() {
  renderAllergens();
  const savedLang = localStorage.getItem(LANG_KEY) as LangCode | null;
  renderLangSelect($('parentLang') as HTMLSelectElement, savedLang && LANGUAGES.some((l) => l.code === savedLang) ? savedLang : (normalizeLang(navigator.language) ?? 'en'));
  $('parentLang').addEventListener('change', () => {
    localStorage.setItem(LANG_KEY, ($('parentLang') as HTMLSelectElement).value);
    if (lastState?.stage === 'done') renderWaiter(lastState);
  });
  $<HTMLInputElement>('photo').addEventListener('change', async (e) => {
    const f = (e.target as HTMLInputElement).files?.[0];
    if (f) { try { setImage(await fileToDataUrl(f)); } catch { $('runHint').textContent = 'Could not open that photo. Try a JPEG or PNG.'; } }
  });
  $('sample').addEventListener('click', () => setImage(sampleMenuDataUrl()));
  $('run').addEventListener('click', () => { void run(); });
  window.addEventListener('online', () => { online = true; renderChips(); });
  window.addEventListener('offline', () => { online = false; renderChips(); });

  saveList();
  renderChips();
  renderLeftPanel(null);

  // Warm the on-device model on page open; retry on the first tap if Chrome needs a gesture.
  void deviceAvailability().then((a) => {
    deviceStatus = a;
    renderChips();
    if (a !== 'unsupported') void warm();
  });
  window.addEventListener('pointerdown', () => { if (deviceStatus !== 'ready' && deviceStatus !== 'unsupported' && warmPct < 0) void warm(); }, { once: false });
}

init();
export type { Mark };
