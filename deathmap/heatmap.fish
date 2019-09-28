#!/usr/bin/fish
#
# Generate heatmaps for all/main/group/qualif games

if ! test -d deathmap
    echo "Execute this from the folder above `deathmap`."
    exit 1
end

cat deathmap/deaths/*_radiant.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]all_death_radiant.png
cat deathmap/deaths/*_dire.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]all_death_dire.png
cat deathmap/deaths/*.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]all_death_both.png

cat deathmap/deaths/{497{6,7,8,9},498{0,1,2,3,4,5,6}}*_radiant.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]main_death_radiant.png
cat deathmap/deaths/{497{6,7,8,9},498{0,1,2,3,4,5,6}}*_dire.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]main_death_dire.png
cat deathmap/deaths/{497{6,7,8,9},498{0,1,2,3,4,5,6}}*.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]main_death_both.png

cat deathmap/deaths/{496{7,8,9},497{0,1,2,3}}*_radiant.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]group_death_radiant.png
cat deathmap/deaths/{496{7,8,9},497{0,1,2,3}}*_dire.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]group_death_dire.png
cat deathmap/deaths/{496{7,8,9},497{0,1,2,3}}*.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]group_death_both.png

cat deathmap/deaths/{488,489,490}*_radiant.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]qualif_death_radiant.png
cat deathmap/deaths/{488,489,490}*_dire.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]qualif_death_dire.png
cat deathmap/deaths/{488,489,490}*.txt | python -m deathmap.heatmap $argv[2..-1] >$argv[1]qualif_death_both.png
