"""Lava lamp loop: anisotropic metaballs + wavy pools, glossy wax shading, bloom. All motion periodic in L => seamless.
usage: lava.py OUT.mp4 W H [test]
"""
import sys, os, subprocess, numpy as np, cv2

OUT, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
TEST = len(sys.argv) > 4
FPS, L = 30, 720
s = H / 720.0                                     # scale: constants are written for 720 tall
rng = np.random.default_rng(42)

# palette (nebula family)
BG_TOP = np.array([.025, .008, .060], np.float32)
BG_BOT = np.array([.20, .035, .22], np.float32)
CORE   = np.array([1.00, .38, .72], np.float32)   # hot pink
MID    = np.array([.80, .12, .55], np.float32)    # magenta
EDGE   = np.array([.36, .07, .55], np.float32)    # violet
LILAC  = np.array([.62, .48, .98], np.float32)    # periwinkle accent
SPEC   = np.array([1.0, .86, .96], np.float32)

# --- blobs: periodic paths --------------------------------------------------
NB = 13
bx0 = rng.uniform(.08, .92, NB) * W
by0 = rng.uniform(.25, .75, NB) * H
ay = rng.uniform(.18, .42, NB) * H                # vertical travel
ky = rng.choice([1, 1, 2], NB)                    # cycles per loop (1 = 24 s up+down)
py = rng.uniform(0, 2 * np.pi, NB)
ax = rng.uniform(10, 45, NB) * s
kx = rng.integers(1, 4, NB)
px = rng.uniform(0, 2 * np.pi, NB)
rad = rng.uniform(38, 78, NB) * s
kr = rng.integers(1, 4, NB)
pr = rng.uniform(0, 2 * np.pi, NB)
lil = (rng.random(NB) < .25).astype(np.float32)   # a few periwinkle-tinted blobs

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
    F += (pb ** 2 + pt ** 2) * .9
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
    m = np.clip((F - T) / gm + .5, 0, 1)                         # 1-px antialiased edge
    h = 1 - np.exp(-np.clip(F - T, 0, None) / (0.9 * T))         # dome height, never plateaus
    hy, hx = np.gradient(cv2.GaussianBlur(h, (0, 0), 1.5 * s))
    k = 38 * s
    nx, ny, nz = -hx * k, -hy * k, np.ones_like(h)
    nn = np.sqrt(nx * nx + ny * ny + 1); nx, ny, nz = nx / nn, ny / nn, nz / nn
    diff = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    spec = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1) ** 60
    rim = (1 - nz) ** 2.5 * np.clip(ny, 0, 1)                     # glow bouncing up from the lamp base
    core = h[..., None]
    core = core ** 1.3
    wax = EDGE * (1 - core) ** 2 + MID * 2 * core * (1 - core) + CORE * core ** 2
    wax = wax * (1 - .55 * tint[..., None]) + LILAC * (.55 * tint[..., None]) * (.4 + .6 * core)
    wax = wax * (.30 + .85 * diff[..., None]) + SPEC * (.55 * spec)[..., None] + CORE * (.45 * rim)[..., None]
    img = BG * (1 - m[..., None]) + wax * m[..., None]
    glow = cv2.GaussianBlur(m[..., None] * (MID * .6 + CORE * .4), (0, 0), 28 * s)
    img = img + .30 * (glow if glow.ndim == 3 else glow[..., None]) * (1 - m[..., None] * .7)
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
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                      "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
for t in range(L):
    e.stdin.write(frame(t).tobytes())
e.stdin.close(); assert e.wait() == 0
os.rename(tmp, OUT); print("DONE")
