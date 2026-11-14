"""Re-render a text texture in Korean imitating the original style.
render(orig_rgba(h,w,4), text, italic, font_path) -> new rgba"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

def analyze(img):
    a = img[:, :, 3].astype(np.float32) / 255
    m = a > 0.5
    if m.sum() < 10: return None
    ys, xs = np.where(m)
    bbox = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    dist = ndimage.distance_transform_edt(m)
    # outline: compare luminance near edge vs deep inside
    lum = img[:, :, :3].astype(np.float32) @ np.array([.3, .59, .11])
    deep = dist >= max(2, dist.max() * 0.5)
    edge = m & (dist <= 1.5)
    rgb = img[:, :, :3].astype(np.float32)
    inner_col = rgb[deep].mean(0) if deep.sum() > 5 else rgb[m].mean(0)
    edge_col = rgb[edge].mean(0)
    has_outline = abs(lum[edge].mean() - lum[deep].mean() if deep.sum() > 5 else 0) > 50
    # outline width: thickness of edge-coloured band
    ow = 0
    if has_outline:
        el = lum[edge].mean()
        band = m & (np.abs(lum - el) < 40)
        ow = float(np.median(dist[band])) * 2 if band.sum() else 2
        ow = max(1.0, min(ow, (bbox[3] - bbox[1]) * 0.15))
    # vertical fill gradient (inner colour per row, relative to bbox)
    prof = []
    H = bbox[3] - bbox[1]
    inner = m & (dist > (ow + 1 if has_outline else 0.5))
    for y in range(bbox[1], bbox[3]):
        row = inner[y]
        prof.append(rgb[y][row].mean(0) if row.sum() else None)
    good = [p for p in prof if p is not None]
    if not good: prof = [inner_col] * H
    else:
        last = good[0]; out = []
        for p in prof:
            last = p if p is not None else last; out.append(last)
        prof = out
    return dict(bbox=bbox, outline=has_outline, ow=ow, ocol=edge_col, prof=np.array(prof), alpha_max=img[:, :, 3].max())

def render(img, text, font_path, italic=0.0, align=None, info=None, pad=1):
    h, w = img.shape[:2]
    info = info or analyze(img)
    if info is None: return img
    x0, y0, x1, y1 = info['bbox']; bw, bh = x1 - x0, y1 - y0
    lines = text.split('\n')
    ow = int(round(info['ow'] * 0.6)) if info['outline'] else 0
    if bh / max(1, len(lines)) <= 15:  # very small text: crisp pixel font
        return small_render(img, lines, info, align, ow > 0)
    # find font size to fit bbox height (cap ~ bbox) and width
    def measure(sz):
        f = ImageFont.truetype(font_path, sz)
        lh = sz * 1.08
        ws = [f.getbbox(l)[2] - f.getbbox(l)[0] if l else 0 for l in lines]
        tot_h = lh * (len(lines) - 1) + (f.getbbox(lines[-1] or ' ')[3] - f.getbbox(lines[0] or ' ')[1])
        return f, max(ws) + 2 * ow + italic * tot_h, tot_h + 2 * ow
    sz = max(6, int(bh * 1.05 / max(1, len(lines)) ))
    f, tw, th = measure(sz)
    while sz > 6 and (th > bh * 1.0 + 1):
        sz -= 1; f, tw, th = measure(sz)
    sx = 1.0
    if tw > bw + 2:
        sx = (bw + 2) / tw  # horizontal condense instead of shrinking height
        if sx < 0.62:  # too much condense: shrink font too
            while sz > 6 and tw * 0.62 > bw:
                sz -= 1; f, tw, th = measure(sz)
            sx = min(1.0, (bw + 2) / tw)
    # draw on large canvas
    S = 3
    CW, CH = int((tw + 8) * S), int((th + 8) * S)
    F = ImageFont.truetype(font_path, sz * S)
    mask = Image.new('L', (CW, CH), 0); d = ImageDraw.Draw(mask)
    lh = sz * 1.08 * S
    top = F.getbbox(lines[0] or ' ')[1]
    for i, l in enumerate(lines):
        lw = F.getbbox(l)[2] - F.getbbox(l)[0] if l else 0
        xx = (CW - lw) / 2 if (align or 'c') == 'c' else (4 + ow) * S
        d.text((xx - F.getbbox(l or ' ')[0], (4 + ow) * S - top + i * lh), l, font=F, fill=255)
    if italic:
        mask = mask.transform(mask.size, Image.AFFINE, (1, italic, -italic * CH * 0.5, 0, 1, 0), Image.BICUBIC)
    fillm = np.array(mask).astype(np.float32) / 255
    if ow:
        om = np.array(mask.filter(ImageFilter.MaxFilter(2 * ow * S + 1))).astype(np.float32) / 255
    else: om = fillm
    # crop to content
    ys, xs = np.where(om > 0.02)
    if len(ys) == 0: return img
    om = om[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; fillm = fillm[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ch, cw = om.shape
    tw_px = cw / S * sx; th_px = ch / S
    if th_px > bh: k = bh / th_px; tw_px *= k; th_px = bh
    if tw_px > bw: k = bw / tw_px; tw_px = bw; th_px *= k
    TW, TH = max(1, int(round(tw_px))), max(1, int(round(th_px)))
    om_s = np.array(Image.fromarray((om * 255).astype(np.uint8)).resize((TW, TH), Image.LANCZOS)).astype(np.float32) / 255
    fm_s = np.array(Image.fromarray((fillm * 255).astype(np.uint8)).resize((TW, TH), Image.LANCZOS)).astype(np.float32) / 255
    # colours
    prof = info['prof']; idx = np.clip((np.arange(TH) / max(1, TH - 1) * (len(prof) - 1)).astype(int), 0, len(prof) - 1)
    fillc = prof[idx][:, None, :].repeat(TW, 1)
    oc = np.array(info['ocol'])[None, None, :]
    rgb = fillc * fm_s[..., None] + oc * (1 - fm_s[..., None]) if ow else fillc
    alpha = (om_s if ow else fm_s) * info['alpha_max']
    out = np.zeros_like(img)
    # place: vertical centre of bbox; horizontal align
    oy = y0 + (bh - TH) // 2
    if align == 'l': ox = x0
    elif align == 'r': ox = x1 - TW
    else: ox = x0 + (bw - TW) // 2
    ox = max(0, min(ox, w - TW)); oy = max(0, min(oy, h - TH))
    out[oy:oy + TH, ox:ox + TW, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[oy:oy + TH, ox:ox + TW, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return out

GALMURI = __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', 'Galmuri11-Bold.ttf')
def small_render(img, lines, info, align, outline):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = info['bbox']; bw, bh = x1 - x0, y1 - y0
    n = len(lines); o = 1 if outline else 0
    lh = bh / n
    sz = 12 if lh - 2 * o >= 11 else 10
    f = ImageFont.truetype(GALMURI if sz >= 12 else GALMURI.replace('11-Bold', '9'), sz)
    m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
    d.fontmode = '1'
    ws = [f.getbbox(l)[2] - f.getbbox(l)[0] for l in lines]
    for i, l in enumerate(lines):
        bb = f.getbbox(l); tw = bb[2] - bb[0]; th = bb[3] - bb[1]
        if align == 'l': xx = x0 + o
        elif align == 'r': xx = x1 - tw - o
        else: xx = x0 + (bw - tw) // 2
        yy = int(y0 + i * lh + (lh - th) / 2)
        d.text((xx - bb[0], yy - bb[1]), l, font=f, fill=255)
    fm = np.array(m).astype(np.float32) / 255
    if max(ws) > bw + 2:  # squeeze horizontally around the bbox centre
        k = (bw + 2) / max(ws); cx = x0 + bw / 2
        fm = np.array(Image.fromarray((fm * 255).astype(np.uint8)).transform((w, h), Image.AFFINE, (1 / k, 0, cx - cx / k, 0, 1, 0), Image.BILINEAR)).astype(np.float32) / 255
    om = np.array(Image.fromarray((fm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255 if o else fm
    prof = info['prof']; ys = np.clip(((np.arange(h) - y0) / max(1, bh - 1) * (len(prof) - 1)).astype(int), 0, len(prof) - 1)
    fillc = prof[ys][:, None, :].repeat(w, 1)
    # keep fill bright: use the brightest part of the profile
    lum = prof @ np.array([.3, .59, .11]); top = prof[lum.argmax()]
    fillc = fillc * 0.5 + top[None, None] * 0.5
    oc = np.array(info['ocol'])[None, None]
    rgb = fillc * fm[..., None] + oc * (1 - fm[..., None]) if o else fillc
    out = np.zeros_like(img)
    out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[:, :, 3] = np.clip(om * info['alpha_max'], 0, 255).astype(np.uint8)
    return out

def guess_align(img, info):
    x0, y0, x1, y1 = info['bbox']; w = img.shape[1]
    l, r = x0, w - x1
    if l < w * 0.06 and r > w * 0.15: return 'l'
    if r < w * 0.06 and l > w * 0.15: return 'r'
    return 'c'

def smart(img, text, font_path, italic=0.0, kind=None, mode=None):
    """choose mode by background; returns new rgba or None (skip)"""
    import cv2
    h, w = img.shape[:2]
    op = (img[:, :, 3] > 200).mean()
    if op < 0.5 or mode == 'alpha':
        info = analyze(img)
        if info is None: return None
        return render(img, text, font_path, italic, align=guess_align(img, info), info=info)
    rgb = img[:, :, :3].astype(np.float32)
    lum = rgb.max(2)
    border = np.concatenate([lum[0], lum[-1], lum[:, 0], lum[:, -1]])
    if np.median(border) < 24:  # additive black background
        a = np.clip(lum * 1.0, 0, 255)
        col = np.where(lum[..., None] > 0, rgb * 255 / np.maximum(lum[..., None], 1), 0)
        tmp = np.dstack([np.clip(col, 0, 255), a]).astype(np.uint8)
        info = analyze(tmp)
        if info is None: return None
        r = render(tmp, text, font_path, italic, align=guess_align(tmp, info), info=info)
        al = r[:, :, 3:4].astype(np.float32) / 255
        out = np.zeros_like(img); out[:, :, :3] = np.clip(r[:, :, :3] * al, 0, 255); out[:, :, 3] = img[:, :, 3]
        return out
    if w * h > 150000: return None
    # plate: text = pixels far from local background
    k = max(15, (min(h, w) // 2) | 1)
    bg = cv2.medianBlur(img[:, :, :3], min(k, 255) if k % 2 else k + 1).astype(np.float32)
    diff = np.abs(rgb - bg).sum(2)
    mask = (diff > 60).astype(np.uint8)
    if mask.mean() < 0.005: return None
    mask_d = cv2.dilate(mask, np.ones((5, 5), np.uint8))
    clean = cv2.inpaint(img[:, :, :3], mask_d * 255, 5, cv2.INPAINT_TELEA)
    tmp = np.dstack([img[:, :, :3], mask * 255]).astype(np.uint8)
    info = analyze(tmp)
    if info is None: return None
    col = np.median(rgb[mask > 0], 0)
    info['outline'] = False; info['ow'] = 0; info['prof'] = np.array([col] * len(info['prof']))
    r = render(tmp, text, font_path, italic, align=guess_align(tmp, info), info=info)
    al = r[:, :, 3:4].astype(np.float32) / 255
    out = img.copy()
    out[:, :, :3] = np.clip(clean * (1 - al) + r[:, :, :3] * al, 0, 255).astype(np.uint8)
    return out

def boxed(img, text, font_path, box, color=(240, 240, 240)):
    """replace light text inside box=(x0,y0,x1,y1) on an opaque picture"""
    import cv2
    x0, y0, x1, y1 = box
    out = img.copy(); reg = np.ascontiguousarray(out[y0:y1, x0:x1, :3])
    m = (reg.max(2) > 140).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    out[y0:y1, x0:x1, :3] = cv2.inpaint(reg, m * 255, 5, cv2.INPAINT_TELEA)
    h = y1 - y0; S = 3
    f = ImageFont.truetype(font_path, int(h * 0.75 * S))
    bb = f.getbbox(text); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    mk = Image.new('L', (tw + 8, th + 8), 0); ImageDraw.Draw(mk).text((4 - bb[0], 4 - bb[1]), text, font=f, fill=255)
    sc = min(1.0, (x1 - x0) / (mk.width / S), h / (mk.height / S)) / S
    mk = np.array(mk.resize((max(1, int(mk.width * sc)), max(1, int(mk.height * sc))), Image.LANCZOS)).astype(np.float32) / 255
    mh, mw = mk.shape; ox = x0 + (x1 - x0 - mw) // 2; oy = y0 + (h - mh) // 2
    r = out[oy:oy + mh, ox:ox + mw, :3].astype(np.float32)
    out[oy:oy + mh, ox:ox + mw, :3] = (r * (1 - mk[..., None]) + np.array(color) * mk[..., None]).astype(np.uint8)
    return out
