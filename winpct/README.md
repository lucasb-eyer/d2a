We get game history data from OpenDota, since the public Valve DOTA2 API only returns 500 most recent games, which would clearly not be enough.

This way we get the pro matches:

```
python get_match_data.py --version 7.22 pro >pro_matches_7.22-(date '+%F_%T').csv
```

And this one gives us the pub games for 7.22, 1558742400 being the [unix timestamp](https://www.unixtimestamp.com/index.php) for 2019-05-25T00:00:00+00:00, which is approximately a day after [the 7.22 patch landed](https://dota2.gamepedia.com/Game_Versions).

```
python get_match_data.py --oldest_time 1558742400 pub >pub_matches_7.22-(date '+%F_%T').csv
```

This retrieves the games in batches of 50k, but unfortunately the API sometimes gives us a flaky error (indistinguishable from an actual error), so we need to manually resume several times, extracting the last retrieved game_id from the previous log:

```
python get_match_data.py --oldest_time 1558742400 --resume_id (tail -1 pub_matches_7.22-LAST_FILE_HERE.csv | cut -d',' -f 3) pub >pub_matches_7.22-(date '+%F_%T').csv
```

Finally, we can merge all the trials into a single data file, currently weighing in at 1.3Gb:

```
cat pub_matches_7.22*.csv >pub_matches_7.22-(date '+%F').csv
```
