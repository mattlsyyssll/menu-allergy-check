// Dev-only helpers for the Vite dev server (used by vite.config.js, never part of `vite build`):
//  - read-only access to a few kit files so /run.html can load menus and profiles;
//  - POST /kit-save: writes one run JSON to <kit>/runs/<name>.json so results do not depend on browser downloads.
// Held-out KEYS and case data are not reachable: only the exact paths below are served.
import fs from 'node:fs';
import path from 'node:path';
import type { IncomingMessage, ServerResponse } from 'node:http';

/** Exactly these URLs are served. Set 1: menus + profiles + heldout.json. Set 2 (M25-M32): menus + profiles.json + heldout.json. */
export const ALLOWED = /^\/kit\/(menus\/M\d\d\.png|profiles\.json|heldout\.json|set2\/menus\/M(?:2[5-9]|3[0-2])\.png|set2\/profiles\.json|set2\/heldout\.json)$/;
/** Where each allowed URL lives under the kit folder. */
export const KIT_PATH_OF = (url: string) => url.slice('/kit/'.length).replace(/^set2\//, 'heldout-set-2/');

export const MAX_SAVE_BYTES = 100 * 1024 * 1024;

/** File-name part of a saved run: letters, digits, dot, dash, underscore; no leading dot; at most 80 characters; never empty. */
export function sanitizeName(raw: string | null | undefined): string {
  const t = String(raw ?? '').replace(/\.json$/i, '').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^[.-]+/, '').slice(0, 80);
  return t || `run-${new Date().toISOString().replace(/[:.]/g, '-')}`;
}

const sameOrigin = (req: IncomingMessage) => {
  const host = req.headers.host ?? '';
  if (!/^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(host)) return false;
  const origin = req.headers.origin;
  return !origin || origin === `http://${host}`;
};

function send(res: ServerResponse, code: number, text: string) {
  res.statusCode = code;
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.end(text);
}

/** Connect-style middleware. `kitDir` is the absolute kit folder. */
export function kitMiddleware(kitDir: string) {
  return (req: IncomingMessage, res: ServerResponse, next: () => void) => {
    const [url, query = ''] = (req.url || '').split('?');
    if (url === '/kit-save') {
      if (req.method !== 'POST') return send(res, 405, 'POST only');
      if (!sameOrigin(req)) return send(res, 403, 'same-origin localhost only');
      if (!/^application\/json\b/i.test(req.headers['content-type'] ?? '')) return send(res, 415, 'content-type must be application/json');
      const name = sanitizeName(new URLSearchParams(query).get('name'));
      const chunks: Buffer[] = [];
      let size = 0;
      let dead = false;
      req.on('data', (c: Buffer) => {
        size += c.length;
        if (size > MAX_SAVE_BYTES) { dead = true; send(res, 413, 'too large'); req.destroy(); return; }
        chunks.push(c);
      });
      req.on('end', () => {
        if (dead) return;
        try {
          const text = Buffer.concat(chunks).toString('utf8');
          JSON.parse(text); // must be valid JSON
          const dir = path.join(kitDir, 'runs');
          fs.mkdirSync(dir, { recursive: true });
          const file = path.join(dir, `${name}.json`);
          if (!file.startsWith(dir + path.sep)) return send(res, 400, 'bad name');
          fs.writeFileSync(file, text, { flag: 'wx' }); // never overwrites an earlier run
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ saved: path.relative(kitDir, file) }));
        } catch (e) {
          const err = e as NodeJS.ErrnoException;
          if (err.code === 'EEXIST') return send(res, 409, `runs/${name}.json already exists; pick another name`);
          send(res, 400, `not saved: ${err.message}`);
        }
      });
      return;
    }
    if (!ALLOWED.test(url)) return next();
    const file = path.join(kitDir, KIT_PATH_OF(url));
    if (!file.startsWith(kitDir + path.sep) || !fs.existsSync(file)) return send(res, 404, 'not found');
    res.setHeader('Content-Type', file.endsWith('.png') ? 'image/png' : 'application/json');
    res.setHeader('Cache-Control', 'no-store');
    fs.createReadStream(file).pipe(res);
  };
}
