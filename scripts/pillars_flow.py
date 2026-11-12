"""Pillars viewscreen v02: the gas itself flows forever (two-scale flow-map advection along curl noise),
plus photo-evaporation streaming off the pillars. Every period divides the loop => seamless.
usage: pillars_flow.py PLATE_PNG OUT_MP4 OUT_W  (OUT_W=1280 preview, 3840 master)  [lo hi for chunks]
"""
import sys, os, subprocess, numpy as np, cv2
args = sys.argv[1:]
sys.argv = ["x"]
exec(open("/home/claude/portal/render2.py").read().split("# ---------------- build world")[0])

OW = int(args[2]); OH = OW * 2 // 5                     # 2.5:1 (3840x1536 / 1280x512)
FPS, L = 30, 720
sc = OW / 3840.0                                        # all px constants below are written for 3840 wide
lo, hi = (int(args[3]), int(args[4])) if len(args) > 4 else (0, L)

big = cv2.cvtColor(cv2.imread(args[0]), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
BH, BW = big.shape[:2]
k = BW / 3840 * 0.985                                   # same framing as v01 still
cw, ch = int(3840 * k), int(1536 * k)
x0, y0 = (BW - cw) // 2, (BH - ch) // 2
img0 = cv2.resize(big[y0:y0 + ch, x0:x0 + cw], (OW, OH), interpolation=cv2.INTER_AREA)
H, W = OH, OW

Lum = img0 @ np.array([.3, .55, .15], np.float32)
# --- masks -------------------------------------------------------------------
# stars: bright compact points -> keep still (flowing stars look wrong)
th = cv2.morphologyEx(Lum, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, int(15 * sc) | 1),) * 2))
star = cv2.GaussianBlur((th > 0.12).astype(np.float32), (0, 0), max(1.0, 6 * sc))
star = np.clip(star * 4, 0, 1)
# pillar density: dark, saturated, large-scale bodies
dense = cv2.GaussianBlur(np.clip((0.30 - Lum) / 0.15, 0, 1) * np.clip(img0[..., 0] - img0[..., 2] + .25, 0, 1), (0, 0), 14 * sc)
dense = np.clip(dense / max(dense.max(), 1e-3), 0, 1)
gas = 1 - 0.7 * ss(.15, .7, dense)                          # cores flow at 30%, surfaces boil, gas streams
fmask = (gas * (1 - star)).astype(np.float32)

# --- flow field (px per period, 3840 units) -----------------------------------
def curl(psi):
    gy, gx = np.gradient(psi)
    return gy, -gx                                       # (vx, vy) divergence-free swirl


def unit(vx, vy):
    m = np.sqrt(vx**2 + vy**2); m = np.percentile(m, 95) + 1e-6
    return vx / m, vy / m


psiL = cv2.GaussianBlur(fbm(H, W, 2.6, 700, lowcut=.4), (0, 0), 30 * sc)
psiS = cv2.GaussianBlur(fbm(H, W, 2.0, 701, lowcut=1.5), (0, 0), 8 * sc)
vLx, vLy = unit(*curl(psiL))
vSx, vSy = unit(*curl(psiS))
# photo-evaporation: gas peels off pillar surfaces, away from the bodies and upward (toward the stars)
dd = cv2.GaussianBlur(dense, (0, 0), 40 * sc)
ex, ey = np.gradient(-dd)[1], np.gradient(-dd)[0]
ex, ey = unit(ex, ey)
ey = ey - 0.35                                           # upward bias
edgeband = ss(.05, .35, dense) * (1 - ss(.6, .95, dense))
D_L, P_L = 84 * sc, 360                                  # big rolling flow: 84px per 12 s
D_S, P_S = 26 * sc, 120                                  # fine turbulence: 26px per 4 s
VX_L = (vLx * 1.0 + ex * 0.9 * edgeband) * D_L * fmask
VY_L = (vLy * 1.0 + ey * 0.9 * edgeband) * D_L * fmask
VX_S = vSx * D_S * fmask
VY_S = vSy * D_S * fmask
# per-pixel phase offsets: hides the flow-map 'pulse' (no global breathing)
offL = cv2.GaussianBlur(fbm(H, W, 1.8, 710), (0, 0), 20 * sc)
offS = cv2.GaussianBlur(fbm(H, W, 1.8, 711), (0, 0), 10 * sc)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# glow for gentle rim shimmer
glow = np.clip(cv2.GaussianBlur(Lum, (0, 0), max(.8, 3 * sc)) - cv2.GaussianBlur(Lum, (0, 0), 40 * sc), 0, None)
glow = np.clip(glow / np.percentile(glow, 99.5), 0, 1.5)
starlayer = img0 * star[..., None]                      # stars re-laid on top, static


def frame(t):
    tl = (t / P_L + offL) % 1.0
    ts = (t / P_S + offS) % 1.0
    out = 0
    for aL, wL in ((tl, 1 - np.abs(2 * tl - 1)), ((tl + .5) % 1, np.abs(2 * tl - 1))):
        for aS, wS in ((ts, 1 - np.abs(2 * ts - 1)), ((ts + .5) % 1, np.abs(2 * ts - 1))):
            # small-scale warp also rides the large flow (nested => filament stretching)
            mx = xx - (aL - .5) * VX_L - (aS - .5) * VX_S
            my = yy - (aL - .5) * VY_L - (aS - .5) * VY_S
            s = cv2.remap(img0, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            out = out + s * (wL * wS)[..., None]
    # flow-map blending slightly softens contrast: restore local contrast a touch
    blur = cv2.GaussianBlur(out, (0, 0), 6 * sc + .5)
    out = out + 0.25 * (out - blur)
    ph = 2 * np.pi * t / L
    shimmer = 1 + 0.08 * glow * np.sin(ph * 6 + offL * 12.0)
    out = out * shimmer[..., None]
    out = out * (1 - star[..., None]) + starlayer * 1.0 + out * star[..., None] * 0  # stars stay crisp
    out = out + starlayer * 0.0
    return (np.clip(tone(out), 0, 1) * 255 + .5).astype(np.uint8)


if lo == -1:                       # test stills
    for t in (0, 60, 900):
        cv2.imwrite(args[1].replace(".mp4", f"_{t:04d}.png"), cv2.cvtColor(frame(t), cv2.COLOR_RGB2BGR))
    a, b, c = frame(L - 1).astype(float), frame(0).astype(float), frame(1).astype(float)
    print("seam", round(np.abs(a - b).mean(), 3), "normal", round(np.abs(b - c).mean(), 3)); sys.exit()

crf = "24" if OW <= 1920 else "14"
tmp = args[1] + ".tmp.mp4"
e = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", crf,
                      "-pix_fmt", "yuv420p", "-g", "60", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
for t in range(lo, hi):
    e.stdin.write(frame(t).tobytes())
    if t % 300 == 0: print(t, flush=True)
e.stdin.close(); assert e.wait() == 0
os.rename(tmp, args[1]); print("DONE", flush=True)
