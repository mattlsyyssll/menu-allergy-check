// Dev tool only (not part of `npm test`): offline replay of saved cloud answers through the real pipeline.
// Run: REPLAY=bodies|score npx vitest run --config scripts/replay/vitest.config.ts
export default { test: { include: ['scripts/replay/*.replay.ts'], testTimeout: 600000 } };
