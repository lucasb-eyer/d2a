#!/usr/bin/fish
#
# Generate heatmaps for all/main/group/qualif games

if ! test -d deathmap
    echo "Execute this from the folder above `deathmap`."
    exit 1
end

for teamline in (python replay/ti2019/make_team_game_list.py <replay/ti2019/ti9.csv)
    set -l teamarr (string split --no-empty ' ' $teamline)
    echo -ne '\r'$teamarr[1]
    cat deathmap/deaths/$teamarr[2..-1] | python -m deathmap.heatmap $argv[2..-1] > $argv[1]team$teamarr[1]_death_both.png
    # And now the radiant/dire-only versions:
    # The awk removes all fields that match dire, and print $0 prints the full line.
    set -l radiant_only (string split --no-empty ' ' (echo $teamarr[2..-1] | awk '{ for(i=1;i<=NF;i++) if($i ~ "dire") $i="" ; print $0 }'))
    if test -n "$radiant_only"
        cat deathmap/deaths/$radiant_only | python -m  deathmap.heatmap $argv[2..-1] > $argv[1]team$teamarr[1]_death_radiant.png
    end
    set -l dire_only (string split --no-empty ' ' (echo $teamarr[2..-1] | awk '{ for(i=1;i<=NF;i++) if($i ~ "radiant") $i="" ; print $0 }'))
    if test -n "$dire_only"
        cat deathmap/deaths/$dire_only | python -m  deathmap.heatmap $argv[2..-1] > $argv[1]team$teamarr[1]_death_dire.png
    end
end
