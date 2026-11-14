"""Keep layered textures (glow _ef*, colour variants _bl/_rd) aligned with their master layer."""
import re, numpy as np, cv2
import retext

def stem(name):
    return re.sub(r'_(ef\d*|bl|rd)(?=[_.]|$)', '', name)

def is_ef(name):
    return re.search(r'_ef\d*(?=[_.]|$)', name) is not None

def intensity(img):
    a = img[:, :, 3].astype(np.float32)
    if (a > 250).mean() > 0.95:  # opaque/additive: use luminance
        return img[:, :, :3].max(2).astype(np.float32), True
    return a, False

def glow_from(master_orig, master_new, ef_orig):
    Am, _ = intensity(master_orig); E, add = intensity(ef_orig)
    An, _ = intensity(master_new)
    if E.max() < 1 or Am.max() < 1: return None
    best = None
    for s in (0, 1, 2, 3, 5, 8, 12, 18):
        b = cv2.GaussianBlur(Am, (0, 0), s) if s else Am
        b = b / max(b.max(), 1) * E.max()
        err = np.abs(b - E).mean()
        if best is None or err < best[0]: best = (err, s)
    s = best[1]
    g = cv2.GaussianBlur(An, (0, 0), s) if s else An
    bm = cv2.GaussianBlur(Am, (0, 0), s) if s else Am
    g = np.clip(g / max(bm.max(), 1) * E.max(), 0, 255)
    w = E > E.max() * 0.3
    col = np.median(ef_orig[:, :, :3][w].astype(np.float32), 0) if w.sum() > 10 else ef_orig[:, :, :3].reshape(-1, 3).max(0)
    if add:
        col = col / max(col.max(), 1) * 255
    out = ef_orig.copy()
    if add:
        out[:, :, :3] = np.clip(col[None, None] * (g[..., None] / 255), 0, 255).astype(np.uint8)
    else:
        out[:, :, :3] = col.astype(np.uint8); out[:, :, 3] = g.astype(np.uint8)
    return out

def variant_from(master_orig, var_orig, text, font, italic):
    mi = retext.analyze(master_orig); vi = retext.analyze(var_orig)
    if mi is None or vi is None or (var_orig[:, :, 3] > 200).mean() >= 0.5: return None
    vi['bbox'] = mi['bbox']
    return retext.render(var_orig, text, font, italic, align=retext.guess_align(master_orig, mi), info=vi)

def additive_variant(master_orig, var_orig, text, font, italic):
    """variant layer drawn additively on black (DXT1 / opaque): keep master's bbox"""
    rgb = var_orig[:, :, :3].astype(np.float32); lum = rgb.max(2)
    col = np.where(lum[..., None] > 0, rgb * 255 / np.maximum(lum[..., None], 1), 0)
    tmp = np.dstack([np.clip(col, 0, 255), lum]).astype(np.uint8)
    mi = retext.analyze(master_orig); vi = retext.analyze(tmp)
    if mi is None or vi is None: return None
    vi['bbox'] = mi['bbox']
    r = retext.render(tmp, text, font, italic, align=retext.guess_align(master_orig, mi), info=vi)
    al = r[:, :, 3:4].astype(np.float32) / 255
    out = var_orig.copy(); out[:, :, :3] = np.clip(r[:, :, :3] * al, 0, 255).astype(np.uint8)
    return out

def layer_from(master_orig, master_new, var_orig, text, font, italic):
    a = var_orig[:, :, 3]
    if (a > 250).mean() > 0.95:  # opaque additive layer
        return additive_variant(master_orig, var_orig, text, font, italic)
    return glow_from(master_orig, master_new, var_orig)
