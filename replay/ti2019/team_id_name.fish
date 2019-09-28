#!/usr/bin/fish
#
# Extract team IDs from the .csv and query OpenDota for their names.
# Note, their logo can be accessed at https://steamcdn-a.akamaihd.net/apps/dota2/images/team_logos/2586976.png


for teamid in (tail -n +2 ti9.csv | awk 'BEGIN{FS=","} {print $8 ; print $9}' | sort -uh)
    echo $teamid,(wget --quiet -O- https://api.opendota.com/api/teams/{$teamid} | jq '.name')
end >team_id_name.csv
