// Round 2: one test group per way a hidden allergen got through in the second real run (app-build3).
import { describe, expect, it } from 'vitest';
import { applyRecipe, CLOUD_INSTRUCTION, firstPass, mergeMarks, untranslatedDishName, type AllergyList, type CloudRecipe } from '../src/core/core';
import { ALLERGENS } from '../src/core/allergens';

const L = (...allergens: AllergyList['allergens']): AllergyList => ({ allergens, custom: [] });
const markOf = (name: string, list: AllergyList, nameEnglish?: string, ingredients: string[] = []) =>
  mergeMarks(firstPass({ name, nameEnglish, ingredients, ingredientsEnglish: ingredients }, list)).mark;
const recipe = (...items: [string, 'essential' | 'common' | 'possible'][]): CloudRecipe =>
  ({ name: 'x', confident: true, ingredients: items.map(([name, level]) => ({ name, level })) });
const recipeMark = (r: CloudRecipe, list: AllergyList) => mergeMarks(applyRecipe(r, list)).mark;

describe('cause 1: the cloud recipe left out the sauce, so the instruction now asks for each component', () => {
  it('asks for cooking sauce, marinade, dips, table condiments, fillings, pastes and toppings, one by one', () => {
    for (const w of ['sauce or seasoning', 'marinated', 'dip, table sauce and condiment', 'filling, paste and spice mix', 'sprinkled on top']) {
      expect(CLOUD_INSTRUCTION, w).toContain(w);
    }
    expect(CLOUD_INSTRUCTION).toContain('served on the side');
  });
  it('round 4: the allergen words in the instruction are exactly the fixed list of all categories (same for every user)', () => {
    const marked = CLOUD_INSTRUCTION.replace(ALLERGENS.map((a) => `${a.id} (${a.label})`).join('; '), '');
    expect(marked).not.toBe(CLOUD_INSTRUCTION);
    for (const w of ['peanut', 'sesame', 'shellfish', 'gluten']) expect(marked.toLowerCase(), w).not.toContain(w);
  });
  it('a "possible" or "common" item from the recipe can only give Ask the kitchen, never No listed', () => {
    expect(recipeMark(recipe(['chicken', 'essential'], ['hoisin sauce', 'possible']), L('peanut'))).toBe('ask');
    expect(recipeMark(recipe(['water spinach', 'essential'], ['xao', 'common']), L('soy'))).toBe('ask');
  });
});

describe('cause 2 (round 4: dish-specific words removed, generic technique and sauce words kept)', () => {
  it('stir-fried dishes (Vietnamese xào with or without accents, English stir-fried) are Ask for soy, wheat and fish', () => {
    for (const name of ['Rau Mừng Xào Tỏi', 'Rau Muong Xao Toi', 'Stir-fried water spinach', 'Stir fried greens']) {
      for (const id of ['soy', 'wheat', 'fish'] as const) expect(markOf(name, L(id)), `${name} ${id}`).toBe('ask');
    }
  });
  it('a stir-fry does not raise a peanut list', () => {
    expect(markOf('Rau Mừng Xào Tỏi', L('peanut'), 'Rau Murong Xao Hoi', ['water spinach'])).toBe('no_listed');
  });
  it('round 4: the dish-name words from rounds 2-3 are gone (the cloud rating covers those dishes)', () => {
    const ask = (name: string, id: AllergyList['allergens'][number]) =>
      firstPass({ name, ingredients: [], ingredientsEnglish: [] }, L(id)).some((f) => f.kind === 'hidden');
    for (const [name, id] of [['Beef Sate', 'soy'], ['Chicken Yakitori', 'wheat'], ['Avocado Toast', 'sesame'], ['Multigrain roll', 'sesame'], ['Phở Bò', 'peanut'], ['煎堆 Sesame ball', 'peanut'], ['Tangyuan', 'peanut']] as const) {
      expect(ask(name, id), `${name} ${id}`).toBe(false);
    }
  });
  it('sweet pastes: the ingredient word "sesame paste" stays (generic), the dish-specific fillings are gone', () => {
    expect(recipeMark(recipe(['glutinous rice flour', 'essential'], ['sesame paste', 'common']), L('peanut'))).toBe('ask');
    expect(recipeMark(recipe(['glutinous rice flour', 'essential'], ['sweet filling', 'common']), L('peanut'))).not.toBe('no_listed'); // no rating -> unknown -> Ask
    expect(firstPass({ name: 'x', ingredients: ['sweet filling'], ingredientsEnglish: ['sweet filling'] }, L('peanut')).some((f) => f.kind === 'hidden')).toBe(false);
  });
  it('gelatin stays as a generic ingredient word for fish', () => {
    expect(markOf('Pudding', L('fish'), undefined, ['gelatin'])).toBe('ask');
  });
  it('table sauces and condiments in a recipe are Ask for peanut', () => {
    expect(recipeMark(recipe(['rice', 'essential'], ['table sauces', 'possible']), L('peanut'))).toBe('ask');
  });
});

describe('cause 3: a wheat word matched inside "broth" (over-caution, found while checking pho)', () => {
  it('broth is not wheat; real German bread words still are', () => {
    expect(markOf('Chicken broth', L('wheat'), undefined, ['chicken'])).toBe('no_listed');
    expect(mergeMarks(firstPass({ name: 'Soup', ingredients: ['chicken broth', 'carrot'], ingredientsEnglish: ['chicken broth', 'carrot'] }, L('wheat'))).mark).toBe('no_listed');
    expect(markOf('Vollkornbrot', L('wheat'))).toBe('avoid');
    expect(markOf('Brot mit Butter', L('wheat'))).toBe('avoid');
  });
});

describe('cause 4: a dish name the tables cannot read is at least Ask the kitchen', () => {
  it('non-Latin name with no Latin English name is untranslated', () => {
    expect(untranslatedDishName({ name: '煎堆', ingredients: [] })).toBe(true);
    expect(untranslatedDishName({ name: '煎堆', nameEnglish: '', ingredients: [] })).toBe(true);
    expect(untranslatedDishName({ name: '煎堆', nameEnglish: '煎堆', ingredients: [] })).toBe(true);
    expect(untranslatedDishName({ name: 'ผัดไทย', ingredients: [] })).toBe(true);
  });
  it('a Latin English name, or a Latin word in the printed name, is enough', () => {
    expect(untranslatedDishName({ name: '煎堆', nameEnglish: 'Sesame Balls', ingredients: [] })).toBe(false);
    expect(untranslatedDishName({ name: '龍門 Dim Sum', ingredients: [] })).toBe(false);
    expect(untranslatedDishName({ name: 'Pad Thai', ingredients: [] })).toBe(false);
  });
  it('firstPass turns such a dish into Ask even when the word tables find nothing', () => {
    expect(markOf('白灼菜心', L('peanut'))).toBe('ask');
    expect(markOf('白灼菜心', L('peanut'), 'Blanched greens', ['lettuce'])).toBe('no_listed');
  });
});
