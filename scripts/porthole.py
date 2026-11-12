"""Upstage viewscreen loop 3840x1536 from the oversized graded plate. Every motion is periodic in the loop => seamless.
usage: porthole.py PLATE_PNG test|full [lo hi]
"""
import sys, subprocess, os, numpy as np, cv2
args = sys.argv[1:]
sys.argv = ["x"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "render2.py")).read().split("# ---------------- build world")[0])

OW, OH = 3840, 1536
FPS, L = 30, 1800
OUTD = os.environ.get("LED_OUT", "out")
plate = cv2.cvtColor(cv2.imread(args[0]), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
BH, BW = plate.shape[:2]                                   # 1720 x 4300

# glow map (bright fine structure: rims, lit gas) for breathing
Lum = plate @ np.array([.3, .55, .15], np.float32)
glow = np.clip(cv2.GaussianBlur(Lum, (0, 0), 3) - cv2.GaussianBlur(Lum, (0, 0), 40), 0, None)
glow = cv2.GaussianBlur(glow / np.percentile(glow, 99.5), (0, 0), 4).clip(0, 1.5)
# churn mask: gas & sky move more than dense dark pillar bodies
dense = np.clip((0.22 - Lum) / 0.12, 0, 1) * 0
mask = (0.45 + 0.55 * cv2.GaussianBlur(np.clip(Lum / 0.35, 0, 1), (0, 0), 25)).astype(np.float32)

# periodic warp fields in plate coords (low frequency, ~smooth over 100s of px)
wf = [cv2.GaussianBlur(fbm(BH, BW, 2.3, 300 + i, lowcut=0.6) - .5, (0, 0), 18) for i in range(4)]
wf = [f / (np.abs(f).max() + 1e-6) for f in wf]
bph = [cv2.GaussianBlur(fbm(BH, BW, 2.0, 310 + i), (0, 0), 20) for i in range(2)]
AMP = 7.0                                                   # px of gas churn (plate px)

# foreground haze (parallax layer), in an extended canvas
HZ = fbm(OH, OW + 512, 2.0, 400, aspect=.7, lowcut=0.5), fbm(OH, OW + 512, 1.6, 401)
STARS = star_list(380, 500, BW, BH, .25, 1.1, .65, 1.0)
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
DITH = ((np.random.default_rng(5).random((OH, OW, 1)) - .5) / 255 * 1.5).astype(np.float32)


def frame(t):
    ph = 2 * np.pi * t / L
    c, s = float(np.cos(ph)), float(np.sin(ph))
    # camera float: ellipse + gentle breathing zoom (all one cycle per loop)
    ox, oy = 46.0 * c, 20.0 * float(np.sin(ph + 0.6))
    zoom = 1.0 + 0.022 * (0.5 - 0.5 * float(np.cos(ph)))   # 1.000 .. 1.022
    k = (BW / OW) * 0.985 / zoom                              # plate px per output px (<1.12)
    px = BW / 2 + ox + (xx - OW / 2) * k
    py = BH / 2 + oy + (yy - OH / 2) * k
    # churn sampled at plate coords: integer lookup is fine (fields are very smooth)
    ix = np.clip(px.astype(np.int32), 0, BW - 1); iy = np.clip(py.astype(np.int32), 0, BH - 1)
    m = mask[iy, ix]
    dx = AMP * m * (wf[0][iy, ix] * c + wf[1][iy, ix] * s)
    dy = AMP * .7 * m * (wf[2][iy, ix] * c + wf[3][iy, ix] * s)
    img = cv2.remap(plate, (px + dx).astype(np.float32), (py + dy).astype(np.float32),
                    cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # rim/gas breathing
    g = glow[iy, ix]
    br = bph[0][iy, ix] * c + bph[1][iy, ix] * s - .5 * (c + s)
    img = img * (1 + (0.10 * g * (0.6 + br))[..., None])
    # twinkling extra stars (plate coords -> screen)
    sx = (STARS["x"] - BW / 2 - ox) / k + OW / 2
    sy = (STARS["y"] - BH / 2 - oy) / k + OH / 2
    S2 = dict(STARS); S2["y"] = sy
    splat(img, S2, sx, ph)
    # foreground haze, 2.2x the camera motion => parallax
    hx = ((xx + 256 + 2.2 * ox / k) % (OW + 512)).astype(np.float32)
    hy = ((yy + 2.2 * oy / k) % OH).astype(np.float32)
    h1 = cv2.remap(HZ[0], hx, hy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    h2 = cv2.remap(HZ[1], hx, hy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    haze = ss(.55, .95, h1) * ss(.3, .8, h2)
    img = img + haze[..., None] * (PINK * .55 + LILAC * .45) * 0.07
    img = tone(img) + DITH
    return (np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)


if args[1] == "test":
    import time
    for t in (0, 450, 900):
        t0 = time.time(); fr = frame(t); print(t, f"{time.time()-t0:.2f}s", flush=True)
        cv2.imwrite(f"{OUTD}/ph_{t:04d}.png", cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    a, b, c2 = frame(L - 1).astype(float), frame(0).astype(float), frame(1).astype(float)
    print("seam diff", round(np.abs(a - b).mean(), 3), "normal diff", round(np.abs(b - c2).mean(), 3))
else:
    lo, hi = int(args[2]), int(args[3])
    tmp = f"{OUTD}/partA_{lo:04d}.tmp.mp4"
    e = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "14", "-pix_fmt", "yuv420p", "-g", "60", tmp], stdin=subprocess.PIPE)
    for t in range(lo, hi):
        e.stdin.write(frame(t).tobytes())
        if t % 100 == 0: print(lo, t, flush=True)
    e.stdin.close(); assert e.wait() == 0
    os.rename(tmp, f"{OUTD}/partA_{lo:04d}.mp4"); print("DONE", lo, flush=True)
