"""Turn a Flow/Veo clip into a seamless 24 s loop:
remove static stars -> counteract constant zoom -> optical-flow time stretch -> morph seam -> re-add twinkling stars.
usage: flowloop.py FRAMES_DIR ZOOM_TOTAL OUT_MP4 [test]
"""
import sys, os, glob, subprocess, numpy as np, cv2
args = sys.argv[1:]
sys.argv = ["x"]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "render2.py")).read().split("# ---------------- build world")[0])

FR = sorted(glob.glob(os.path.join(args[0], "f*.png")))
ZT = float(args[1])
OUT = args[2]
TEST = len(args) > 3
N = len(FR)
src = [cv2.imread(f) for f in FR]                         # BGR uint8
H, W = src[0].shape[:2]
FPS, L, K = 30, 720, 90                                   # 24 s loop, 3 s seam

# 1. static star mask: points that are bright-compact in most frames
ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
th = np.stack([cv2.morphologyEx(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.MORPH_TOPHAT, ker) for f in src[::4]])
persist = np.percentile(th, 60, axis=0)
early = th[:8].max(0)                                     # the big flare that fades out early
raw = ((persist > 22) | (early > 70)).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(raw, 8)
keep = np.zeros(n, np.uint8); keep[1:] = (st[1:, cv2.CC_STAT_AREA] <= 30)   # stars are tiny; rims/gas are not
mask = keep[lab]
mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
# flare spikes: long thin bright lines near strong early stars
big = cv2.dilate(((early > 120).astype(np.uint8)), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
spikes = ((th[:8].max(0) > 25) & (big > 0)).astype(np.uint8)
mask = cv2.dilate(mask | spikes, None)
print("star mask px:", int(mask.sum()), flush=True)
def flare_mask(f):
    g = cv2.GaussianBlur(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (0, 0), 3)
    g[int(H * .3):] = 0                                   # moving flare lives in the top of frame
    y, x = np.unravel_index(np.argmax(g), g.shape)
    m = np.zeros((H, W), np.uint8)
    if g[y, x] < 235: return m
    cv2.circle(m, (int(x), int(y)), int(34 * W / 1280), 1, -1)
    R = int(240 * W / 1280); t = max(5, int(9 * W / 1280))
    cv2.line(m, (int(x) - R, int(y)), (int(x) + R, int(y)), 1, t)
    cv2.line(m, (int(x), int(y) - R), (int(x), int(y) + R), 1, t)
    return m
clean = []
for i, f in enumerate(src):
    m = mask | (flare_mask(f) if i < 48 else 0)
    clean.append(cv2.inpaint(f, m, 5, cv2.INPAINT_TELEA))

# 2. counteract zoom: lock to the last frame's (most zoomed) framing -> scale earlier frames up
def unzoom(img, i):
    z = ZT ** ((N - 1 - i) / (N - 1))
    M = np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H / 2]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
stab = [unzoom(f, i) for i, f in enumerate(clean)]
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in stab]
d = np.abs(stab[0].astype(float) - stab[-1].astype(float)).mean()
print("after stabilise: first vs last diff %.2f" % d, flush=True)

# 3. optical-flow interpolation
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
cache = {}
def flows(i):
    if i not in cache:
        if len(cache) > 6: cache.pop(next(iter(cache)))
        cache[i] = (dis.calc(gray[i], gray[i + 1], None), dis.calc(gray[i + 1], gray[i], None))
    return cache[i]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def at(tau):
    tau = min(max(tau, 0.0), N - 1.0)
    i = min(int(tau), N - 2); a = tau - i
    if a < 1e-4: return stab[i].astype(np.float32)
    fw, bw = flows(i)
    # backward-warp: pixel p at time a came from p - a*fw in frame i, and from p - (1-a)*bw in frame i+1
    A = cv2.remap(stab[i], xx - a * fw[..., 0], yy - a * fw[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    B = cv2.remap(stab[i + 1], xx - (1 - a) * bw[..., 0], yy - (1 - a) * bw[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return A.astype(np.float32) * (1 - a) + B.astype(np.float32) * a

r = (N - 1) / (L + K - 1)                                 # source frames per output frame
print("slow-down vs real time: %.2fx" % (1 / (r * FPS / 24)), flush=True)

# 5. stars (BGR order for splat tints is irrelevant: tints are near-white)
S1 = star_list(int(260 * W * H / 921600), 900, W, H, .08, .9, .55, .85)
S2 = star_list(int(40 * W * H / 921600), 901, W, H, .3, 1.4, .7, 1.05, flare_p=.1)
def frame(j):
    if j < K:
        w = j / K; w = w * w * (3 - 2 * w)
        img = at((j + L) * r) * (1 - w) + at(j * r) * w
    else:
        img = at(j * r)
    img = img / 255.0
    ph = 2 * np.pi * j / L
    for S in (S1, S2):
        splat(img, S, S["x"].copy(), ph)
    img = tone(img)
    return (np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)

if TEST:
    for j in (0, 45, 360, 719):
        cv2.imwrite(OUT.replace(".mp4", f"_{j:04d}.png"), frame(j))
    a, b, c = frame(L - 1).astype(float), frame(0).astype(float), frame(1).astype(float)
    print("loop seam %.3f vs normal %.3f" % (np.abs(a - b).mean(), np.abs(b - c).mean()))
    sys.exit()

tmp = OUT + ".tmp.mp4"
e = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                      "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                      "-pix_fmt", "yuv420p", "-g", "60", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
for j in range(L):
    e.stdin.write(frame(j).tobytes())
    if j % 120 == 0: print(j, flush=True)
e.stdin.close(); assert e.wait() == 0
os.rename(tmp, OUT); print("DONE", flush=True)
