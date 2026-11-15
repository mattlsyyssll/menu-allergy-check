// Firebase AI Logic hybrid inference wrapper.
//  - ONLY_ON_DEVICE for everything that touches the photo or the allergy list: it can never
//    fall back to the cloud, so a failure shows up as an error instead of a silent upload.
//  - ONLY_IN_CLOUD for the dish-names-only recipe lookup (one request per menu, all dish names).
// The Firebase config comes from VITE_FIREBASE_* env vars. With no config the on-device path
// still runs (placeholder app, never used for network) and the cloud step is off.

import { initializeApp, type FirebaseApp } from 'firebase/app';
import { initializeAppCheck, ReCaptchaEnterpriseProvider } from 'firebase/app-check';
import { getAI, getGenerativeModel, GoogleAIBackend, InferenceMode, InferenceSource, Schema, type GenerativeModel } from 'firebase/ai';
import { CLOUD_ALLERGEN_IDS, type CloudPayload } from './core/core';
import type { CloudEngine, DeviceEngine } from './pipeline';

const env = import.meta.env;
const cfg = {
  apiKey: env.VITE_FIREBASE_API_KEY as string | undefined,
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN as string | undefined,
  projectId: env.VITE_FIREBASE_PROJECT_ID as string | undefined,
  storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET as string | undefined,
  messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID as string | undefined,
  appId: env.VITE_FIREBASE_APP_ID as string | undefined,
};

export const cloudConfigured = Boolean(cfg.apiKey && cfg.projectId && cfg.appId);
// Dev only: ?model=NAME on the page overrides the cloud model, to compare models on the same requests.
const devModel = env.DEV && typeof location !== 'undefined' ? new URLSearchParams(location.search).get('model') : null;
export const CLOUD_MODEL = devModel || (env.VITE_CLOUD_MODEL as string | undefined) || 'gemini-3.5-flash-lite';

const MENU_PROMPT =
  'Read this restaurant menu photo. Reply with JSON only. ' +
  '"language": the menu\'s main language as a two-letter ISO 639-1 code (en, zh, ja, ko, th, vi, es, fr, it, de, pt...). ' +
  '"dishes": every dish on the menu, in reading order, from every section and column. ' +
  'A section heading (such as Starters, Snacks and Desserts, Drinks) is not a dish: list each dish under it as its own dish. ' +
  '"name": the dish name exactly as printed, in the original language and script. ' +
  '"nameEnglish": an English translation of the dish name (copy the name if it is already English). ' +
  '"ingredients": only the ingredients printed on the menu for that dish, as separate items; use an empty list if none are printed. ' +
  'For each ingredient, "text" is the ingredient exactly as printed and "english" is its English translation ' +
  '(copy it if it is already English). Never leave "english" empty. Do not guess or add ingredients.';

const MENU_SCHEMA = {
  type: 'object',
  properties: {
    language: { type: 'string' },
    dishes: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          nameEnglish: { type: 'string' },
          ingredients: {
            type: 'array',
            items: {
              type: 'object',
              properties: { text: { type: 'string' }, english: { type: 'string' } },
              required: ['text', 'english'],
            },
          },
        },
        required: ['name', 'nameEnglish', 'ingredients'],
      },
    },
  },
  required: ['language', 'dishes'],
};

const CREATE_OPTIONS = {
  expectedInputs: [{ type: 'text' as const, languages: ['en'] }, { type: 'image' as const }],
  expectedOutputs: [{ type: 'text' as const, languages: ['en'] }],
};

// App Check guards the cloud model against abuse (enforced for Firebase AI Logic).
// Live site: Fraud Defense (reCAPTCHA Enterprise) site key in VITE_RECAPTCHA_V3_KEY.
// Local development: the App Check debug provider; register the token it prints in the Firebase console.
function startAppCheck(a: FirebaseApp) {
  const siteKey = import.meta.env.VITE_RECAPTCHA_V3_KEY as string | undefined;
  // localhost is not a reCAPTCHA domain, so the dev server always uses the registered debug token.
  if (import.meta.env.DEV) {
    (self as unknown as { FIREBASE_APPCHECK_DEBUG_TOKEN?: boolean | string }).FIREBASE_APPCHECK_DEBUG_TOKEN =
      (import.meta.env.VITE_APPCHECK_DEBUG_TOKEN as string | undefined) || true;
  }
  initializeAppCheck(a, {
    provider: new ReCaptchaEnterpriseProvider(siteKey || 'debug-only'),
    isTokenAutoRefreshEnabled: true,
  });
}

let app: FirebaseApp | undefined;
function getApp(): FirebaseApp {
  if (!app) {
    app = initializeApp(cloudConfigured
      ? cfg
      // Placeholder so the SDK can run on-device only. ONLY_ON_DEVICE never sends a network request.
      : { apiKey: 'local-only', projectId: 'local-only', appId: '1:0:web:local' });
    if (cloudConfigured) startAppCheck(app);
  }
  return app;
}

let menuModel: GenerativeModel | undefined;
let cloudModel: GenerativeModel | undefined;

function deviceModel(schema: object): GenerativeModel {
  const ai = getAI(getApp(), { backend: new GoogleAIBackend() });
  return getGenerativeModel(ai, {
    mode: InferenceMode.ONLY_ON_DEVICE,
    onDeviceParams: { createOptions: CREATE_OPTIONS, promptOptions: { responseConstraint: schema } },
  });
}

function getMenuModel() { return (menuModel ??= deviceModel(MENU_SCHEMA)); }
function getCloudModel() {
  if (!cloudConfigured) return undefined;
  if (!cloudModel) {
    const ai = getAI(getApp(), { backend: new GoogleAIBackend() });
    cloudModel = getGenerativeModel(ai, {
      mode: InferenceMode.ONLY_IN_CLOUD,
      inCloudParams: {
        model: CLOUD_MODEL,
        generationConfig: {
          responseMimeType: 'application/json',
          responseSchema: Schema.object({
            properties: {
              dishes: Schema.array({
                items: Schema.object({
                  properties: {
                    name: Schema.string(),
                    confident: Schema.boolean(),
                    // Rating for ALL allergen categories (fixed list, same for every user).
                    ratings: Schema.array({
                      items: Schema.object({
                        properties: {
                          allergen: Schema.enumString({ enum: [...CLOUD_ALLERGEN_IDS] }),
                          rating: Schema.enumString({ enum: ['usually', 'often', 'rarely', 'unknown'] }),
                          why: Schema.string(),
                        },
                      }),
                    }),
                    ingredients: Schema.array({
                      items: Schema.object({
                        properties: {
                          name: Schema.string(),
                          level: Schema.enumString({ enum: ['essential', 'common', 'possible'] }),
                        },
                      }),
                    }),
                  },
                }),
              }),
            },
          }),
        },
      },
    });
  }
  return cloudModel;
}

// Timeouts and the one retry live in src/pipeline.ts (withTimeoutRetry): device read 90 s, cloud 45 s.

export type DeviceStatus = 'unsupported' | 'downloadable' | 'downloading' | 'available' | 'ready' | 'error';

/** What the browser says about the built-in model (before any download). */
export async function deviceAvailability(): Promise<DeviceStatus> {
  const LM = (globalThis as { LanguageModel?: { availability(o?: unknown): Promise<string> } }).LanguageModel;
  if (!LM) return 'unsupported';
  try {
    const a = await LM.availability(CREATE_OPTIONS);
    return a === 'unavailable' ? 'unsupported' : (a as DeviceStatus);
  } catch { return 'error'; }
}

/** Warm the on-device model. Needs a user gesture the first time the model must download. */
export async function warmDevice(onProgress?: (fraction: number) => void): Promise<void> {
  await getMenuModel().initializeDeviceModel(onProgress);
}

export const deviceEngine: DeviceEngine = {
  async readMenu(imageDataUrl, onPartial) {
    const m = imageDataUrl.match(/^data:(image\/(?:jpeg|png));base64,(.+)$/);
    if (!m) throw new Error('Photo must be JPEG or PNG');
    const parts = [MENU_PROMPT, { type: 'inlineData' as const, inlineData: { data: m[2], mimeType: m[1] } }];
    const run = async (): Promise<string> => {
      if (!onPartial) {
        const result = await getMenuModel().generateContent(parts);
        if (result.response.inferenceSource !== InferenceSource.ON_DEVICE) throw new Error('Reply did not come from the device model');
        return result.response.text();
      }
      // Streamed: the screen shows finished dishes while the model is still writing.
      const streamed = await getMenuModel().generateContentStream(parts);
      let text = '';
      for await (const chunk of streamed.stream) {
        text += chunk.text();
        onPartial(text);
      }
      const final = await streamed.response;
      if (final.inferenceSource !== InferenceSource.ON_DEVICE) throw new Error('Reply did not come from the device model');
      return final.text() || text;
    };
    return run();
  },
};

/** Undefined when no Firebase config is present ("cloud step off"). */
export const cloudEngine: CloudEngine | undefined = cloudConfigured
  ? {
      async recipes(payload: CloudPayload) {
        const model = getCloudModel()!;
        const result = await model.generateContent(payload.prompt);
        if (result.response.inferenceSource !== InferenceSource.IN_CLOUD) throw new Error('Reply did not come from the cloud model');
        return result.response.text();
      },
    }
  : undefined;
