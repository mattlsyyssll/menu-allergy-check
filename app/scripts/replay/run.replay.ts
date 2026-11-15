// Offline replay (dev tool). The device read is replaced by the TRUE printed menu text from the kit's case data,
// and the cloud by a saved cloud answer, then the real pipeline (runCheck) labels every dish for every kit list.
// Use: compare cloud models or rule changes on the same saved answers. It is not the kit's official score:
// the official numbers come only from real runs scored by the kit scripts.
//   REPLAY=bodies  -> writes probe-tmp/bodies.json: the cloud request for each of the 32 menus (dish names only)
//   REPLAY=score FILES=a.json,b.json  -> scores saved answer files ({ menus: { M01: "<reply text>" } }) in kit/runs/saved/ (or a path under kit/runs/)
import fs from 'node:fs';
import path from 'node:path';
import { it } from 'vitest';
import { allergenIdsFromName, buildCloudPayload, RATING_POLICY, type AllergyList } from '../../src/core/core';
import { runCheck, type CloudEngine, type DeviceEngine } from '../../src/pipeline';

const KIT = path.resolve(__dirname, '../../../kit');
type Dish = { printed_name: string; english_gloss?: string; printed_description: string; labels: Record<string, string> };
type Case = { id: string; lang: string; dishes: Dish[] };
const cases: Case[] = [
  ...JSON.parse(fs.readFileSync(path.join(KIT, 'case-data.json'), 'utf8')).cases,
  ...JSON.parse(fs.readFileSync(path.join(KIT, 'heldout-set-2/case-data.json'), 'utf8')).cases,
];
// Set 3 (spent) is replayed with the documented re-score labels (set 1-2 key rules), never its official labels.
if (process.env.SET3) {
  const set3: Case[] = JSON.parse(fs.readFileSync(path.join(KIT, 'heldout-set-3/case-data.json'), 'utf8')).cases;
  const lab: Record<string, Record<string, Record<string, string>>> = JSON.parse(fs.readFileSync(path.join(KIT, 'rescore-set3/labels-rescore.json'), 'utf8'));
  for (const c of set3) for (const d of c.dishes) d.labels = lab[c.id][d.printed_name];
  cases.push(...set3);
}
// Set 4 (spent) is replayed with its official labels (its key follows the named-food rule written before the run).
if (process.env.SET5) cases.push(...(JSON.parse(fs.readFileSync(path.join(KIT, 'heldout-set-5/case-data.json'), 'utf8')).cases as Case[]));
if (process.env.SET4) cases.push(...(JSON.parse(fs.readFileSync(path.join(KIT, 'heldout-set-4/case-data.json'), 'utf8')).cases as Case[]));
// POLICY="often:peanut,tree_nut;possible:all" sets RATING_POLICY for the comparison.
if (process.env.POLICY) {
  for (const part of process.env.POLICY.split(';')) {
    const [k, v] = part.split(':');
    const val = v === 'all' ? 'all' : (v ? v.split(',') : []);
    if (k === 'often') RATING_POLICY.oftenAsk = val as typeof RATING_POLICY.oftenAsk;
    if (k === 'possible') RATING_POLICY.possibleAsk = val as typeof RATING_POLICY.possibleAsk;
  }
}
const profiles: Record<string, { allergens: string[] }> = JSON.parse(fs.readFileSync(path.join(KIT, 'profiles.json'), 'utf8')).profiles;
const listOf = (pid: string): AllergyList => ({ allergens: [...new Set(profiles[pid].allergens.flatMap(allergenIdsFromName))], custom: [] });

const menuJson = (c: Case) => JSON.stringify({
  language: c.lang,
  dishes: c.dishes.map((d) => ({
    name: d.printed_name,
    nameEnglish: d.english_gloss || d.printed_name,
    ingredients: d.printed_description.split(/[,、，]/).map((t) => t.trim()).filter(Boolean).map((t) => ({ text: t, english: t })),
  })),
});
const LABEL = { no_listed: 'No listed allergen found', ask: 'Ask the kitchen', avoid: 'Avoid' } as const;
const IMG = 'data:image/jpeg;base64,QUJD';

it('replay', async () => {
  const mode = process.env.REPLAY;
  if (mode === 'bodies') {
    const out: Record<string, string> = {};
    for (const c of cases) out[c.id] = buildCloudPayload(c.dishes.map((d) => ({ name: d.printed_name, nameEnglish: d.english_gloss || '' }))).prompt;
    fs.mkdirSync(path.resolve(__dirname, '../../probe-tmp'), { recursive: true });
    fs.writeFileSync(path.resolve(__dirname, '../../probe-tmp/bodies.json'), JSON.stringify(out));
    console.log(`bodies for ${Object.keys(out).length} menus`);
    return;
  }
  const files = (process.env.FILES || '').split(',').filter(Boolean);
  const rows: string[] = ['| Answers | Menus | Hazards | Caught | Recall | False-safe | Clean | Over-caution | Label accuracy |', '|---|---|---|---|---|---|---|---|---|'];
  const misses: string[] = [];
  const overBy: Record<string, number> = {};
  for (const f of files) {
    const saved = JSON.parse(fs.readFileSync(fs.existsSync(path.join(KIT, 'runs', 'saved', f)) ? path.join(KIT, 'runs', 'saved', f) : path.join(KIT, 'runs', f), 'utf8'));
    let haz = 0, caught = 0, fs_ = 0, clean = 0, over = 0, exact = 0, n = 0, menus = 0;
    for (const c of cases) {
      const reply: string | undefined = saved.menus?.[c.id];
      if (reply === undefined && process.env.CLOUD !== 'off') continue;
      menus++;
      const device: DeviceEngine = { readMenu: async () => menuJson(c) };
      const cloud: CloudEngine | undefined = reply === undefined ? undefined : { recipes: async () => reply };
      for (const pid of Object.keys(profiles)) {
        const st = await runCheck({ imageDataUrl: IMG, list: listOf(pid), device, cloud });
        c.dishes.forEach((d, i) => {
          const got = LABEL[st.dishes[i]?.decision?.mark ?? 'ask'];
          const want = d.labels[pid];
          n++; if (got === want) exact++;
          if (process.env.ALL) fs.appendFileSync(process.env.ALL, JSON.stringify({ file: f, case: c.id, lang: c.lang, dish: d.printed_name, pid, want, got, findings: st.dishes[i]?.decision?.findings ?? [] }) + '\n');
          if (want !== LABEL.no_listed) { haz++; if (got !== LABEL.no_listed) caught++; else { fs_++; misses.push(`${f} ${c.id} ${d.printed_name} ${pid}`); } }
          else { clean++; if (got !== LABEL.no_listed) { over++;
            const dec = st.dishes[i]?.decision;
            const top = dec ? dec.findings.filter((x) => x.mark === dec.mark) : [];
            const key = [...new Set(top.map((x) => `${x.kind}:${x.source}`))].sort().join('+') || 'no decision';
            const k2 = `${c.lang === 'en' ? 'en' : 'non-en'} ${key}`; overBy[k2] = (overBy[k2] ?? 0) + 1;
            if (process.env.DETAIL) fs.appendFileSync(process.env.DETAIL, JSON.stringify({ file: f, case: c.id, lang: c.lang, dish: d.printed_name, pid, mark: dec?.mark, findings: top }) + '\n'); } }
        });
      }
    }
    const pct = (a: number, b: number) => (b ? `${(100 * a / b).toFixed(1)}%` : 'n/a');
    rows.push(`| ${f} | ${menus} | ${haz} | ${caught} | ${pct(caught, haz)} | ${fs_} | ${clean} | ${pct(over, clean)} | ${pct(exact, n)} |`);
  }
  console.log(rows.join('\n'));
  console.log('False-safe:\n' + misses.join('\n'));
  const ob = Object.entries(overBy).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${v} ${k}`).join('\n');
  console.log('Over-caution causes:\n' + ob);
  if (process.env.OUT) fs.appendFileSync(process.env.OUT, '');
  if (process.env.OUT) fs.writeFileSync(process.env.OUT, rows.join('\n') + '\n\nFalse-safe:\n' + misses.join('\n') + '\n\nOver-caution causes (language, deciding finding kinds):\n' + Object.entries(overBy).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${v} ${k}`).join('\n') + '\n');
});
