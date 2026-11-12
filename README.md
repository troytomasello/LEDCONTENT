# Retro 70s Space Party: LED Content Notes

## Working preferences
- **Previews only by default:** 720p-class H.264 at roughly 1280 px wide and a few MB. Never send masters unless asked.
- **Masters live in the private GitHub repo `troytomasello/ledcontent`** (masters/, stills/, previews/, scripts/). Troy downloads them when bandwidth allows.
- **AI-generated motion:** Troy generates short clips in Flow/Veo; Claude loops them to 24 s, fits them to the screen size, regrades and encodes.
- **Previews first:** the full-res master is rendered only after the preview is approved.
- **Tools:** Troy works in C4D for stills and room renders, and uses Google Flow only for walk-through animations, not screen content.
- **Loops are exactly 24 seconds at 60 fps** (1440 frames) and seamless. Previews are 30 fps to save bandwidth.
- **Playback:** a disguise server. The operator wants **ProRes**, so masters stay as small H.264 in the repo and Troy converts locally with `scripts/make_prores.sh` (422 HQ by default; confirm 422 vs 422 HQ with the operator). Frame rate confirmed: 60 fps..

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

## Deliverables (current: all 60 fps, 24 s)
| Look | Screens | Repo folder | Notes |
|---|---|---|---|
| Nebula drift v04 | B, C, ceiling | `masters/nebula_drift/` | Slow drift, churning clouds, twinkling stars. C is a mirrored crop of B. Ceiling drifts down the canvas (top assumed upstage). |
| Lava neon v03 | A, B, C, ceiling | `masters/lava_neon/` | Neon pink/blue glowing wax, no shine. Blob size scales with each screen's height. Ceiling has no pools. |
| Lava classic v04 (big) | A, B, C, ceiling | `masters/lava_classic/` | Red/orange on periwinkle-indigo (from Troy's lamp photo). Big blobs (150–250 px radius), the same physical size on every screen, about 60–70% wax coverage. B uses 8 blobs, C uses 4. |
| Pillars still v02 | A | `stills/` | Graded Pillars, sides extended with nebula. |
| Pillars from Flow clip v01 | A | `masters/pillars_flow_30fps/` | Still 30 fps and 720p; redo from a 4K Flow export. |

### Open items
- Scenic overlay for A: Troy is making it in Nano Banana (green-screen window); Claude cuts the mask and composites.
- Pillars flowing-gas loop: rejected the procedural version; the Flow-clip route is in progress.
- Confirm the ceiling orientation (top = upstage?) and whether all 150 map slots are real tiles (Troy said 140).
- Confirm every screen has the same pixel pitch (classic lava assumes it does).
- Warp-speed full-room idea: needs screen geometry from C4D.

## Repo layout
- `masters/`: full-res 60 fps loops (H.264). Convert to ProRes with `scripts/make_prores.sh`.
- `stills/`: full-res still plates
- `previews/`: small 30 fps review copies
- `source/`: clips from Flow
- `scripts/`: the generators below

The old 30 fps masters were removed from the folders but remain in the git history.

## Scripts (in the cloud workspace, /home/claude/portal)
- `render2.py`: side loops B and C.
- `grade.py`: Pillars regrade and wide plate.
- `widefill.py`: nebula fill for the plate sides.
- `render_ceiling.py`: ceiling loop (960 × 5760).
- `flowloop.py`: turns a Flow clip into a 24 s loop (removes push-in, slows down, blends the loop point, replaces stars).
- `lava.py`: lava lamp loop for any screen size (`seed=`, `nopools`, `classic` palette, `fixed` = same blob size on every screen, `big`, `nb=` blob count).
- `pillars_flow.py`: flowing-gas loop for A. Use `1280` for the preview and `3840` for the master.

## Convert to HAP (run locally)
```
ffmpeg -i INPUT.mp4 -c:v hap -format hap_q -chunks 4 OUTPUT_HAPQ.mov
```
