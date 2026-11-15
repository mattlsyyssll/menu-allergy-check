import { describe, expect, it } from 'vitest';
import {
  applyRecipe, buildCloudPayload, CLOUD_INSTRUCTION, buildWaiterQuestion, checkHidden, checkListed, extractJson, firstPass, isPlaced,
  MARK_LABEL, mergeMarks, normalizeLang, parseRecipesJson, parseMenuJson, sanitizeDishNames, termMatches,
  type AllergyList, type Finding,
} from '../src/core/core';
import { ALLERGENS } from '../src/core/allergens';

const ALL_IDS = ['banana', 'buckwheat', 'celery', 'corn', 'crustacean', 'egg', 'fish', 'kiwi', 'lupin', 'milk', 'mollusc', 'mustard', 'peach', 'peanut', 'sesame', 'soy', 'sulphites', 'tree_nut', 'wheat'];
const peanut: AllergyList = { allergens: ['peanut'], custom: [] };
const dish = (name: string, ingredients: string[] = []) => ({ name, ingredients });

describe('labels', () => {
  it('has exactly three labels and never says safe', () => {
    expect(Object.values(MARK_LABEL)).toEqual(['No listed allergen found', 'Ask the kitchen', 'Avoid']);
    expect(JSON.stringify(MARK_LABEL).toLowerCase()).not.toContain('safe');
  });
});

describe('parse model JSON', () => {
  it('parses a clean menu reply', () => {
    const m = parseMenuJson('{"language":"TH","dishes":[{"name":"Pad Thai","ingredients":["noodles","peanuts"]}]}');
    expect(m.language).toBe('th');
    expect(m.dishes).toEqual([{ name: 'Pad Thai', ingredients: ['noodles', 'peanuts'] }]);
  });
  it('handles code fences, chatter, string ingredients, duplicates and nameless dishes', () => {
    const raw = 'Sure!\n```json\n{"dishes":[{"name":"A","ingredients":"egg, milk"},{"name":"a"},{"ingredients":["x"]},{"name":"  "}]}\n```';
    const m = parseMenuJson(raw);
    expect(m.dishes).toEqual([{ name: 'A', ingredients: ['egg', 'milk'] }]);
  });
  it('accepts a bare array and rejects junk', () => {
    expect(parseMenuJson('[{"name":"Soup"}]').dishes[0].name).toBe('Soup');
    expect(() => parseMenuJson('no json here')).toThrow();
    expect(() => parseMenuJson('{"foo":1}')).toThrow(/dishes/);
    expect(() => extractJson('{"a":')).toThrow();
  });
  it('parses cloud recipes with levels and requires ingredients for "confident"', () => {
    const g = parseRecipesJson('{"dishes":[{"name":"Khao Soi","ingredients":[{"name":"noodles","level":"essential"},{"name":"peanuts","level":"possible"},"lime"],"confident":true},{"name":"X","ingredients":[],"confident":true},{"name":"Y","ingredients":[{"name":"a","level":"common"}],"confident":false}]}');
    expect(g.map((x) => x.confident)).toEqual([true, false, false]);
    expect(g[0].ingredients).toEqual([{ name: 'noodles', level: 'essential' }, { name: 'peanuts', level: 'possible' }, { name: 'lime', level: 'common' }]);
  });
  it('an unknown or missing level is the weakest one ("possible"), a bare string is "common"', () => {
    const g = parseRecipesJson('{"dishes":[{"name":"X","ingredients":[{"name":"a"},{"name":"b","level":"weird"},"c"],"confident":true}]}');
    expect(g[0].ingredients.map((i) => i.level)).toEqual(['possible', 'possible', 'common']);
  });
});

describe('matching', () => {
  it('matches whole words only', () => {
    expect(termMatches('peanut sauce', 'peanut')).toBe(true);
    expect(termMatches('Peanuts', 'peanut')).toBe(true);
    expect(termMatches('nutmeg', 'nut')).toBe(false);
    expect(termMatches('coconut', 'nut')).toBe(false);
    expect(termMatches('eggplant', 'egg')).toBe(false);
  });
  it('matches CJK and Thai as substrings', () => {
    expect(termMatches('宫保鸡丁配花生', '花生')).toBe(true);
    expect(termMatches('ผัดไทยใส่ถั่วลิสง', 'ถั่วลิสง')).toBe(true);
  });
});

describe('listed allergens -> Avoid', () => {
  it('avoids a dish that lists peanuts', () => {
    const f = checkListed(dish('Pad Thai', ['noodles', 'crushed peanuts']), peanut);
    expect(f).toHaveLength(1);
    expect(f[0].mark).toBe('avoid');
  });
  it('does not treat coconut milk as milk or peanut butter as dairy', () => {
    const milk: AllergyList = { allergens: ['milk'], custom: [] };
    expect(checkListed(dish('Curry', ['coconut milk']), milk)).toEqual([]);
    expect(checkListed(dish('Toast', ['peanut butter']), milk)).toEqual([]);
    expect(checkListed(dish('Latte'), milk)).toHaveLength(1);
  });
  it('supports custom words and other scripts', () => {
    expect(checkListed(dish('Kiwi tart'), { allergens: [], custom: ['kiwi'] })[0].mark).toBe('avoid');
    expect(checkListed(dish('宫保鸡丁', ['鸡肉', '花生']), peanut)[0].mark).toBe('avoid');
  });
});

describe('hidden-source table -> Ask the kitchen', () => {
  const cases: [string, string, AllergyList['allergens'][number]][] = [
    ['Chicken Satay', 'satay', 'peanut'],
    ['Green Papaya Salad', 'papaya salad', 'peanut'],
    ['Mole Poblano', 'mole', 'peanut'],
    ['Pesto Genovese', 'pesto', 'tree_nut'],
    ['Lamb Korma', 'korma', 'tree_nut'],
    ['Pad Kra Pao Curry', 'curry', 'peanut'],
    ['Fettuccine Alfredo', 'alfredo', 'milk'],
    ['Caesar Salad', 'caesar', 'egg'],
    ['Chicken Teriyaki', 'teriyaki', 'wheat'],
    ['Miso Soup', 'miso soup', 'fish'],
    ['Oyster sauce beef', 'oyster sauce', 'mollusc'],
    ['Hummus Plate', 'hummus', 'sesame'],
    ['Stir-fry greens', 'stir fry', 'soy'],
  ];
  for (const [name, , id] of cases) {
    it(`flags "${name}" for ${id}`, () => {
      const f = checkHidden(dish(name), { allergens: [id], custom: [] });
      expect(f).toHaveLength(1);
      expect(f[0].mark).toBe('ask');
      expect(f[0].kind).toBe('hidden');
    });
  }
  it('never returns Avoid and only checks allergens on the saved list', () => {
    expect(checkHidden(dish('Chicken Satay'), { allergens: ['fish'], custom: [] })).toEqual([]);
    for (const a of ALLERGENS) {
      for (const h of a.hidden) {
        const f = checkHidden(dish(h.term), { allergens: [a.id], custom: [] });
        expect(f.every((x) => x.mark === 'ask')).toBe(true);
      }
    }
  });
  it('has a table and direct words for all 9 major allergens', () => {
    expect(ALLERGENS.map((a) => a.id).sort()).toEqual(
      [...ALL_IDS].sort());
    for (const a of ALLERGENS) { expect(a.direct.length).toBeGreaterThan(5); expect(a.hidden.length).toBeGreaterThan(5); }
  });
  it('flags a satay dish even when the menu lists ingredients without peanuts', () => {
    const f = firstPass(dish('Chicken Satay', ['chicken', 'cucumber']), peanut);
    expect(mergeMarks(f).mark).toBe('ask');
  });
});

describe('first pass, placed, guesses', () => {
  it('marks a dish with listed ingredients and no hit as No listed allergen found', () => {
    const f = firstPass(dish('Grilled Salmon', ['salmon', 'rice']), peanut);
    expect(mergeMarks(f).mark).toBe('no_listed');
    expect(isPlaced(dish('Grilled Salmon', ['salmon']), f)).toBe(true);
  });
  it('leaves a bare unknown dish unplaced', () => {
    const d = dish('Khao Soi');
    expect(isPlaced(d, firstPass(d, peanut))).toBe(false);
  });
  const recipe = (ingredients: [string, 'essential' | 'common' | 'possible'][], confident = true) =>
    ({ name: 'X', confident, ingredients: ingredients.map(([name, level]) => ({ name, level })) });
  it('a recipe hit on a common or possible ingredient is Ask, never Avoid', () => {
    for (const level of ['common', 'possible'] as const) {
      const f = applyRecipe(recipe([['noodles', 'essential'], ['peanuts', level]]), peanut, 'cloud');
      expect(mergeMarks(f).mark).toBe('ask');
      expect(f[0].source).toBe('cloud');
    }
  });
  it('a recipe hit on an essential ingredient is Avoid', () => {
    expect(mergeMarks(applyRecipe(recipe([['peanut sauce', 'essential']]), peanut, 'cloud')).mark).toBe('avoid');
  });
  it('a hidden-source table hit on a recipe ingredient is Ask even when essential', () => {
    const wheatList: AllergyList = { allergens: ['wheat'], custom: [] };
    expect(mergeMarks(applyRecipe(recipe([['soy sauce', 'essential']]), wheatList, 'cloud')).mark).toBe('ask');
  });
  it('an unsure or missing recipe is Ask the kitchen', () => {
    expect(applyRecipe(recipe([], false), peanut, 'cloud')[0].mark).toBe('ask');
    expect(applyRecipe(undefined, peanut, 'cloud')[0].mark).toBe('ask');
  });
  it('a clean confident recipe gives No listed allergen found with the cloud as source', () => {
    const r = { ...recipe([['rice', 'essential'], ['egg', 'common']]), ratings: { peanut: { level: 'rarely' as const, why: '' } } };
    const d = mergeMarks(applyRecipe(r, peanut, 'cloud'));
    expect(d.mark).toBe('no_listed');
    expect(d.source).toBe('cloud');
  });
  it('a clean recipe with NO rating for the user\'s allergen is Ask the kitchen (a missing rating is unknown)', () => {
    expect(mergeMarks(applyRecipe(recipe([['rice', 'essential']]), peanut, 'cloud')).mark).toBe('ask');
  });
  it('generic hidden-source gaps: sauces, wrappers, batter, mayonnaise, pastry, ghee, fish sauce', () => {
    const cases: [string, string, string][] = [
      ['wheat', 'hoisin sauce', 'ask'], ['wheat', 'spring roll wrapper', 'ask'], ['wheat', 'tempura batter', 'ask'], ['wheat', 'filo pastry', 'ask'],
      ['soy', 'oyster sauce', 'ask'], ['soy', 'soy sauce', 'ask'], ['egg', 'coleslaw dressing', 'ask'], ['egg', 'beer batter', 'ask'],
      ['milk', 'ghee', 'ask'], ['milk', 'puff pastry', 'ask'], ['fish', 'fish sauce', 'ask'], ['fish', 'dipping sauce', 'ask'],
      ['mollusc', 'oyster sauce', 'ask'], ['crustacean', 'oyster sauce', 'ask'], ['tree_nut', 'marzipan', 'ask'],
    ];
    for (const [id, ing, want] of cases) {
      const l: AllergyList = { allergens: [id as AllergyList['allergens'][number]], custom: [] };
      expect(mergeMarks(applyRecipe(recipe([[ing, 'possible']]), l, 'cloud')).mark, `${id} / ${ing}`).toBe(want);
    }
  });
});

describe('merge marks', () => {
  const f = (mark: Finding['mark'], source: Finding['source']): Finding => ({ mark, kind: 'listed', allergen: 'x', reason: 'r', source });
  it('strictest mark wins', () => {
    expect(mergeMarks([f('no_listed', 'device'), f('ask', 'device'), f('avoid', 'device')]).mark).toBe('avoid');
    expect(mergeMarks([f('no_listed', 'cloud'), f('ask', 'device')]).mark).toBe('ask');
  });
  it('a later cloud answer can never lower a device Avoid', () => {
    const d = mergeMarks([f('avoid', 'device'), f('no_listed', 'cloud')]);
    expect(d.mark).toBe('avoid');
    expect(d.source).toBe('device');
  });
  it('an empty list is Ask the kitchen, not a pass', () => {
    expect(mergeMarks([]).mark).toBe('ask');
  });
});

describe('cloud payload', () => {
  it('contains dish names (printed and English) and the instruction only', () => {
    const p = buildCloudPayload([{ name: 'Khao Soi' }, { name: '虾饺', nameEnglish: 'Shrimp dumpling' }, 'Laksa']);
    expect(p.dishNames).toEqual(['Khao Soi', '虾饺', 'Shrimp dumpling', 'Laksa']);
    expect(p.dishes).toEqual([{ name: 'Khao Soi' }, { name: '虾饺', english: 'Shrimp dumpling' }, { name: 'Laksa' }]);
    expect(Object.keys(p).sort()).toEqual(['dishNames', 'dishes', 'prompt']);
  });
  it('the request is exactly the fixed instruction plus the dish list, nothing else', () => {
    const p = buildCloudPayload([{ name: 'Khao Soi', nameEnglish: 'Curry noodle soup' }, { name: 'Laksa' }]);
    expect(p.prompt).toBe(`${CLOUD_INSTRUCTION}\n\nDishes:\n${JSON.stringify([{ name: 'Khao Soi', english: 'Curry noodle soup' }, { name: 'Laksa' }])}`);
  });
  it('the fixed instruction names ALL 19 allergen categories (the same for every user) and no list, person or diet', () => {
    expect(ALLERGENS).toHaveLength(19);
    for (const a of ALLERGENS) expect(CLOUD_INSTRUCTION, a.id).toContain(`${a.id} (${a.label})`);
    const text = CLOUD_INSTRUCTION.toLowerCase();
    for (const w of ['intoleran', 'child', 'my son', 'my daughter', 'profile', 'saved list', 'diet', 'your list', 'the user']) expect(text).not.toContain(w);
  });
  it('buildCloudPayload takes dish names only: no parameter through which a list could enter', () => {
    expect(buildCloudPayload.length).toBe(1);
  });
  it('never contains image data', () => {
    const fake = 'data:image/jpeg;base64,' + 'A'.repeat(500);
    const p = buildCloudPayload(['Soup', fake, 'B'.repeat(80), 'https://x.test/a.png', { name: 'Tea', nameEnglish: fake }]);
    expect(p.dishNames).toEqual(['Soup', 'Tea']);
    expect(p.prompt).not.toMatch(/base64|data:image/i);
    expect(p.prompt).not.toMatch(/[A-Za-z0-9+/=]{60,}/);
  });
  it('caps and de-duplicates names', () => {
    const many = Array.from({ length: 100 }, (_, i) => `Dish ${i}`);
    expect(sanitizeDishNames([...many, 'Dish 1'])).toHaveLength(60);
    expect(buildCloudPayload(many).dishes).toHaveLength(60);
    expect(sanitizeDishNames(['  a   b  ', 'a b'])).toEqual(['a b']);
  });
});

describe('waiter question', () => {
  const list: AllergyList = { allergens: ['peanut', 'tree_nut'], custom: ['kiwi'] };
  it('is written in each supported language from the list', () => {
    expect(buildWaiterQuestion(list, 'en')).toContain('peanuts');
    expect(buildWaiterQuestion(list, 'zh')).toContain('花生');
    expect(buildWaiterQuestion(list, 'es')).toContain('cacahuetes');
    expect(buildWaiterQuestion(list, 'th')).toContain('ถั่วลิสง');
    expect(buildWaiterQuestion(list, 'ja', ['Satay'])).toContain('"Satay"');
    expect(buildWaiterQuestion(list, 'fr')).toContain('kiwi');
  });
  it('normalises language names', () => {
    expect(normalizeLang('zh-TW')).toBe('zh');
    expect(normalizeLang('Thai')).toBe('th');
    expect(normalizeLang('xx')).toBeNull();
    expect(normalizeLang('')).toBeNull();
  });
});
