# paper doll reel: the easy guide

this is how i make my big-head paper doll reels. your face goes on cut-out outfits, the dolls walk on the spot, a crayon writes each look's name in kid handwriting, and the reel ends with a car driving off.

you don't need to code. claude does the cutting out and the animating, you just collect the photos and tell it what you want.

setup takes about 15 minutes the first time. after that, a reel is about 20 minutes of collecting photos and checking stills, plus one minute of rendering.

---

## what you need

- a mac (that's what i've tested it on)
- a paid claude plan (pro or higher)
- 2 or 3 photos of your face, pulling different expressions
- a screenshot of each outfit (one per look)

---

## step 1: get claude code

1. download the claude desktop app from [claude.com/download](https://claude.com/download) and sign in.
2. click the **</>** icon at the top of the app. that's the **code** tab, the version of claude that can work with files on your computer.

## step 2: install the skill

paste this into the code tab and press return:

```
install the paper doll reel skill from github.com/nicolapocock/paper-doll-reel, then set up everything it needs (the python packages and ffmpeg) and tell me when it's ready
```

claude might ask before it installs things. say yes. this is the slow bit, about 10 minutes, and you only do it once.

## step 3: collect your photos

make a folder on your desktop called **paper doll** and put these in it:

- **your face.** 2 or 3 photos, each with a different expression (laughing, a kiss face, a big smile). a plain wall behind you works best, and hair down looks great as a cut-out. the heads are big in these reels, so a face that's pulling an expression is what makes it fun.
- **your outfits.** one screenshot per look, from your camera roll, pinterest or a shop website. a flat-lay showing the whole outfit is perfect, because claude crops each piece out of it.
- **extras (optional):** props like a phone, bag or laptop, and a car or bike for the ending.

## step 4: ask for the reel

paste this, swapping the bits in [brackets] for yours:

```
use the paper doll reel skill to make me a reel from the photos in the paper doll folder on my desktop. 3 looks: [morning at 9am, lunch at 12pm, night out at 8pm]. my brand colours are [#ED84B0 and #EFA6C2] and my fonts are [your fonts, or pick some for me]. the hook is "[spend the day with me]" and it should end with "[comment PAPER]". show me the stills before you render.
```

claude cuts out every piece, builds a doll for each look and shows you a still of each one.

## step 5: check the stills

look at the stills side by side before you say go. check that:

- **the heads are all the same size**
- **the top looks the right size** for the body, not tiny and not huge
- **there's one shoe under each leg**, with both toes pointing the same way
- **there are no white edges or leftover bits** of the photo round anything

if something's off, just say it in normal words, like "the jumper's too big" or "there's a bit of hanger left on the jeans". claude fixes it and shows you again.

## step 6: render it

when the stills look right, say **"render it"**. it takes about a minute, and claude tells you where the mp4 is saved.

## step 7: before you post

- watch it through once. check every photo for anything you wouldn't want online, like your kids, your house number or an open laptop screen.
- add a trending sound in instagram. the reel comes out silent on purpose, so you can pick the audio.

---

## if something goes wrong

- **the first cut-out takes ages.** that's normal. it downloads the cut-out model (about 170 MB) the first time, and after that each piece takes seconds.
- **"externally-managed-environment" error.** tell claude: "set up a virtual environment for the paper doll skill like it says in the skill". the skill explains how.
- **a piece has a white halo or a bit of background left.** say "re-cut the [piece], it still has background round it".
- **the doll looks like a box.** the top is too long. say "tuck the top into the jeans more".

made by [@getgitgirl](https://instagram.com/getgitgirl)
