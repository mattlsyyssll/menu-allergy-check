// Round 4: all-allergen rating, variable dishes, timeouts with one retry.
import { describe, expect, it } from 'vitest';
import {
  applyRatings, applyRecipe, CLOUD_ALLERGEN_IDS, firstPass, mergeMarks, parseRecipesJson, type AllergyList, type CloudRecipe,
} from '../src/core/core';
import { runCheck, withTimeoutRetry, DEVICE_TIMEOUT_MS, CLOUD_TIMEOUT_MS, type AttemptEvent, type CloudEngine, type DeviceEngine } from '../src/pipeline';
import { variableDishWord } from '../src/core/variable';

const L = (...allergens: AllergyList['allergens']): AllergyList => ({ allergens, custom: [] });
const rec = (ratings: CloudRecipe['ratings'], ingredients: CloudRecipe['ingredients'] = [{ name: 'rice', level: 'essential' }]): CloudRecipe =>
  ({ name: 'x', confident: true, ingredients, ratings });

describe('parsing the all-allergen rating', () => {
  it('reads a ratings list, normalises words and category names, keeps the stricter of a repeated category', () => {
    const [r] = parseRecipesJson(JSON.stringify({ dishes: [{ name: 'Burger', confident: true, ingredients: [{ name: 'beef', level: 'essential' }], ratings: [
      { allergen: 'sesame', rating: 'often', why: 'seeded bun' }, { allergen: 'Tree nuts', rating: 'Usually contains', why: '' },
      { allergen: 'milk', rating: 'rarely' }, { allergen: 'milk', rating: 'usually' }, { allergen: 'egg', rating: 'maybe?' }, { allergen: 'plutonium', rating: 'usually' },
    ] }] }));
    expect(r.ratings!.sesame).toEqual({ level: 'often', why: 'seeded bun' });
    expect(r.ratings!.tree_nut!.level).toBe('usually');
    expect(r.ratings!.milk!.level).toBe('usually');
    expect(r.ratings!.egg!.level).toBe('unknown');
    expect(Object.keys(r.ratings!)).not.toContain('plutonium');
  });
  it('a dish with ratings and no ingredient list is still usable; no ratings and no ingredients is not confident', () => {
    const ok = parseRecipesJson('{"dishes":[{"name":"A","confident":true,"ratings":[{"allergen":"soy","rating":"rarely"}]}]}');
    expect(ok[0].confident).toBe(true);
    expect(parseRecipesJson('{"dishes":[{"name":"A","confident":true}]}')[0].confident).toBe(false);
  });
  it('the fixed list has all 19 categories', () => {
    expect(CLOUD_ALLERGEN_IDS).toHaveLength(19);
  });
});

describe('device reads only the user\'s allergens', () => {
  it('usually -> Avoid; often -> Ask; unknown or missing -> Ask; rarely -> keeps the clean result', () => {
    const r = rec({ sesame: { level: 'usually', why: 'bun' }, milk: { level: 'often', why: '' }, egg: { level: 'unknown', why: '' }, soy: { level: 'rarely', why: '' } });
    const m = (...ids: AllergyList['allergens']) => mergeMarks(applyRecipe(r, L(...ids))).mark;
    expect(m('sesame')).toBe('avoid');
    expect(m('milk')).toBe('ask');
    expect(m('egg')).toBe('ask');
    expect(m('fish')).toBe('ask'); // no rating returned for fish
    expect(m('soy')).toBe('no_listed');
    expect(m('soy', 'milk')).toBe('ask'); // the stricter allergen wins
  });
  it('usually is contradicted by printed ingredients that do not show it: Ask, not Avoid and not No listed', () => {
    const r = rec({ sesame: { level: 'usually', why: 'seeded bun' } });
    const printed = { name: 'Cheeseburger', ingredients: ['beef patty', 'cheddar', 'lettuce'] };
    const f = applyRatings(r, L('sesame'), 'cloud', printed);
    expect(f).toHaveLength(1);
    expect(f[0].mark).toBe('ask');
    // printed ingredients that DO show it keep Avoid
    expect(applyRatings(r, L('sesame'), 'cloud', { name: 'Bun', ingredients: ['sesame bun'] })[0].mark).toBe('avoid');
    // a menu that prints nothing cannot contradict
    expect(applyRatings(r, L('sesame'), 'cloud', { name: 'Cheeseburger', ingredients: [] })[0].mark).toBe('avoid');
  });
  it('the stricter of printed text and rating wins: a printed allergen stays Avoid when the rating says rarely', () => {
    const printed = firstPass({ name: 'Pad Thai', ingredients: ['peanuts'] }, L('peanut'));
    const all = [...printed, ...applyRecipe(rec({ peanut: { level: 'rarely', why: '' } }), L('peanut'), 'cloud', { name: 'Pad Thai', ingredients: ['peanuts'] })];
    expect(mergeMarks(all).mark).toBe('avoid');
  });
  it('the reason of the rating is shown', () => {
    const f = applyRatings(rec({ sesame: { level: 'often', why: 'seeded bun' } }), L('sesame'));
    expect(f[0].reason).toContain('seeded bun');
  });
});

describe('variable dishes are at least Ask the kitchen', () => {
  const names = [
    'Soup of the day', 'Zuppa del Giorno', 'Soupe du jour', 'Chef\'s special', 'Seasonal vegetables', 'Market fish', 'Daily catch', 'House salad', 'Today\'s special',
    'Sopa del día', 'Plato del chef', 'Sopa de temporada', 'Prato do dia', 'Sopa da casa', 'Tagessuppe', 'Suppe des Tages', 'Zuppa di stagione', 'Menu du chef',
    '今日例湯', '本日のスープ', '日替わりランチ', '오늘의 수프', 'ซุปประจำวัน', 'Canh của ngày', 'Món đặc biệt', '时令蔬菜', '主厨推介',
  ];
  it.each(names)('%s', (n) => {
    expect(variableDishWord(n), n).not.toBeNull();
    // Ask even when the list is empty of matching words and the menu prints a clean ingredient list
    const f = firstPass({ name: n, nameEnglish: 'Dish', ingredients: ['water'], ingredientsEnglish: ['water'] }, L('peanut'));
    expect(mergeMarks(f).mark, n).toBe('ask');
    expect(f.some((x) => x.kind === 'variable')).toBe(true);
  });
  it('ordinary dishes and look-alike words are not variable', () => {
    for (const n of ['Pad Thai', 'Seasoned fries', 'Chicken Satay', 'Grilled Salmon', 'Marketplace burger deluxe'.replace('Marketplace', 'Hamburg')]) expect(variableDishWord(n), n).toBeNull();
  });
  it('the English name counts too', () => {
    expect(variableDishWord('ซุป', 'Soup of the day')).not.toBeNull();
  });
  it('the cloud cannot lower it', async () => {
    const device: DeviceEngine = { readMenu: async () => JSON.stringify({ language: 'it', dishes: [{ name: 'Zuppa del Giorno', nameEnglish: 'Soup of the day', ingredients: [] }] }) };
    const cloud: CloudEngine = { recipes: async () => JSON.stringify({ dishes: [{ name: 'Zuppa del Giorno', confident: true, ingredients: [{ name: 'water', level: 'essential' }],
      ratings: CLOUD_ALLERGEN_IDS.map((allergen) => ({ allergen, rating: 'rarely', why: '' })) }] }) };
    const s = await runCheck({ imageDataUrl: 'data:image/jpeg;base64,QUJD', list: L('milk'), device, cloud });
    expect(s.dishes[0].decision!.mark).toBe('ask');
  });
});

describe('timeouts and one retry', () => {
  const IMG = 'data:image/jpeg;base64,QUJD';
  const menu = JSON.stringify({ language: 'en', dishes: [{ name: 'Plain Rice', nameEnglish: 'Plain Rice', ingredients: ['rice'] }, { name: 'Soup', ingredients: [] }, { name: 'Green Tea', ingredients: [] }] });
  const cloudOk = JSON.stringify({ dishes: [{ name: 'Plain Rice', confident: true, ingredients: [{ name: 'rice', level: 'essential' }],
    ratings: CLOUD_ALLERGEN_IDS.map((allergen) => ({ allergen, rating: 'rarely', why: '' })) }] });
  const hang = () => new Promise<never>(() => { /* never settles */ });

  it('defaults: device 90 s, cloud 45 s', () => {
    expect(DEVICE_TIMEOUT_MS).toBe(90_000);
    expect(CLOUD_TIMEOUT_MS).toBe(45_000);
  });
  it('withTimeoutRetry: a hang is cut at the timeout, retried once, and recorded', async () => {
    const events: AttemptEvent[] = [];
    let calls = 0;
    const v = await withTimeoutRetry('cloud', async () => { calls++; return calls === 1 ? hang() : 'ok'; }, 30, 1, events);
    expect(v).toBe('ok');
    expect(calls).toBe(2);
    expect(events).toHaveLength(1);
    expect(events[0]).toMatchObject({ step: 'cloud', attempt: 1, kind: 'timeout' });
  });
  it('withTimeoutRetry: two failures throw the last one after exactly two attempts', async () => {
    const events: AttemptEvent[] = [];
    let calls = 0;
    await expect(withTimeoutRetry('device', async () => { calls++; throw new Error('boom ' + calls); }, 30, 1, events)).rejects.toThrow('boom 2');
    expect(calls).toBe(2);
    expect(events.map((e) => e.kind)).toEqual(['error', 'error']);
  });
  it('a hung cloud call: timed out, retried once, then every dish that is not Avoid is Ask the kitchen with a clear message', async () => {
    let cloudCalls = 0;
    const device: DeviceEngine = { readMenu: async () => menu };
    const cloud: CloudEngine = { recipes: () => { cloudCalls++; return hang(); } };
    const s = await runCheck({ imageDataUrl: IMG, list: L('peanut'), device, cloud, cloudTimeoutMs: 40, deviceTimeoutMs: 40 });
    expect(cloudCalls).toBe(2);
    expect(s.events.filter((e) => e.step === 'cloud' && e.kind === 'timeout')).toHaveLength(2);
    expect(s.cloudLog[0].outcome).toBe('failed');
    expect(s.dishes.map((d) => d.decision!.mark)).toEqual(['ask', 'ask', 'ask']); // Plain Rice has clean printed ingredients but is still Ask
    expect(s.message).toMatch(/cloud recipe step failed/);
    expect(s.warnings[0]).toMatch(/timed out/);
    expect(s.stage).toBe('done');
  });
  it('a cloud call that hangs once then answers: one retry, normal result', async () => {
    let calls = 0;
    const device: DeviceEngine = { readMenu: async () => menu };
    const cloud: CloudEngine = { recipes: () => (++calls === 1 ? hang() : Promise.resolve(cloudOk)) };
    const s = await runCheck({ imageDataUrl: IMG, list: L('peanut'), device, cloud, cloudTimeoutMs: 40 });
    expect(calls).toBe(2);
    expect(s.events).toHaveLength(1);
    expect(s.dishes[0].decision!.mark).toBe('no_listed');
    expect(s.warnings).toEqual([]);
  });
  it('a hung device read with no dish seen yet: clear error, two tries', async () => {
    let calls = 0;
    const device: DeviceEngine = { readMenu: () => { calls++; return hang(); } };
    const s = await runCheck({ imageDataUrl: IMG, list: L('peanut'), device, deviceTimeoutMs: 40 });
    expect(calls).toBe(2);
    expect(s.stage).toBe('error');
    expect(s.error).toMatch(/did not answer in time/);
    expect(s.events.filter((e) => e.kind === 'timeout')).toHaveLength(2);
  });
  it('a hung device read after some dishes were seen: those dishes are all Ask the kitchen', async () => {
    const device: DeviceEngine = { readMenu: (_i, onPartial) => { onPartial?.(menu.slice(0, menu.indexOf('"Soup"') - 3)); return hang(); } };
    const s = await runCheck({ imageDataUrl: IMG, list: L('peanut'), device, deviceTimeoutMs: 40 });
    expect(s.dishes.length).toBeGreaterThan(0);
    expect(s.dishes.every((d) => d.decision?.mark === 'ask' && d.state === 'done')).toBe(true);
    expect(s.stage).toBe('done');
    expect(s.message).toMatch(/Ask the kitchen/);
  });
  it('a late answer from a timed-out device attempt does not change the result', async () => {
    let calls = 0;
    const device: DeviceEngine = { readMenu: () => (++calls === 1 ? new Promise((r) => setTimeout(() => r('garbage'), 80)) : Promise.resolve(menu)) };
    const s = await runCheck({ imageDataUrl: IMG, list: L('peanut'), device, deviceTimeoutMs: 30 });
    expect(s.dishes).toHaveLength(3);
    await new Promise((r) => setTimeout(r, 120));
    expect(s.dishes).toHaveLength(3);
  });
});
