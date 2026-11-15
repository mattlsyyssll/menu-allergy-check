// Thin core: pure functions only (no DOM, no network, no Firebase).
// parse model JSON, apply the hidden-source table, merge marks, build the cloud payload.

import { ALLERGENS, ALLERGEN_BY_ID, type AllergenDef, type AllergenId } from './allergens';
import { variableDishWord } from './variable';

// ---------- types ----------

/** Exactly three labels. There is deliberately no "safe". */
export type Mark = 'no_listed' | 'ask' | 'avoid';
export const MARK_LABEL: Record<Mark, string> = {
  no_listed: 'No listed allergen found',
  ask: 'Ask the kitchen',
  avoid: 'Avoid',
};
const SEVERITY: Record<Mark, number> = { no_listed: 0, ask: 1, avoid: 2 };

export type Source = 'device' | 'cloud';

export interface AllergyList {
  allergens: AllergenId[];
  /** Free-text extra items, e.g. "kiwi". Matched as direct words. */
  custom: string[];
}

export interface MenuDish {
  /** Dish name exactly as printed. */
  name: string;
  /** English translation of the dish name, when the device model gave one. */
  nameEnglish?: string;
  /** Ingredients as printed on the menu (original language). */
  ingredients: string[];
  /** English translation of each ingredient, same order and length as `ingredients` ('' = none given). */
  ingredientsEnglish?: string[];
}
export interface ReadMenu { language: string; dishes: MenuDish[] }
/** How central an ingredient is to the dish, as reported by the cloud recipe lookup. */
export type RecipeLevel = 'essential' | 'common' | 'possible';
export interface RecipeIngredient { name: string; level: RecipeLevel }
/** One dish's typical recipe from the cloud, including sauces, batters, doughs, garnishes and common variants. */
export interface CloudRecipe {
  name: string; ingredients: RecipeIngredient[]; confident: boolean;
  /** The cloud's rating for each of the fixed allergen categories (all 19 asked; a missing one counts as unknown). */
  ratings?: Partial<Record<AllergenId, AllergenRating>>;
}
/** How likely a dish holds an allergen: usually / often (in common versions) / rarely / unknown. */
export type RatingLevel = 'usually' | 'often' | 'rarely' | 'unknown';
export interface AllergenRating { level: RatingLevel; why: string }

export type FindingKind = 'listed' | 'hidden' | 'typical' | 'unplaced' | 'placed' | 'untranslated' | 'rated' | 'variable';
export interface Finding {
  mark: Mark;
  kind: FindingKind;
  /** Allergen label from the saved list; empty for 'unplaced' / 'placed'. */
  allergen: string;
  /** Plain-words reason shown to the parent. */
  reason: string;
  source: Source;
}

export interface Decision {
  mark: Mark;
  source: Source;
  findings: Finding[];
}

// ---------- JSON parsing ----------

const MAX_DISHES = 60;
const MAX_INGREDIENTS = 30;

/** Pull the first JSON value out of model text (handles ```json fences and chatter). */
export function extractJson(raw: string): unknown {
  if (typeof raw !== 'string') throw new Error('Model reply is not text');
  let t = raw.trim();
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) t = fence[1].trim();
  try { return JSON.parse(t); } catch { /* fall through to bracket scan */ }
  const start = t.search(/[{[]/);
  if (start < 0) throw new Error('No JSON found in model reply');
  const open = t[start];
  const close = open === '{' ? '}' : ']';
  const end = t.lastIndexOf(close);
  if (end <= start) throw new Error('JSON in model reply is cut off');
  return JSON.parse(t.slice(start, end + 1));
}

function cleanText(v: unknown, max: number): string {
  if (typeof v !== 'string') return '';
  return v.replace(/\s+/g, ' ').trim().slice(0, max);
}

function cleanList(v: unknown, maxItems: number, maxLen: number): string[] {
  if (typeof v === 'string') v = v.split(/[,;、，；]/);
  if (!Array.isArray(v)) return [];
  const out: string[] = [];
  for (const item of v) {
    const t = cleanText(item, maxLen);
    if (t && !out.includes(t)) out.push(t);
    if (out.length >= maxItems) break;
  }
  return out;
}

/** Ingredient items may be plain strings or {text, english} objects (the device schema uses objects). */
function parseIngredientItems(v: unknown): { text: string[]; english: string[] } {
  if (typeof v === 'string') v = v.split(/[,;、，；]/);
  const text: string[] = [];
  const english: string[] = [];
  if (!Array.isArray(v)) return { text, english };
  for (const item of v) {
    let t = '';
    let en = '';
    if (typeof item === 'string') t = cleanText(item, 60);
    else if (item && typeof item === 'object') {
      const r = item as Record<string, unknown>;
      t = cleanText(r.text ?? r.name ?? r.ingredient ?? r.original, 60);
      en = cleanText(r.english ?? r.en ?? r.translation, 60);
    }
    if (!t) continue;
    const dup = text.indexOf(t);
    if (dup >= 0) { if (!english[dup] && en) english[dup] = en; continue; }
    text.push(t);
    english.push(en);
    if (text.length >= MAX_INGREDIENTS) break;
  }
  return { text, english };
}

function parseDishRecord(rec: Record<string, unknown>, name: string): MenuDish {
  const ing = parseIngredientItems(rec.ingredients);
  const dish: MenuDish = { name, ingredients: ing.text };
  const nameEnglish = cleanText(rec.nameEnglish ?? rec.name_english ?? rec.english, 100);
  if (nameEnglish) dish.nameEnglish = nameEnglish;
  if (ing.english.some(Boolean)) dish.ingredientsEnglish = ing.english;
  return dish;
}

/**
 * Read the dishes that are already complete in a half-finished streamed reply, so the screen can
 * show them before the model has stopped. Only whole {...} dish objects count; a cut-off one is ignored.
 */
export function parsePartialMenu(raw: string): ReadMenu {
  const lang = raw.match(/"language"\s*:\s*"([^"]{0,20})"/);
  const dishes: MenuDish[] = [];
  const key = raw.search(/"dishes"\s*:\s*\[/);
  if (key >= 0) {
    let i = raw.indexOf('[', key) + 1;
    while (i < raw.length) {
      while (i < raw.length && raw[i] !== '{' && raw[i] !== ']') i++;
      if (i >= raw.length || raw[i] === ']') break;
      let depth = 0;
      let inStr = false;
      let esc = false;
      let end = -1;
      for (let j = i; j < raw.length; j++) {
        const c = raw[j];
        if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
        if (c === '"') inStr = true;
        else if (c === '{') depth++;
        else if (c === '}') { depth--; if (depth === 0) { end = j; break; } }
      }
      if (end < 0) break;
      try {
        const rec = JSON.parse(raw.slice(i, end + 1)) as Record<string, unknown>;
        const name = cleanText(rec.name ?? rec.dish, 100);
        if (name && !dishes.some((x) => x.name.toLowerCase() === name.toLowerCase())) dishes.push(parseDishRecord(rec, name));
      } catch { /* skip a malformed dish */ }
      i = end + 1;
    }
  }
  return { language: lang ? lang[1].toLowerCase() : '', dishes: dishes.slice(0, MAX_DISHES) };
}

/** Parse the on-device "read the menu photo" reply. Drops dishes without a name. */
export function parseMenuJson(raw: string): ReadMenu {
  const data = extractJson(raw) as Record<string, unknown> | unknown[];
  const obj = Array.isArray(data) ? { dishes: data } : data;
  const list = (obj as { dishes?: unknown }).dishes;
  if (!Array.isArray(list)) throw new Error('Menu JSON has no "dishes" list');
  const dishes: MenuDish[] = [];
  for (const d of list) {
    if (!d || typeof d !== 'object') continue;
    const rec = d as Record<string, unknown>;
    const name = cleanText(rec.name ?? rec.dish, 100);
    if (!name) continue;
    if (dishes.some((x) => x.name.toLowerCase() === name.toLowerCase())) continue;
    dishes.push(parseDishRecord(rec, name));
    if (dishes.length >= MAX_DISHES) break;
  }
  const language = cleanText((obj as { language?: unknown }).language, 20).toLowerCase();
  return { language, dishes };
}

function parseLevel(v: unknown): RecipeLevel {
  const t = typeof v === 'string' ? v.toLowerCase().trim() : '';
  if (t === 'essential' || t === 'required' || t === 'core') return 'essential';
  if (t === 'common' || t === 'usual' || t === 'typical') return 'common';
  return 'possible'; // unknown or missing level is the weakest claim, so it can only raise "Ask the kitchen"
}

function parseRatingLevel(v: unknown): RatingLevel {
  const t = typeof v === 'string' ? v.toLowerCase().trim() : '';
  if (/^(usually|always|nearly always|almost always|typically)\b/.test(t)) return 'usually';
  if (/^(often|common|commonly|frequently|sometimes|in common versions)\b/.test(t)) return 'often';
  if (/^(rarely|never|seldom|no|none)\b/.test(t)) return 'rarely';
  return 'unknown'; // anything else is the weakest claim: it can only raise "Ask the kitchen"
}

/** Allergen id from the cloud's name for a category (id, label or plain name). */
function ratingAllergenId(v: unknown): AllergenId | null {
  const t = typeof v === 'string' ? v.toLowerCase().trim().replace(/[\s_/-]+/g, '_') : '';
  if (!t) return null;
  if (t in ALLERGEN_BY_ID) return t as AllergenId;
  for (const a of ALLERGENS) if (a.label.toLowerCase().replace(/[\s_/-]+/g, '_') === t) return a.id;
  return null;
}

function parseRatings(v: unknown): CloudRecipe['ratings'] {
  const out: NonNullable<CloudRecipe['ratings']> = {};
  let any = false;
  const put = (idRaw: unknown, levelRaw: unknown, whyRaw: unknown) => {
    const id = ratingAllergenId(idRaw);
    if (!id) return;
    const level = parseRatingLevel(levelRaw);
    const why = cleanText(whyRaw, 160);
    const old = out[id];
    // a repeated category keeps the stricter rating
    const rank: Record<RatingLevel, number> = { rarely: 0, unknown: 1, often: 2, usually: 3 };
    if (!old || rank[level] > rank[old.level]) out[id] = { level, why };
    any = true;
  };
  if (Array.isArray(v)) {
    for (const x of v) {
      if (!x || typeof x !== 'object') continue;
      const r = x as Record<string, unknown>;
      put(r.allergen ?? r.category ?? r.id ?? r.name, r.rating ?? r.level, r.why ?? r.reason);
    }
  } else if (v && typeof v === 'object') {
    for (const [k, x] of Object.entries(v as Record<string, unknown>)) {
      if (x && typeof x === 'object') { const r = x as Record<string, unknown>; put(k, r.rating ?? r.level, r.why ?? r.reason); }
      else put(k, x, '');
    }
  }
  return any ? out : undefined;
}

/** Parse the cloud recipe reply: per dish, ingredients each with a level (essential, common, possible). */
export function parseRecipesJson(raw: string): CloudRecipe[] {
  const data = extractJson(raw) as Record<string, unknown> | unknown[];
  const list = Array.isArray(data) ? data : (data as { dishes?: unknown }).dishes;
  if (!Array.isArray(list)) throw new Error('Recipe JSON has no "dishes" list');
  const out: CloudRecipe[] = [];
  for (const d of list) {
    if (!d || typeof d !== 'object') continue;
    const rec = d as Record<string, unknown>;
    const name = cleanText(rec.name ?? rec.dish, 100);
    if (!name) continue;
    const ingredients: RecipeIngredient[] = [];
    const raw = rec.ingredients ?? rec.typicalIngredients;
    const items = typeof raw === 'string' ? raw.split(/[,;、，；]/) : raw;
    if (Array.isArray(items)) {
      for (const item of items) {
        let n = '';
        let level: RecipeLevel = 'common'; // a bare string has no level: "common" is never Avoid
        if (typeof item === 'string') n = cleanText(item, 60);
        else if (item && typeof item === 'object') {
          const r = item as Record<string, unknown>;
          n = cleanText(r.name ?? r.ingredient ?? r.text, 60);
          level = parseLevel(r.level ?? r.importance ?? r.kind);
        }
        if (!n) continue;
        const dup = ingredients.find((x) => x.name.toLowerCase() === n.toLowerCase());
        if (dup) { if (level === 'essential') dup.level = 'essential'; else if (level === 'common' && dup.level === 'possible') dup.level = 'common'; continue; }
        ingredients.push({ name: n, level });
        if (ingredients.length >= 60) break;
      }
    }
    const ratings = parseRatings(rec.ratings ?? rec.allergens);
    const c = rec.confident ?? rec.confidence;
    const confident = c === true || (typeof c === 'string' && /^(high|medium|yes|true)$/i.test(c));
    out.push({ name, ingredients, ratings, confident: confident && (ingredients.length > 0 || !!ratings) });
  }
  return out;
}

// ---------- matching ----------

function norm(s: string): string {
  return s
    .normalize('NFD').replace(/[̀-ͯ]/g, '').normalize('NFC')
    .toLowerCase()
    .replace(/[-_/]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

const LATIN_ONLY = /^[a-z0-9' ]+$/;
const reCache = new Map<string, RegExp>();

/** True if `term` appears in `text` (whole word for Latin scripts, substring for CJK/Thai). */
export function termMatches(text: string, term: string): boolean {
  const t = norm(term);
  if (!t) return false;
  const hay = norm(text);
  if (!LATIN_ONLY.test(t)) return hay.includes(t);
  let re = reCache.get(t);
  if (!re) {
    const esc = t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    re = new RegExp(`(?<![a-z0-9])${esc}(?:s|es)?(?![a-z0-9])`);
    reCache.set(t, re);
  }
  return re.test(hay);
}

const nfcLower = (s: string) => s.normalize('NFC').toLowerCase().replace(/\s+/g, ' ').trim();
const exactCache = new Map<string, RegExp>();

/** Accent-sensitive whole-word match (Vietnamese "cá" must not match "ca phe"). */
export function exactMatches(text: string, term: string): boolean {
  const t = nfcLower(term);
  if (!t) return false;
  let re = exactCache.get(t);
  if (!re) {
    re = new RegExp(`(?<![\\p{L}\\p{M}])${t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\p{L}\\p{M}])`, 'u');
    exactCache.set(t, re);
  }
  return re.test(nfcLower(text));
}

function stripIgnoredExact(text: string, ignore: string[] | undefined): string {
  let t = nfcLower(text);
  for (const phrase of ignore ?? []) {
    const p = nfcLower(phrase);
    if (p) t = t.split(p).join(' ');
  }
  return t;
}

function stripIgnored(text: string, ignore: string[] | undefined): string {
  let t = norm(text);
  for (const phrase of ignore ?? []) {
    const p = norm(phrase);
    if (p) t = t.split(p).join(' ');
  }
  return t;
}

function listedDefs(list: AllergyList): AllergenDef[] {
  return list.allergens.map((id) => ALLERGEN_BY_ID[id]).filter(Boolean);
}

function directHit(text: string, def: AllergenDef): string | null {
  const cleaned = stripIgnored(text, def.ignore);
  for (const w of def.direct) if (termMatches(cleaned, w)) return w;
  for (const w of def.loose ?? []) { const n = norm(w); if (n && cleaned.includes(n)) return w; }
  if (def.exact?.length) {
    const ex = stripIgnoredExact(text, def.ignore);
    for (const w of def.exact) if (exactMatches(ex, w)) return w;
  }
  return null;
}

// ---------- marking ----------

/** Texts to scan for one dish: its name and every ingredient the menu lists. */
function dishTexts(dish: MenuDish): { text: string; where: string }[] {
  const out = [{ text: dish.name, where: 'dish name' }, ...dish.ingredients.map((i) => ({ text: i, where: 'listed ingredient' }))];
  if (dish.nameEnglish) out.push({ text: dish.nameEnglish, where: 'English dish name' });
  for (const e of dish.ingredientsEnglish ?? []) if (e) out.push({ text: e, where: 'English ingredient' });
  return out;
}

/** Allergen named in the menu text itself -> "Avoid". */
export function checkListed(dish: MenuDish, list: AllergyList, source: Source = 'device'): Finding[] {
  const out: Finding[] = [];
  for (const def of listedDefs(list)) {
    for (const { text, where } of dishTexts(dish)) {
      const hit = directHit(text, def);
      if (hit) {
        out.push({ mark: 'avoid', kind: 'listed', allergen: def.label, source,
          reason: `${def.label} is listed on the menu ("${hit}" in the ${where}).` });
        break;
      }
    }
  }
  for (const word of list.custom) {
    for (const { text, where } of dishTexts(dish)) {
      if (termMatches(text, word)) {
        out.push({ mark: 'avoid', kind: 'listed', allergen: word, source,
          reason: `"${word}" from your list is on the menu (${where}).` });
        break;
      }
    }
  }
  return out;
}

/** Hidden-source table hit -> "Ask the kitchen". Never "Avoid". */
export function checkHidden(dish: MenuDish, list: AllergyList, source: Source = 'device'): Finding[] {
  const out: Finding[] = [];
  for (const def of listedDefs(list)) {
    const texts = dishTexts(dish);
    const found = def.hidden.find((h) => texts.some(({ text }) => termMatches(text, h.term)))
      ?? def.hiddenExact?.find((h) => texts.some(({ text }) => exactMatches(text, h.term)));
    if (found) {
      out.push({ mark: 'ask', kind: 'hidden', allergen: def.label, source,
        reason: `${def.label} may be hidden: ${found.why}.` });
    }
  }
  return out;
}

// ---------- ingredients the app cannot read ----------

/** Languages the built-in word tables cover (English plus ten more). */
export const TABLE_LANG_CODES = ['en', 'zh', 'ja', 'ko', 'th', 'vi', 'es', 'fr', 'it', 'de', 'pt'];

/** True if the text has letters outside the Latin script (Chinese, Thai, Korean, Cyrillic, Arabic...). */
export function hasNonLatinLetters(text: string): boolean {
  return /\p{L}/u.test(text.replace(/\p{Script=Latin}/gu, ''));
}

function langBase(language: string | undefined): string {
  const named = normalizeLang(language);
  if (named) return named;
  return (language ?? '').toLowerCase().trim().slice(0, 2);
}

/**
 * Ingredients the app cannot check: non-Latin script with no English translation, or (when the
 * menu language is one the word tables do not cover) any ingredient with no English translation.
 */
export function untranslatedIngredients(dish: MenuDish, language?: string): string[] {
  const lang = langBase(language);
  const unknownLatin = lang !== '' && !TABLE_LANG_CODES.includes(lang);
  const out: string[] = [];
  dish.ingredients.forEach((ing, i) => {
    const en = dish.ingredientsEnglish?.[i]?.trim() ?? '';
    const hasEnglish = en !== '' && !hasNonLatinLetters(en);
    if (hasEnglish) return;
    if (hasNonLatinLetters(ing) || unknownLatin) out.push(ing);
  });
  return out;
}

function untranslatedFinding(items: string[], source: Source): Finding[] {
  if (items.length === 0) return [];
  const shown = items.slice(0, 3).map((x) => `"${x}"`).join(', ') + (items.length > 3 ? ' and more' : '');
  return [{ mark: 'ask', kind: 'untranslated', allergen: '', source,
    reason: `The app could not translate ${shown}, so it cannot check it against your list. Ask the kitchen what is in this dish.` }];
}

/**
 * The dish NAME itself cannot be read by the word tables: it has no Latin word of 3+ letters and the device gave no
 * Latin English name. Such a dish is at least "Ask the kitchen", whatever the recipe lookup says, because the name is
 * what the recipe lookup and the tables work from.
 */
export function untranslatedDishName(dish: MenuDish): boolean {
  if (!hasNonLatinLetters(dish.name)) return false;
  if (/[A-Za-z]{3,}/.test(dish.name)) return false;
  const en = dish.nameEnglish?.trim() ?? '';
  return !(/[A-Za-z]{3,}/.test(en) && !hasNonLatinLetters(en));
}

/** A dish is "placed" when we have ingredients or a table hit to judge it by. */
export function isPlaced(dish: MenuDish, findings: Finding[]): boolean {
  return dish.ingredients.length > 0 || findings.length > 0;
}

/** Finding for a dish the cloud lookup could not describe (or did not return). */
export function unknownRecipeFinding(source: Source, why?: string): Finding {
  return { mark: 'ask', kind: 'unplaced', allergen: '', source,
    reason: why ?? 'The typical recipe of this dish could not be worked out with confidence. Ask the kitchen what is in it.' };
}

/**
 * The cloud's all-allergen rating, read on the device for the allergens on THIS user's list only.
 *   usually -> Avoid, unless the menu prints ingredients for the dish and none of them (or the hidden-source table)
 *              points to that allergen: a printed list contradicts the guess, so it becomes Ask the kitchen;
 *   often, unknown, or no rating returned for this allergen -> Ask the kitchen;
 *   rarely -> nothing here (the printed-text and recipe results stand).
 */
export function applyRatings(recipe: CloudRecipe, list: AllergyList, source: Source = 'cloud', dish?: MenuDish): Finding[] {
  const out: Finding[] = [];
  for (const def of listedDefs(list)) {
    const r = recipe.ratings?.[def.id] ?? { level: 'unknown' as RatingLevel, why: '' };
    if (r.level === 'rarely') continue;
    const why = r.why ? ` (${r.why})` : '';
    if (r.level === 'usually') {
      const printedClean = !!dish && dish.ingredients.length > 0
        && !checkListed(dish, { allergens: [def.id], custom: [] }).length && !checkHidden(dish, { allergens: [def.id], custom: [] }).length;
      out.push(printedClean
        ? { mark: 'ask', kind: 'rated', allergen: def.label, source,
            reason: `${def.label}: a typical version usually contains it${why}, but the printed ingredients do not show it. Ask the kitchen.` }
        : { mark: 'avoid', kind: 'rated', allergen: def.label, source,
            reason: `${def.label}: this dish usually contains it${why}.` });
    } else if (r.level === 'often') {
      out.push({ mark: 'ask', kind: 'rated', allergen: def.label, source,
        reason: `${def.label}: common versions of this dish contain it${why}.` });
    } else {
      out.push({ mark: 'ask', kind: 'rated', allergen: def.label, source,
        reason: `${def.label}: the cloud lookup could not say whether this dish contains it${why}. Ask the kitchen.` });
    }
  }
  return out;
}

/**
 * Match a cloud recipe against the saved list and the hidden-source tables, on the device.
 * Label rule: "Avoid" only when the allergen is an ESSENTIAL ingredient of the dish; a "common" or
 * "possible" ingredient, or a hidden-source table hit, gives "Ask the kitchen". Never "No listed
 * allergen found" unless the recipe is confident and nothing from the list appears in it.
 */
export function applyRecipe(recipe: CloudRecipe | undefined, list: AllergyList, source: Source = 'cloud', dish?: MenuDish): Finding[] {
  if (!recipe || !recipe.confident) return [unknownRecipeFinding(source)];
  const out: Finding[] = [...applyRatings(recipe, list, source, dish)];
  const unread = recipe.ingredients.filter((i) => hasNonLatinLetters(i.name)).map((i) => i.name);
  out.push(...untranslatedFinding(unread, source));
  for (const ing of recipe.ingredients) {
    const asDish: MenuDish = { name: '', ingredients: [ing.name] };
    for (const f of checkListed(asDish, list, source)) {
      const essential = ing.level === 'essential';
      out.push({ ...f, mark: essential ? 'avoid' : 'ask', kind: 'typical',
        reason: essential
          ? `${f.allergen}: ${ing.name} is an essential part of a typical recipe for this dish.`
          : `${f.allergen}: ${ing.name} is ${ing.level === 'common' ? 'commonly' : 'sometimes'} in this dish (a typical recipe, not the menu).` });
    }
    for (const f of checkHidden(asDish, list, source)) {
      out.push({ ...f, mark: 'ask', kind: 'typical', reason: `${f.reason.replace(/\.$/, '')} (found in a typical recipe: ${ing.name}).` });
    }
  }
  if (out.length === 0) {
    out.push({ mark: 'no_listed', kind: 'placed', allergen: '', source,
      reason: 'No allergen from your list appears in the typical recipe.' });
  }
  return out;
}

/** Merge findings into one decision: strictest mark wins; its source is shown. */
export function mergeMarks(findings: Finding[]): Decision {
  if (findings.length === 0) {
    return { mark: 'ask', source: 'device', findings: [{ mark: 'ask', kind: 'unplaced', allergen: '', source: 'device',
      reason: 'Nothing was checked for this dish.' }] };
  }
  let best = findings[0];
  for (const f of findings) if (SEVERITY[f.mark] > SEVERITY[best.mark]) best = f;
  // With no concern raised, show where the dish was placed: cloud if the cloud supplied the ingredients.
  const source: Source = best.mark === 'no_listed' && findings.some((f) => f.source === 'cloud') ? 'cloud' : best.source;
  return { mark: best.mark, source, findings };
}

/** First-pass marks for a dish read from the photo (device only). */
export function firstPass(dish: MenuDish, list: AllergyList, language?: string): Finding[] {
  const findings = [...checkListed(dish, list), ...checkHidden(dish, list), ...untranslatedFinding(untranslatedIngredients(dish, language), 'device')];
  if (untranslatedDishName(dish)) {
    findings.push({ mark: 'ask', kind: 'untranslated', allergen: '', source: 'device',
      reason: `The app could not translate the dish name "${dish.name}", so it cannot check it against your list. Ask the kitchen what is in this dish.` });
  }
  const variable = variableDishWord(dish.name, dish.nameEnglish);
  if (variable) {
    findings.push({ mark: 'ask', kind: 'variable', allergen: '', source: 'device',
      reason: `"${dish.name}" changes from day to day or cook to cook ("${variable}"), so no recipe can be trusted. Ask the kitchen what is in it today.` });
  }
  if (findings.length === 0 && dish.ingredients.length > 0) {
    findings.push({ mark: 'no_listed', kind: 'placed', allergen: '', source: 'device',
      reason: 'No allergen from your list appears in the menu text.' });
  }
  return findings;
}

// ---------- cloud payload ----------

/**
 * The fixed list of allergen categories asked about in EVERY request: all 19 the app supports, the same for every user.
 * Asking about all of them reveals nothing about any one user's list. Ids are the reply keys.
 */
export const CLOUD_ALLERGEN_IDS: readonly AllergenId[] = ALLERGENS.map((a) => a.id);
const CLOUD_ALLERGEN_TEXT = ALLERGENS.map((a) => `${a.id} (${a.label})`).join('; ');

/**
 * The words sent to the cloud model. They are the same for every user: the fixed list of all allergen categories
 * plus the dish names. They never name a person, a diet or a saved list.
 */
export const CLOUD_INSTRUCTION =
  'You help with restaurant menus. For each dish below, give the typical recipe of a standard version of the dish. ' +
  'Include every ingredient, also in sauces, marinades, batters, doughs, wrappers, fillings, glazes, stocks, oils and garnishes, ' +
  'and the ingredients of common regional and restaurant variants. ' +
  'Do not stop at the main ingredients. Also list, one by one: ' +
  '(1) the sauce or seasoning the dish is cooked, simmered or marinated in, written as its own ingredients (never just the word "sauce"); ' +
  '(2) every dip, table sauce and condiment that is usually served with the dish or offered at the table; ' +
  '(3) every filling, paste and spice mix; ' +
  '(4) everything sprinkled on top of the dish, baked into it or brushed on it, and the usual side garnishes. ' +
  'List one ingredient per item, in English. ' +
  'Give each ingredient a level: "essential" (without it the dish is not this dish), "common" (most recipes include it), ' +
  'or "possible" (some variants or cooks add it, or it is served on the side). ' +
  'Then rate EVERY dish for EVERY one of these allergen categories, with no category left out: ' + CLOUD_ALLERGEN_TEXT + '. ' +
  'Rating: "usually" (the standard version contains it), "often" (it is in common versions or common variants, ' +
  'for example in the bun, batter, breading, sauce, stock, glaze, topping or dressing of one common version), ' +
  '"rarely" (only an unusual version would contain it), or "unknown" (you cannot tell). ' +
  'Think about the common variants, not only one recipe. A dish that changes each day or by cook, such as a soup of the day, is "unknown". ' +
  'For "usually", "often" and "unknown" give the main reason in a few words. ' +
  'Each dish is given as {"name": the name as printed, "english": an English name, optional}. ' +
  'Reply with JSON only: {"dishes":[{"name":string,"confident":boolean,"ingredients":[{"name":string,"level":"essential"|"common"|"possible"}],' +
  '"ratings":[{"allergen":string (one of the ids above),"rating":"usually"|"often"|"rarely"|"unknown","why":string}]}]}. ' +
  'Copy "name" exactly as given. Set confident to false if you do not know the dish.';

export interface CloudDish { name: string; nameEnglish?: string }

export interface CloudPayload {
  /** The only user data in the request: every dish name sent (printed names and English names). */
  dishNames: string[];
  /** The dishes in the request, in order. */
  dishes: { name: string; english?: string }[];
  /** The exact text sent to the cloud model. */
  prompt: string;
}

const BASE64ISH = /[A-Za-z0-9+/=_-]{60,}/;

function cleanDishName(n: string): string {
  const t = cleanText(n, 80);
  if (!t || /^data:/i.test(t) || BASE64ISH.test(t) || /^https?:/i.test(t)) return '';
  return t;
}

/** Clean dish names for sending. Drops anything that looks like image data. */
export function sanitizeDishNames(names: string[]): string[] {
  const out: string[] = [];
  for (const n of names) {
    const t = cleanDishName(n);
    if (t && !out.includes(t)) out.push(t);
    if (out.length >= 60) break;
  }
  return out;
}

/**
 * Build the ONE cloud request from dish names only: the name as printed plus the English name.
 * The function takes no allergy list, no ingredients and no image by design, so none can leak.
 */
export function buildCloudPayload(input: (string | CloudDish)[]): CloudPayload {
  const dishes: { name: string; english?: string }[] = [];
  for (const d of input) {
    const dish = typeof d === 'string' ? { name: d } : d;
    const name = cleanDishName(dish.name);
    if (!name || dishes.some((x) => x.name.toLowerCase() === name.toLowerCase())) continue;
    const english = cleanDishName(dish.nameEnglish ?? '');
    dishes.push(english && english.toLowerCase() !== name.toLowerCase() ? { name, english } : { name });
    if (dishes.length >= 60) break;
  }
  const dishNames = sanitizeDishNames(dishes.flatMap((d) => (d.english ? [d.name, d.english] : [d.name])));
  const prompt = `${CLOUD_INSTRUCTION}\n\nDishes:\n${JSON.stringify(dishes)}`;
  return { dishNames, dishes, prompt };
}

// ---------- waiter question ----------

export type LangCode = 'en' | 'zh' | 'es' | 'fr' | 'it' | 'ja' | 'th';
export const LANGUAGES: { code: LangCode; name: string }[] = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'it', name: 'Italiano' },
  { code: 'ja', name: '日本語' },
  { code: 'th', name: 'ไทย' },
];

const NAMES: Record<LangCode, Record<AllergenId, string>> = {
  en: { peanut: 'peanuts', tree_nut: 'tree nuts (almond, cashew, walnut, pistachio...)', milk: 'milk and dairy', egg: 'egg', wheat: 'wheat and gluten (barley, rye, oats)', soy: 'soy', fish: 'fish', crustacean: 'crustaceans (shrimp, prawn, crab, lobster)', mollusc: 'molluscs (squid, octopus, clam, mussel, oyster, snail)', sesame: 'sesame', celery: 'celery', mustard: 'mustard', lupin: 'lupin', sulphites: 'sulphites (sulfites)', buckwheat: 'buckwheat', kiwi: 'kiwi', banana: 'banana', peach: 'peach', corn: 'corn (maize)' },
  zh: { peanut: '花生', tree_nut: '树坚果（杏仁、腰果、核桃等）', milk: '牛奶和乳制品', egg: '鸡蛋', wheat: '小麦和麸质（大麦、黑麦、燕麦）', soy: '大豆', fish: '鱼', crustacean: '甲壳类（虾、蟹、龙虾）', mollusc: '软体动物（鱿鱼、章鱼、蛤蜊、贻贝、牡蛎、蜗牛）', sesame: '芝麻', celery: '芹菜', mustard: '芥末籽（芥子）', lupin: '羽扇豆', sulphites: '亚硫酸盐', buckwheat: '荞麦', kiwi: '猕猴桃（奇异果）', banana: '香蕉', peach: '桃子', corn: '玉米' },
  es: { peanut: 'cacahuetes', tree_nut: 'frutos secos (almendra, anacardo, nuez, pistacho...)', milk: 'leche y lácteos', egg: 'huevo', wheat: 'trigo y gluten (cebada, centeno, avena)', soy: 'soja', fish: 'pescado', crustacean: 'crustáceos (gambas, langostinos, cangrejo, langosta)', mollusc: 'moluscos (calamar, pulpo, almejas, mejillones, ostras, caracoles)', sesame: 'sésamo', celery: 'apio', mustard: 'mostaza', lupin: 'altramuces', sulphites: 'sulfitos', buckwheat: 'trigo sarraceno', kiwi: 'kiwi', banana: 'plátano (banana)', peach: 'melocotón', corn: 'maíz' },
  fr: { peanut: 'arachides', tree_nut: 'fruits à coque (amande, noix de cajou, noix, pistache...)', milk: 'lait et produits laitiers', egg: 'œuf', wheat: 'blé et gluten (orge, seigle, avoine)', soy: 'soja', fish: 'poisson', crustacean: 'crustacés (crevettes, crabe, homard, langoustines)', mollusc: 'mollusques (calmar, poulpe, palourdes, moules, huîtres, escargots)', sesame: 'sésame', celery: 'céleri', mustard: 'moutarde', lupin: 'lupin', sulphites: 'sulfites', buckwheat: 'sarrasin', kiwi: 'kiwi', banana: 'banane', peach: 'pêche', corn: 'maïs' },
  it: { peanut: 'arachidi', tree_nut: 'frutta a guscio (mandorle, anacardi, noci, pistacchi...)', milk: 'latte e latticini', egg: 'uova', wheat: 'frumento e glutine (orzo, segale, avena)', soy: 'soia', fish: 'pesce', crustacean: 'crostacei (gamberi, granchio, aragosta)', mollusc: 'molluschi (calamari, polpo, vongole, cozze, ostriche, lumache)', sesame: 'sesamo', celery: 'sedano', mustard: 'senape', lupin: 'lupini', sulphites: 'solfiti', buckwheat: 'grano saraceno', kiwi: 'kiwi', banana: 'banana', peach: 'pesca', corn: 'mais' },
  ja: { peanut: 'ピーナッツ', tree_nut: 'ナッツ類（アーモンド、カシューナッツ、くるみ等）', milk: '乳製品', egg: '卵', wheat: '小麦（グルテン、大麦、ライ麦、オーツ麦）', soy: '大豆', fish: '魚', crustacean: '甲殻類（えび・かに）', mollusc: '軟体動物（いか・たこ・貝類）', sesame: 'ごま', celery: 'セロリ', mustard: 'からし（マスタード）', lupin: 'ルピナス', sulphites: '亜硫酸塩', buckwheat: 'そば', kiwi: 'キウイ', banana: 'バナナ', peach: 'もも', corn: 'とうもろこし' },
  th: { peanut: 'ถั่วลิสง', tree_nut: 'ถั่วเปลือกแข็ง (อัลมอนด์ เม็ดมะม่วง วอลนัท พิสตาชิโอ)', milk: 'นมและผลิตภัณฑ์จากนม', egg: 'ไข่', wheat: 'ข้าวสาลีและกลูเตน (บาร์เลย์ ไรย์ ข้าวโอ๊ต)', soy: 'ถั่วเหลือง', fish: 'ปลา', crustacean: 'สัตว์น้ำเปลือกแข็ง (กุ้ง ปู)', mollusc: 'หอยและหมึก (หอย ปลาหมึก หมึกยักษ์)', sesame: 'งา', celery: 'ขึ้นฉ่าย (เซเลอรี่)', mustard: 'มัสตาร์ด', lupin: 'ลูพิน', sulphites: 'ซัลไฟต์', buckwheat: 'บัควีท (โซบะ)', kiwi: 'กีวี', banana: 'กล้วย', peach: 'พีช (ท้อ)', corn: 'ข้าวโพด' },
};

const TEMPLATE: Record<LangCode, (items: string, dishes: string) => string> = {
  en: (i, d) => `I have a serious allergy to: ${i}. ${d ? `Please check these dishes: ${d}. ` : ''}Do the dishes I am asking about contain any of these, including in sauces, oils, stock or shared cooking surfaces?`,
  zh: (i, d) => `我对以下食物严重过敏：${i}。${d ? `请帮我确认这些菜：${d}。` : ''}我要点的菜里是否含有这些成分？包括酱汁、食用油、汤底，或使用了同一块砧板和炒锅？`,
  es: (i, d) => `Tengo una alergia grave a: ${i}. ${d ? `Por favor, revise estos platos: ${d}. ` : ''}¿Contienen alguno de estos ingredientes, incluso en salsas, aceites, caldos o por contacto en la cocina?`,
  fr: (i, d) => `J'ai une allergie grave à : ${i}. ${d ? `Pouvez-vous vérifier ces plats : ${d}. ` : ''}Contiennent-ils l'un de ces ingrédients, y compris dans les sauces, les huiles, les bouillons ou par contact en cuisine ?`,
  it: (i, d) => `Ho una grave allergia a: ${i}. ${d ? `Può controllare questi piatti: ${d}. ` : ''}Contengono uno di questi ingredienti, anche nelle salse, negli oli, nei brodi o per contatto in cucina?`,
  ja: (i, d) => `私は次の食べ物に重いアレルギーがあります：${i}。${d ? `次の料理を確認してください：${d}。` : ''}ソース、油、だし、同じ調理器具を使う場合も含めて、これらは入っていますか？`,
  th: (i, d) => `ฉันแพ้อาหารอย่างรุนแรง: ${i} ${d ? `ช่วยตรวจสอบเมนูเหล่านี้: ${d} ` : ''}เมนูที่ถามมีส่วนผสมเหล่านี้หรือไม่ รวมถึงในซอส น้ำมัน น้ำซุป หรืออุปกรณ์ปรุงอาหารที่ใช้ร่วมกัน`,
};

/** Map a model- or browser-reported language ("zh-TW", "Thai", "ja") to a supported code. */
export function normalizeLang(raw: string | undefined | null): LangCode | null {
  if (!raw) return null;
  const s = raw.toLowerCase().trim();
  const table: [RegExp, LangCode][] = [
    [/^(en|english)/, 'en'], [/^(zh|chinese|cantonese|mandarin|中文|汉语|漢語)/, 'zh'], [/^(es|spanish|español|espanol)/, 'es'],
    [/^(fr|french|français|francais)/, 'fr'], [/^(it|italian|italiano)/, 'it'], [/^(ja|japanese|日本語)/, 'ja'], [/^(th|thai|ไทย)/, 'th'],
  ];
  for (const [re, code] of table) if (re.test(s)) return code;
  return null;
}

/** The question for the waiter, written from the saved list in a supported language. */
export function buildWaiterQuestion(list: AllergyList, lang: LangCode, dishNames: string[] = []): string {
  const names = NAMES[lang];
  const items = [...list.allergens.map((id) => names[id]), ...list.custom].filter(Boolean);
  const joiner = lang === 'zh' || lang === 'ja' ? '、' : ', ';
  const dishes = dishNames.filter(Boolean).map((n) => `"${n}"`).join(joiner);
  return TEMPLATE[lang](items.join(joiner), dishes);
}

export const ALL_ALLERGEN_IDS: AllergenId[] = ALLERGENS.map((a) => a.id);

// ---------- saved-list migration and names ----------

/**
 * Bring an older saved list up to date. The old "shellfish" item becomes both Crustaceans and
 * Molluscs (the safer side). Unknown ids are dropped. Returns null if the value is not a list.
 */
export function migrateList(raw: unknown): AllergyList | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as { allergens?: unknown; custom?: unknown };
  if (!Array.isArray(r.allergens) || !Array.isArray(r.custom)) return null;
  const out: AllergenId[] = [];
  const add = (id: string) => { if (id in ALLERGEN_BY_ID && !out.includes(id as AllergenId)) out.push(id as AllergenId); };
  for (const id of r.allergens) {
    if (typeof id !== 'string') continue;
    if (id === 'shellfish') { add('crustacean'); add('mollusc'); } else add(id);
  }
  return { allergens: out, custom: r.custom.filter((c): c is string => typeof c === 'string') };
}

/** Allergen ids for a plain name such as "tree nut", "wheat/gluten" or "shellfish" (kit profile names). */
export function allergenIdsFromName(name: string): AllergenId[] {
  const n = name.toLowerCase().trim().replace(/[\s_-]+/g, ' ');
  const table: [RegExp, AllergenId[]][] = [
    [/^shellfish$/, ['crustacean', 'mollusc']],
    [/^(crustacean|crustaceans)$/, ['crustacean']],
    [/^(mollusc|molluscs|mollusk|mollusks)$/, ['mollusc']],
    [/^tree ?nuts?$/, ['tree_nut']],
    [/^wheat( ?\/ ?gluten)?$|^gluten$/, ['wheat']],
    [/^(sulphites?|sulfites?)$/, ['sulphites']],
    [/^(corn|maize)$/, ['corn']],
  ];
  for (const [re, ids] of table) if (re.test(n)) return ids;
  if (n in ALLERGEN_BY_ID) return [n as AllergenId];
  throw new Error(`Unknown allergen name: ${name}`);
}
