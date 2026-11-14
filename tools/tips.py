"""Loading TIPS composite (1280x720) re-texter: header (subtitle+title) and bottom caption(s)."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def _blocks(ko):
    bl = [b for b in ko.split('\n\n') if b.strip()]
    head = bl[0].split('\n')
    rest = bl[1:]
    bodies = [b for b in rest if b.count('\n') >= 1 or len(b) > 22]
    if not bodies and rest: bodies = [max(rest, key=len)]
    return head, bodies

def draw(canvas, text, x, y, h, maxw, top, bot, outline=None, ow=0, italic=0.2, font=None):
    S = 3; f = ImageFont.truetype(font, int(h * S * 1.25))
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = (ow + 2) * S + int(th * italic) + 4
    m = Image.new('L', (tw + 2 * pad, th + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), text, font=f, fill=255)
    if italic: m = m.transform(m.size, Image.AFFINE, (1, italic, -italic * m.size[1] * 0.5, 0, 1, 0), Image.BICUBIC)
    om = m.filter(ImageFilter.MaxFilter(2 * ow * S + 1)) if ow else m
    a = np.array(om); ys, xs = np.where(a > 8)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    m = m.crop(box); om = om.crop(box)
    sc = (h + 2 * ow) / m.size[1]
    W = int(m.size[0] * sc); Hh = int(m.size[1] * sc)
    if W > maxw: W = int(maxw)
    m = np.array(m.resize((W, Hh), Image.LANCZOS)).astype(np.float32) / 255
    om = np.array(om.resize((W, Hh), Image.LANCZOS)).astype(np.float32) / 255
    t = np.linspace(0, 1, Hh)[:, None, None]
    fill = np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t
    col = fill * m[..., None] + (np.array(outline)[None, None] if outline else fill) * (1 - m[..., None])
    al = (om if ow else m)[..., None]
    reg = canvas[y:y + Hh, x:x + W, :3].astype(np.float32)
    hh, ww = reg.shape[:2]
    canvas[y:y + hh, x:x + ww, :3] = np.clip(reg * (1 - al[:hh, :ww]) + col[:hh, :ww] * al[:hh, :ww], 0, 255).astype(np.uint8)

def _textmask(reg, maskfn, dark_thr=80, frac=0.35):
    rgb = reg[:, :, :3].astype(np.float32)
    m = maskfn(rgb).astype(np.uint8)
    dark = (rgb.max(2) < dark_thr).astype(np.float32)
    df = cv2.blur(dark, (31, 31))
    m &= (df > frac).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, 4] >= 4: keep[lab == i] = 1
    return keep

def _inpaint(img, x0, y0, keep):
    h, w = keep.shape
    reg = np.ascontiguousarray(img[y0:y0 + h, x0:x0 + w, :3])
    md = cv2.dilate(keep, np.ones((7, 7), np.uint8))
    img[y0:y0 + h, x0:x0 + w, :3] = cv2.inpaint(reg, md * 255, 4, cv2.INPAINT_TELEA)

def _clusters(keep, gap):
    cols = np.where(keep.sum(0) > 0)[0]
    if len(cols) == 0: return []
    cl = [[cols[0], cols[0]]]
    for c in cols[1:]:
        if c - cl[-1][1] > gap: cl.append([c, c])
        else: cl[-1][1] = c
    out = []
    for a, b in cl:
        sub = keep[:, a:b + 1]; rows = np.where(sub.sum(1) > 0)[0]
        if (b - a) > 40: out.append((a, rows.min(), b + 1, rows.max() + 1))
    return out

def _cover(img, x0, y0, x1, y1, pad=4):
    H, W = img.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad + 4), min(H, y1 + pad)
    reg = img[Y0:Y1, X0:X1, :3].reshape(-1, 3).astype(np.float32)
    d = reg[reg.max(1) < 90]
    col = np.median(d, 0) if len(d) > 20 else np.array([25, 25, 25])
    img[Y0:Y1, X0:X1, :3] = col.astype(np.uint8)

def _rowgroups(k):
    rows = np.where(k.sum(1) > 0)[0]
    if len(rows) == 0: return []
    g = [[rows[0], rows[0]]]
    for r in rows[1:]:
        if r - g[-1][1] > 2: g.append([r, r])
        else: g[-1][1] = r
    return [(a, b + 1) for a, b in g if b - a >= 5]

def retip(img, ko, font_head, font_body):
    img = img.copy(); H, W = img.shape[:2]; sx, sy = W / 1280, H / 720
    head, bodies = _blocks(ko)
    def hmask(rgb):
        mx = rgb.max(2); mn = rgb.min(2); sat = mx - mn
        return ((sat > 80) & (mx > 140)) | (mn > 160)
    X0, Y0, X1, Y1 = int(100 * sx), int(78 * sy), int(900 * sx), int(160 * sy)
    k = _textmask(img[Y0:Y1, X0:X1], hmask, frac=0.15)
    if k.sum() > 20:
        ys, xs = np.where(k > 0); x0, y0, x1, y1 = X0 + xs.min(), Y0 + ys.min(), X0 + xs.max() + 1, Y0 + ys.max() + 1
        _cover(img, x0, y0, x1, y1)
        hh = y1 - y0; sub_h = int(hh * 0.30); tit_h = int(hh * 0.52)
        if len(head) >= 2:
            draw(img, head[0], x0 + int(10 * sx), y0, sub_h, 800 * sx, (255, 255, 255), (230, 230, 230), (20, 20, 20), 1, 0.2, font_head)
            draw(img, head[1], x0, y0 + hh - tit_h - 2, tit_h, 820 * sx, (255, 235, 60), (240, 120, 10), (40, 10, 0), 2, 0.2, font_head)
        else:
            draw(img, head[0], x0, y0, hh, 820 * sx, (255, 235, 60), (240, 120, 10), (40, 10, 0), 2, 0.2, font_head)
    band = (img[int(560 * sy):int(675 * sy), int(240 * sx):int(1140 * sx), :3].max(2) < 60).mean()
    if bodies and band > 0.2:
        def bmask(rgb):
            mn = rgb.min(2); mx = rgb.max(2)
            return (mn > 130) & (mx - mn < 70)
        X0, Y0, X1, Y1 = int(30 * sx), int(555 * sy), int(1250 * sx), int(690 * sy)
        k = _textmask(img[Y0:Y1, X0:X1], bmask)
        cl = sorted(_clusters(k, int(50 * sx)))
        if len(cl) > len(bodies):  # keep widest clusters, in x order
            cl = sorted(sorted(cl, key=lambda c: -(c[2] - c[0]))[:len(bodies)])
        bl = bodies if len(bodies) == len(cl) else [max(bodies, key=len)] * 0 + bodies[:len(cl)]
        for (a, t, b, u), body in zip(cl, bl):
            sub = k[t:u, a:b]
            x0, y0, x1, y1 = X0 + a, Y0 + t, X0 + b, Y0 + u
            rg = _rowgroups(sub)
            _cover(img, x0, y0, x1, y1)
            lines = body.split(chr(10)); n = len(lines)
            if len(rg) == n:
                pos = [(Y0 + t + ra, rb - ra) for ra, rb in rg]
            else:
                lh = (y1 - y0) / n; pos = [(int(y0 + i * lh), int(lh * 0.8)) for i in range(n)]
            hc = max(h for _, h in pos)
            for (yy, hh), l in zip(pos, lines):
                draw(img, l, x0, yy + hh - hc, int(min(hc * 0.95, 26 * sy)), (x1 - x0) * 1.08, (255, 255, 255), (235, 235, 235), (30, 30, 30), 1, 0.18, font_body)
    return img
