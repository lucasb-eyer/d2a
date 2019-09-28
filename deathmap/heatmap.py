#!/usr/bin/env python

# heatmap - High performance heatmap creation in C.
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Lucas Beyer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
__package__ = 'deathmap.heatmap'  # Allow running as script: see PEP366

from argparse import ArgumentParser
from ctypes import CDLL, POINTER, c_float, c_ulong, c_ubyte, c_void_p
from os.path import join as pjoin, dirname
import sys

from PIL import Image

from maps import get_map_722

parser = ArgumentParser(description='Create a heatmap from C/V DOTA2 coordinates.')
parser.add_argument('--scale', type=float, default=None,
                    help='Optionally downscale the image by that factor.')
parser.add_argument('--radius', type=float, default=0.02,
                    help='Radius of the stamp (how many % of map a death leaks into)')
FLAGS = parser.parse_args()


if __name__ == "__main__":
    map722 = get_map_722(shrink=FLAGS.scale)

    # The dimensions of the output image and the stamp radius.
    W, H, _ = map722.img.shape

    # Load the heatmap library using ctypes
    libhm = CDLL(pjoin(dirname(__file__), 'libheatmap.so'))

    # Here, we describe the signatures of the various functions.
    # It wasn't necessary in the past, but now crashes without this...
    libhm.heatmap_new.argtypes = [c_ulong, c_ulong]
    libhm.heatmap_new.restype = c_void_p
    libhm.heatmap_stamp_gen.argtypes = [c_ulong]
    libhm.heatmap_stamp_gen.restype = c_void_p
    libhm.heatmap_add_point_with_stamp.argtypes = [c_void_p, c_ulong, c_ulong, c_void_p]
    libhm.heatmap_render_default_to.argtypes = [c_void_p, POINTER(c_ubyte)]
    libhm.heatmap_free.argtypes = [c_void_p]
    libhm.heatmap_stamp_free.argtypes = [c_void_p]

    # Create the large stamp.
    stamp = libhm.heatmap_stamp_gen(c_ulong(round(W * FLAGS.radius)))

    # Create the heatmap object with the given dimensions (in pixel).
    hm = libhm.heatmap_new(W, H)

    # Read all pairs of points and stamp them.
    for line in sys.stdin:
        cx, cy, vx, vy = line.strip().split(' ')
        c = [[int(cx), int(cy)]]
        v = [[float(vx), float(vy)]]
        x, y = map(int, map722.cv2pix(c, v)[0])
        libhm.heatmap_add_point_with_stamp(hm, c_ulong(x), c_ulong(y), stamp)

    # Done drawing, no need for the stamp anymore.
    libhm.heatmap_stamp_free(stamp)

    # This creates an image out of the heatmap.
    # `rawimg` now contains the image data in 32-bit RGBA.
    rawimg = (c_ubyte*(W*H*4))()
    # I actually didn't manage to let it draw onto the map image without crashing.
    # import numpy as np
    # img = np.ones((H, W, 4), np.uint8)
    # img[:,:,:3] = map722.img
    # rawimg = map722.img.ctypes.data_as(POINTER(c_ubyte))
    libhm.heatmap_render_default_to(hm, rawimg)

    # Now that we've got a finished heatmap picture, we don't need the map anymore.
    libhm.heatmap_free(hm)

    # Use the PIL (for example) to make a png file out of that.
    img = Image.frombuffer('RGBA', (W, H), rawimg, 'raw', 'RGBA', 0, 1)
    img.save(sys.stdout.buffer, format='PNG')
