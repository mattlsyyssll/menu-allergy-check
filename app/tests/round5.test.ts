import { describe, expect, it } from 'vitest';
import { MIN_PLAUSIBLE_DISHES, runCheck, type DeviceEngine } from '../src/pipeline';
import type { AllergyList } from '../src/core/core';

// Round 4b: the device model once answered a 10-dish menu with valid JSON holding 1 dish (9.7 s, no error, no timeout).
// The pipeline accepted it, so 9 dishes were silently missing from the result (the kit counted them as unread hazard dishes).

const IMG = 'data:image/jpeg;base64,QUJD';
const list: AllergyList = { allergens: ['milk'], custom: [] };
const dishes = (n: number) => Array.from({ length: n }, (_, i) => ({ name: `Dish ${i + 1}`, nameEnglish: `Dish ${i + 1}`, ingredients: ['rice'] }));
const reply = (n: number) => JSON.stringify({ language: 'en', dishes: dishes(n) });

function device(answers: string[]) {
  const calls: { fresh: boolean }[] = [];
  const d: DeviceEngine = {
    async readMenu(_img, _p, opts) {
      calls.push({ fresh: !!opts?.fresh });
      const a = answers[Math.min(calls.length - 1, answers.length - 1)];
      if (a === 'throw') throw new Error('device boom');
      return a;
    },
  };
  return { d, calls };
}

describe('short device read is read again', () => {
  it('threshold is 3', () => expect(MIN_PLAUSIBLE_DISHES).toBe(3));

  it('1 dish then 10 dishes: the longer read is used, one extra fresh call', async () => {
    const { d, calls } = device([reply(1), reply(10)]);
    const s = await runCheck({ imageDataUrl: IMG, list, device: d });
    expect(s.dishes).toHaveLength(10);
    expect(calls).toEqual([{ fresh: false }, { fresh: true }]);
    expect(s.warnings).toEqual([]);
  });

  it('a normal read (3+ dishes) is not repeated', async () => {
    const { d, calls } = device([reply(3)]);
    const s = await runCheck({ imageDataUrl: IMG, list, device: d });
    expect(s.dishes).toHaveLength(3);
    expect(calls).toHaveLength(1);
  });

  it('still short after the re-read: the longer one is kept and a warning says dishes may be missing', async () => {
    const { d, calls } = device([reply(1), reply(2)]);
    const s = await runCheck({ imageDataUrl: IMG, list, device: d });
    expect(s.dishes).toHaveLength(2);
    expect(calls).toHaveLength(2);
    expect(s.warnings.join(' ')).toMatch(/Only 2 dish/);
    expect(s.message).toMatch(/Only 2 dish/);
  });

  it('a failing re-read keeps the first read and records the failed attempt', async () => {
    const { d } = device([reply(1), 'throw']);
    const s = await runCheck({ imageDataUrl: IMG, list, device: d });
    expect(s.dishes).toHaveLength(1);
    expect(s.events.filter((e) => e.step === 'device' && e.kind === 'error')).toHaveLength(1);
    expect(s.warnings.join(' ')).toMatch(/Only 1 dish/);
  });

  it('a shorter second read never replaces a longer first one', async () => {
    const { d } = device([reply(2), reply(1)]);
    const s = await runCheck({ imageDataUrl: IMG, list, device: d });
    expect(s.dishes).toHaveLength(2);
  });
});
