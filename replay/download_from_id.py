#!/usr/bin/env python3
import pathlib
import requests
import sys


def stdin_or_argv():
    if len(sys.argv) > 1:
        for line in sys.argv[1:]:
            yield line
    else:
        for line in sys.stdin:
            yield line.rstrip()


def params(**kw):
    if "ODOTA_API_KEY" in os.environ:
        return dict(api_key=os.environ['ODOTA_API_KEY'], **kw)
    else:
        return dict(**kw)


if __name__ == "__main__":
    for mid in stdin_or_argv():
        details = requests.get("https://api.opendota.com/api/matches/{}".format(mid), params=params()).json()
        try:
            url = details["replay_url"]
        except KeyError:
            print("Missing replay_url for match {}. Returned info on next line, skipping:".format(mid), file=sys.stderr)
            print(details, file=sys.stderr)
            continue

        r = requests.get(url)
        r.raise_for_status()
        pathlib.Path(mid + ".dem.bz2").write_bytes(r.content)
