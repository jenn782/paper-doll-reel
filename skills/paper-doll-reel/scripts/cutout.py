"""Cut a sticker piece (head, top, jeans, shoe, prop) out of a photo or screenshot.

Usage:
  python cutout.py in.png out.png                       # whole image, AI background removal (rembg)
  python cutout.py in.png out.png --box 200,10,400,240  # crop one item from a flat-lay first
  python cutout.py in.png out.png --poly "455,30 730,20 804,802 70,802"  # keep only inside a polygon
                                                       # (e.g. the FRONT shoe of a pair; coords in the cut piece)
  python cutout.py head.png out.png --mode border       # heads that already have a paper outline:
                                                       # remove only the flat background touching the edges
  python cutout.py in.png out.png --keep 2              # keep the 2 biggest pieces (e.g. two arms)

Small screenshots are upscaled (default: long side to ~1200px, max 3x) so edges stay soft.
Bigger images are matted as they are: matting time grows with pixel count.
"""
import argparse
import numpy as np
from PIL import Image, ImageDraw


def border_bg(im, tol=40):
    # flat background connected to the image border (keeps a cream paper outline inside it)
    from scipy import ndimage
    a = np.asarray(im.convert('RGB')).astype(int)
    corners = np.array([a[0, 0], a[0, -1], a[-1, 0], a[-1, -1]])
    bg = np.median(corners, axis=0)
    near = np.abs(a - bg).sum(-1) < tol
    lab, _ = ndimage.label(near)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    alpha = np.where(np.isin(lab, list(edge)), 0, 255).astype('uint8')
    out = im.convert('RGBA')
    out.putalpha(Image.fromarray(alpha))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--box', help='x0,y0,x1,y1 crop in source pixels')
    ap.add_argument('--poly', help='"x,y x,y ..." keep-polygon, in pixels of the cut piece (after --box, before upscale)')
    ap.add_argument('--mode', choices=['ai', 'border'], default='ai')
    ap.add_argument('--upscale', type=float, default=0, help='0 = auto (long side to ~1200px, max 3x)')
    ap.add_argument('--keep', type=int, default=0, help='keep only the N largest opaque pieces')
    a = ap.parse_args()

    im = Image.open(a.src).convert('RGBA')
    if a.box:
        im = im.crop(tuple(int(v) for v in a.box.split(',')))
    poly = [tuple(float(v) for v in p.split(',')) for p in a.poly.split()] if a.poly else None
    if not a.upscale:
        a.upscale = min(3, max(1, 1200 / max(im.size)))
    if a.upscale != 1:
        im = im.resize((round(im.width * a.upscale), round(im.height * a.upscale)), Image.LANCZOS)
        if poly:
            poly = [(x * a.upscale, y * a.upscale) for x, y in poly]

    if a.mode == 'border':
        out = border_bg(im)
    else:
        from rembg import remove, new_session
        out = remove(im.convert('RGB'), session=new_session('u2net'), alpha_matting=True)

    alpha = np.asarray(out.getchannel('A')).copy()
    if poly:
        m = Image.new('L', out.size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        alpha = np.minimum(alpha, np.asarray(m))
    if a.keep:
        from scipy import ndimage
        lab, n = ndimage.label(alpha > 128)
        if n > a.keep:
            sizes = ndimage.sum(alpha > 128, lab, range(1, n + 1))
            keep = 1 + np.argsort(sizes)[-a.keep:]
            alpha = np.where(np.isin(lab, keep), alpha, 0).astype('uint8')
    out.putalpha(Image.fromarray(alpha))
    out = out.crop(out.getchannel('A').getbbox())
    out.save(a.dst)
    print(a.dst, out.size)


if __name__ == '__main__':
    main()
