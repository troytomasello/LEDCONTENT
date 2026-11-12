"""Side-portal space loop v02: slow drift, churning clouds, sub-pixel stars, crossfade loop.
B (house left) 3648x576; C (house right) 1728x576 = mirrored crop of B (drift reverses).
usage: render2.py test | full | widefill
"""
import sys, subprocess, numpy as np, cv2

FPS = 60
LOOP_S, XF_S = 24, 6                      # loop length, crossfade length (s)
L, T = LOOP_S * FPS, XF_S * FPS
W, H, WC, X0 = 5760, 960, 960, 0
WP = 6144                                  # world width (periodic noise)
# drift speeds in px/s (v01 was 60 / 120 / 180)
V_NEB, V_FAR, V_WISP, V_MID, V_NEAR = 4.0, 6.0, 9.0, 11.0, 18.0
OUT = "/home/claude/portal/out60"

VOID   = np.array([.022, .010, .055], np.float32)
SKY    = np.array([.26, .22, .58], np.float32)
MAG    = np.array([.70, .12, .52], np.float32)
PINK   = np.array([1.0, .38, .72], np.float32)
CYAN   = np.array([.30, .80, .95], np.float32)
LILAC  = np.array([.78, .62, .92], np.float32)


def fbm(h, w, beta, seed, aspect=1.0, lowcut=0.0):
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.rfftfreq(w)[None, :] * h * aspect
    f = np.sqrt(fx**2 + fy**2); f[0, 0] = 1
    spec = (r.standard_normal((h, w // 2 + 1)) + 1j * r.standard_normal((h, w // 2 + 1))) * f**-beta
    spec[0, 0] = 0
    if lowcut: spec *= 1 - np.exp(-(f / lowcut) ** 2)
    n = np.fft.irfft2(spec, s=(h, w))
    lo, hi = np.percentile(n, [1, 99])
    return np.clip((n - lo) / (hi - lo), 0, 1).astype(np.float32)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def nebula_fields(h, w, seed=0):
    """Density + colour-control fields; colour is applied per frame so breathing can modulate density."""
    return dict(
        n1=fbm(h, w, 1.85, seed + 1, lowcut=0.9), n2=fbm(h, w, 1.7, seed + 2, lowcut=0.8), n3=fbm(h, w, 1.6, seed + 3),
        det=fbm(h, w, 1.55, seed + 6, lowcut=1.2), lane=fbm(h, w, 1.9, seed + 4), base=fbm(h, w, 1.4, seed + 5),
        b1=fbm(h, w, 2.2, seed + 7), b2=fbm(h, w, 2.2, seed + 8))


def shade(F, ph):
    """F: dict of (h,w) fields already warped/sliced. ph: loop phase (radians) for breathing."""
    breathe = 0.10 * ((F["b1"] - .5) * float(np.cos(ph)) + (F["b2"] - .5) * float(np.sin(ph)))
    n1 = F["n1"] + breathe
    d = ss(0.32, 0.97, n1) ** 1.5 * (0.45 + 0.75 * F["det"]) * (0.65 + 0.5 * F["base"])
    warm = ss(.35, .7, F["n2"])[..., None]
    col = VOID + 0.10 * F["base"][..., None] * SKY
    col = col + ss(.2, .9, F["n3"])[..., None] * (SKY * .7 + MAG * .3) * 0.22
    col = col + d[..., None] * (SKY * (1 - warm) + MAG * warm) * 1.05
    col = col + (d ** 2)[..., None] * (PINK * warm + LILAC * (1 - warm)) * 0.42
    # rim glow on cloud boundaries: pink on warm side, cyan on cool side
    d = d.astype(np.float32)
    db = cv2.GaussianBlur(d, (0, 0), 2.5)
    e = np.hypot(cv2.Sobel(db, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(db, cv2.CV_32F, 0, 1, ksize=3))
    e = cv2.GaussianBlur(np.clip(e * 9, 0, 1), (0, 0), 3) * ss(.15, .5, d)
    col = col + e[..., None] * (PINK * warm + CYAN * (1 - warm)) * 0.30
    ridge = 1 - np.abs(2 * F["lane"] - 1)
    dust = ss(.70, .95, ridge) * ss(.3, .65, F["n1"]) + ss(.62, .9, 1 - F["det"]) * ss(.45, .8, d) * .5
    return col * (1 - 0.8 * np.clip(dust, 0, 1)[..., None])


def warp_fields(h, w, seed):
    r = [cv2.GaussianBlur(fbm(h, w, 2.4, seed + i) - .5, (0, 0), 6) for i in range(4)]
    return r  # ax, bx, ay, by


def star_list(n, seed, w, h, bmin, bmax, smin, smax, flare_p=0.0):
    r = np.random.default_rng(seed)
    b = bmin + (bmax - bmin) * r.random(n) ** 4
    s = r.uniform(smin, smax, n) * (0.75 + 0.5 * b / bmax)
    tints = np.array([[1, 1, 1], [1, .8, .95], [.8, .85, 1], [1, .7, .88], [.75, 1, .98], [.95, .85, 1]], np.float32)
    return dict(x=r.uniform(0, w, n), y=r.uniform(0, h, n), b=b, s=np.maximum(s, .75),
                tint=tints[r.integers(len(tints), size=n)],
                k=r.integers(2, 9, n), ph=r.uniform(0, 2 * np.pi, n), amp=r.uniform(0, .35, n),
                flare=r.random(n) < flare_p)


def splat(img, S, xs, t_phase, K=9):
    """Additive sub-pixel gaussian splat. xs: screen x positions (float)."""
    h, w, _ = img.shape
    keep = (xs > -K) & (xs < w + K) & ~S["flare"]
    x, y, s = xs[keep], S["y"][keep], S["s"][keep]
    b = S["b"][keep] * (1 - S["amp"][keep] + S["amp"][keep] * (0.5 + 0.5 * np.sin(S["k"][keep] * t_phase + S["ph"][keep])))
    tint = S["tint"][keep]
    o = np.arange(K) - K // 2
    ix = np.floor(x).astype(int)[:, None, None] + o[None, None, :]
    iy = np.floor(y).astype(int)[:, None, None] + o[None, :, None]
    d2 = (ix + .5 - x[:, None, None]) ** 2 + (iy + .5 - y[:, None, None]) ** 2
    g = np.exp(-d2 / (2 * s[:, None, None] ** 2)) + .1 * np.exp(-d2 / (2 * (2.6 * s[:, None, None]) ** 2))
    g *= b[:, None, None]
    ix, iy = np.broadcast_to(ix, g.shape), np.broadcast_to(iy, g.shape)
    ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
    flat = (iy * w + ix)[ok]
    gw = g[ok]
    tt = np.broadcast_to(tint[:, None, None, :], g.shape + (3,))[ok]
    for c in range(3):
        img[..., c] += np.bincount(flat, gw * tt[:, c], minlength=h * w).reshape(h, w)
    # flares
    for i in np.nonzero((xs > -60) & (xs < w + 60) & S["flare"])[0]:
        x, y, s = xs[i], S["y"][i], S["s"][i]
        R = int(s * 26)
        x0, x1, y0, y1 = max(0, int(x) - R), min(w, int(x) + R + 1), max(0, int(y) - R), min(h, int(y) + R + 1)
        if x0 >= x1 or y0 >= y1: continue
        dx = (np.arange(x0, x1) + .5 - x)[None, :]; dy = (np.arange(y0, y1) + .5 - y)[:, None]
        g = np.exp(-(dx**2 + dy**2) / (2 * s * s)) + .15 * np.exp(-(dx**2 + dy**2) / (2 * (3 * s) ** 2)) \
            + .45 * np.exp(-np.abs(dx) / (6 * s)) * np.exp(-dy**2 / (.45 * s * s)) \
            + .45 * np.exp(-np.abs(dy) / (6 * s)) * np.exp(-dx**2 / (.45 * s * s))
        bb = S["b"][i] * (1 - S["amp"][i] + S["amp"][i] * (0.5 + 0.5 * np.sin(S["k"][i] * t_phase + S["ph"][i])))
        img[y0:y1, x0:x1] += (bb * g)[..., None] * S["tint"][i]


def tone(x):
    k = 0.8
    return np.where(x > k, k + 0.13 * np.tanh((x - k) / 0.13), x)


# ---------------- build world ----------------
print("building world...", flush=True)
NF = nebula_fields(H, WP, 0)
WF = fbm(H, WP, 2.1, 11, aspect=.55), fbm(H, WP, 1.5, 12)          # wisps
WRP = warp_fields(H, WP, 50)
FAR = star_list(7000, 20, WP, H, .06, 1.3, .55, .85)
MID = star_list(1150, 30, WP, H, .25, 1.7, .7, 1.1, flare_p=.03)
NEAR = star_list(180, 40, WP, H, .5, 2.4, .95, 1.5, flare_p=.3)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
DITH = ((np.random.default_rng(3).random((H, W, 1)) - .5) / 255 * 1.5).astype(np.float32)
AMP1 = 20.0  # px of cloud churn


def X(t):
    """Raw frame at time index t (not yet loop-blended), float32 linear-ish RGB."""
    sec = t / FPS
    ph = float(2 * np.pi * t / L)
    # cloud warp in world coords (periodic in L => churn itself loops)
    sh = V_NEB * sec
    cols = (np.arange(W) + int(sh)) % WP
    ax, bx, ay, by = [f[:, cols] for f in WRP]
    dx = AMP1 * (ax * float(np.cos(ph)) + bx * float(np.sin(ph))) + 0.5 * AMP1 * (ay * np.cos(2 * ph + 1) - bx * np.sin(2 * ph + 1))
    dy = AMP1 * .55 * (ay * np.cos(ph) + by * np.sin(ph))
    dx, dy = dx.astype(np.float32), dy.astype(np.float32)
    mx = ((XX + sh + dx) % WP).astype(np.float32)
    my = ((YY + dy) % H).astype(np.float32)
    F = {k: cv2.remap(v, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP) for k, v in NF.items()}
    img = shade(F, ph)
    # wisps (mid layer, own speed, same churn fields)
    shw = V_WISP * sec
    mxw = ((XX + shw + 1.4 * dx) % WP).astype(np.float32)
    w1 = cv2.remap(WF[0], mxw, ((YY + 1.4 * dy) % H).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    w2 = cv2.remap(WF[1], mxw, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    img = img + (ss(.6, .98, w1) * ss(.3, .8, w2))[..., None] * (PINK * .6 + LILAC * .4) * .2
    # stars
    for S, v in ((FAR, V_FAR), (MID, V_MID), (NEAR, V_NEAR)):
        xs = (S["x"] - v * sec) % WP
        xs = np.where(xs > WP - 64, xs - WP, xs)
        splat(img, S, xs, ph)
    v = np.linspace(-1, 1, H, dtype=np.float32)[:, None, None]
    img = img  # no edge falloff on the ceiling
    return img


def final(i):
    if i < T:
        w = i / T
        w = w * w * (3 - 2 * w)
        img = X(i) * w + X(i + L) * (1 - w)
    else:
        img = X(i)
    img = tone(img) + DITH
    return (np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)


def c_view(fr):
    return np.ascontiguousarray(fr[:, X0:X0 + WC][:, ::-1])


def canvas(fr):
    return np.ascontiguousarray(cv2.rotate(fr, cv2.ROTATE_90_COUNTERCLOCKWISE))   # 960 x 5760, content moves down


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "test":
        fr = canvas(final(int(sys.argv[2])))
        cv2.imwrite(f"{OUT}/ceil_test.png", cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    else:
        lo, hi = int(sys.argv[2]), int(sys.argv[3])
        tmp = f"{OUT}/ceil_{lo:04d}.tmp.mp4"
        e = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x5760",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
                              "-pix_fmt", "yuv420p", "-g", "60", tmp], stdin=subprocess.PIPE)
        for i in range(lo, hi):
            e.stdin.write(canvas(final(i)).tobytes())
            if i % 60 == 0: print(lo, i, flush=True)
        e.stdin.close(); assert e.wait() == 0
        import os; os.rename(tmp, f"{OUT}/ceil_{lo:04d}.mp4"); print("DONE", lo, flush=True)
