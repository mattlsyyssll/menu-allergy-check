import { describe, expect, it } from 'vitest';
import { firstPass, mergeMarks, parseMenuJson, splitSectionHeadings, type MenuDish } from '../src/core/core';

// Round 8: final exam 4, menu M42. The device model read the heading 小吃与甜品 (Snacks and Desserts) as one dish
// and listed the 5 dishes under it as its ingredients; those dishes were never checked.
const read = JSON.stringify({ language: 'zh', dishes: [
  { name: '蒜泥白肉', nameEnglish: 'Garlic Pork', ingredients: [{ text: '五花肉片、蒜泥', english: 'pork belly, garlic' }] },
  { name: '小吃与甜品', nameEnglish: 'Snacks and Desserts', ingredients: [
    { text: '酸辣粉', english: 'Hot and sour noodles' }, { text: '红油抄手', english: 'Red oil wontons' }, { text: '钟水饺', english: 'Zhong dumplings' },
    { text: '红糖糍粑', english: 'Brown sugar rice cake' }, { text: '冰粉', english: 'Ice jelly' }] },
  { name: '今日特色菜', nameEnglish: "Today's Special", ingredients: [{ text: '请问服务员', english: 'Please ask the waiter' }] },
] });

describe('section headings read as dishes', () => {
  it('round 8b: the app no longer splits; a heading line stays one item and is at least Ask the kitchen', () => {
    const m = parseMenuJson(read);
    expect(m.dishes.map((d) => d.name)).toEqual(['蒜泥白肉', '小吃与甜品', '今日特色菜']);
    const f = firstPass(m.dishes[1], { allergens: ['milk'], custom: [] }, 'zh');
    expect(mergeMarks(f).mark).toBe('ask');
    expect(f.some((x) => x.reason.includes('looks like a menu section'))).toBe(true);
    expect(firstPass(m.dishes[0], { allergens: ['milk'], custom: [] }, 'zh').some((x) => x.reason.includes('looks like a menu section'))).toBe(false);
  });
  it('splitSectionHeadings (kept as a helper, unused) splits the heading into its dishes', () => {
    const m = { dishes: splitSectionHeadings(parseMenuJson(read).dishes) };
    expect(m.dishes.map((d) => d.name)).toEqual(['蒜泥白肉', '酸辣粉', '红油抄手', '钟水饺', '红糖糍粑', '冰粉', '今日特色菜']);
    expect(m.dishes[2].nameEnglish).toBe('Red oil wontons');
    expect(m.dishes[2].ingredients).toEqual([]);
  });
  it('real dishes are not split', () => {
    const d = (name: string, nameEnglish: string, ingredients: string[]): MenuDish => ({ name, nameEnglish, ingredients, ingredientsEnglish: ingredients });
    for (const x of [d('Garden Salad', 'Garden Salad', ['lettuce', 'tomato']), d('Soup of the Day', 'Soup of the Day', ['ask', 'staff']),
      d('Noodle Soup with Beef', 'Noodle Soup with Beef', ['noodles', 'beef']), d('Desserts', 'Desserts', ['tiramisu']), d('担担面', 'Dan dan noodles', ['麺', '芝麻酱'])])
      expect(splitSectionHeadings([x])).toEqual([x]);
  });
  it('English and Japanese headings split too', () => {
    const h = (name: string, nameEnglish: string): MenuDish => ({ name, nameEnglish, ingredients: ['A', 'B'], ingredientsEnglish: ['A', 'B'] });
    expect(splitSectionHeadings([h('Starters & Sides', 'Starters & Sides')]).map((x) => x.name)).toEqual(['A', 'B']);
    expect(splitSectionHeadings([h('デザート', 'デザート')]).map((x) => x.name)).toEqual(['A', 'B']);
  });
});

describe('round 8b synonyms', () => {
  const d = (name: string, ing: string[]): MenuDish => ({ name, nameEnglish: name, ingredients: ing, ingredientsEnglish: ing });
  const m = (x: MenuDish, ids: Parameters<typeof firstPass>[1]['allergens']) => mergeMarks(firstPass(x, { allergens: ids, custom: [] })).mark;
  it('chorizo counts as sausage, telera as a roll, biscotti as cookies', () => {
    expect(m(d('Sope de Chorizo', ['masa', 'chorizo']), ['sesame'])).toBe('ask');
    expect(m(d('Torta de Jamón', ['ham', 'telera']), ['sesame'])).toBe('ask');
    expect(m(d('Cantucci', ['biscotti']), ['peanut'])).toBe('ask');
  });
});

describe('round 8b heading words', () => {
  it('a dish named Soup or Salad is not a heading; Soups and Salads is', async () => {
    const { isSectionHeading } = await import('../src/core/core');
    const x = (n: string): MenuDish => ({ name: n, nameEnglish: n, ingredients: ['a', 'b'], ingredientsEnglish: ['a', 'b'] });
    expect(isSectionHeading(x('Soup'))).toBe(false);
    expect(isSectionHeading(x('Salad'))).toBe(false);
    expect(isSectionHeading(x('Soups and Salads'))).toBe(true);
    expect(isSectionHeading({ name: 'Salade et soupes', nameEnglish: 'Salads and soups', ingredients: ['a', 'b'] })).toBe(true);
  });
});
