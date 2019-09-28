#!/usr/bin/fish

# Pipe the file into this script.

while read -la line
    wget -O  replays/(string split ' ' $line)[1].dem.bz2 (string split ' ' $line)[2]
end
