#!/usr/bin/fish
#
# Compresses the .png heatmap files and also creates a .webp copy.
# This way they are better suited to being served on the web (smaller).

if ! test -d deathmap
    echo "Execute this from the folder above `deathmap`."
    exit 1
end

mkdir -p deathmap/img_pub/{teams,games}

cp deathmap/img/map-7.20-1k.jpg deathmap/img_pub/

for img in deathmap/img/*_{dire,radiant,both}.png deathmap/img/teams/* # deathmap/img/games/*
    echo -ne "\r$img"
    cwebp -quiet -m 6 -q 90 $img -o (string replace .png .webp (string replace /img/ /img_pub/ $img))
    pngquant --strip --speed 1 $img -o (string replace /img/ /img_pub/ $img)
end
