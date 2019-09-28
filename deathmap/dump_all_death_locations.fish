#!/usr/bin/fish
#
# For TI9: replay/ti2019/files/*

mkdir -p deathmap/deaths

for i in (seq (count $argv))
    set -l dem $argv[$i]
    echo -ne "\r$dem ($i/"(count $argv)")"
    go run deathmap/dump_deaths.go $dem >deathmap/deaths/(basename -s .dem.bz2 $dem)_radiant.txt ^deathmap/deaths/(basename -s .dem.bz2 $dem)_dire.txt
end

# Concat all into one file:
# for dem in replay/ti2019/files/*
#     echo -ne "\r$dem"
#     go run dump_deaths.go $dem >>all_deaths_2.txt ^^all_deaths_3.txt
# end
