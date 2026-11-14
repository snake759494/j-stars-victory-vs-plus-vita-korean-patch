"""Per-image caption replacement for TIPS screenshots (coords in 960x428 grid view: x*4/3, y*4/3+150)."""
import numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# (x0,y0,x1,y1, style w|o, rise_deg, text, line_h or 0)
CAPS = {
 1983: [(75,150,415,205,'w',3,'상대를 쓰러뜨리면\n빅토리 게이지가 한 칸 찬다!',0), (527,105,860,175,'o',3,'빅토리 게이지를\n가득 채우면 승리!',0)],
 1984: [(450,215,835,268,'w',2,'록온하면\n카메라가 상대를 계속 따라간다!',0)],
 1985: [(372,90,795,140,'w',2,'내가 쓰러지면\n상대의 빅토리 게이지가 한 칸 찬다!',0)],
 1987: [(100,75,475,155,'o',11,'시간이 지나면 회복되고...',24), (495,180,862,262,'o',12,'...체력 충전으로도 회복!',24)],
 1988: [(468,212,890,242,'w',2,'스태미나가 부족하면 게이지가 깜박인다!',0)],
 1989: [(185,75,335,100,'w',0,'원거리',0),(425,75,610,105,'w',0,'근거리',0),(728,75,830,100,'w',0,'무적',0)],
 1990: [(268,97,435,122,'w',0,'근거리 록온',0)],
 1993: [(470,0,890,65,'o',5,'대혼란과 파괴를 일으켜라!',24)],
 1994: [(365,290,885,322,'w',2,'서포트는 도착까지 조금 걸리니 버텨라!',0)],
 1996: [(82,298,470,355,'w',2,'동료가 적을 공중에 띄우면\n버튼 표시에 따라 입력하자.',0), (590,285,880,342,'w',2,'계속 정확히 입력하면\n맹렬한 태그팀 난무가 터진다!',0)],
 1999: [(640,110,880,180,'o',10,'일반 공격',30), (300,235,430,295,'o',8,'가드',32), (680,265,880,330,'o',8,'가드 브레이크',28)],
 2000: [(110,215,475,290,'o',8,'고무고무 연사!',30), (460,215,880,300,'o',7,'고무고무 제트 개틀링!',30)],
 2002: [(395,35,885,80,'w',2,'속도가 느려지면 수리할 때가 된 것이다.',0)],
}
NOAUTO = {1994, 1996}
def _o(x, y): return int(x * 4 / 3), int(y * 4 / 3 + 150)

def _line(text, h, top, bot, outline, ow, italic, font):
    S = 3; f = ImageFont.truetype(font, int(h * S * 1.25)); bb = f.getbbox(text)
    pad = (ow + 2) * S + int((bb[3] - bb[1]) * italic) + 6
    m = Image.new('L', (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), text, font=f, fill=255)
    m = m.transform(m.size, Image.AFFINE, (1, italic, -italic * m.size[1] * 0.5, 0, 1, 0), Image.BICUBIC)
    om = m.filter(ImageFilter.MaxFilter(2 * ow * S + 1))
    a = np.array(om); ys, xs = np.where(a > 8); box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    m, om = m.crop(box), om.crop(box)
    sc = (h + 2 * ow) / m.size[1]; W, H = max(1, int(m.size[0] * sc)), int(m.size[1] * sc)
    m = np.array(m.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    om = np.array(om.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    t = np.linspace(0, 1, H)[:, None, None]
    fill = np.array(top)[None, None] * (1 - t) + np.array(bot)[None, None] * t
    col = fill * m[..., None] + np.array(outline)[None, None] * (1 - m[..., None])
    return np.dstack([col, om * 255]).astype(np.uint8)

def apply(img, k, font):
    img = img.copy()
    for x0, y0, x1, y1, st, ang, text, lh in CAPS.get(k, []):
        X0, Y0 = _o(x0, y0); X1, Y1 = _o(x1, y1)
        X0, Y0 = max(0, X0 - 4), max(0, Y0 - 4); X1, Y1 = min(img.shape[1], X1 + 4), min(img.shape[0], Y1 + 4)
        reg = np.ascontiguousarray(img[Y0:Y1, X0:X1, :3]); rgb = reg.astype(np.int32)
        mn, mx = rgb.min(2), rgb.max(2)
        if st == 'w':
            m = ((rgb[..., 1] > 85) & (rgb[..., 2] > 80)).astype(np.uint8); m = cv2.dilate(m, np.ones((5, 5), np.uint8))
        else:
            org = ((rgb[..., 0] > 170) & (rgb[..., 0] - rgb[..., 2] > 70)).astype(np.uint8)
            dk = (mx < 80).astype(np.uint8)
            near = cv2.dilate(dk, np.ones((9, 9), np.uint8))
            m = org & near
            m = cv2.dilate(m, np.ones((7, 7), np.uint8))
            m = m | (dk & cv2.dilate(m, np.ones((5, 5), np.uint8)))
            wh = (mn > 150).astype(np.uint8)
            for _ in range(3): m = m | (wh & cv2.dilate(m, np.ones((7, 7), np.uint8)))
            m = cv2.dilate(m, np.ones((5, 5), np.uint8))
        img[Y0:Y1, X0:X1, :3] = cv2.inpaint(reg, m * 255, 5, cv2.INPAINT_TELEA)
        lines = text.split('\n'); n = len(lines); r = math.radians(ang)
        bw, bh = X1 - X0, Y1 - Y0
        h = int(lh * 4 / 3) if lh else int((bh - bw * abs(math.sin(r))) / n * 0.7) if ang > 4 else int(bh / n * (0.85 if st == 'w' and n > 1 else 0.72))
        h = max(h, 12)
        if st == 'w': L = [_line(l, h, (255, 255, 255), (232, 232, 232), (25, 25, 25), 1, 0.18, font) for l in lines]
        else: L = [_line(l, h, (255, 238, 70), (240, 110, 10), (45, 12, 0), 3, 0.18, font) for l in lines]
        gap = int(h * 0.35); W = max(l.shape[1] for l in L); H = sum(l.shape[0] for l in L) + gap * (n - 1)
        lay = np.zeros((H, W, 4), np.uint8); y = 0
        for l in L: lay[y:y + l.shape[0], :l.shape[1]] = l; y += l.shape[0] + gap
        maxw = bw / max(math.cos(r), 0.5) * 1.02
        im = Image.fromarray(lay, 'RGBA')
        if W > maxw: im = im.resize((int(maxw), H), Image.LANCZOS)
        if ang: im = im.rotate(ang, Image.BICUBIC, expand=True)
        a = np.array(im).astype(np.float32); cx, cy = (X0 + X1) // 2, (Y0 + Y1) // 2
        ox, oy = cx - a.shape[1] // 2, cy - a.shape[0] // 2
        sx0, sy0 = max(0, -ox), max(0, -oy); ox, oy = max(0, ox), max(0, oy)
        a = a[sy0:, sx0:]; a = a[:img.shape[0] - oy, :img.shape[1] - ox]
        al = a[..., 3:] / 255; R = img[oy:oy + a.shape[0], ox:ox + a.shape[1], :3].astype(np.float32)
        img[oy:oy + a.shape[0], ox:ox + a.shape[1], :3] = np.clip(R * (1 - al) + a[..., :3] * al, 0, 255).astype(np.uint8)
    return img
