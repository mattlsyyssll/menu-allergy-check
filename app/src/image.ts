// Photo helpers: shrink a photo to a JPEG data URL the on-device model can take
// (the on-device image limit is small), and draw a sample menu for trying the app.

export async function fileToDataUrl(file: Blob, maxSide = 1280): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const h = Math.round(bitmap.height * scale);
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, w, h);
  ctx.drawImage(bitmap, 0, 0, w, h);
  bitmap.close();
  return canvas.toDataURL('image/jpeg', 0.85);
}

export const SAMPLE_DISHES: { name: string; ingredients: string }[] = [
  { name: 'Pad Thai', ingredients: 'rice noodles, egg, tofu, bean sprouts, crushed peanuts' },
  { name: 'Green Papaya Salad', ingredients: 'green papaya, lime, chili, tomato, long beans' },
  { name: 'Chicken Satay', ingredients: 'grilled chicken skewers, cucumber relish' },
  { name: 'Grilled Salmon', ingredients: 'salmon, steamed rice, bok choy' },
  { name: 'Khao Soi', ingredients: '' },
  { name: 'Mango Sticky Rice', ingredients: 'mango, sticky rice, coconut milk' },
];

export function sampleMenuDataUrl(): string {
  const canvas = document.createElement('canvas');
  canvas.width = 900;
  canvas.height = 560;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = '#fffdf7';
  ctx.fillRect(0, 0, 900, 560);
  ctx.fillStyle = '#222';
  ctx.font = 'bold 34px Georgia, serif';
  ctx.fillText('Lotus Kitchen - Dinner Menu', 40, 56);
  let y = 112;
  for (const d of SAMPLE_DISHES) {
    ctx.font = 'bold 26px Georgia, serif';
    ctx.fillText(d.name, 40, y);
    if (d.ingredients) {
      ctx.font = '20px Georgia, serif';
      ctx.fillText(d.ingredients, 40, y + 26);
    }
    y += 76;
  }
  return canvas.toDataURL('image/png');
}
