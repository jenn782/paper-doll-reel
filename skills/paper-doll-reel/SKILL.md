---
name: paper-doll-reel
description: Make a paper-doll stop-motion reel. Big cut-out heads go on cut-out outfits and walk on the spot, a crayon writes on the screen in kid handwriting, starbursts pop behind, and the reel ends on a CTA and a vehicle exit. Use this for a "big head" or "bubble head" outfit lookbook, a "spend the day with me" or "day in my life" reel built from outfit flat-lays, a paper-doll edit like the Canva / Pinterest lookbooks, or turning outfit screenshots plus head cut-outs into an animated 1080x1920 reel. Use it even when the person doesn't say "paper doll", for example "make my outfits walk", "cut these clothes out and put my head on them", or "lookbook reel with my face".
---

# Paper-doll reel

This makes a short vertical reel (1080x1920, 30 fps) in a paper-doll stop-motion style. Each "look" is built from separate cut-out pieces: a head, a top, the bottoms, one shoe used twice, and optional arms and props. Each look gets a cream torn-paper outline and a soft shadow. Poses swap 6 times a second, so it reads as hand-made stop motion, not a smooth AI edit.

The two scripts do the heavy lifting. Run them, don't rewrite them:
- `scripts/cutout.py` cuts any piece out of a photo or screenshot.
- `scripts/render.py` builds every doll from a `looks.json` and renders the reel.

Both need Python 3 with `pillow numpy scipy rembg`, plus `ffmpeg`. On a Mac, plain `pip install` is often blocked ("externally-managed-environment"), so set up a virtual environment once and run the scripts with its Python:

```bash
python3 -m venv ~/.paper-doll-venv
~/.paper-doll-venv/bin/pip install pillow numpy scipy "rembg[cpu]"
```

Run the scripts as `~/.paper-doll-venv/bin/python scripts/...`. If `ffmpeg` is missing, install it with `brew install ffmpeg`. rembg downloads its model (about 170 MB) the first time it runs, so the first cut-out is slow. After that, a cut-out takes about 3 to 25 seconds.

**Fonts.** `render.py` needs real font files: a handwriting font, a bold font and a mono font. Use the person's brand fonts. If they have none, use the Go Be Creative defaults, all free from Google Fonts: Permanent Marker (handwriting), Anton (bold) and Poppins SemiBold (mono/timeline). Download the .ttf files into a `fonts/` folder and point `fonts.hand`, `fonts.bold` and `fonts.mono` at them with absolute paths (the renderer doesn't expand `~`). A Mac also has a kid-handwriting fallback at `/System/Library/Fonts/Supplemental/ChalkboardSE.ttc`, index 2.

## Workflow

### 1. Collect the pieces
Ask for these, or find them in the files the person mentions:
- **Heads.** 1 to 3 cut-out photos of the person's head with different expressions (laugh, kiss, ooh, smile). Using a different expression per look makes the reel feel alive.
- **Outfits.** Flat-lay screenshots, one per look. A single photo that shows a whole outfit is fine, because you crop each item out of it.
- **Optional extras:**
  - Props, such as a mic, laptop, phone, bag or crayon.
  - A crayon or pen photo, which does the writing.
  - A vehicle for the ending.
  - A folder of their own post screenshots, which scroll behind one look as their "feed".
  - A full-body photo or sticker, either to use whole for a look or to borrow its arms from.

### 2. Cut every piece out
Run `python scripts/cutout.py <in> <out> [--box x0,y0,x1,y1] [--poly "..."] [--keep N] [--mode border]`.
- **Speed:** by default, small screenshots are upscaled to about 1200px on the long side before matting, and big photos are matted as they are. Don't force `--upscale 3` on big photos, because it takes minutes.
- **Flat-lays:** crop each item with `--box` in the source's pixel coordinates. Look at the image first and read the coordinates off it. Draw a labelled grid over it if that helps.
- **Shoes:** cut out only the FRONT shoe of a pair. Use `--poly` around it, in the cut piece's pixel coordinates. The renderer places that one shoe twice, once under each leg. A photographed pair placed whole looks stuck together and can't step.
- **Heads from a normal photo:** use `--box` around the whole head with the shoulders in it, then `--poly` to cut off just below the chin. Keep the full width of the hair and cheeks down to the jaw, and only angle the polygon in under the chin and neck. A tight polygon leaves straight cuts across the cheeks. Check for leftover collar or top under the chin, and set `chin` to about 0.85 for these cuts. Hair worn down looks far better than hair pulled back.
- **Heads that already have a paper outline:** use `--mode border`. It removes only the flat background touching the image edges, so the outline survives.
- **Arms from a body photo:** remove the top they're wearing, then keep the two largest skin pieces (`--keep 2`), or mask by skin colour. Thin slivers of the old top left beside the hands are a common glitch, so check for them.
- **After every cut, check it on a coloured background.** Look for leftovers like hangers, a second shoe's toe, a fake checkerboard or white halos. Re-cut until it's clean. Never fake transparency with a multiply blend.

### 3. Write `looks.json` next to the pieces
Paths in the file are relative to `looks.json`. The colours shown are an example brand palette, so swap in the person's own.

```json
{
  "out": "lookbook.mp4",
  "head_px": 480,
  "colors": {"bg": "#6A4CFF", "burst": "#8F78FF", "ink": "#FFD400", "text": "#F8F6F2", "shadow": "#0A0A0A", "accent": "#FF5A4F", "line": "#F8F6F2"},
  "fonts": {"hand": "fonts/PermanentMarker-Regular.ttf", "hand_index": 0,
            "bold": "fonts/Anton-Regular.ttf", "mono": "fonts/Poppins-SemiBold.ttf"},
  "pen": "parts/crayon.png",
  "hook": ["spend the day", "with me"],
  "looks": [
    {"label": "filming", "time": "9am", "feed": "feed",
     "heads": ["parts/head-laugh.png", "parts/head-kiss.png"],
     "top": "parts/jumper.png", "top_w": 1.0, "bottoms": "parts/jeans.png", "bottoms_w": 0.52,
     "shoe": "parts/shoe.png", "shoe_faces": "right", "shoe_w": 0.4,
     "hand_left": "parts/mic.png", "hand_right": "parts/laptop.png"},
    {"label": "building", "time": "12pm", "body": "parts/full-body.png", "prop": "parts/phone.png", "prop_w": 0.4},
    {"label": "mum mode", "time": "3pm", "heads": ["parts/head-smile.png"], "chin": 0.70,
     "top": "parts/tee.png", "top_w": 0.57, "waist": 0.66, "bottoms": "parts/wide-jeans.png", "bottoms_w": 0.41,
     "shoe": "parts/boot.png", "shoe_w": 0.27, "shoe_ankle": 0.7,
     "arms": "parts/arms.png", "arms_w": 1.3, "arms_y": 0.3, "arms_out": 0.03, "prop": "parts/bag.png", "prop_w": 0.6}
  ],
  "cta": ["want to make one?", "grab the free guide", "link in my", "bio"],
  "ending": {"image": "parts/car.png", "faces": "left", "line": "Go Be Creative"}
}
```

| Field | What it does |
|---|---|
| `head_px` | On-screen head width, the same for every look. Bigger heads make bigger dolls. Lower it if a head touches the label. |
| `*_w` | Each piece's size as a multiple of the head width. Tune these until the top is in proportion to the body. |
| `chin` | How far down the head image the chin sits. Use 0.6 for tight cut-outs and 0.7 for stickers with long hair. |
| `waist` | How far down the top the bottoms start (default 0.75). The top overlaps the waistband. |
| `shoe_faces` | Which way the toe points in the cut shoe. The renderer flips it so both shoes point left. |
| `shoe_ankle` | Where the ankle sits across the shoe, from 0 to 1. Adjust it until the ankle sits under the leg. |
| `shoe_spread` | Pushes the two shoes apart, so they never stack when the legs swing in. |
| `walk` / `stride` | Trousers are split at the crotch automatically and the legs swing ±`stride`°. Set `walk: false` for a skirt or dress. |
| `body` | A whole full-body sticker used instead of separate parts. It wobbles rather than walks. |
| `arms`, `arms_w`, `arms_y`, `arms_out` | Two arms (one image) drawn BEHIND the top and nudged outward, so they hang from the sleeves. |
| `hand_left` / `hand_right` | Props held at the cuffs. |
| `prop` | A prop that bobs beside the doll. |
| `time` | When any look has a time, a day timeline runs across the top and a dot hops between the times. |
| `feed` | A folder of screenshots that scrolls as a 3-column grid behind that look, washed in the background colour. |
| `pen` | The crayon image, tip pointing RIGHT. It writes the hook and each label. Without it, the text still writes on. |
| `ending.faces` | Which way the vehicle faces. It always drives the way it faces: in from the right, out to the left. |

### 4. Check the stills, then render
1. Run `python scripts/render.py looks.json --stills`. It writes `look-N.png` for each look. Look at them side by side and check:
   - **Heads:** all the same size.
   - **Top:** in proportion to the body, not tiny and not huge.
   - **Shoes:** one under each leg, toes the same way.
   - **Glitches:** no slivers or halos.
   - **Arms:** present when the top is sleeveless.
2. Fix the cut-outs or the `*_w` values, then check the stills again.
3. Run `python scripts/render.py looks.json` for the full render. It takes about a minute for 14 seconds of reel.
4. Pull 6 frames into a contact sheet and check them before handing over. Check against the "Taste rules" section below.

## Taste rules (learned the hard way)
- **Only the head is out of proportion.** The body and clothes keep real human proportions: tee about shoulder width, torso about half a head-width tall, waist-to-floor about 0.85 head-width. A long top over long trousers turns the doll into a box. Tuck the top into the waistband (`waist` around 0.6) when the top is long, and hang the arms behind the top so they come out of the sleeves.
- **Big heads.** The charm is a bubble head on a small paper body. Every look's head should be the same width on screen. Small heads read as "tiny on screen".
- **Walking, not sliding.** Trousers are split into two legs that swing round the hips, with one shoe under each leg. The front foot lifts a little. The waistband overlaps the leg tops, so no seam shows.
- **Real crayon, kid handwriting.** The crayon tip leads the writing letter by letter, then flies off. The letters wobble in size, angle and baseline. A neat font is wrong.
- **Brand colours for everything designed.** The background, starbursts, ink, timeline and CTA all use the brand palette. A dusty pink that's "nearly" the brand colour reads as off. Starbursts look best a lighter tint of the background.
- **Graphics never sit over copy.** The label, timeline and CTA stay clear of dolls, props and the vehicle. The feed fades out before it reaches the label.
- **Copy.** Put the hook and labels in the person's own words, lowercase for socials, and end on a CTA keyword. Check every line reads naturally out loud.
- **Privacy.** Before anything is posted, check the feed screenshots and photos for kids, house numbers, locations or open screens. ffmpeg strips the metadata from the render (`-map_metadata -1`).

## Adapting
- **More or fewer looks:** add or remove entries in `looks`. The timeline spaces itself out.
- **Dropping beats:** remove `hook`, `cta` or `ending` and that beat is skipped.
- **Another brand:** change `colors`, the fonts, and the pen and vehicle images. Nothing else is tied to one brand.
