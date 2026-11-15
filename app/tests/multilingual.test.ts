import { describe, expect, it } from 'vitest';
import {
  allergenIdsFromName, applyRecipe, checkHidden, checkListed, firstPass, hasNonLatinLetters, mergeMarks, migrateList,
  parseMenuJson, parsePartialMenu, untranslatedIngredients, type AllergyList,
} from '../src/core/core';
import { ALLERGENS, type AllergenId } from '../src/core/allergens';
import { MULTI_DIRECT, MULTI_HIDDEN, TABLE_LANGS, type TableLang } from '../src/core/multilingual';

const only = (id: AllergenId): AllergyList => ({ allergens: [id], custom: [] });
const dish = (name: string, ingredients: string[] = [], ingredientsEnglish?: string[], nameEnglish?: string) => ({ name, ingredients, ingredientsEnglish, nameEnglish });
const marks = (ingredients: string[], id: AllergenId, name = 'x') => checkListed(dish(name, ingredients), only(id)).map((f) => f.mark);

describe('allergen list: EU 14 plus extras', () => {
  it('has 19 items with a plain "covers" text and enough words', () => {
    expect(ALLERGENS).toHaveLength(19);
    for (const a of ALLERGENS) {
      expect(a.covers.length).toBeGreaterThan(5);
      expect(a.direct.length).toBeGreaterThan(5);
      expect(a.hidden.length).toBeGreaterThan(5);
    }
  });
  it('names what the split items cover', () => {
    const by = Object.fromEntries(ALLERGENS.map((a) => [a.id, a]));
    expect(by.crustacean.label).toBe('Crustaceans');
    expect(by.crustacean.covers).toMatch(/prawn.*shrimp.*crab.*lobster.*crayfish/);
    expect(by.mollusc.label).toBe('Molluscs');
    expect(by.mollusc.covers).toMatch(/escargot.*squid.*octopus.*clam.*mussel.*oyster.*scallop.*abalone.*cuttlefish/);
    expect(by.wheat.covers).toMatch(/barley.*rye.*oats/);
  });
});

describe('Shellfish is split into Crustaceans and Molluscs', () => {
  it('shrimp is a crustacean and not a mollusc', () => {
    expect(marks(['shrimp'], 'crustacean')).toEqual(['avoid']);
    expect(marks(['shrimp'], 'mollusc')).toEqual([]);
  });
  it('squid, oyster and escargot are molluscs and not crustaceans', () => {
    for (const w of ['squid', 'oyster', 'escargot', 'scallop', 'octopus', 'cuttlefish', 'abalone', 'clam', 'mussel']) {
      expect(marks([w], 'mollusc')).toEqual(['avoid']);
      expect(marks([w], 'crustacean')).toEqual([]);
    }
    for (const w of ['prawn', 'crab', 'lobster', 'crayfish']) expect(marks([w], 'crustacean')).toEqual(['avoid']);
  });
  it('oyster sauce raises Molluscs, shrimp paste raises Crustaceans, XO sauce raises both', () => {
    expect(marks(['oyster sauce'], 'mollusc')).toEqual(['avoid']);
    expect(checkHidden(dish('Beef in shrimp paste'), only('crustacean'))[0].mark).toBe('ask');
    expect(checkListed(dish('Fried rice', ['shrimp paste']), only('crustacean'))[0].mark).toBe('avoid');
    expect(checkHidden(dish('XO sauce noodles'), only('crustacean'))[0].mark).toBe('ask');
    expect(checkHidden(dish('XO sauce noodles'), only('mollusc'))[0].mark).toBe('ask');
    expect(checkHidden(dish('Dipping fish sauce'), only('crustacean'))[0].mark).toBe('ask');
  });
  it('a list with both items marks a mixed dish once per item', () => {
    const f = firstPass(dish('Seafood paella', ['rice', 'squid', 'shrimp']), { allergens: ['crustacean', 'mollusc'], custom: [] });
    expect(f.filter((x) => x.kind === 'listed').map((x) => x.allergen).sort()).toEqual(['Crustaceans', 'Molluscs']);
  });
});

describe('saved lists with the old Shellfish item migrate to both new items', () => {
  it('turns shellfish into crustacean + mollusc and keeps order and custom words', () => {
    const m = migrateList({ allergens: ['peanut', 'shellfish', 'milk'], custom: ['kiwi'] })!;
    expect(m.allergens).toEqual(['peanut', 'crustacean', 'mollusc', 'milk']);
    expect(m.custom).toEqual(['kiwi']);
  });
  it('does not duplicate, drops unknown ids, and leaves new lists alone', () => {
    expect(migrateList({ allergens: ['shellfish', 'crustacean', 'bogus'], custom: [] })!.allergens).toEqual(['crustacean', 'mollusc']);
    expect(migrateList({ allergens: ['celery'], custom: [] })!.allergens).toEqual(['celery']);
  });
  it('rejects junk', () => {
    expect(migrateList(null)).toBeNull();
    expect(migrateList({ allergens: 'x' })).toBeNull();
  });
  it('maps kit profile names, including "fish and shellfish" and "wheat/gluten"', () => {
    expect(allergenIdsFromName('shellfish')).toEqual(['crustacean', 'mollusc']);
    expect(allergenIdsFromName('tree nut')).toEqual(['tree_nut']);
    expect(allergenIdsFromName('wheat/gluten')).toEqual(['wheat']);
    expect(allergenIdsFromName('fish')).toEqual(['fish']);
    expect(() => allergenIdsFromName('unobtainium')).toThrow();
  });
});

describe('new items: hidden sources and synonyms', () => {
  const hid = (name: string, id: AllergenId) => checkHidden(dish(name), only(id)).map((f) => f.mark);
  it('sulphites: wine, dried fruit, vinegar', () => {
    expect(hid('Coq au vin with red wine', 'sulphites')).toEqual(['ask']);
    expect(hid('Dried fruit plate', 'sulphites')).toEqual(['ask']);
    expect(marks(['sulfites'], 'sulphites')).toEqual(['avoid']);
    expect(marks(['sulphur dioxide (E220)'], 'sulphites')).toEqual(['avoid']);
  });
  it('mustard: dressings and curries; direct words', () => {
    expect(hid('House dressing', 'mustard')).toEqual(['ask']);
    expect(hid('Chicken curry', 'mustard')).toEqual(['ask']);
    expect(marks(['Dijon mustard'], 'mustard')).toEqual(['avoid']);
  });
  it('celery: stock and celeriac', () => {
    expect(hid('Chicken stock risotto', 'celery')).toEqual(['ask']);
    expect(marks(['celeriac puree'], 'celery')).toEqual(['avoid']);
  });
  it('lupin, buckwheat, kiwi, banana, peach, corn', () => {
    expect(marks(['lupin flour'], 'lupin')).toEqual(['avoid']);
    expect(hid('Gluten-free bread', 'lupin')).toEqual(['ask']);
    expect(marks(['soba noodles'], 'buckwheat')).toEqual(['avoid']);
    expect(hid('Galette complete', 'buckwheat')).toEqual(['ask']);
    expect(marks(['kiwi'], 'kiwi')).toEqual(['avoid']);
    expect(hid('Fruit salad', 'kiwi')).toEqual(['ask']);
    expect(marks(['plantain'], 'banana')).toEqual(['avoid']);
    expect(marks(['nectarine'], 'peach')).toEqual(['avoid']);
    expect(hid('Bellini', 'peach')).toEqual(['ask']);
    expect(marks(['sweetcorn', 'polenta'], 'corn')).toEqual(['avoid']);
    expect(hid('Beef taco', 'corn')).toEqual(['ask']);
  });
  it('wheat also covers barley, rye and oats', () => {
    for (const w of ['barley', 'rye', 'oats', 'spelt']) expect(marks([w], 'wheat')).toEqual(['avoid']);
  });
  it('words that look alike do not trigger', () => {
    expect(marks(['peppercorn', 'corned beef'], 'corn')).toEqual([]);
    expect(marks(['yakisoba'], 'buckwheat')).toEqual([]);
  });
});

describe('multilingual tables (zh ja ko th vi es fr it de pt)', () => {
  const strip = (t: string) => t.replace(/^[*!]/, '');
  const terms = (row: string) => row.split('|').filter(Boolean);

  it('every allergen has words in all ten languages', () => {
    expect(TABLE_LANGS).toHaveLength(10);
    for (const a of ALLERGENS) {
      for (const lang of TABLE_LANGS) {
        expect(terms(MULTI_DIRECT[a.id][lang]).length, `${a.id}/${lang}`).toBeGreaterThan(0);
      }
    }
  });

  it('every table word marks Avoid for its own allergen', () => {
    const misses: string[] = [];
    for (const a of ALLERGENS) {
      for (const lang of TABLE_LANGS) {
        for (const t of terms(MULTI_DIRECT[a.id][lang])) {
          const w = strip(t);
          // Latin words: also try in a menu-like sentence; non-Latin: bare
          const ok = checkListed(dish('x', [w]), only(a.id)).length > 0;
          if (!ok) misses.push(`${a.id}/${lang}: ${w}`);
        }
      }
    }
    expect(misses).toEqual([]);
  });

  it('every multilingual hidden source marks Ask (never Avoid) for its own allergen', () => {
    const misses: string[] = [];
    for (const h of MULTI_HIDDEN) {
      const w = h.term.replace(/^!/, '');
      const f = checkHidden(dish(w), only(h.allergen as AllergenId));
      if (f.length === 0 || f.some((x) => x.mark !== 'ask')) misses.push(`${h.allergen}/${h.lang}: ${w}`);
    }
    expect(misses).toEqual([]);
  });

  it('has hidden sources for every one of the ten languages', () => {
    for (const lang of TABLE_LANGS) expect(MULTI_HIDDEN.filter((h) => h.lang === lang).length, lang).toBeGreaterThan(5);
  });

  // Real menu words, one or more per language and allergen group.
  const real: [TableLang, string, AllergenId][] = [
    ['zh', '鲜虾', 'crustacean'], ['zh', '芝麻', 'sesame'], ['zh', '腰果', 'tree_nut'], ['zh', '蛋黄', 'egg'],
    ['zh', '花生酱', 'peanut'], ['zh', '牛奶', 'milk'], ['zh', '豆腐', 'soy'], ['zh', '鱼露', 'fish'], ['zh', '生蚝', 'mollusc'],
    ['zh', '麵粉', 'wheat'], ['zh', '芹菜', 'celery'], ['zh', '荞麦面', 'buckwheat'], ['zh', '猕猴桃', 'kiwi'], ['zh', '玉米', 'corn'],
    ['ja', 'えび', 'crustacean'], ['ja', 'ごま油', 'sesame'], ['ja', 'くるみ', 'tree_nut'], ['ja', '卵', 'egg'],
    ['ja', 'ピーナッツ', 'peanut'], ['ja', '牛乳', 'milk'], ['ja', '醤油', 'soy'], ['ja', 'まぐろ', 'fish'], ['ja', 'ホタテ', 'mollusc'],
    ['ja', '小麦粉', 'wheat'], ['ja', 'そば', 'buckwheat'], ['ja', 'バナナ', 'banana'], ['ja', '桃', 'peach'],
    ['ko', '새우', 'crustacean'], ['ko', '참기름', 'sesame'], ['ko', '호두', 'tree_nut'], ['ko', '계란', 'egg'],
    ['ko', '땅콩', 'peanut'], ['ko', '우유', 'milk'], ['ko', '간장', 'soy'], ['ko', '고등어', 'fish'], ['ko', '오징어', 'mollusc'],
    ['ko', '밀가루', 'wheat'], ['ko', '메밀', 'buckwheat'], ['ko', '복숭아', 'peach'], ['ko', '옥수수', 'corn'],
    ['th', 'กุ้ง', 'crustacean'], ['th', 'งา', 'sesame'], ['th', 'เม็ดมะม่วงหิมพานต์', 'tree_nut'], ['th', 'ไข่', 'egg'],
    ['th', 'ถั่วลิสง', 'peanut'], ['th', 'เนย', 'milk'], ['th', 'เต้าหู้', 'soy'], ['th', 'น้ำปลา', 'fish'], ['th', 'หอยนางรม', 'mollusc'],
    ['th', 'แป้งสาลี', 'wheat'], ['th', 'กล้วย', 'banana'], ['th', 'ข้าวโพด', 'corn'],
    ['vi', 'tôm', 'crustacean'], ['vi', 'mè', 'sesame'], ['vi', 'hạt điều', 'tree_nut'], ['vi', 'trứng', 'egg'],
    ['vi', 'đậu phộng', 'peanut'], ['vi', 'sữa', 'milk'], ['vi', 'đậu hũ', 'soy'], ['vi', 'nước mắm', 'fish'], ['vi', 'mực', 'mollusc'],
    ['vi', 'bột mì', 'wheat'], ['vi', 'cần tây', 'celery'], ['vi', 'mù tạt', 'mustard'],
    ['es', 'gambas', 'crustacean'], ['es', 'sésamo', 'sesame'], ['es', 'almendras', 'tree_nut'], ['es', 'huevo', 'egg'],
    ['es', 'cacahuete', 'peanut'], ['es', 'queso', 'milk'], ['es', 'soja', 'soy'], ['es', 'bacalao', 'fish'], ['es', 'calamares', 'mollusc'],
    ['es', 'harina', 'wheat'], ['es', 'apio', 'celery'], ['es', 'mostaza', 'mustard'], ['es', 'altramuces', 'lupin'], ['es', 'sulfitos', 'sulphites'],
    ['fr', 'crevettes', 'crustacean'], ['fr', 'sésame', 'sesame'], ['fr', 'noisettes', 'tree_nut'], ['fr', 'œufs', 'egg'],
    ['fr', 'arachides', 'peanut'], ['fr', 'beurre', 'milk'], ['fr', 'soja', 'soy'], ['fr', 'saumon', 'fish'], ['fr', 'moules', 'mollusc'],
    ['fr', 'farine', 'wheat'], ['fr', 'céleri', 'celery'], ['fr', 'moutarde', 'mustard'], ['fr', 'lupin', 'lupin'], ['fr', 'sarrasin', 'buckwheat'], ['fr', 'maïs', 'corn'],
    ['it', 'gamberi', 'crustacean'], ['it', 'sesamo', 'sesame'], ['it', 'pistacchio', 'tree_nut'], ['it', 'uova', 'egg'],
    ['it', 'arachidi', 'peanut'], ['it', 'formaggio', 'milk'], ['it', 'soia', 'soy'], ['it', 'acciughe', 'fish'], ['it', 'vongole', 'mollusc'],
    ['it', 'farina', 'wheat'], ['it', 'sedano', 'celery'], ['it', 'senape', 'mustard'], ['it', 'solfiti', 'sulphites'], ['it', 'pesca', 'peach'],
    ['de', 'Garnelen', 'crustacean'], ['de', 'Sesam', 'sesame'], ['de', 'Haselnuss', 'tree_nut'], ['de', 'Eigelb', 'egg'],
    ['de', 'Erdnusssoße', 'peanut'], ['de', 'Sahne', 'milk'], ['de', 'Sojasoße', 'soy'], ['de', 'Lachs', 'fish'], ['de', 'Miesmuscheln', 'mollusc'],
    ['de', 'Weizenmehl', 'wheat'], ['de', 'Sellerie', 'celery'], ['de', 'Senf', 'mustard'], ['de', 'Lupinenmehl', 'lupin'], ['de', 'Buchweizen', 'buckwheat'], ['de', 'Pfirsich', 'peach'],
    ['pt', 'camarão', 'crustacean'], ['pt', 'gergelim', 'sesame'], ['pt', 'castanha de caju', 'tree_nut'], ['pt', 'ovos', 'egg'],
    ['pt', 'amendoim', 'peanut'], ['pt', 'queijo', 'milk'], ['pt', 'soja', 'soy'], ['pt', 'bacalhau', 'fish'], ['pt', 'polvo', 'mollusc'],
    ['pt', 'farinha', 'wheat'], ['pt', 'aipo', 'celery'], ['pt', 'tremoço', 'lupin'], ['pt', 'milho', 'corn'], ['pt', 'banana', 'banana'],
  ];
  for (const [lang, word, id] of real) {
    it(`${lang}: "${word}" is found for ${id}`, () => {
      expect(marks([word], id)).toEqual(['avoid']);
    });
  }

  it('covers every one of the ten languages in the real-word list', () => {
    expect(new Set(real.map((r) => r[0]))).toEqual(new Set(TABLE_LANGS));
  });
});

describe('look-alike words do not trigger a false Avoid', () => {
  it('Vietnamese accents matter: "cà phê" is not fish, "cá" is', () => {
    expect(marks(['cà phê'], 'fish')).toEqual([]);
    expect(marks(['cá hồi nướng'], 'fish')).toEqual(['avoid']);
    expect(marks(['cà phê sữa đá'], 'milk')).toEqual(['avoid']);
    expect(marks(['sữa dừa'], 'milk')).toEqual([]);
  });
  it('squid and abalone are not fish; they are molluscs', () => {
    expect(marks(['鱿鱼'], 'fish')).toEqual([]);
    expect(marks(['鱿鱼'], 'mollusc')).toEqual(['avoid']);
    expect(marks(['鲍鱼'], 'fish')).toEqual([]);
    expect(marks(['ปลาหมึก'], 'fish')).toEqual([]);
    expect(marks(['ปลาหมึก'], 'mollusc')).toEqual(['avoid']);
    expect(marks(['Tintenfisch'], 'fish')).toEqual([]);
    expect(marks(['Tintenfisch'], 'mollusc')).toEqual(['avoid']);
  });
  it('bread (ขนมปัง), avocado (牛油果), coconut milk and nutmeg are not milk or tree nut', () => {
    expect(marks(['ขนมปัง'], 'milk')).toEqual([]);
    expect(marks(['牛油果'], 'milk')).toEqual([]);
    expect(marks(['leche de coco', 'mantequilla de cacahuete'], 'milk')).toEqual([]);
    expect(marks(['noz moscada'], 'tree_nut')).toEqual([]);
    expect(marks(['noix de coco'], 'tree_nut')).toEqual([]);
    expect(marks(['Erdnussbutter'], 'milk')).toEqual([]);
  });
  it('buckwheat is not wheat; soy sprouts keep soy but peanut is not soy', () => {
    expect(marks(['Buchweizen'], 'wheat')).toEqual([]);
    expect(marks(['trigo sarraceno'], 'wheat')).toEqual([]);
    expect(marks(['땅콩'], 'soy')).toEqual([]);
    expect(marks(['焼きそば'], 'buckwheat')).toEqual([]);
  });
});

describe('English translation fields (safety fix for non-English menus)', () => {
  it('parses {text, english} ingredients and the English dish name', () => {
    const m = parseMenuJson(JSON.stringify({ language: 'zh', dishes: [
      { name: '虾饺', nameEnglish: 'Shrimp dumpling', ingredients: [{ text: '鲜虾', english: 'fresh shrimp' }, { text: '竹笋', english: 'bamboo shoot' }] },
    ] }));
    expect(m.dishes[0]).toEqual({ name: '虾饺', nameEnglish: 'Shrimp dumpling', ingredients: ['鲜虾', '竹笋'], ingredientsEnglish: ['fresh shrimp', 'bamboo shoot'] });
  });
  it('still parses plain-string ingredients', () => {
    expect(parseMenuJson('{"dishes":[{"name":"A","ingredients":["egg","milk"]}]}').dishes[0].ingredients).toEqual(['egg', 'milk']);
  });
  it('matches on the English translation when the original word is unknown', () => {
    // 蝦仁 variant not needed: the translation alone is enough
    const d = dish('X', ['某种酱'], ['sesame paste']);
    expect(checkListed(d, only('sesame'))[0].mark).toBe('avoid');
  });
  it('matches the original word when the translation is wrong or empty', () => {
    const d = dish('X', ['芝麻'], ['seeds']);
    expect(checkListed(d, only('sesame'))[0].mark).toBe('avoid');
  });
  it('hidden sources work on the English dish name too', () => {
    const d = { name: '沙拉', nameEnglish: 'Papaya salad', ingredients: [] as string[] };
    expect(checkHidden(d, only('peanut'))[0].mark).toBe('ask');
  });
});

describe('an ingredient the app cannot read is never "No listed allergen found"', () => {
  const sesameNut: AllergyList = { allergens: ['tree_nut', 'sesame'], custom: [] };
  it('detects non-Latin scripts', () => {
    for (const t of ['鲜虾', 'กุ้ง', '새우', 'エビ', 'креветки', 'جمبري']) expect(hasNonLatinLetters(t), t).toBe(true);
    for (const t of ['shrimp', 'crème fraîche', 'tôm', 'Erdnuss', '12 oz']) expect(hasNonLatinLetters(t), t).toBe(false);
  });
  it('non-Latin ingredient with no English translation -> Ask the kitchen', () => {
    const d = dish('白饭', ['大米']);
    expect(untranslatedIngredients(d)).toEqual(['大米']);
    expect(mergeMarks(firstPass(d, sesameNut)).mark).toBe('ask');
  });
  it('an empty, whitespace or still-non-Latin translation counts as missing', () => {
    for (const en of ['', '  ', '大米']) {
      expect(mergeMarks(firstPass(dish('白饭', ['大米'], [en]), sesameNut)).mark, JSON.stringify(en)).toBe('ask');
    }
  });
  it('with a real English translation and no hit, the dish can be No listed allergen found', () => {
    expect(mergeMarks(firstPass(dish('白饭', ['大米'], ['rice'], 'Plain rice'), sesameNut)).mark).toBe('no_listed');
  });
  it('one untranslated ingredient among translated ones still forces Ask', () => {
    expect(mergeMarks(firstPass(dish('炒饭', ['大米', '葱'], ['rice', '']), sesameNut)).mark).toBe('ask');
  });
  it('a listed allergen still wins with Avoid over the untranslated Ask', () => {
    expect(mergeMarks(firstPass(dish('饭', ['腰果', '大米']), sesameNut)).mark).toBe('avoid');
  });
  it('Thai, Korean and Japanese behave the same', () => {
    for (const ing of ['ข้าว', '쌀', '米']) expect(mergeMarks(firstPass(dish('x', [ing]), sesameNut)).mark, ing).toBe('ask');
  });
  it('a menu in a language the tables do not cover needs English for every ingredient', () => {
    const d = dish('Pierogi', ['ser', 'mąka']);
    expect(mergeMarks(firstPass(d, sesameNut, 'pl')).mark).toBe('ask');
    expect(mergeMarks(firstPass(d, sesameNut, 'de')).mark).toBe('no_listed');
    expect(mergeMarks(firstPass(dish('Pierogi', ['ser', 'mąka'], ['cheese', 'flour']), sesameNut, 'pl')).mark).toBe('no_listed');
  });
  it('a cloud recipe in a non-Latin script also forces Ask', () => {
    const f = applyRecipe({ name: 'X', ingredients: [{ name: '米饭', level: 'common' }, { name: 'rice', level: 'common' }], confident: true }, sesameNut, 'cloud');
    expect(mergeMarks(f).mark).toBe('ask');
  });
});

describe('streamed partial reply', () => {
  const full = JSON.stringify({ language: 'zh', dishes: [
    { name: '虾饺', nameEnglish: 'Shrimp dumpling', ingredients: [{ text: '鲜虾', english: 'shrimp' }] },
    { name: '烧卖', nameEnglish: 'Siu mai', ingredients: [] },
    { name: '白饭', nameEnglish: 'Rice', ingredients: [{ text: '大米', english: 'rice' }] },
  ] });
  it('returns only the whole dishes and the language so far', () => {
    const cut = full.indexOf('白饭') + 4;
    const p = parsePartialMenu(full.slice(0, cut));
    expect(p.language).toBe('zh');
    expect(p.dishes.map((d) => d.name)).toEqual(['虾饺', '烧卖']);
  });
  it('is safe on empty, early and braces-in-strings text', () => {
    expect(parsePartialMenu('').dishes).toEqual([]);
    expect(parsePartialMenu('{"language":"en","dishes":[').dishes).toEqual([]);
    const tricky = '{"language":"en","dishes":[{"name":"Mac } {\\" and cheese","ingredients":[]},{"name":"Soup","ing';
    expect(parsePartialMenu(tricky).dishes.map((d) => d.name)).toEqual(['Mac } {" and cheese']);
  });
  it('the whole reply gives the same dishes as the final parse', () => {
    expect(parsePartialMenu(full).dishes).toEqual(parseMenuJson(full).dishes);
  });
});
