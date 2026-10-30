# paper doll reel

a claude code skill that turns photos of your face and screenshots of your outfits into a big-head paper doll stop-motion reel (1080x1920). the dolls walk on the spot, a crayon writes each look's name in kid handwriting, starbursts pop behind them, and it ends on your call to action with a car driving off.

made by [@getgitgirl](https://instagram.com/getgitgirl).

## new to claude code?

follow the [easy guide](GUIDE.md). it goes from zero to a finished reel, no coding needed.

## install

open claude code and paste:

```
install the paper doll reel skill from github.com/nicolapocock/paper-doll-reel, then set up everything it needs (the python packages and ffmpeg) and tell me when it's ready
```

or in terminal:

```bash
npx skills add nicolapocock/paper-doll-reel
```

it needs python 3 with `pillow numpy scipy "rembg[cpu]"` (in a virtual environment) and `ffmpeg`. [SKILL.md](skills/paper-doll-reel/SKILL.md) has the setup commands.

## use it

put your face photos and outfit screenshots in a folder, then ask:

```
use the paper doll reel skill to make me a reel from the photos in [folder]. show me the stills before you render.
```

there's an example config in [examples/looks.json](examples/looks.json).

## tested

tested on a mac (python 3.14) on 2026-10-30 from a clean install. a cut-out takes about 3 to 25 seconds once the model has downloaded, stills take 4 seconds, and a 14-second reel renders in about a minute. windows and linux are untested.
