"""Lava lamp loop: anisotropic metaballs + wavy pools, glossy wax shading, bloom. All motion periodic in L => seamless.
usage: lava.py OUT.mp4 W H [test]
"""
import sys, os, subprocess, numpy as np, cv2

OUT, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
FLAGS = sys.argv[4:]
TEST = "test" in FLAGS
POOLS = "nopools" not in FLAGS
SEED = int([f.split("=")[1] for f in FLAGS if f.startswith("seed=")][0]) if any(f.startswith("seed=") for f in FLAGS) else 42
FPS, L = 30, 720
s = H / 720.0                                     # scale: constants are written for 720 tall
rng = np.random.default_rng(SEED)

# palette: neon pink / neon blue on near-black violet
BG_TOP = np.array([.012, .006, .035], np.float32)
BG_BOT = np.array([.06, .02, .12], np.float32)
PINK   = np.array([1.00, .10, .62], np.float32)
BLUE   = np.array([.08, .52, 1.00], np.float32)
HOT    = np.array([1.00, .80, .95], np.float32)   # near-white tube core

# --- blobs: periodic paths --------------------------------------------------
NB = max(5, int(round(9 * (W / H) / (16 / 9))))
bx0 = ((np.arange(NB) + rng.uniform(.15, .85, NB)) / NB * .9 + .05)[rng.permutation(NB)] * W
by0 = rng.uniform(.25, .75, NB) * H
ay = rng.uniform(.14, .26, NB) * H                # vertical travel (slow)
ky = np.ones(NB, int)                             # one rise+fall per 24 s loop
py = rng.uniform(0, 2 * np.pi, NB)
ax = rng.uniform(10, 45, NB) * s
kx = rng.integers(1, 3, NB)
px = rng.uniform(0, 2 * np.pi, NB)
rad = rng.uniform(70, 125, NB) * s
kr = rng.integers(1, 3, NB)
pr = rng.uniform(0, 2 * np.pi, NB)
lil = rng.permutation(np.resize(np.array([0, 1, 0, 1, 0, 1, 1, 0, 0.5], np.float32), NB))   # 0 = pink, 1 = blue

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
T = 0.42                                          # iso threshold: wyvill (1-.25)^3 at d = r


def field(t):
    ph = 2 * np.pi * t / L
    F = np.zeros((H, W), np.float32)
    tint = np.zeros((H, W), np.float32)
    for i in range(NB):
        cy = by0[i] + ay[i] * np.sin(ky[i] * ph + py[i])
        vy = ay[i] * ky[i] * np.cos(ky[i] * ph + py[i])            # vertical speed (px/rad)
        cx = bx0[i] + ax[i] * np.sin(kx[i] * ph + px[i])
        r = rad[i] * (1 + .12 * np.sin(kr[i] * ph + pr[i]))
        st = 1 + .45 * abs(vy) / (ay.max() * 2)                   # stretch when moving
        R = 2 * r
        x0, x1 = int(max(0, cx - R * 1.1)), int(min(W, cx + R * 1.1 + 1))
        y0, y1 = int(max(0, cy - R * st * 1.1)), int(min(H, cy + R * st * 1.1 + 1))
        if x0 >= x1 or y0 >= y1: continue
        dx = (xx[y0:y1, x0:x1] - cx) / R
        dy = (yy[y0:y1, x0:x1] - cy) / (R * st)
        q = np.clip(1 - (dx * dx + dy * dy), 0, None)
        g = q * q * q
        F[y0:y1, x0:x1] += g
        tint[y0:y1, x0:x1] += g * lil[i]
    # pools: hot wax at the bottom, a thinner cooled layer at the top (wavy, periodic)
    wb = (H - 70 * s) + 22 * s * np.sin(2 * np.pi * (xx[0] / (420 * s)) + ph) + 12 * s * np.sin(2 * np.pi * (xx[0] / (190 * s)) - 2 * ph + 1)
    wt = (38 * s) + 14 * s * np.sin(2 * np.pi * (xx[0] / (360 * s)) - ph + 2) + 8 * s * np.sin(2 * np.pi * (xx[0] / (150 * s)) + 3 * ph)
    pb = np.clip((yy - wb[None, :]) / (90 * s) + .75, 0, 1.6)
    pt = np.clip((wt[None, :] - yy) / (70 * s) + .75, 0, 1.6)
    if POOLS:
        F += (pb ** 2 + pt ** 2) * .9
        tint += pt ** 2 * .9
    return F, np.clip(tint / np.maximum(F, 1e-4), 0, 1)


LIGHT = np.array([-.35, -.62, .70], np.float32); LIGHT /= np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1], np.float32); HALF /= np.linalg.norm(HALF)
vgrad = (yy / H)[..., None]
BG = BG_TOP * (1 - vgrad ** 1.6) + BG_BOT * vgrad ** 1.6
DITH = ((np.random.default_rng(3).random((H, W, 1)) - .5) / 255 * 1.5).astype(np.float32)


def frame(t):
    F, tint = field(t)
    gy, gx = np.gradient(F)
    gm = np.sqrt(gx * gx + gy * gy) + 1e-6
    m = np.clip((F - T) / (2.0 * gm) + .5, 0, 1)                 # soft 2-px edge
    core = (1 - np.exp(-np.clip(F - T, 0, None) / (1.1 * T)))[..., None]
    col = PINK * (1 - tint[..., None]) + BLUE * tint[..., None]
    wax = col * (.55 + .55 * core) + HOT * (.22 * core ** 3)      # glows from inside, hot centre
    img = BG * (1 - m[..., None]) + wax * m[..., None]
    lit = m[..., None] * col
    q = cv2.resize(lit, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.resize(cv2.GaussianBlur(q, (0, 0), 2.5 * s), (W, H), interpolation=cv2.INTER_LINEAR)
    g2 = cv2.resize(cv2.GaussianBlur(q, (0, 0), 11.25 * s), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img + .35 * g1 * (1 - .6 * m[..., None]) + .30 * g2
    kk = .82
    img = np.where(img > kk, kk + .11 * np.tanh((img - kk) / .11), img) + DITH
    return (np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)


if TEST:
    for t in (0, 180, 360, 540):
        cv2.imwrite(OUT.replace(".mp4", f"_{t:04d}.png"), cv2.cvtColor(frame(t), cv2.COLOR_RGB2BGR))
    a, b, c = frame(L - 1).astype(float), frame(0).astype(float), frame(1).astype(float)
    print("seam %.3f normal %.3f" % (np.abs(a - b).mean(), np.abs(b - c).mean()))
    sys.exit()

tmp = OUT + ".tmp.mp4"
e = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14" if W * H > 1.5e6 else "18",
                      "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
for t in range(L):
    e.stdin.write(frame(t).tobytes())
e.stdin.close(); assert e.wait() == 0
os.rename(tmp, OUT); print("DONE")
