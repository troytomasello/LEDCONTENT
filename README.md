# Retro 70s Space Party: LED Content (handoff notes)

Everything a new chat needs to pick this project up. Last updated 2026-11-12.

---

## 1. The project
- **Event:** a space-station party themed on 70s retro NASA and Austin Powers. There's a DJ, and the AV is run by a disguise media server.
- **Client ask:** several looks, each mostly loops, for every LED surface.
- **Troy:** the content designer. He works in **C4D** for stills and room renders, uses **Google Flow** (Veo / Gemini Omni) for walk-throughs and AI video, and **Nano Banana** for image edits.
- **Repo:** private GitHub repo `troytomasello/LEDCONTENT`, where all masters, scripts and sources live. Attach it to the new chat with push access, then clone it.
- **Notes:** this file lives in the repo as the README and in the claude.ai Project **CONTENT** as `claude/PROJECT_NOTES.md`.

## 2. Working preferences (important)
- **Bandwidth:** Troy has very limited bandwidth.
  - Send previews only by default: H.264 about 1280 px on the long edge, 30 fps, CRF 24, usually 0.3–3 MB.
  - Never send masters in chat unless asked; masters go to the GitHub repo.
  - Render the full master only after the preview is approved. (Once a look is approved, rendering every screen at once is fine.)
- **Loop length:** every loop is exactly **24 s** and seamless.
- **Frame rate:** **60 fps** for masters (1440 frames). Previews are 30 fps.
- **Operator format:** the disguise operator wants **ProRes**. Masters stay small H.264 (CRF 14) in the repo, and Troy converts locally with `scripts/make_prores.sh` (ProRes 422 HQ; pass `2` for plain 422). ProRes 4444 is only needed for transparency, such as the scenic overlay; a PNG with alpha is fine for stills.
- **Size limits:** GitHub refuses single files over 100 MB. Keep masters under about 95 MB (raise CRF slightly if needed).
- **Naming:** `LOOK_SCREEN_WxH_vNN_24s_60fps.mp4`.
- **Communication:** Troy wants honest assessments. He rejected weak results directly ("not cutting it"), so be candid about limits.

## 3. LED surfaces
| ID | Surface | Pixels | Notes |
|---|---|---|---|
| A | Upstage viewscreen, behind the DJ | 3840 × 1536 (2.5:1) | The DJ booth covers the lower centre. |
| B | Long porthole window, house left | 3648 × 576 | Framed by a portal facade. |
| C | Short porthole window, house right | 1728 × 576 | Framed by a portal facade. |
| Ceiling | 960 × 5760 canvas | 5 columns × 30 tiles of 192 × 192 px | Troy said 28 panels × 5 rows = 140 tiles, but the map shows 150 slots; to confirm. |

- The LED floor was cut.
- **Ceiling assumption:** each canvas column is one row of panels running the length of the room, and the canvas top is upstage (to confirm). Content drifts down the canvas, away from the DJ.
- **Pixel pitch:** assumed equal on every screen, which the classic lava's "same physical size" relies on. To confirm.

## 4. Look direction and palette
- **Style:** clean, bright 70s space station with shiny plastic and pops of colour. For LED, cap peaks at about 92% (soft highlight shoulder) and avoid full-white flashes and fine pinstripes, which cause moiré.
- **Space palette (nebula):**
  - void (.022, .010, .055)
  - sky (.26, .22, .58)
  - magenta (.70, .12, .52)
  - pink (1.0, .38, .72)
  - cyan (.30, .80, .95)
  - lilac (.78, .62, .92)
- **Neon lava:**
  - pink (1.0, .10, .62)
  - blue (.08, .52, 1.0)
  - background (.012, .006, .035) to (.06, .02, .12)
- **Classic lava** (sampled from Troy's lamp photo, `source/lava_lamp_color_reference.png`):
  - wax edge (.78, 0, .14)
  - wax mid (.96, .22, .22)
  - wax core (.99, .45, .32)
  - wax hot (1, .60, .41)
  - background (.17, .12, .30) to (.30, .25, .58)
- **Pillars of Creation:** ESA/Hubble heic1501a, CC BY 4.0. Credit **"NASA, ESA/Hubble and the Hubble Heritage Team"**. Hi-res source is in `source/`.

## 5. Current deliverables (all 24 s, 60 fps, in `masters/`)
| Look | Screens | Folder | Details |
|---|---|---|---|
| Nebula drift v04 | B, C, ceiling | `nebula_drift/` | Slow parallax drift (4–18 px/s), churning clouds, sub-pixel twinkling stars, 6 s crossfade at the loop point. C is a mirrored crop of B. The ceiling has no edge darkening. Approved. |
| Lava neon v03 | A, B, C, ceiling | `lava_neon/` | Glowing neon wax with no shine. Blob size scales with screen height. Ceiling has no pools. Approved. |
| Lava classic v04 big | A, B, C, ceiling | `lava_classic/` | Red/orange on blue. Blob radius 150–250 px, the same physical size everywhere, about 60–70% coverage. B uses 8 blobs, C uses 4 (seed 34). Approved ("looks great"). |
| Pillars still v02 | A | `stills/` | Regraded Pillars at 3840 × 1536, sides extended with matching nebula. The 4300 × 1720 oversized plate is also there. |
| Pillars from Flow clip v01 | A | `pillars_flow_30fps/` | From Troy's 8 s Flow clip: push-in removed, slowed 3.4×, stars replaced. Still 30 fps and 720p; redo from a 4K Flow export at 60 fps. |

Previews of everything are in `previews/`. The old 30 fps masters were removed but remain in the git history.

## 6. What was tried and rejected (don't repeat)
- **Pillars loop v01:** slow camera float plus a small warp. Rejected as "just moved the position".
- **Pillars v02/v03:** procedural flow-map advection of the still. Rejected because it can't create new cloud detail, so it reads as smearing.
- **Conclusion:** use AI video (Flow/Veo) for evolving clouds, with Claude finishing the result: loop, grade, fit, stars.
- **Lava v01 (glossy specular):** "too artificial". Lava now uses emissive, unshaded glow.

## 7. Workflows
### Flow clip to 24 s loop (`scripts/flowloop.py`)
1. Troy generates in Flow, using Gemini Omni 1.1 Flash or Veo 3.1. Start frames, end frames and Extend all work.
2. For a native loop, chain clips: clip 1 starts on the still; clip 2 starts from clip 1's last frame (Save frame, then Frames to Video); clip 3 ends on the original still. Prompt for a locked-off camera with no zoom or pan.
3. Claude's processing:
   - measure camera zoom with dense optical flow (ORB features lock onto Flow's static star layer)
   - remove static stars and the moving flare by inpainting
   - counteract the constant zoom
   - stretch to 24 s with optical-flow in-between frames
   - smoothstep crossfade at the loop point
   - re-add procedural twinkling stars
4. Usage: `flowloop.py FRAMES_DIR ZOOM_TOTAL OUT.mp4 [test]`. The 2026-11-11 clip measured a total zoom of 1.0969. The script's `FPS`/`L` values are still 30/720, so set them to 60/1440.

### Scenic overlay for A (in progress, Troy's side)
- **Nano Banana:** Troy turns `source/BG1_wall_panels_reference.jpg` (white sci-fi wall panels, with mirrored text on the right half) into a 70s observation-deck wall.
  - The large octagonal viewport is filled with **pure #00FF00**: about 60% of the width and 70% of the height, centred, slightly above centre.
  - Above it, a "VIEWPORT 01 — DEEP SPACE" label.
  - Racing stripes in orange, mustard, teal and hot pink.
  - Readable, non-mirrored labels in a Futura/Eurostile style.
  - Off-white rather than blown-out whites.
- **Claude, once he sends it:**
  - chroma-key the window into a clean mask
  - fit to 3840 × 1536 and soften hotspots
  - deliver the plate and mask as separate layers (PNG with alpha, or ProRes 4444)
  - composite over a nebula or Pillars loop for a preview

### Converting for disguise
- Run `bash scripts/make_prores.sh` from the repo folder (needs ffmpeg). Output goes to `./prores/` and files already converted are skipped.
- ProRes 422 HQ size at 60 fps: about 3.6 GB per 24 s for A, about 1.4 GB for B, about 3.2 GB for the ceiling. Roughly 20 GB for everything.

## 8. Scripts (`scripts/`, run from any folder; output goes to `$LED_OUT`, default `./out`)
| Script | What it does | Key settings |
|---|---|---|
| `render2.py` | Nebula drift for B and C, written in chunks | `python3 render2.py full LO HI` writes `partB_LO.mp4` / `partC_LO.mp4`; join them with the ffmpeg concat demuxer. `test N` renders a test frame. `FPS=60`, `LOOP_S=24`, `XF_S=6`. |
| `render_ceiling.py` | Ceiling nebula, 960 × 5760 | Same chunk interface. Renders a 5760 × 960 strip and rotates it 90° counter-clockwise. |
| `lava.py` | Lava for any size | `lava.py OUT W H [seed=N] [nopools] [classic] [fixed] [big] [nb=N] [test]`. The ceiling is rendered as a `5760 960 ... nopools` strip, then `ffmpeg -vf transpose=2`. |
| `grade.py` / `widefill.py` | Pillars regrade and nebula-extended wide plate | `grade.py SRC OUT_SQ OUT_WIDE PALETTE_NPY TW TH` |
| `pillars_flow.py` / `porthole.py` | Rejected procedural Pillars loops | Kept for reference. |
| `flowloop.py` | Flow clip to loop | See section 7. |
| `make_prores.sh` | Batch ProRes conversion | |

**Seeds and flags used:**
- Nebula: fixed inside the scripts.
- Neon lava: A seed=11, B 22, C 33, ceiling 44 + nopools.
- Classic lava: `classic fixed big`; A seed=11, B seed=22 nb=8, C seed=34 nb=4, ceiling seed=44 nopools.

**Render times** (2-core cloud workspace, 60 fps):
- Ceiling nebula: about 65 CPU-minutes.
- Lava A: about 26–33 minutes.
- Lava ceiling: about 25 minutes.
- B and C: 5–15 minutes.
- Run two jobs in parallel with `xargs -P 2`.
- Python gotcha: multiplying float32 arrays by `np.cos(...)` scalars promotes them to float64, which makes renders about 2.5× slower. Wrap those scalars in `float()`.

## 9. Open items and ideas
1. **Scenic overlay for A:** waiting on Troy's Nano Banana result (see section 7).
2. **Pillars evolving loop:** get a better or 4K Flow clip, chained for a native loop, then run `flowloop.py` at 60 fps.
3. **Confirm with the operator:**
   - ceiling orientation, and 150 vs 140 tiles
   - pixel pitch per surface
   - ProRes 422 vs 422 HQ
4. **Warp-speed full-room idea:** one 3D star tunnel rendered per surface so the streaks continue across all screens and the ceiling. Needs screen geometry from C4D (OBJ/FBX) and the ceiling map. Alternative: one 360° equirectangular loop that disguise maps spatially.
5. **Possible next steps:**
   - an After Effects `.jsx` setup (layered Turbulent Displace with Cycle Evolution, exact comps, render queue)
   - a GLSL shader for TouchDesigner or Notch for live fractal clouds
   - Notch running live on disguise as an "infinite" option
   - retro NASA label copy for the C4D panels

## 10. Claude's capabilities on this project (for expectations)
- **Can:**
  - procedural loops (noise, metaballs, particles) at any resolution, perfectly seamless
  - grading, compositing, keying, optical-flow retiming, stabilisation, encoding
  - scripts for After Effects, C4D, TouchDesigner, ffmpeg
  - prompts for Flow and Nano Banana
- **Cannot:**
  - generate images or video with AI models
  - watch video playback (Claude judges stills and measurements, so Troy's notes on motion are essential)
  - reach the open web from the workspace
  - use a GPU (the workspace has two CPU cores)
- **Workspace files don't carry over between chats.** The repo is the source of truth.
