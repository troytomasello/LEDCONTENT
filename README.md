# Retro 70s Space Party: LED Content Notes

## Working preferences
- **Previews only by default:** 720p-class H.264 at roughly 1280 px wide and a few MB. Never send masters unless asked.
- **Masters stay in the cloud workspace.** They're delivered on request when bandwidth allows.
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
| Ceiling | 28 LED panels in 5 rows, 140 tiles | **960 × 5760 raster.** Tile layout is in the ceiling raster Troy supplied (re-attach still needed). |

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
| Interior plate (look 1) | Troy, in C4D | Flat-on camera at 3840 × 1536 with the porthole as an alpha. |
| Ceiling | Waiting | Canvas is 960 × 5760; needs the raster to see the tile layout. |
| Warp-speed full-room loop | Idea only | Needs screen geometry (OBJ/FBX from C4D) and the ceiling map. Render each surface from one 3D tunnel, or one 360° loop that disguise maps spatially. |

## Repo layout
- `masters/`: full-res loops (H.264; convert to HAP for disguise)
- `stills/`: full-res still plates
- `previews/`: small review copies
- `scripts/`: the generators below

## Scripts
- `render2.py`: side loops B and C.
- `grade.py`: Pillars regrade and wide plate.
- `widefill.py`: nebula fill for the plate sides.
- `pillars_flow.py`: flowing-gas loop for A. Use `1280` for the preview and `3840` for the master.

## Convert to HAP (run locally)
```
ffmpeg -i INPUT.mp4 -c:v hap -format hap_q -chunks 4 OUTPUT_HAPQ.mov
```
