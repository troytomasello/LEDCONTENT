# Retro 70s Space Party: LED Content Notes

## Working preferences
- **Previews only by default:** 720p-class H.264 at roughly 1280 px wide and a few MB. Never send masters unless asked.
- **Masters live in the private GitHub repo `troytomasello/ledcontent`** (masters/, stills/, previews/, scripts/). Troy downloads them when bandwidth allows.
- **AI-generated motion:** Troy generates short clips in Flow/Veo; Claude loops them to 24 s, fits them to the screen size, regrades and encodes.
- **Previews first:** the full-res master is rendered only after the preview is approved.
- **Tools:** Troy works in C4D for stills and room renders, and uses Google Flow only for walk-through animations, not screen content.
- **Loops are exactly 24 seconds** (720 frames at 30 fps) and seamless.
- **Playback:** a disguise server. Final codec is HAP / HAP Q at 30 fps (to be confirmed with the operator).

## LED surfaces
| ID | Surface | Pixels |
|---|---|---|
| A | Upstage viewscreen (behind the DJ) | 3840 × 1536 |
| B | Long porthole window, house left | 3648 × 576 |
| C | Short porthole window, house right | 1728 × 576 |
| Ceiling | 5 columns × 30 tiles of 192 × 192 px on the pixel map | **960 × 5760.** Each column is read as one panel row running the length of the room; canvas top is assumed upstage (to confirm). |

The LED floor has been cut.

## Look direction
- 70s retro NASA / Austin Powers space station: clean, bright, shiny plastic with pops of color.
- The party palette is pink and iridescent: deep violet space, magenta, hot pink, periwinkle, with pink and cyan rims.
- Peaks are capped at about 92% for LED headroom. Avoid full-white flashes and fine pinstripes, which cause moiré.
- Pillars of Creation: ESA/Hubble heic1501a, CC BY 4.0. Credit "NASA, ESA/Hubble and the Hubble Heritage Team".

## Deliverables
| Item | Status | Notes |
|---|---|---|
| B/C side loops v03 | Preview sent | 24 s seamless (6 s crossfade at the loop point), slow drift and churning clouds. C is a mirrored crop of B. Masters rendered and kept in the workspace. |
| A still plate v02 | Delivered | Graded Pillars, sides extended with the matching nebula. |
| A loop v01 | Rejected | Mostly camera float; too little internal motion. |
| A loop v02 (gas flows) | Superseded | 60 s version. |
| A loop v03 (gas flows) | Preview sent | 24 s. Flowing gas, gas peeling off the pillars, stars held still. Awaiting feedback before the 4K master. |
| A loop from Flow clip v01 | Preview sent | Troy's Flow clip (1280×720, 8 s): push-in removed, slowed 3.4× with generated in-between frames, 3 s blend at the loop point, stars replaced. `scripts/flowloop.py`. |
| Lava lamp look v02 (all screens) | Masters in repo | Neon pink and blue glowing wax, no shine, one slow rise and fall per 24 s. A, B and C have wax pools top (blue) and bottom (pink); the ceiling has free-floating blobs, no pools. `masters/lava/`, `scripts/lava.py`. |
| Lava lamp classic v03 (all screens) | Masters in repo | Red/orange wax on periwinkle-indigo, colors sampled from Troy's lamp photo. Same physical blob size on every screen (assumes equal pixel pitch). `masters/lava_classic/`, run with `classic fixed`. |
| Interior plate (look 1) | Troy, in C4D | Flat-on camera at 3840 × 1536 with the porthole as an alpha. |
| Ceiling loop v01 | Preview sent | 24 s, same nebula engine as the side windows, drifting top to bottom of the canvas (away from the DJ). Flat, no edge darkening. `scripts/render_ceiling.py`. |
| Warp-speed full-room loop | Idea only | Needs screen geometry (OBJ/FBX from C4D) and the ceiling map. Render each surface from one 3D tunnel, or one 360° loop that disguise maps spatially. |

## Repo layout
- `masters/`: full-res loops (H.264; convert to HAP for disguise). Lava looks in `masters/lava/` (neon) and `masters/lava_classic/`
- `stills/`: full-res still plates
- `previews/`: small review copies
- `source/`: clips from Flow
- `scripts/`: the generators below

## Scripts (in the cloud workspace, /home/claude/portal)
- `render2.py`: side loops B and C.
- `grade.py`: Pillars regrade and wide plate.
- `widefill.py`: nebula fill for the plate sides.
- `render_ceiling.py`: ceiling loop (960 × 5760).
- `flowloop.py`: turns a Flow clip into a 24 s loop (removes push-in, slows down, blends the loop point, replaces stars).
- `lava.py`: lava lamp loop for any screen size (`seed=`, `nopools`, `classic` palette, `fixed` = same blob size on every screen).
- `pillars_flow.py`: flowing-gas loop for A. Use `1280` for the preview and `3840` for the master.

## Convert to ProRes for disguise (run locally)
From the repo folder: `bash scripts/make_prores.sh` (ProRes 422 HQ; pass `2` for plain 422). Output goes to `./prores/`.
One file: `ffmpeg -i INPUT.mp4 -c:v prores_ks -profile:v 3 -vendor apl0 -pix_fmt yuv422p10le -an OUTPUT_PRORES.mov`
Sizes per 24 s loop at 422 HQ: about 1.8 GB upstage, 0.7 GB house left, 1.6 GB ceiling.

## Convert to HAP (run locally)
```
ffmpeg -i INPUT.mp4 -c:v hap -format hap_q -chunks 4 OUTPUT_HAPQ.mov
```
