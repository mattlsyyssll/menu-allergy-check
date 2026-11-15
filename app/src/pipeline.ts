// The check, step by step. Depends only on two small engine interfaces so it can be tested
// with fakes (no browser, no Firebase). Privacy rule enforced here: the cloud engine only ever
// receives a CloudPayload (dish names), never the allergy list or the image.
//
// Round 4: the cloud also rates every dish for ALL allergen categories (fixed list, same request for every user);
// the device reads only the user's allergens from that rating. Every device and cloud call has a timeout and one retry.
//
// Design (changed after the first measured run: 34 false-safe labels, 0 cloud requests):
//   1. device reads the photo and the ingredients printed on the menu;
//   2. device marks each dish from the printed text (list + hidden-source tables);
//   3. cloud: ONE request with ALL dish names (printed and English), asking for each dish's typical recipe
//      (sauces, batters, doughs, garnishes, common variants), each ingredient marked essential/common/possible;
//   4. the recipe is matched ON THE DEVICE against the list + tables; final label = the stricter of 2 and 4;
//   5. offline or cloud failure: device-only path; a dish with no printed ingredients is "Ask the kitchen".

import {
  applyRecipe, buildCloudPayload, firstPass, isPlaced, mergeMarks, parseMenuJson, parsePartialMenu, parseRecipesJson, unknownRecipeFinding,
  type AllergyList, type CloudPayload, type CloudRecipe, type Decision, type Finding, type MenuDish,
} from './core/core';

export interface DeviceEngine {
  /**
   * Read the menu photo (data URL) in ONE device call. Returns the raw model text (JSON).
   * `onPartial` receives the reply so far while the model is still writing, so the screen can
   * show finished dishes early.
   */
  readMenu(imageDataUrl: string, onPartial?: (textSoFar: string) => void, opts?: { fresh?: boolean }): Promise<string>;
}
export interface CloudEngine {
  /** Typical recipes for all dishes of a menu. Receives only the cloud payload (dish names). Returns raw model text (JSON). */
  recipes(payload: CloudPayload): Promise<string>;
}

export interface DishResult {
  dish: MenuDish;
  decision: Decision | null; // null while still being checked
  state: 'waiting' | 'checking' | 'done';
}

export interface CloudLogEntry {
  at: string;
  dishNames: string[];
  /** The exact text sent. */
  prompt: string;
  outcome: 'sent' | 'answered' | 'failed';
  error?: string;
}

/** One failed or timed-out attempt of a device or cloud call. */
export interface AttemptEvent {
  step: 'device' | 'cloud';
  /** 1 = first try, 2 = the retry. */
  attempt: number;
  kind: 'timeout' | 'error';
  seconds: number;
  message: string;
}

/**
 * A read with fewer dishes than this is read once more and the longer list is kept. Round 5 evidence: the device model
 * once returned valid JSON with 1 dish for a 10-dish menu (9.7 s, no error, no timeout); every other dish was silently
 * missing from the result. 1 or 2 dishes is a plausible menu only rarely, and a second read costs one more device call.
 */
export const MIN_PLAUSIBLE_DISHES = 3;

/** Longest wait for one attempt. A hung call must never freeze the screen. */
export const DEVICE_TIMEOUT_MS = 90_000;
export const CLOUD_TIMEOUT_MS = 45_000;

export interface CheckState {
  stage: 'reading' | 'checking' | 'cloud' | 'done' | 'error';
  message: string;
  language: string;
  dishes: DishResult[];
  cloudLog: CloudLogEntry[];
  /** Every failed or timed-out attempt (the batch runner records these). */
  events: AttemptEvent[];
  /** Plain messages for the parent, e.g. "the cloud step timed out: every dish is Ask the kitchen". */
  warnings: string[];
  error?: string;
}

export interface RunOptions {
  imageDataUrl: string;
  list: AllergyList;
  device: DeviceEngine;
  /** Undefined means the cloud step is off. */
  cloud?: CloudEngine;
  onUpdate?: (s: CheckState) => void;
  /** Overrides for tests. Defaults: device 90 s, cloud 45 s, one retry. */
  deviceTimeoutMs?: number;
  cloudTimeoutMs?: number;
  retries?: number;
}

/**
 * Run `fn` with a timeout; on a timeout or an error try once more (`retries`). The last failure is thrown.
 * A late answer from a timed-out attempt is ignored.
 */
export async function withTimeoutRetry<T>(
  step: 'device' | 'cloud', fn: (isCurrent: () => boolean) => Promise<T>, ms: number, retries: number, events: AttemptEvent[],
): Promise<T> {
  let last: Error = new Error('no attempt made');
  for (let attempt = 1; attempt <= retries + 1; attempt++) {
    const t0 = Date.now();
    let timer: ReturnType<typeof setTimeout> | undefined;
    let live = true;
    try {
      return await Promise.race([
        fn(() => live),
        new Promise<never>((_, reject) => { timer = setTimeout(() => reject(new TimeoutError(step, ms)), ms); }),
      ]);
    } catch (e) {
      last = e as Error;
      events.push({ step, attempt, kind: e instanceof TimeoutError ? 'timeout' : 'error', seconds: Math.round((Date.now() - t0) / 100) / 10, message: last.message });
    } finally {
      live = false;
      if (timer) clearTimeout(timer);
    }
  }
  throw last;
}

class TimeoutError extends Error {
  constructor(step: string, ms: number) { super(`The ${step} step timed out after ${Math.round(ms / 1000)} s`); }
}

const foldName = (a: string) => a.normalize('NFC').replace(/\s+/g, ' ').trim().toLowerCase();
const sameName = (a: string, b: string) => foldName(a) === foldName(b);
/** Looser match for the cloud's copy of a name: accents, case, punctuation and spacing do not matter. */
const looseName = (a: string) => a.normalize('NFD').replace(/[\u0300-\u036f]/g, '').normalize('NFC').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();

/** The cloud recipe for a dish: matched by the printed name first, then the English name, then the same two ignoring accents and punctuation. */
function recipeFor(dish: MenuDish, recipes: CloudRecipe[]): CloudRecipe | undefined {
  const exact = recipes.find((r) => sameName(r.name, dish.name)) ?? (dish.nameEnglish ? recipes.find((r) => sameName(r.name, dish.nameEnglish!)) : undefined);
  if (exact) return exact;
  const names = [dish.name, dish.nameEnglish].filter((n): n is string => !!n).map(looseName).filter(Boolean);
  return recipes.find((r) => names.includes(looseName(r.name)));
}

export async function runCheck(opts: RunOptions): Promise<CheckState> {
  const { imageDataUrl, list, device, cloud, onUpdate } = opts;
  const state: CheckState = { stage: 'reading', message: 'Reading the menu on this device...', language: '', dishes: [], cloudLog: [], events: [], warnings: [] };
  const deviceMs = opts.deviceTimeoutMs ?? DEVICE_TIMEOUT_MS;
  const cloudMs = opts.cloudTimeoutMs ?? CLOUD_TIMEOUT_MS;
  const retries = opts.retries ?? 1;
  const emit = () => onUpdate?.(structuredClone(state));
  emit();

  // 1. On device, ONE call: read every dish and its printed ingredients (with English translations).
  //    Early previews show a dish only when it is already "Avoid" from the menu text (that mark cannot be lowered later).
  const onPartial = (text: string, isCurrent: () => boolean = () => true) => {
    if (!isCurrent()) return;
    let part;
    try { part = parsePartialMenu(text); } catch { return; }
    let changed = false;
    for (const dish of part.dishes) {
      if (state.dishes.some((r) => sameName(r.dish.name, dish.name))) continue;
      const d = mergeMarks(firstPass(dish, list, part.language));
      const r: DishResult = { dish, decision: null, state: 'checking' };
      if (d.mark === 'avoid') { r.decision = d; r.state = 'done'; }
      state.dishes.push(r);
      changed = true;
    }
    if (changed) {
      state.message = `Reading the menu on this device... ${state.dishes.length} dish(es) read so far`;
      emit();
    }
  };
  let menu;
  try {
    menu = await withTimeoutRetry('device', async (isCurrent) =>
      parseMenuJson(await device.readMenu(imageDataUrl, (t) => onPartial(t, isCurrent))), deviceMs, retries, state.events);
  } catch (e) {
    const timedOut = state.events.some((x) => x.step === 'device' && x.kind === 'timeout');
    const msg = `Could not read the menu on this device after ${state.events.filter((x) => x.step === 'device').length} tries${timedOut ? ' (the device model did not answer in time)' : ''}: ${(e as Error).message}`;
    state.warnings.push(msg);
    state.error = msg;
    state.message = msg;
    if (state.dishes.length > 0) {
      // Some dishes were already seen while the model was writing: none can be trusted, so each is "Ask the kitchen".
      for (const r of state.dishes) {
        r.decision = mergeMarks([...(r.decision?.findings ?? []), unknownRecipeFinding('device',
          `The menu reading failed or timed out, so this dish was not checked. Ask the kitchen. (${(e as Error).message})`)]);
        r.state = 'done';
      }
      state.stage = 'done';
      state.message = `${msg}. The dishes seen so far are all marked Ask the kitchen.`;
    } else {
      state.stage = 'error';
    }
    emit();
    return state;
  }
  if (menu.dishes.length < MIN_PLAUSIBLE_DISHES) {
    // Short read: ask the device once more (no streaming, no retry) and keep the longer list. A failed re-read keeps the first.
    try {
      const again = await withTimeoutRetry('device', async () => parseMenuJson(await device.readMenu(imageDataUrl, undefined, { fresh: true })), deviceMs, 0, state.events);
      if (again.dishes.length > menu.dishes.length) menu = again;
    } catch { /* keep the first read; the event is recorded in state.events */ }
    if (menu.dishes.length > 0 && menu.dishes.length < MIN_PLAUSIBLE_DISHES) {
      state.warnings.push(`Only ${menu.dishes.length} dish(es) were read from this photo. If the menu has more, some are missing: try a closer, sharper photo.`);
    }
  }
  state.language = menu.language;
  if (menu.dishes.length === 0) {
    state.dishes = [];
    state.stage = 'error';
    state.error = 'No dishes found in the photo. Try a closer, sharper photo of the menu text.';
    state.message = state.error;
    emit();
    return state;
  }

  // 2. On device: first pass for every dish against the saved list and the word tables (printed text only).
  //    The final read is the one that counts: marks are recomputed from it (the streamed ones were early previews).
  state.stage = 'checking';
  state.message = `Checking ${menu.dishes.length} dishes on this device...`;
  const findings: Finding[][] = [];
  state.dishes = menu.dishes.map((dish) => ({ dish, decision: null, state: 'checking' as const }));
  for (const r of state.dishes) {
    const f = firstPass(r.dish, list, menu.language);
    findings.push(f);
    const d = f.length ? mergeMarks(f) : null;
    if (d?.mark === 'avoid') { r.decision = d; r.state = 'done'; } // printed allergen: final whatever the cloud says
  }
  emit();

  // 3. Cloud: ONE request with ALL dish names. Nothing else leaves the device.
  let recipes: CloudRecipe[] | undefined;
  let failure: string | undefined;
  if (cloud) {
    state.stage = 'cloud';
    const payload = buildCloudPayload(menu.dishes.map((d) => ({ name: d.name, nameEnglish: d.nameEnglish })));
    state.message = `Sending ${payload.dishes.length} dish name(s) to the cloud model for typical recipes...`;
    const entry: CloudLogEntry = { at: new Date().toISOString(), dishNames: payload.dishNames, prompt: payload.prompt, outcome: 'sent' };
    state.cloudLog.push(entry);
    emit();
    try {
      recipes = await withTimeoutRetry('cloud', async () => parseRecipesJson(await cloud.recipes(payload)), cloudMs, retries, state.events);
      entry.outcome = 'answered';
    } catch (e) {
      failure = (e as Error).message;
      entry.outcome = 'failed';
      entry.error = failure;
      state.warnings.push(`The cloud recipe step failed (${failure}). Every dish that is not already Avoid is marked Ask the kitchen.`);
    }
  }

  // 4. Final label per dish = the stricter of the printed-text findings and the cloud recipe findings.
  for (let i = 0; i < state.dishes.length; i++) {
    const r = state.dishes[i];
    const printed = isPlaced(r.dish, findings[i]);
    if (recipes) {
      const recipe = recipeFor(r.dish, recipes);
      if (recipe?.confident) findings[i].push(...applyRecipe(recipe, list, 'cloud', r.dish));
      else findings[i].push(unknownRecipeFinding('cloud',
        printed ? 'The cloud lookup could not work out the typical recipe of this dish, and a printed ingredient list may be incomplete. Ask the kitchen what is in it.' : undefined));
      // The cloud step was on but gave no usable recipe: the dish is at least "Ask the kitchen",
      // even with printed ingredients (a printed list can leave out sauces and garnishes).
    } else if (cloud) {
      // The cloud step was on but failed or timed out: nothing backs up the printed text, so every dish is at least Ask.
      findings[i].push(unknownRecipeFinding('device',
        `The cloud step failed (${failure}). ${printed ? 'A printed ingredient list can leave out sauces and garnishes.' : 'The menu does not say what is in this dish.'} Ask the kitchen.`));
    } else if (!printed) {
      findings[i].push(unknownRecipeFinding('device', 'The menu does not say what is in this dish, and the cloud recipe step is not available (off or offline). Ask the kitchen.'));
    }
    r.decision = mergeMarks(findings[i]);
    r.state = 'done';
  }
  emit();

  state.stage = 'done';
  state.message = `Done. ${state.dishes.length} dishes checked.${state.warnings.length ? ' ' + state.warnings.join(' ') : ''}`;
  emit();
  return state;
}
