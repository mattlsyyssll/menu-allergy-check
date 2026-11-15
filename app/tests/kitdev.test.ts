import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { ALLOWED, KIT_PATH_OF, kitMiddleware, sanitizeName } from '../scripts/kit-dev';

let dir = '';
let server: http.Server;
let port = 0;

beforeAll(async () => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'kitdev-'));
  fs.mkdirSync(path.join(dir, 'heldout-set-2', 'menus'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'heldout-set-2', 'keys'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'heldout-set-2', 'menus', 'M25.png'), 'png');
  fs.writeFileSync(path.join(dir, 'heldout-set-2', 'heldout.json'), '{"heldout":["M25"]}');
  fs.writeFileSync(path.join(dir, 'heldout-set-2', 'keys', 'M25.json'), 'SECRET');
  const mw = kitMiddleware(dir);
  server = http.createServer((req, res) => mw(req, res, () => { res.statusCode = 418; res.end('next'); }));
  await new Promise<void>((r) => server.listen(0, '127.0.0.1', r));
  port = (server.address() as { port: number }).port;
});
afterAll(() => { server.close(); fs.rmSync(dir, { recursive: true, force: true }); });

const call = (p: string, init: { method?: string; body?: string; headers?: Record<string, string> } = {}) =>
  fetch(`http://127.0.0.1:${port}${p}`, init).then(async (r) => ({ status: r.status, text: await r.text() }));
const post = (p: string, body: string, headers: Record<string, string> = { 'content-type': 'application/json' }) => call(p, { method: 'POST', body, headers });

describe('set 2 files', () => {
  it('allows exactly the set 2 menus M25-M32, profiles.json and heldout.json', () => {
    for (let n = 25; n <= 32; n++) expect(ALLOWED.test(`/kit/set2/menus/M${n}.png`)).toBe(true);
    for (const u of ['/kit/set2/profiles.json', '/kit/set2/heldout.json', '/kit/menus/M01.png', '/kit/profiles.json', '/kit/heldout.json']) expect(ALLOWED.test(u)).toBe(true);
  });
  it('rejects keys, cases, case data, prompts, traversal, other set 2 menu ids', () => {
    for (const u of ['/kit/set2/keys/M25.json', '/kit/keys/M02.json', '/kit/set2/case-data.json', '/kit/case-data.json', '/kit/set2/cases/M25.json', '/kit/set2/ANSWER-KEYS.md',
      '/kit/set2/prompts/x', '/kit/set2/menus/M24.png', '/kit/set2/menus/M33.png', '/kit/set2/menus/../keys/M25.json', '/kit/set2/../keys/M02.json', '/kit/set2/kit.json',
      '/kit/set2/menus/M25.png/..', '/kit/ANSWER-KEYS.md']) expect(ALLOWED.test(u), u).toBe(false);
  });
  it('maps set2 to heldout-set-2', () => expect(KIT_PATH_OF('/kit/set2/menus/M25.png')).toBe('heldout-set-2/menus/M25.png'));
  it('serves a set 2 menu and falls through for a key path', async () => {
    expect((await call('/kit/set2/menus/M25.png')).text).toBe('png');
    expect((await call('/kit/set2/heldout.json')).status).toBe(200);
    expect((await call('/kit/set2/keys/M25.json')).status).toBe(418);
  });
});

describe('/kit-save', () => {
  it('sanitizes names', () => {
    expect(sanitizeName('app-build6')).toBe('app-build6');
    expect(sanitizeName('../../etc/passwd')).toBe('etc-passwd');
    expect(sanitizeName('a b/c\\d.json')).toBe('a-b-c-d');
    expect(sanitizeName('...hidden')).toBe('hidden');
    expect(sanitizeName('x'.repeat(200))).toHaveLength(80);
    expect(sanitizeName('')).toMatch(/^run-/);
    expect(sanitizeName(null)).toMatch(/^run-/);
  });
  it('writes runs/saved/<name>.json and refuses to overwrite', async () => {
    const r = await post('/kit-save?name=app-build6', '{"a":1}');
    expect(r.status).toBe(200);
    expect(fs.readFileSync(path.join(dir, 'runs', 'saved', 'app-build6.json'), 'utf8')).toBe('{"a":1}');
    expect((await post('/kit-save?name=app-build6', '{"a":2}')).status).toBe(409);
    expect(fs.readFileSync(path.join(dir, 'runs', 'saved', 'app-build6.json'), 'utf8')).toBe('{"a":1}');
  });
  it('a traversal name stays inside runs/saved/', async () => {
    expect((await post('/kit-save?name=../../evil', '{}')).status).toBe(200);
    expect(fs.existsSync(path.join(dir, 'runs', 'saved', 'evil.json'))).toBe(true);
    expect(fs.existsSync(path.join(path.dirname(dir), 'evil.json'))).toBe(false);
  });
  it('rejects GET, non-JSON body, wrong content type and a foreign origin', async () => {
    expect((await call('/kit-save?name=g')).status).toBe(405);
    expect((await post('/kit-save?name=bad', 'not json')).status).toBe(400);
    expect(fs.existsSync(path.join(dir, 'runs', 'saved', 'bad.json'))).toBe(false);
    expect((await post('/kit-save?name=ct', '{}', { 'content-type': 'text/plain' })).status).toBe(415);
    expect((await post('/kit-save?name=orig', '{}', { 'content-type': 'application/json', origin: 'http://evil.example' })).status).toBe(403);
  });
});

describe('set 3 paths', () => {
  it('allows exactly the set 3 menus M33-M40, profiles.json and heldout.json', () => {
    for (let n = 33; n <= 40; n++) expect(ALLOWED.test(`/kit/set3/menus/M${n}.png`)).toBe(true);
    for (const u of ['/kit/set3/profiles.json', '/kit/set3/heldout.json']) expect(ALLOWED.test(u)).toBe(true);
    for (const u of ['/kit/set3/keys/M33.json', '/kit/set3/case-data.json', '/kit/set3/ANSWER-KEYS.md', '/kit/set3/menus/M32.png', '/kit/set3/menus/M41.png', '/kit/set3/kit.json', '/kit/set3/menus/../keys/M33.json'])
      expect(ALLOWED.test(u), u).toBe(false);
  });
  it('maps set3 to heldout-set-3', () => expect(KIT_PATH_OF('/kit/set3/menus/M33.png')).toBe('heldout-set-3/menus/M33.png'));
});

describe('set 4 paths', () => {
  it('allows exactly the set 4 menus M41-M48, profiles.json and heldout.json', () => {
    for (let n = 41; n <= 48; n++) expect(ALLOWED.test(`/kit/set4/menus/M${n}.png`)).toBe(true);
    for (const u of ['/kit/set4/profiles.json', '/kit/set4/heldout.json']) expect(ALLOWED.test(u)).toBe(true);
    for (const u of ['/kit/set4/keys/M41.json', '/kit/set4/case-data.json', '/kit/set4/menus/M40.png', '/kit/set4/menus/M49.png', '/kit/set4/kit.json']) expect(ALLOWED.test(u), u).toBe(false);
  });
  it('maps set4 to heldout-set-4', () => expect(KIT_PATH_OF('/kit/set4/menus/M41.png')).toBe('heldout-set-4/menus/M41.png'));
});

describe('set 5 paths', () => {
  it('allows exactly the set 5 menus M49-M56, profiles.json and heldout.json', () => {
    for (let n = 49; n <= 56; n++) expect(ALLOWED.test(`/kit/set5/menus/M${n}.png`)).toBe(true);
    for (const u of ['/kit/set5/profiles.json', '/kit/set5/heldout.json']) expect(ALLOWED.test(u)).toBe(true);
    for (const u of ['/kit/set5/keys/M49.json', '/kit/set5/case-data.json', '/kit/set5/menus/M48.png', '/kit/set5/menus/M57.png']) expect(ALLOWED.test(u), u).toBe(false);
  });
  it('maps set5 to heldout-set-5', () => expect(KIT_PATH_OF('/kit/set5/menus/M49.png')).toBe('heldout-set-5/menus/M49.png'));
});
