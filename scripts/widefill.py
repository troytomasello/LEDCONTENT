"""Upstage viewscreen plate 3840x1536: graded Pillars centred, sides extended with the side-loop nebula engine.
usage: widefill.py GRADED_WIDE_NPY OUT_PNG
"""
import sys, numpy as np, cv2
sys.argv, args = ["x"], sys.argv[1:]
src = open("/home/claude/portal/render2.py").read().split("# ---------------- build world")[0]
exec(src)

TW, TH = int(args[2]), int(args[3])
F = nebula_fields(TH, TW, 100)
img = shade(F, 0.0) * 0.85
for S in (star_list(int(5200 * TW * TH / 5.9e6), 120, TW, TH, .06, 1.2, .6, .95),
          star_list(700, 130, TW, TH, .25, 1.6, .8, 1.25, flare_p=.04),
          star_list(60, 140, TW, TH, .6, 2.2, 1.1, 1.7, flare_p=.4)):
    splat(img, S, S["x"].copy(), 0.0)
v = np.linspace(-1, 1, TH, dtype=np.float32)[:, None, None]
img = tone(img * (1 - .15 * v**2))

wide = np.load(args[0])                          # graded pillars + blurred extension, 0..1 RGB
pw = int(open(args[0].replace('.npy', '.pw')).read())
x = np.arange(TW, dtype=np.float32)
cx0, cx1 = (TW - pw) / 2, (TW + pw) / 2
m = np.clip(np.minimum(x - cx0 + 60, cx1 - x + 60) / (420 * TH / 1536), 0, 1)
m = (m * m * (3 - 2 * m))[None, :, None]
# outside the pillars: procedural nebula, tinted slightly toward the blurred grade so colour flows across
bgtint = cv2.GaussianBlur(wide, (0, 0), 120)
side = np.clip(img * 0.8 + bgtint * 0.35, 0, 1)
out = wide * m + side * (1 - m)
dith = (np.random.default_rng(9).random(out.shape[:2] + (1,)) - .5) / 255 * 1.5
out = np.clip(out + dith, 0, 1)
cv2.imwrite(args[1], cv2.cvtColor((out * 255 + .5).astype(np.uint8), cv2.COLOR_RGB2BGR))
print("ok")
