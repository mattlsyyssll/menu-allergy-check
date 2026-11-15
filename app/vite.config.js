// Dev-only: serve a few read-only files of the test kit at /kit/* so the batch runner page (/run.html)
// can load menu images, profiles.json and heldout.json (set 1, and held-out set 2 under /kit/set2/*), and accept
// POST /kit-save to write a run JSON to <kit>/runs/<name>.json. Nothing else of the kit is reachable (no keys,
// no answer files). The plugin has no effect on `vite build`, and run.html is not part of the build.
// Logic and tests: scripts/kit-dev.ts, tests/kitdev.test.ts.
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { kitMiddleware } from './scripts/kit-dev.ts';

const here = path.dirname(fileURLToPath(import.meta.url));
const kitDir = path.resolve(here, process.env.KIT_DIR || '../kit');

function kitFiles() {
  return {
    name: 'kit-files-dev-only',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use(kitMiddleware(kitDir));
    },
  };
}

export default { plugins: [kitFiles()] };
