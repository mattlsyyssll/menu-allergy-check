// Dishes whose recipe changes day to day or cook to cook ("soup of the day", "chef's special", "seasonal").
// No recipe lookup can describe them, so they are always at least "Ask the kitchen".
// Latin-script words match whole words with accents ignored; words in other scripts match anywhere in the name.

const LATIN: string[] = [
  // English
  'of the day', 'du jour', 'special', 'specials', "chef's", 'chefs', 'chef', 'seasonal', 'season', 'market', 'daily', 'house', 'today', "today's", 'catch of the day', 'soup of the day',
  // Italian
  'del giorno', 'di giornata', 'del giorno', 'di stagione', 'dello chef', 'della casa', 'del mercato', 'mercato', 'speciale',
  // French
  'du jour', 'de saison', 'du chef', 'du marche', 'de la maison', 'maison', 'special', 'speciaux',
  // Spanish
  'del dia', 'de temporada', 'del chef', 'de la casa', 'del mercado', 'mercado', 'especial', 'sugerencia',
  // Portuguese
  'do dia', 'da estacao', 'de estacao', 'do chef', 'da casa', 'do mercado', 'prato do dia', 'sugestao',
  // German
  'des tages', 'tagessuppe', 'tagesgericht', 'tagesangebot', 'tagesfisch', 'saisonal', 'saison', 'vom chef', 'des hauses', 'hausgemacht', 'marktfrisch', 'tages',
  // Vietnamese (accent-folded)
  'cua ngay', 'hom nay', 'theo mua', 'dac biet', 'dau bep', 'cua nha',
];
// Substring words for scripts without spaces or with their own word rules.
const OTHER: string[] = [
  // Chinese (simplified and traditional)
  '今日', '今天', '每日', '日替', '例汤', '例湯', '时令', '時令', '当季', '當季', '厨师', '廚師', '主厨', '主廚', '招牌', '特选', '特選', '特色', '特別', '特别', '本店', '市场', '市場', '店家',
  // Japanese
  '本日', '日替わり', '季節', 'シェフ', 'おまかせ', 'お任せ', '本日の', 'スペシャル', '当店', '週替わり',
  // Korean
  '오늘의', '오늘', '시즌', '계절', '셰프', '쉐프', '특선', '스페셜', '하우스',
  // Thai
  'ประจำวัน', 'วันนี้', 'ตามฤดูกาล', 'เชฟ', 'พิเศษ', 'ประจำร้าน', 'เมนูแนะนำ',
];

const fold = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().replace(/[’`]/g, "'");
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const RE = new RegExp(`(?<![a-z0-9])(?:${[...new Set(LATIN)].sort((a, b) => b.length - a.length).map(esc).join('|')})(?![a-z0-9])`);

/** The word that makes the dish variable, or null. Checks the printed name and the English name. */
export function variableDishWord(...names: (string | undefined)[]): string | null {
  for (const n of names) {
    if (!n) continue;
    const f = fold(n);
    const m = RE.exec(f);
    if (m) return m[0];
    const lower = n.normalize('NFC').toLowerCase();
    for (const w of OTHER) if (lower.includes(w)) return w;
  }
  return null;
}
