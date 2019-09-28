#!/usr/bin/fish
#
# Generate heatmaps for every single individual game.

if ! test -d deathmap
    echo "Execute this from the folder above `deathmap`."
    exit 1
end

for game in deathmap/deaths/*_dire.txt
    set -l base (basename -s _dire.txt $game)
    cat deathmap/deaths/{$base}_radiant.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]{$base}_death_radiant.png
    cat deathmap/deaths/{$base}_dire.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]{$base}_death_dire.png
    cat deathmap/deaths/{$base}_{dire,radiant}.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]{$base}_death_both.png
end
