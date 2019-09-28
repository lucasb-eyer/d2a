import requests
import sys

player_id = int(sys.argv[1])

def params(**kw):
    if "ODOTA_API_KEY" in os.environ:
        return dict(api_key=os.environ['ODOTA_API_KEY'], **kw)
    else:
        return dict(**kw)

r = requests.get("https://api.opendota.com/api/players/{}/matches".format(player_id), params=params(
    patch = 41,  # 7.22, see https://raw.githubusercontent.com/odota/dotaconstants/master/json/patch.json
    is_radiant = 1,
    # Other possibilities not yet used:
    # hero_id = None,
    # with_hero_id = None,
))

game_infos = r.json()
game_details = {}

for gi in game_infos:
    mid = gi["match_id"]
    details = requests.get("https://api.opendota.com/api/matches/{}".format(mid), params=params()).json()
    game_details[mid] = details
    try:
        print(mid, details["replay_url"])
    except KeyError:
        print("Missing replay_url for match {}".format(mid), file=sys.stderr)
        print(details, file=sys.stderr)
