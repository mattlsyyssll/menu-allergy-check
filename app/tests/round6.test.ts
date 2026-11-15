import { describe, expect, it } from 'vitest';
import { applyRecipe, checkHidden, firstPass, mergeMarks, type AllergyList, type MenuDish } from '../src/core/core';

// Round 6: hidden sources named by the FARE allergen pages that the table lacked, kept only where the answer keys agree.
// Each case is a dish shape that was marked "No listed allergen found" in final exam 2 although the key says "Ask the kitchen".

const L = (...a: AllergyList['allergens']): AllergyList => ({ allergens: a, custom: [] });
const dish = (name: string, ingredients: string[]): MenuDish => ({ name, nameEnglish: name, ingredients, ingredientsEnglish: ingredients });
const mark = (d: MenuDish, l: AllergyList) => mergeMarks(firstPass(d, l)).mark;

describe('round 6 hidden sources', () => {
  it('barbecue sauce raises Ask for fish and soy', () => {
    const d = dish('Bacon BBQ Burger', ['beef patty', 'bacon', 'house bbq sauce']);
    expect(mark(d, L('fish'))).toBe('ask');
    expect(mark(d, L('soy'))).toBe('ask');
    expect(mark(d, L('crustacean', 'mollusc'))).toBe('no_listed');
  });
  it('a typical recipe with barbecue sauce raises Ask for fish', () => {
    const r = { name: 'Baby Back Ribs', confident: true, ingredients: [{ name: 'pork ribs', level: 'essential' as const }, { name: 'barbecue sauce', level: 'common' as const }],
      ratings: { fish: { level: 'rarely' as const, why: '' } } };
    expect(mergeMarks(applyRecipe(r, L('fish'))).mark).toBe('ask');
  });
  it('chili sauce, sweet chili dip and sambal raise Ask for peanut', () => {
    for (const ing of ['sweet chili dip', 'sambal', 'chilli sauce']) expect(mark(dish('X', [ing]), L('peanut'))).toBe('ask');
    expect(mark(dish('X', ['soy sauce']), L('peanut'))).toBe('no_listed');
  });
  it('taramosalata and skordalia raise Ask for tree nuts', () => {
    expect(mark(dish('Taramosalata', ['whipped spread', 'lemon']), L('tree_nut'))).toBe('ask');
    expect(mark(dish('Skordalia', ['garlic', 'potato']), L('tree_nut'))).toBe('ask');
  });
  it('soto raises Ask for crustaceans', () => {
    expect(checkHidden(dish('Soto Ayam', ['chicken soup']), L('crustacean')).length).toBe(1);
  });
  it('glazes without barbecue sauce are not matched for fish', () => {
    expect(mark(dish('Honey Glazed Carrots', ['carrot', 'honey glaze']), L('fish'))).toBe('no_listed');
  });
});

describe('round 6 dish rules', () => {
  it('chili the stew raises Ask for peanut; chili the spice does not', () => {
    expect(mark(dish('Beef Chili', ['beef', 'beans']), L('peanut'))).toBe('ask');
    expect(mark(dish('Spaghetti Puttanesca', ['tomato', 'chili']), L('peanut'))).toBe('no_listed');
  });
  it('rendang raises Ask for tree nuts', () => {
    expect(mark(dish('Beef Rendang', ['beef', 'coconut']), L('tree_nut'))).toBe('ask');
  });
});

describe('round 6 bread and sesame', () => {
  it('bread, buns and rolls raise Ask for sesame', () => {
    for (const [n, i] of [['Baguette Tradition', ['crisp crust']], ['Brisket Plate', ['brisket', 'white bread']], ['Lobster Roll', ['lobster', 'mayo']]] as const)
      expect(mark(dish(n, [...i]), L('sesame'))).toBe('ask');
  });
  it('spring rolls and rice dishes are not matched by the bread rule', () => {
    expect(mark(dish('Spring Rolls', ['cabbage', 'carrot']), L('sesame'))).toBe('no_listed');
    expect(mark(dish('Fried Rice', ['rice', 'egg']), L('sesame'))).toBe('no_listed');
  });
});

describe('round 7', () => {
  it('the generic word curry no longer raises peanut or tree nuts; named curries still do', () => {
    expect(mark(dish('Chicken Curry', ['chicken', 'potato']), L('peanut', 'tree_nut'))).toBe('no_listed');
    expect(mark(dish('Massaman Curry', ['beef']), L('peanut'))).toBe('ask');
    expect(mark(dish('Lamb Korma', ['lamb']), L('tree_nut'))).toBe('ask');
    expect(mark(dish('Green Curry', ['chicken']), L('fish'))).toBe('ask'); // curry paste and fish sauce stay
  });
});
