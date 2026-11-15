"""Renderer for set 5: like make_kit.render_menu (read-only import of its helpers) but a column may hold several headed sections,
and a menu may be one column (m['colsplit'] = [3]) or two (m['colsplit'] = [2, 1]). Needs Pillow."""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools'))
from make_kit import *  # noqa: E402,F401,F403
from make_kit import W, BG, LATIN, UNI, font, wrap, apply_style  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def render_menu5(m, out_path):
    rnd = random.Random(m['id'])
    bgc, fg = BG[m['bg']]
    fam = LATIN[m['font']]
    th = m['lang'] == 'th'
    f_title = font((fam[2], fam[3]), 66)
    f_head = font((fam[2], fam[3]), 40)
    f_name = font((fam[2], fam[3]), 34)
    f_desc = font((fam[0], fam[1]), 26)
    f_sub = font(UNI if th else (fam[0], fam[1]), 24)
    f_price = font(UNI if th else (fam[2], fam[3]), 34)
    ncol = len(m['colsplit'])
    if ncol == 1:
        colw = 1000
        margin, gap = (W - colw) // 2, 0
    else:
        margin, gap = 70, 60
        colw = (W - 2 * margin - gap) // 2
    probe = ImageDraw.Draw(Image.new('RGB', (10, 10)))

    def faux_bold(d, xy, t, f):
        d.text(xy, t, font=f, fill=fg)
        d.text((xy[0] + 1, xy[1]), t, font=f, fill=fg)

    def layout(d, col_groups, draw):
        heights = []
        for ci, group in enumerate(col_groups):
            x = margin + ci * (colw + gap)
            y = 230
            for heading, dishes in group:
                if draw:
                    faux_bold(d, (x, y), heading, f_head)
                    d.line([(x, y + 58), (x + colw, y + 58)], fill=fg, width=2)
                y += 85
                for dish in dishes:
                    pw = int(d.textlength(dish['price'], font=f_price))
                    nl = wrap(d, dish['name'], f_name, colw - pw - 20)
                    if draw:
                        for i, ln in enumerate(nl):
                            faux_bold(d, (x, y + i * 42), ln, f_name)
                        d.text((x + colw - pw, y), dish['price'], font=f_price, fill=fg)
                    y += 42 * len(nl)
                    if dish['sub']:
                        if draw:
                            d.text((x, y), dish['sub'], font=f_sub, fill=fg)
                        y += 32
                    for ln in wrap(d, dish['desc'], f_desc, colw):
                        if draw:
                            d.text((x, y), ln, font=f_desc, fill=fg)
                        y += 34
                    y += 26
                y += 30
            heights.append(y)
        return max(heights)

    secs, k = [], 0
    for n in m['colsplit']:
        secs.append(m['sections'][k:k + n])
        k += n
    H = layout(probe, secs, False) + margin
    im = Image.new('RGB', (W, H), bgc)
    d = ImageDraw.Draw(im)
    tw = d.textlength(m['title'], font=f_title)
    faux_bold(d, ((W - tw) / 2, 70), m['title'], f_title)
    d.line([(margin, 175), (W - margin, 175)], fill=fg, width=4)
    layout(d, secs, True)
    im = apply_style(im, m['style'], rnd, bgc)
    im.save(out_path, optimize=True)
    return im.size


