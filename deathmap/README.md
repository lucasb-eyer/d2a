# Instruction for creating death heatmaps (deathmaps)

This is very ad-hoc as I'm less interested in a clean setup than in the final results.
Here are notes (mostly for myself) on the steps required to get to the results.

## 1. Get all desired replay files

This is done by various scripts in the `../replay/` folder.
First, getting the list of game IDs for TI9 was done by downloading the HTML page from [datdota.com](datdota.com) and doing various regex and macro magic in vim to transform it to `ti9.csv`.
Then, `download_from_id.py` uses the [opendota.com matches API](https://docs.opendota.com/#tag/matches) in order to get links to the replay files URLs and download them.

## 2. Parse the death locations in the replays

This uses DotaBuff's [manta parser](https://github.com/dotabuff/manta) in Go, it's all done by the `dump_deaths.go` file.
The go file works for a single replay and writes the deaths of `team 2` to stdout and those of `team 3` to stderr, so that we can show both heatmaps independently, and also easily combine them later.
The `dump_all_death_locations.fish` is a fish shell script file looping over all replay files and joining their outputs.

## 3. Generate the heatmap image

This uses my own [libheatmap](https://github.com/lucasb-eyer/libheatmap), called from Python via `ctypes`, so you need to download and `make` that one first.
Then, link the compiled library into here, for example using `ln -s /path/to/libheatmap.so deathmap/`.
The file `heatmap.py` reads DOTA2 cell/vec coordinates, as dumped in the previous step, on `stdin` and renders them onto a heatmap on `stdout`.
To make it look good, there are various flags, such as the stamp radius.

The `heatmap.fish` script is a shorthad to create all three variants of {radiant, dire, both} and {main stage, group stage, qualifier}, and should be called with an output prefix as first argument, followed by anything arguments forwarded to `heatmap.py`, such as `--radius` for example.

### 3.2 Per-team heatmaps
For the per-team heatmaps, the first step is to get a list of all games for each team with the small `make_team_game_list.py` script which extracts them from the `ti9.csv` file.
The `heatmap_team.fish` script then loops through these, and creates all three variants of heatmaps for each, with a little `awk` magic to filter the dire/radiant-only files.

### 3.3 Per-game heatmaps
I also have the `heatmap_game.fish` which creates one heatmap for each game, but these turned out to be less interesting as there is not much aggregation.

## 4. The interactive HTML page

This is kinda intermingled with my homepage scripts which are not open-sourced.
They basically render a Markdown file with some minor processing, then add a header and footer to it.

### 4.2 Reducing image size

Since there are a lot of heatmaps, which need RGBA transparency and are 1 megapixel each, that would use a lot of space and bandwidth as-is.
Even PNG compression is not great, requiring around 800kB for each individual heatmap - so I played around with compressing transparent images a bit.

I tried `pngquant`, `pngnq-s9`, and `webp`.
[WebP](https://en.wikipedia.org/wiki/WebP) is by far the best format, reducing file-size by about 10x without noticeable loss of quality!
I used the following command for converting the PNG files to lossy Webp:

```
><((("> for f in *.png
  cwebp -m 6 -q 90 $f -o (basename -s .png $f).webp
end
```

I played with other quality values: 75 is visibly (slightly) worse at minor reduction in file size, so not worth it.
Similarly for 95, it is almost imperceptibly better at about 25% increase in file size.
Finally, lossless compression (`-lossless -z 9`) reduces image size to about half compared to png.

Out of `pngquant` and `pngnq-s9`, both reduce file-size by about 2x-3x, `pngnq-s9` had very visible color quantization, while `pngquant` had only minor loss in quality.
Thus, I'm using `pngquant` as backup for browsers which don't support webp (safari, hum):

```
><((("> pngquant --strip --speed 1 *.png
```

I automated this in `heatmaps_publish.fish` which converts and moves all relevant files into `img_pub`.
