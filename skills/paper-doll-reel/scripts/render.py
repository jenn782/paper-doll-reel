"""Paper-doll stop-motion lookbook reel: big cut-out heads on cut-out outfits, driven by a JSON config.

  python render.py looks.json            -> renders frames + MP4 (silent AAC track, metadata stripped)
  python render.py looks.json --stills   -> only writes one PNG per look (fast check of the dolls)

Beats: hook (thumbnails pop on, crayon writes the hook) -> one beat per look (starburst pops, doll drops
in and walks on the spot, crayon writes the label, prop bobs, optional day timeline and scrolling feed)
-> CTA lines + vehicle drives in, parks, drives off. 6 fps stop motion inside a 30 fps file.
See ../SKILL.md for the config fields.
"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

STEP = 5  # frames per stop-motion pose (30 fps / 5 = 6 poses a second)
rng = np.random.default_rng(7)


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fit(im, w):
    return im.resize((max(1, round(w)), max(1, round(im.height * w / im.width))), Image.LANCZOS)


def padded(im, p=40):
    c = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p))
    c.alpha_composite(im, (p, p))
    return c


def tight(im):
    return im.crop(im.getchannel('A').getbbox())


def paste_rot(canvas, im, cx, top, rot):
    r = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(r, (int(cx - r.width / 2), int(top - (r.height - im.height) / 2)))


def paper_outline(im, cream=(238, 227, 210)):
    # torn cream paper edge + soft rose shadow round the whole sticker
    a = im.getchannel('A')
    for _ in range(3):
        a = a.filter(ImageFilter.MaxFilter(9))
    a = a.filter(ImageFilter.GaussianBlur(3))
    noise = Image.fromarray((rng.random((im.height, im.width)) * 90).astype('uint8')).filter(ImageFilter.GaussianBlur(1.5))
    arr = np.asarray(a).astype(int) + np.asarray(noise).astype(int) - 45
    edge = Image.fromarray(np.where(arr > 110, 255, 0).astype('uint8')).filter(ImageFilter.GaussianBlur(0.8))
    tex = (np.array(cream) + rng.normal(0, 5, (im.height, im.width, 1))).clip(0, 255).astype('uint8')
    paper = Image.fromarray(tex, 'RGB').convert('RGBA')
    paper.putalpha(edge)
    sh = Image.new('RGBA', im.size, (150, 60, 95, 0))
    sh.putalpha(edge.point(lambda v: v * 0.55).filter(ImageFilter.GaussianBlur(8)))
    out = Image.new('RGBA', im.size)
    out.alpha_composite(sh, (6, 12))
    out.alpha_composite(paper)
    out.alpha_composite(im)
    return out


def runs(row):
    out, s = [], None
    for x, v in enumerate(row):
        if v and s is None:
            s = x
        if not v and s is not None:
            out.append((s, x)); s = None
    if s is not None:
        out.append((s, len(row)))
    return [r for r in out if r[1] - r[0] > 4]


def measure_legs(bottoms):
    # find the crotch (first row with two leg runs), the gap column, hip pivots and hem centres
    a = np.asarray(bottoms.getchannel('A')) > 100
    h, w = a.shape
    split = next((y for y in range(int(h * 0.15), h) if len(runs(a[y])) == 2), None)
    if split is None:
        return None  # skirt / one piece: no leg split
    (l0, l1), (r0, r1) = runs(a[split])
    gap = (l1 + r0) / 2
    hip_row = runs(a[min(split + 10, h - 1)])
    hem = runs(a[int(h * 0.96)])
    hem = hem if len(hem) == 2 else [(l0, l1), (r0, r1)]
    return dict(split=split, gap=gap, hip=max(split - h * 0.02, 0),
                lx=(hip_row[0][0] + hip_row[0][1]) / 2 if len(hip_row) == 2 else (l0 + l1) / 2,
                rx=(hip_row[1][0] + hip_row[1][1]) / 2 if len(hip_row) == 2 else (r0 + r1) / 2,
                hem_l=(hem[0][0] + hem[0][1]) / 2, hem_r=(hem[1][0] + hem[1][1]) / 2)


def walk_legs(bottoms, m, a, pad=60):
    # split at the crotch; legs swing opposite ways round each hip; waist piece overlaps the leg tops
    w, h = bottoms.size
    arr = np.zeros((h, w + 2 * pad, 4), 'uint8')
    arr[:, pad:pad + w] = np.asarray(bottoms)
    top, left, right = arr.copy(), arr.copy(), arr.copy()
    split, gap = int(m['split']), int(pad + m['gap'])
    top[split + 10:] = 0
    left[:split] = 0; left[:, gap:] = 0
    right[:split] = 0; right[:, :gap] = 0
    out = Image.new('RGBA', (w + 2 * pad, h))
    for leg, lx, ang in ((left, m['lx'], a), (right, m['rx'], -a)):
        out.alpha_composite(Image.fromarray(leg).rotate(ang, resample=Image.BICUBIC, center=(pad + lx, m['hip'])))
    out.alpha_composite(Image.fromarray(top))
    return out, (h - m['hip']) * np.sin(np.radians(a)), pad


POSES = [  # head rot, head dx, top rot, bottoms rot (if no split), whole tilt
    (-4, -4, -2, 1, -2), (3, 3, 1, -1, 1), (-6, -2, 2, 2, -1),
    (2, 4, -1, 0, 2), (5, 0, 1, -2, 0), (-3, -3, -2, 1, -2)]


def build_look(look, root, head_px):
    """Six stop-motion poses of one doll. Every size is a multiple of the head width, so heads match across looks."""
    ld = lambda p: Image.open(os.path.join(root, p)).convert('RGBA')
    if look.get('body'):  # one full-body sticker (no separate parts): stop-motion it with tilt + tiny squash
        b = fit(ld(look['body']), head_px * look.get('body_w', 1.0))
        b = paper_outline(padded(b))
        return [tight(b.resize((b.width, int(b.height * sq)), Image.LANCZOS).rotate(t, resample=Image.BICUBIC, expand=True))
                for t, sq in ((-3, 1.0), (2, 0.98), (-1, 1.01), (3, 0.99), (0, 1.0), (-2, 0.985))]
    heads = [fit(ld(p), head_px) for p in look['heads']]
    top = fit(ld(look['top']), head_px * look.get('top_w', 0.85))
    bottoms = fit(ld(look['bottoms']), head_px * look.get('bottoms_w', 0.55))
    shoe = fit(ld(look['shoe']), head_px * look.get('shoe_w', 0.42)) if look.get('shoe') else None
    if shoe is not None and look.get('shoe_faces', 'left') == 'right':
        shoe = shoe.transpose(Image.FLIP_LEFT_RIGHT)
    ankle = look.get('shoe_ankle', 0.65)  # where the ankle sits across the shoe (0 = toe end on the left)
    arms = fit(ld(look['arms']), top.width * look.get('arms_w', 1.15)) if look.get('arms') else None
    hands = [fit(ld(look[k]), head_px * look.get('hand_w', 0.35)) for k in ('hand_left', 'hand_right') if look.get(k)]
    m = measure_legs(bottoms) if look.get('walk', True) else None
    stride = look.get('stride', 7)
    out = []
    for i, (hrot, hdx, trot, brot, tilt) in enumerate(POSES):
        h = heads[i % len(heads)]
        c = Image.new('RGBA', (int(head_px * 3), int(head_px * 6)))
        cx = c.width // 2
        top_y = 60 + int(h.height * look.get('chin', 0.62)) - int(head_px * 0.04)
        bot_y = top_y + int(top.height * look.get('waist', 0.75))
        a = stride if i % 2 == 0 else -stride
        if m:
            legs, swing, pad = walk_legs(bottoms, m, a)
            c.alpha_composite(legs, (cx - legs.width // 2, bot_y))
            hem_l, hem_r = m['hem_l'] - bottoms.width / 2, m['hem_r'] - bottoms.width / 2
        else:
            paste_rot(c, bottoms, cx, bot_y, brot)
            swing, hem_l, hem_r = 0, -bottoms.width * 0.22, bottoms.width * 0.22
        if shoe is not None:
            sy = bot_y + bottoms.height - int(shoe.height * 0.55)
            spread = look.get('shoe_spread', 0.06) * head_px  # pushes the pair apart so they never stack
            lift_l, lift_r = (0, 10) if a > 0 else (10, 0)
            c.alpha_composite(shoe, (int(cx + hem_r + spread - ankle * shoe.width - 0.6 * swing), sy - 6 - lift_r))
            c.alpha_composite(shoe, (int(cx + hem_l - spread - ankle * shoe.width + 0.6 * swing), sy - lift_l))
        if arms is not None:  # behind the top, split and nudged out so they hang from the sleeves
            ay = top_y + int(top.height * look.get('arms_y', 0.3))
            sw, half, out_px = (-5 if i % 2 else 0), arms.width // 2, int(head_px * look.get('arms_out', 0.05))
            c.alpha_composite(arms.crop((0, 0, half, arms.height)), (cx - half - out_px, ay + sw))
            c.alpha_composite(arms.crop((half, 0, arms.width, arms.height)), (cx + out_px, ay - sw))
        paste_rot(c, top, cx, top_y, trot)
        for k, hand in enumerate(hands):  # props held at the cuffs
            side = -1 if k == 0 else 1
            paste_rot(c, hand, cx + side * top.width * 0.42, top_y + top.height * 0.82 - hand.height * 0.4, side * 6 - trot * 2)
        paste_rot(c, h, cx + hdx, 60, hrot)
        c = tight(c)
        c = paper_outline(padded(c)).rotate(tilt, resample=Image.BICUBIC, expand=True)
        out.append(tight(c))
    return out


def kid_text(s, font, size, ink, index=0):
    # kid handwriting: every letter wobbles in size, angle and baseline, then gets a waxy crayon texture
    r = np.random.default_rng(3)
    cells = []
    for ch in s:
        f = ImageFont.truetype(font, int(size * r.uniform(0.88, 1.12)), index=index)
        l, t, rr, b = f.getbbox(ch) if ch.strip() else (0, 0, size // 3, size)
        P = size // 2  # room for the tilt and descenders (a tight cell clipped the tail of g/y/j)
        g = Image.new('L', (max(rr - l, 1) + 2 * P, size * 3))
        if ch.strip():
            ImageDraw.Draw(g).text((P - l, size // 2), ch, font=f, fill=255)
        cells.append((g.rotate(r.uniform(-9, 9), resample=Image.BICUBIC), rr - l, int(r.uniform(-10, 10))))
    P = size // 2
    m = Image.new('L', (sum(w for _, w, _ in cells) + 4 * len(cells) + 2 * P + 80, size * 3 + 40))
    x = P + 20
    for g, w, dy in cells:
        box = (x - P, 20 + dy, x - P + g.width, 20 + dy + g.height)
        m.paste(Image.fromarray(np.maximum(np.asarray(m.crop(box)), np.asarray(g))), box[:2])
        x += w + 4
    m = m.crop(m.getbbox())
    a = np.asarray(m).astype(float) / 255
    streak = np.repeat(rng.random((1, a.shape[1])), a.shape[0], 0) * 0.35
    a = a * np.clip(0.55 + 0.6 * rng.random(a.shape) - streak, 0, 1)
    out = Image.new('RGBA', m.size, ink + (0,))
    out.putalpha(Image.fromarray((a * 255).astype('uint8')))
    return out


def bold_text(s, font, size, fill, shadow):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(s)
    im = Image.new('RGBA', (r - l + 60, b - t + 60))
    ImageDraw.Draw(im).text((30 - l, 36 - t), s, font=f, fill=shadow + (150,))
    im = im.filter(ImageFilter.GaussianBlur(5))
    ImageDraw.Draw(im).text((30 - l, 30 - t), s, font=f, fill=fill + (255,))
    return im


def pen_from(im):
    # crayon image with the tip on the RIGHT -> turned so the tip points down-left; returns image + tip pixel
    r = im.rotate(205, resample=Image.BICUBIC, expand=True)
    ys, xs = np.nonzero(np.asarray(r.getchannel('A')) > 128)
    i = np.argmax(ys - xs)
    return r, (xs[i], ys[i])


def write_on(im, f, t, x, y, f0, f1, pen):
    # crayon writes t left to right between frames f0..f1, then flies off top-right
    k = min(max((f - f0) / (f1 - f0), 0), 1)
    if k <= 0:
        return
    cut = int(t.width * k)
    im.alpha_composite(t.crop((0, 0, cut, t.height)), (x, y))
    pos = None
    if k < 1:
        pos = (x + cut, y + t.height * (0.5 + 0.3 * np.sin(f * 2.3)))
    elif f < f1 + 8:
        e = (f - f1) / 8
        pos = (x + t.width + 500 * e ** 1.5, y - 600 * e ** 1.5)
    if pos and pen:
        img, tip = pen
        im.alpha_composite(img, (int(pos[0] - tip[0]), int(pos[1] - tip[1])))


def starburst(r_out, r_in, color, n=18):
    s = r_out * 2 + 20
    im = Image.new('RGBA', (s, s))
    pts = []
    for k in range(n * 2):
        ang = np.pi * k / n
        r = (r_out if k % 2 == 0 else r_in) * (1 + 0.06 * np.sin(k * 1.7))  # hand-cut, not perfect
        pts.append((s / 2 + r * np.cos(ang), s / 2 + r * np.sin(ang)))
    ImageDraw.Draw(im).polygon(pts, fill=color + (255,))
    return im


def feed_strip(folder, W, wash, mix=0.5):
    # a 3-column IG-style grid from screenshots / reel frames, tall enough to scroll
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')))
    tiles = [Image.open(os.path.join(folder, f)).convert('RGB') for f in files]
    g = 6
    tw = (W - 2 * g) // 3
    th = round(tw * 4 / 3)
    rows = 8
    strip = Image.new('RGB', (W, rows * (th + g)), (255, 255, 255))
    for k in range(rows * 3):
        t = tiles[(k * 7) % len(tiles)]
        t = t.resize((tw, round(t.height * tw / t.width))).crop((0, 0, tw, th))
        strip.paste(t, ((k % 3) * (tw + g), (k // 3) * (th + g)))
    return Image.blend(strip, Image.new('RGB', strip.size, wash), mix).convert('RGBA')


def main():
    cfg_path = sys.argv[1]
    stills = '--stills' in sys.argv
    cfg = json.load(open(cfg_path))
    root = os.path.dirname(os.path.abspath(cfg_path))
    W, H = cfg.get('size', [1080, 1920])
    FPS = cfg.get('fps', 30)
    col = {k: hexrgb(v) for k, v in {'bg': '#ED84B0', 'burst': '#EFA6C2', 'ink': '#C4245C', 'text': '#FFFFFF',
                                     'shadow': '#C9547F', 'accent': '#EFA6C2', 'line': '#FFEEF5',
                                     **cfg.get('colors', {})}.items()}
    fonts = cfg['fonts']
    head_px = cfg.get('head_px', 480)  # on-screen head width, the same for every look

    looks = []
    for lk in cfg['looks']:
        poses = build_look(lk, root, head_px)
        prop = None
        if lk.get('prop'):
            prop = paper_outline(padded(fit(Image.open(os.path.join(root, lk['prop'])).convert('RGBA'), head_px * lk.get('prop_w', 0.5))))
        label = kid_text(lk['label'], fonts['hand'], 150, col['ink'], fonts.get('hand_index', 0))
        label = fit(label, min(label.width, W * 0.6))
        feed = feed_strip(os.path.join(root, lk['feed']), W, col['bg']) if lk.get('feed') else None
        looks.append(dict(poses=poses, prop=prop, label=label, feed=feed, time=lk.get('time')))

    out_dir = os.path.join(root, cfg.get('frames_dir', 'frames'))
    if stills:
        for i, lk in enumerate(looks):
            lk['poses'][1].save(os.path.join(root, f'look-{i + 1}.png'))
        print('wrote', len(looks), 'stills'); return

    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    bg = Image.fromarray((np.array(col['bg'], float)[None, None] + rng.normal(0, 3.5, (H, W, 1))).clip(0, 255).astype('uint8')).convert('RGBA')
    pen = pen_from(fit(Image.open(os.path.join(root, cfg['pen'])).convert('RGBA'), 360)) if cfg.get('pen') else None
    burst = starburst(int(W * 0.52), int(W * 0.41), col['burst'])
    mono = ImageFont.truetype(fonts['mono'], 34) if fonts.get('mono') else ImageFont.load_default()
    hook = [kid_text(t, fonts['hand'], 150, col['ink'], fonts.get('hand_index', 0)) for t in cfg.get('hook', [])]
    hook = [fit(t, min(t.width, W * 0.72)) for t in hook]
    thumbs = [fit(lk['poses'][1], lk['poses'][1].width * 0.55) for lk in looks]
    times = [lk['time'] for lk in looks if lk['time']]
    cta = cfg.get('cta', [])
    cta_l = [bold_text(t, fonts['bold'], 230 if j == len(cta) - 1 else 84, col['text'], col['shadow']) for j, t in enumerate(cta)]
    end = cfg.get('ending')
    car = fit(Image.open(os.path.join(root, end['image'])).convert('RGBA'), W * 0.83) if end else None
    if car is not None and end.get('faces', 'left') == 'right':
        car = car.transpose(Image.FLIP_LEFT_RIGHT)  # always drive the way it faces: left
    getin = None
    if end and end.get('line'):
        getin = bold_text(end['line'], fonts['bold'], 120, col['accent'], col['shadow'])

    TITLE, LOOK, END = (66 if hook else 0), 78, (120 if (cta or car) else 0)
    total = TITLE + LOOK * len(looks) + END
    ground = int(H * 0.88)
    label_y = 225 if times else 160

    for f in range(total):
        im = bg.copy()
        step = f // STEP
        if f < TITLE:
            n = len(thumbs)
            for i, t in enumerate(thumbs):
                if f >= 4 + i * 5:
                    tx = int((i + 0.5) * W / n - t.width / 2)
                    r = t.rotate((-8, 3, 7, -4)[i % 4] + (2 if (step + i) % 2 else -2), resample=Image.BICUBIC, expand=True)
                    im.alpha_composite(r, (tx, int(H * 0.36) + (i % 2) * -80))
            y = 280
            for j, t in enumerate(hook):
                f0 = 14 + j * 20
                write_on(im, f, t, (W - t.width) // 2, y, f0, f0 + 18, pen)
                y += t.height + 30
        elif f < TITLE + LOOK * len(looks):
            i, lf = divmod(f - TITLE, LOOK)
            lk = looks[i]
            ls = lf // STEP
            if lk['feed'] is not None:  # her feed scrolls behind, faded in under the label
                yoff = int(lf * 14) % (lk['feed'].height - H)
                fc = lk['feed'].crop((0, yoff, W, yoff + H - 380))
                fade = np.clip(np.arange(fc.height) / 120, 0, 1)
                fc.putalpha(Image.fromarray((np.repeat(fade[:, None], W, 1) * 255).astype('uint8')))
                im.alpha_composite(fc, (0, 380))
            s = (0.6, 1.08)[ls] if ls < 2 else 1.0
            b = burst.rotate(ls * 4, resample=Image.BICUBIC)
            b = b.resize((int(b.width * s), int(b.height * s)), Image.LANCZOS)
            im.alpha_composite(b, ((W - b.width) // 2, int(H * 0.54) - b.height // 2))
            if times:
                d = ImageDraw.Draw(im)
                y, xs = 150, np.linspace(W * 0.14, W * 0.86, len(times))
                d.line([(xs[0], y), (xs[-1], y)], fill=col['line'] + (255,), width=4)
                for k, x in enumerate(xs):
                    d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col['burst'] + (255,), outline=col['line'] + (255,), width=3)
                    tw = d.textlength(times[k], font=mono)
                    d.text((x - tw / 2, y + 22), times[k], font=mono, fill=col['text'] + (255,))
                prev = xs[i - 1] if i else xs[0]
                mx = xs[i] if ls >= 3 else prev + (xs[i] - prev) * ls / 3
                d.ellipse([mx - 20, y - 20, mx + 20, y + 20], fill=(255, 255, 255, 255))
            dl = lk['poses'][ls % len(lk['poses'])]
            drop = (900, 380, -30, 0)[ls] if ls < 4 else (-12 if ls % 2 else 0)
            im.alpha_composite(dl, ((W - dl.width) // 2, ground - dl.height + drop))
            if lk['prop'] is not None and ls >= 3:
                r = lk['prop'].rotate(-6 if ls % 2 else 6, resample=Image.BICUBIC, expand=True)
                im.alpha_composite(r, (W - r.width - 20, int(H * 0.55) + (-14 if ls % 2 else 0)))
            write_on(im, lf, lk['label'], (W - lk['label'].width) // 2, label_y, 14, 44, pen)
        else:
            ef = f - TITLE - LOOK * len(looks)
            y = 260
            for j, t in enumerate(cta_l):
                if ef >= j * 5:
                    im.alpha_composite(t, ((W - t.width) // 2, y))
                y += t.height - 30 + (20 if j == len(cta_l) - 3 else 0)
            if car is not None:
                cf = (ef // 3) * 3
                stop_x, car_y = int(W * 0.08), int(H * 0.81) - car.height
                cx = None
                if 24 <= ef < 51:
                    k = (cf - 24) / 27
                    cx = W + 40 + (stop_x - W - 40) * (1 - (1 - k) ** 2)
                elif 51 <= ef < 96:
                    cx = stop_x + (6 if (ef // 3) % 2 else 0)
                elif ef >= 96:
                    k = (cf - 96) / max(END - 96, 1)
                    cx = stop_x - (stop_x + car.width + 60) * k ** 1.6
                if cx is not None:
                    im.alpha_composite(car, (int(cx), car_y))
                if getin is not None and 54 <= ef < 100:
                    im.alpha_composite(getin, ((W - getin.width) // 2, car_y - getin.height + 10))
        im.convert('RGB').save(os.path.join(out_dir, f'{f:04d}.png'))

    out = os.path.join(root, cfg.get('out', 'lookbook.mp4'))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(out_dir, '%04d.png'),
                    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest',
                    '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-map_metadata', '-1',
                    '-movflags', '+faststart', out], check=True)
    print(out, total, 'frames', f'{total / FPS:.1f}s')


if __name__ == '__main__':
    main()
