#!/usr/bin/env python3
from argparse import ArgumentParser
import csv
import requests
import os
import sys
import time

parser = ArgumentParser(description='Query matchups')
# I tested that it worked with 100k but not with 1M. Let's use 50k as safety buffer.
parser.add_argument('--batch_size', type=int, default=50000,
                    help='How many matches to retrieve at once before pausing (default: 50000).')
parser.add_argument('--oldest_time', type=int,
                    help='Unix timestamp of the oldest match to retrieve. For example 1558742400 is when 7.22 appeared, see also https://dota2.gamepedia.com/Game_Versions')
parser.add_argument('--oldest_id', type=int,
                    help='Match ID of the oldest match to retrieve.')
parser.add_argument('--resume_id', type=int,
                    help='Start fetching from this match ID, useful to resume.')
parser.add_argument('--version', type=str,
                    help='The version number, such as 7.22 (only works for pro).')
parser.add_argument('which', choices=['pub', 'pro'],
                    help='Whether to query pub matches, or pro matches.')
args = parser.parse_args()

FILTER = " "
if args.oldest_time is not None:
    FILTER += " AND start_time > {} ".format(args.oldest_time)
if args.oldest_id is not None:
    FILTER += " AND match_id > {} ".format(args.oldest_id)


if args.which == 'pro':
    FILTER += " AND (leagues.tier = 'premium' OR leagues.tier = 'professional') "
    if args.version is not None:
        FILTER += " AND (match_patch.patch >= '{version}' AND match_patch.patch <= '{version}') ".format(version=args.version)

COLUMNS = ['match_id', 'match_seq_num', 'radiant_win', 'start_time', 'duration', 'lobby_type', 'game_mode', 'cluster']
if args.which == 'pub':
    COLUMNS += ['lobby_type', 'game_mode', 'avg_mmr', 'num_mmr', 'avg_rank_tier', 'num_rank_tier']

# Used in order to iterate through batches of matches.
UPPER_ID_FILTER = "AND match_id < {id}"

if args.which == 'pub':
    QUERY = ("""
WITH match_ids AS (SELECT match_id FROM public_matches
                   WHERE TRUE
                   """ + FILTER + """
                   {upper_id_filter}
                   ORDER BY match_id DESC LIMIT {limit})
SELECT * FROM (SELECT """ + ', '.join(COLUMNS) + """ FROM public_matches WHERE match_id IN (SELECT match_id FROM match_ids)) matches
JOIN (SELECT match_id, string_agg(hero_id::text, ':') radiant_team FROM public_player_matches WHERE match_id IN (SELECT match_id FROM match_ids) AND player_slot <= 127 GROUP BY match_id) radiant_team USING(match_id)
JOIN (SELECT match_id, string_agg(hero_id::text, ':') dire_team FROM public_player_matches WHERE match_id IN (SELECT match_id FROM match_ids) AND player_slot > 127 GROUP BY match_id) dire_team USING(match_id)
ORDER BY match_id DESC
""").strip()

elif args.which == 'pro':
    QUERY = ("""
WITH match_ids AS (
    SELECT match_id FROM matches
    JOIN match_patch using(match_id)
    JOIN leagues using(leagueid)
    WHERE TRUE
      """ + FILTER + """
      {upper_id_filter}
    ORDER BY match_id DESC LIMIT {limit})
SELECT * FROM (SELECT """ + ', '.join(COLUMNS) + """ FROM matches WHERE match_id IN (SELECT match_id FROM match_ids)) matches
JOIN (SELECT match_id, string_agg(concat(hero_id::text, ' ', account_id::text), ':') radiant_team FROM player_matches WHERE match_id IN (SELECT match_id FROM match_ids) AND player_slot <= 127 GROUP BY match_id) radiant_team USING(match_id)
JOIN (SELECT match_id, string_agg(concat(hero_id::text, ' ', account_id::text), ':') dire_team FROM player_matches WHERE match_id IN (SELECT match_id FROM match_ids) AND player_slot > 127 GROUP BY match_id) dire_team USING(match_id)
ORDER BY match_id DESC
""").strip()


def params(**kw):
    if "ODOTA_API_KEY" in os.environ:
        return dict(api_key=os.environ['ODOTA_API_KEY'], **kw)
    else:
        return dict(**kw)

writer = csv.DictWriter(sys.stdout, ['radiant_team', 'dire_team'] + COLUMNS)
writer.writeheader()

n = 0
last_id = args.resume_id
print('   ', end='', flush=True, file=sys.stderr)
while True:
    print('\b\b\b...', end='', flush=True, file=sys.stderr)
    query = QUERY.format(limit=args.batch_size, upper_id_filter=UPPER_ID_FILTER.format(id=last_id) if last_id else '')
    r = requests.get('https://api.opendota.com/api/explorer', params=params(sql=query))
    r.raise_for_status()

    rows = r.json()['rows']
    n += len(rows)
    for row in rows:
        writer.writerow(row)
        last_id = row['match_id']
        print('\rRetrieved {}, oldest id: {}   '.format(n, last_id), end='', flush=True, file=sys.stderr)
    sys.stdout.flush()

    # Check if we're at the end.
    if len(rows) < args.batch_size:
        break

    time.sleep(2.0)  # Not spam them too much.

print('\nDone, ciao!', file=sys.stderr)
