import { describe, expect, it } from 'vitest';
import { runCheck, type CloudEngine, type DeviceEngine } from '../src/pipeline';
import { CLOUD_INSTRUCTION, CLOUD_ALLERGEN_IDS, type AllergyList, type CloudPayload } from '../src/core/core';

const IMAGE = 'data:image/jpeg;base64,' + 'QUJD'.repeat(200);
const list: AllergyList = { allergens: ['peanut', 'crustacean', 'wheat'], custom: ['kiwi'] };

const menuReply = JSON.stringify({
  language: 'th',
  dishes: [
    { name: 'Pad Thai', nameEnglish: 'Pad Thai', ingredients: [{ text: 'noodles', english: 'noodles' }, { text: 'peanuts', english: 'peanuts' }] },
    { name: 'Chicken Satay', ingredients: [] },
    { name: 'Grilled Salmon', ingredients: ['salmon', 'rice'] },
    { name: 'Khao Soi', nameEnglish: 'Northern curry soup', ingredients: [] },
    { name: 'Gaeng Som', ingredients: [] },
    { name: 'Plain Rice', ingredients: ['rice'] },
  ],
});

type R = { name: string; confident: boolean; ingredients: [string, string][]; ratings?: Record<string, string> };
const DEFAULT_RECIPES: R[] = [
  { name: 'Pad Thai', confident: true, ingredients: [['rice noodles', 'essential'], ['peanuts', 'essential']] },
  { name: 'Chicken Satay', confident: true, ingredients: [['chicken', 'essential'], ['peanut sauce', 'essential']] },
  { name: 'Grilled Salmon', confident: true, ingredients: [['salmon', 'essential'], ['soy sauce', 'common']] }, // soy sauce hides wheat
  { name: 'Khao Soi', confident: true, ingredients: [['egg noodles', 'common'], ['coconut milk', 'essential'], ['peanuts', 'possible']] },
  { name: 'Gaeng Som', confident: true, ingredients: [['fish', 'essential'], ['tamarind', 'essential']] },
  { name: 'Plain Rice', confident: true, ingredients: [['rice', 'essential']] },
];

function fakes(opts: { cloudFails?: boolean; recipes?: R[]; reply?: string } = {}) {
  const deviceCalls: string[] = [];
  const cloudPayloads: CloudPayload[] = [];
  const device: DeviceEngine = {
    async readMenu(img) { deviceCalls.push('read:' + img.length); return opts.reply ?? menuReply; },
  };
  const cloud: CloudEngine = {
    async recipes(payload) {
      cloudPayloads.push(payload);
      if (opts.cloudFails) throw new Error('boom');
      return JSON.stringify({ dishes: (opts.recipes ?? DEFAULT_RECIPES).map((r) => ({
        name: r.name, confident: r.confident, ingredients: r.ingredients.map(([name, level]) => ({ name, level })),
        // all 19 categories, "rarely" unless the test says otherwise (the real cloud model rates every one)
        ratings: CLOUD_ALLERGEN_IDS.map((allergen) => ({ allergen, rating: r.ratings?.[allergen] ?? 'rarely', why: 'test' })) })) });
    },
  };
  return { device, cloud, deviceCalls, cloudPayloads };
}

const mark = (s: Awaited<ReturnType<typeof runCheck>>, name: string) => s.dishes.find((d) => d.dish.name === name)!.decision!;

describe('pipeline with the cloud recipe lookup', () => {
  it('sends ONE request with ALL dish names, printed and English, even dishes that have printed ingredients', async () => {
    const f = fakes();
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(f.cloudPayloads).toHaveLength(1);
    expect(f.cloudPayloads[0].dishNames).toEqual(['Pad Thai', 'Chicken Satay', 'Grilled Salmon', 'Khao Soi', 'Northern curry soup', 'Gaeng Som', 'Plain Rice']);
    expect(s.cloudLog).toHaveLength(1);
    expect(s.cloudLog[0].prompt).toBe(f.cloudPayloads[0].prompt);
    expect(s.cloudLog[0].dishNames).toEqual(f.cloudPayloads[0].dishNames);
    expect(s.cloudLog[0].outcome).toBe('answered');
  });

  it('the request holds only the fixed instruction and dish names: no list, no image, no per-dish hints', async () => {
    const f = fakes();
    await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    const p = f.cloudPayloads[0];
    // Remove the fixed instruction and every dish name: nothing else may remain except JSON punctuation and keys.
    let rest = p.prompt.replace(CLOUD_INSTRUCTION, '');
    for (const n of [...p.dishNames].sort((a, b) => b.length - a.length)) rest = rest.split(JSON.stringify(n)).join('');
    expect(rest.replace(/"name"|"english"|Dishes:|[\s:,{}[\]]/g, '')).toBe('');
    const text = JSON.stringify(p).toLowerCase();
    for (const w of ['peanut allergy', 'my allerg', 'data:image', 'qujd', 'my child']) expect(text).not.toContain(w);
    expect(Object.keys(p).sort()).toEqual(['dishNames', 'dishes', 'prompt']);
  });

  it('the cloud request is byte-identical for two users with different lists', async () => {
    const a = fakes(); const b = fakes();
    await runCheck({ imageDataUrl: IMAGE, list, device: a.device, cloud: a.cloud });
    await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['sesame', 'milk', 'egg', 'fish', 'soy'], custom: ['durian', 'my son tom'] }, device: b.device, cloud: b.cloud });
    expect(a.cloudPayloads).toHaveLength(1);
    expect(b.cloudPayloads).toHaveLength(1);
    expect(b.cloudPayloads[0].prompt).toBe(a.cloudPayloads[0].prompt);
    expect(JSON.stringify(b.cloudPayloads[0])).toBe(JSON.stringify(a.cloudPayloads[0]));
    expect(a.cloudPayloads[0].prompt).not.toContain('durian');
    expect(a.cloudPayloads[0].prompt).not.toContain('tom');
    // the request asks about every one of the 19 categories, not only the user's
    for (const id of CLOUD_ALLERGEN_IDS) expect(a.cloudPayloads[0].prompt).toContain(id);
  });

  it('the device reads only the user\'s allergens from the all-allergen rating', async () => {
    const r: R[] = [{ name: 'Gaeng Som', confident: true, ingredients: [['fish', 'essential']], ratings: { wheat: 'usually', sesame: 'usually', tree_nut: 'often' } }];
    const wheat = fakes({ recipes: r }); const sesame = fakes({ recipes: r }); const none = fakes({ recipes: r });
    const asWheat = await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['wheat'], custom: [] }, device: wheat.device, cloud: wheat.cloud });
    const asCrust = await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['tree_nut'], custom: [] }, device: sesame.device, cloud: sesame.cloud });
    const asMilk = await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['milk'], custom: [] }, device: none.device, cloud: none.cloud });
    expect(mark(asWheat, 'Gaeng Som').mark).toBe('avoid'); // usually, nothing printed to contradict it
    expect(mark(asCrust, 'Gaeng Som').mark).toBe('ask'); // often -> Ask (peanut and tree nuts only, round 7)
    expect(mark(asMilk, 'Gaeng Som').mark).toBe('no_listed'); // rarely -> keep the clean result
  });

  it('final label = the stricter of the printed text and the cloud recipe', async () => {
    const f = fakes();
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Pad Thai').mark).toBe('avoid'); // printed peanuts
    expect(mark(s, 'Chicken Satay').mark).toBe('avoid'); // peanut sauce essential in the cloud recipe
    expect(mark(s, 'Chicken Satay').source).toBe('cloud');
    expect(mark(s, 'Grilled Salmon').mark).toBe('ask'); // printed text is clean, soy sauce in the recipe hides wheat
    expect(mark(s, 'Khao Soi').mark).toBe('ask'); // peanuts only "possible" and egg noodles hide wheat: Ask, not Avoid
    expect(mark(s, 'Gaeng Som').mark).toBe('no_listed'); // fish is not on this list and nothing else matches
  });

  it('a clean recipe gives No listed allergen found, decided by the cloud', async () => {
    const f = fakes();
    const s = await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['kiwi'], custom: [] }, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Gaeng Som').mark).toBe('no_listed');
    expect(mark(s, 'Gaeng Som').source).toBe('cloud');
  });

  it('"common" and "possible" ingredients give Ask the kitchen, only "essential" gives Avoid', async () => {
    const mk = (level: string) => fakes({ recipes: [{ name: 'Khao Soi', confident: true, ingredients: [['peanuts', level]] }] });
    for (const [level, want] of [['essential', 'avoid'], ['common', 'ask'], ['possible', 'ask']] as const) {
      const f = mk(level);
      const s = await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['peanut'], custom: [] }, device: f.device, cloud: f.cloud });
      expect(mark(s, 'Khao Soi').mark, level).toBe(want);
    }
  });

  it('a cloud answer can never lower a printed Avoid', async () => {
    const f = fakes({ recipes: [{ name: 'Pad Thai', confident: true, ingredients: [['rice', 'essential']] }] });
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Pad Thai').mark).toBe('avoid');
  });

  it('a dish the cloud does not know is Ask the kitchen, even with printed ingredients (a printed list can omit sauces)', async () => {
    const f = fakes({ recipes: [{ name: 'Gaeng Som', confident: false, ingredients: [] }] });
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Plain Rice').mark).toBe('ask');
    expect(mark(s, 'Plain Rice').findings.some((x) => x.kind === 'unplaced')).toBe(true);
    expect(mark(s, 'Gaeng Som').mark).toBe('ask');
    expect(mark(s, 'Khao Soi').mark).toBe('ask');
  });

  it('with the cloud step off, a dish with printed ingredients and no hit keeps No listed allergen found (device-only mode)', async () => {
    const f = fakes();
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device });
    expect(mark(s, 'Plain Rice').mark).toBe('no_listed');
  });

  it('the cloud copy of a name with different accents or punctuation still finds its recipe', async () => {
    const f = fakes({ recipes: [{ name: 'plain-rice', confident: true, ingredients: [['peanuts', 'essential']] }] });
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Plain Rice').mark).toBe('avoid');
  });

  it('matches a recipe by the English name when the printed name is not echoed', async () => {
    const f = fakes({ recipes: [{ name: 'Northern curry soup', confident: true, ingredients: [['peanuts', 'essential']] }] });
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Khao Soi').mark).toBe('avoid');
  });

  it('makes exactly one device call and one cloud request per menu', async () => {
    const f = fakes();
    await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(f.deviceCalls).toHaveLength(1);
    expect(f.cloudPayloads).toHaveLength(1);
  });
});

describe('pipeline fallbacks', () => {
  it('with the cloud step off, dishes without printed ingredients become Ask the kitchen and nothing is logged', async () => {
    const f = fakes();
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device });
    expect(mark(s, 'Khao Soi').mark).toBe('ask');
    expect(mark(s, 'Khao Soi').source).toBe('device');
    expect(mark(s, 'Gaeng Som').mark).toBe('ask');
    expect(mark(s, 'Chicken Satay').mark).toBe('ask'); // table hit (satay) and no printed ingredients
    expect(mark(s, 'Plain Rice').mark).toBe('no_listed'); // printed ingredients, device-only path
    expect(mark(s, 'Pad Thai').mark).toBe('avoid');
    expect(s.cloudLog).toEqual([]);
    expect(s.stage).toBe('done');
  });

  it('a failed cloud call falls back to the device-only path and is logged', async () => {
    const f = fakes({ cloudFails: true });
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(s.cloudLog[0].outcome).toBe('failed');
    expect(s.cloudLog[0].error).toBe('boom');
    expect(mark(s, 'Khao Soi').mark).toBe('ask');
    expect(mark(s, 'Gaeng Som').mark).toBe('ask');
    expect(mark(s, 'Gaeng Som').findings[0].reason).toContain('cloud step failed');
    expect(mark(s, 'Pad Thai').mark).toBe('avoid');
    expect(mark(s, 'Plain Rice').mark).toBe('ask'); // round 4: cloud step on but failed -> every dish is at least Ask
    expect(s.warnings.join(' ')).toMatch(/cloud recipe step failed/);
    expect(s.stage).toBe('done');
  });

  it('a cloud reply that is not JSON falls back the same way', async () => {
    const f = fakes();
    const cloud: CloudEngine = { recipes: async () => 'sorry, no' };
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud });
    expect(s.cloudLog[0].outcome).toBe('failed');
    expect(mark(s, 'Gaeng Som').mark).toBe('ask');
  });

  it('a recipe for the wrong dish name is ignored (fails closed)', async () => {
    const f = fakes({ recipes: [{ name: 'Something else', confident: true, ingredients: [['rice', 'essential']] }] });
    const s = await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud });
    expect(mark(s, 'Khao Soi').mark).toBe('ask');
    expect(mark(s, 'Gaeng Som').mark).toBe('ask');
  });
});

describe('pipeline reading', () => {
  it('reports a clear error when the photo cannot be read', async () => {
    const device: DeviceEngine = { readMenu: async () => 'not json' };
    const s = await runCheck({ imageDataUrl: IMAGE, list, device });
    expect(s.stage).toBe('error');
    expect(s.error).toMatch(/Could not read the menu/);
  });

  it('reports an error when no dishes are found, and sends nothing', async () => {
    const f = fakes({ reply: '{"language":"en","dishes":[]}' });
    expect((await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud })).stage).toBe('error');
    expect(f.cloudPayloads).toHaveLength(0);
  });

  it('streams finished dishes to the screen before the read ends', async () => {
    const full = menuReply;
    const device: DeviceEngine = {
      async readMenu(_img, onPartial) {
        const cut = full.indexOf('"Grilled Salmon"') + 10; // cut in the middle of the 3rd dish
        onPartial?.(full.slice(0, cut));
        return full;
      },
    };
    const seen: number[] = [];
    await runCheck({ imageDataUrl: IMAGE, list, device, onUpdate: (s) => seen.push(s.dishes.length) });
    expect(seen).toContain(2);
    expect(seen[seen.length - 1]).toBe(6);
  });

  it('a Chinese menu with English translations is checked on both texts', async () => {
    const device: DeviceEngine = {
      readMenu: async () => JSON.stringify({ language: 'zh', dishes: [
        { name: '虾饺', nameEnglish: 'Shrimp dumpling', ingredients: [{ text: '鲜虾', english: 'fresh shrimp' }, { text: '腰果', english: 'cashew' }] },
        { name: '白饭', nameEnglish: 'Steamed rice', ingredients: [{ text: '大米', english: '' }] },
      ] }),
    };
    const s = await runCheck({ imageDataUrl: IMAGE, list: { allergens: ['tree_nut', 'sesame'], custom: [] }, device });
    expect(s.dishes[0].decision!.mark).toBe('avoid');
    expect(s.dishes[1].decision!.mark).toBe('ask'); // 大米 has no English translation
  });

  it('reports progress while checking and while waiting for the cloud', async () => {
    const f = fakes();
    const messages: string[] = [];
    await runCheck({ imageDataUrl: IMAGE, list, device: f.device, cloud: f.cloud, onUpdate: (s) => messages.push(s.message) });
    expect(messages.some((m) => m.includes('Checking 6 dishes'))).toBe(true);
    expect(messages.some((m) => m.includes('Sending 6 dish name(s)'))).toBe(true);
  });
});
