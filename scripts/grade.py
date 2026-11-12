"""Regrade Pillars of Creation into the party palette (violet/blue space, magenta pillars, pink+cyan iridescent rims).
usage: grade.py SRC OUT_SQUARE OUT_WIDE_3840x1536 PALETTE_NPY
"""
import sys, numpy as np, cv2
from skimage import color

src = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
lab = color.rgb2lab(src)
L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
C = np.hypot(a, b)
sf = src.shape[1] / 1280.0
h = np.degrees(np.arctan2(b, a)) % 360

# hue remap (Lab hue angles): teal/blue sky -> blue-violet, orange/brown pillars -> magenta-pink,
# gold rims -> hot pink/peach. Piecewise-linear on a circular key table.
kin  = np.array([0,   30,  60,  90, 150, 200, 240, 290, 330, 360], np.float32)
kout = np.array([340, 345, 355, 10, 300, 295, 290, 310, 330, 340], np.float32)
kout_u = np.unwrap(np.radians(kout))
hn = np.degrees(np.interp(h, kin, np.degrees(kout_u)) * np.pi / 180) % 360

# rims: bright, thin, high-gradient areas get an iridescent hue sweep (pink -> lilac -> cyan)
Ls = cv2.GaussianBlur(L, (0, 0), 1.2 * sf)
gx, gy = cv2.Sobel(Ls, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(Ls, cv2.CV_32F, 0, 1, ksize=3)
edge = np.clip(np.hypot(gx, gy) * sf / 40, 0, 1)
edge = cv2.GaussianBlur(edge, (0, 0), 5 * sf)
rim = np.clip((L - 35) / 35, 0, 1) * edge
rim = np.clip(rim / max(np.percentile(rim, 99.5), 1e-3), 0, 1)
H, W = L.shape
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
sweep = 0.5 + 0.5 * np.sin((xx * 0.6 + yy) / H * 9.0 + L / 18.0)
irid_h = np.where(sweep > 0.5, 345 + (sweep - 0.5) * 2 * 40, 215 + sweep * 2 * 60) % 360   # pink..rose / cyan..lilac
dh = ((irid_h - hn + 180) % 360) - 180
hn = (hn + dh * rim * 0.6) % 360

Cn = C * 1.6 + rim * 12
Ln = np.clip(100 * (L / 100) ** 1.18 + rim * 5, 0, 100)
# lift pillar bodies (dark & warm) slightly toward plum so they don't go muddy
body = np.clip((45 - L) / 30, 0, 1) * np.clip((C - 8) / 20, 0, 1)
Ln = Ln + body * 4

out = color.lab2rgb(np.stack([Ln, Cn * np.cos(np.radians(hn)), Cn * np.sin(np.radians(hn))], -1))
out = np.clip(out, 0, 1).astype(np.float32)
# LED headroom
k = 0.8; out = np.where(out > k, k + 0.13 * np.tanh((out - k) / 0.13), out)
cv2.imwrite(sys.argv[2], cv2.cvtColor((out * 255 + .5).astype(np.uint8), cv2.COLOR_RGB2BGR))

# palette sample for the side loops: median colours of sky / pillars / rims
sky = (L > 15) & (L < 45) & (body < .2) & (rim < .1)
np.save(sys.argv[4], np.stack([np.median(out[sky], 0), np.median(out[body > .5], 0),
                               np.median(out[rim > .5], 0), np.percentile(out[sky], 90, axis=0)]))

# wide 3840x1536: pillars fit to height, centred, sides extended from mirrored + blurred edges of the grade
TW, TH = int(sys.argv[5]), int(sys.argv[6])
s = TH / H
pw = int(round(W * s))
pil = cv2.resize(out, (pw, TH), interpolation=cv2.INTER_LANCZOS4)
ext = cv2.copyMakeBorder(pil, 0, 0, (TW - pw) // 2, TW - pw - (TW - pw) // 2, cv2.BORDER_REFLECT)
bg = cv2.GaussianBlur(ext, (0, 0), 60)
x = np.arange(TW, dtype=np.float32)
cx0, cx1 = (TW - pw) / 2, (TW + pw) / 2
m = np.clip(np.minimum(x - cx0, cx1 - x) / (260 * TH / 1536), 0, 1)
m = (m * m * (3 - 2 * m))[None, :, None]
wide = ext * m + bg * (1 - m)
np.save(sys.argv[3] + ".npy", wide.astype(np.float32))
cv2.imwrite(sys.argv[3], cv2.cvtColor((np.clip(wide, 0, 1) * 255 + .5).astype(np.uint8), cv2.COLOR_RGB2BGR))
print("ok", pw)
open(sys.argv[3] + ".pw", "w").write(str(pw))
