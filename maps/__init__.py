import os.path

import numpy as np
import cv2


def homography(origin, target):
    N = len(target)
    assert N >= 4

    # This calculation is from the paper, A Plane Measuring Device
    # by A. Criminisi, I. Reid, A. Zisserman.  For more details, see:
    # http://www.robots.ox.ac.uk/~vgg/presentations/bmvc97/criminispaper/
    A = np.zeros((N*2,9))
    for i in range(N):
        x, y = origin[i]
        X, Y = target[i]
        A[2*i+0] = x, y, 1, 0, 0, 0, -x*X, -y*X, -X
        A[2*i+1] = 0, 0, 0, x, y, 1, -x*Y, -y*Y, -Y

    U, s, V = np.linalg.svd(A)

    if np.abs(V[-1,-1]) < 1e-10:
        raise ValueError("Points are likely extremely collinear, giving up since the result will be wrong.")

    h = V[-1] / V[-1,-1]
    return h.reshape((3,3))


def transform(H, pts):
    pts_homog = np.c_[pts, np.ones(len(pts))]
    pts_homog = np.dot(pts_homog, H.T)
    return pts_homog[:,:-1] / pts_homog[:,-1:]


def cv2world(cs, vs):
    # Just in case someone also gives the Z value, we don't care.
    cs = np.array(cs)[:,:2]
    vs = np.array(vs)[:,:2]
    # This is by trial and error and differs from what it should be in theory.
    # coords = cs*127 + vs - 16384
    # From here: https://github.com/spheenik/clarity-analyzer/blob/master/src/main/java/skadistats/clarity/analyzer/main/icon/EntityIcon.java
    coords = (cs*[128, -128] + vs*[1, -1] + [-16384, 16384]) / 8192.
    return coords


def cv2pix(H, cs, vs):
    return transform(H, cv2world(cs, vs))


class Map(object):

    def __init__(self, fname, towercoords, towerpixels, shrink=None):
        # Good sources for map image are:
        # https://dota2.gamepedia.com/Map
        # https://devilesk.com/dota2/maps
        # and guide on creating one: https://devilesk.com/blog/creating-a-dota-map-image
        towerpixels = np.array(towerpixels, float)
        towercoords = np.array(towercoords, float)

        self.img_orig = cv2.imread(fname)[:,:,::-1]  # BGR->RGB
        self.H_orig = homography(towercoords, towerpixels)
        if shrink is None:
            self.img = self.img_orig
            self.H = self.H_orig
        else:
            self.img = cv2.resize(self.img_orig, None, None, fx=shrink, fy=shrink, interpolation=cv2.INTER_LANCZOS4)
            self.H = homography(towercoords, towerpixels*shrink)

    def cv2pix(cs, vs):
        return cv2pix(self.H, cs, vs)


def get_map_722(shrink=None):
    # Unfortunately, we don't have a 7.22 png yet.
    # But it's fine, only the Dire T2 mid tower moved bit and few tiny camp changes.
    fname = os.path.join(os.path.dirname(__file__), 'map-7.20.jpg')

    TOWER_CV = np.array([
        [ 96,  80, 130, 144.000000,  32.000000, 127.968742],  # Rad Bot T3
        [ 90,  94, 130, 224.000000, 208.000000, 128.000000],  # Rad Mid T3
        [ 76, 100, 130,  64.000000, 176.000000, 128.000000],  # Rad Top T3
        [126,  78, 130, 152.000000,  80.000000,   0.000000],  # Rad Bot T2
        [166,  80, 130,  60.000000,  16.000000,   0.000000],  # Rad Bot T1
        # [100, 106, 130, 111.968742, 159.968750,   0.000000],  # Rad Mid T2  (this is 722 position)
        [ 78, 120, 130, 240.000000, 152.000000,   0.000000],  # Rad Top T2
        [ 78, 142, 130, 144.000000,  24.000000,   0.000000],  # Rad Top T1
        [ 82,  90, 130, 176.000000,   0.000000, 127.968742],  # Rad Top T4
        [166, 164, 130,  79.968742, 168.000000, 127.968742],  # Dir Top T4
        [128, 174, 130,   0.000000, 128.000000,   0.000000],  # Dir Top T2
        [ 90, 174, 130, 191.968750, 128.000000,   0.000000],  # Dir Top T1
        [146, 144, 130, 192.000000,  63.968750,   0.000000],  # Dir Mid T2
        [132, 132, 130,  11.968750, 139.968750,   0.000000],  # Dir Mid T1
        [176, 130, 130,  64.000000, 127.968742,   0.000000],  # Dir Bot T2
        [176, 150, 130, 192.000000, 215.968750, 127.968742],  # Dir Bot T3
        [154, 172, 130, 223.968750, 144.000000, 128.000000],  # Dir Top T3
        [160, 156, 130, 176.000000, 175.000000, 128.000000],  # Dir Mid T3
        [168, 162, 130, 159.968750,  79.968742, 127.968742],  # Dir Bot T4
        [ 84,  86, 130, 240.000000, 184.000000, 127.968742],  # Rad Bot T4
        [114, 116, 128, 248.000000, 128.000000, 255.968750],  # Rad Mid T1
        [176, 114, 130, 125.312500,  63.250000,   0.000000],  # Dir Bot T1
    ])

    # TODO: TOWER_PIXELS.
    # Hand-annotated on the above image.
    # X goes left->right, Y goes top->bottom
    TOWER_PIXELS = np.array([
        [1033, 3488],  # Rad Bot T3
        [ 868, 3000],  # Rad Mid T3
        [ 390, 2820],  # Rad Top T3
        [1975, 3540],  # Rad Bot T2
        [3208, 3493],  # Rad Bot T1
        # [1228, 2727],  # Rad Mid T2  (this is 720-721 position)
        [ 497, 2195],  # Rad Top T2
        [ 474, 1538],  # Rad Top T1
        [ 605, 3181],  # Rad Top T4
        [3208,  822],  # Dir Top T4
        [2000,  525],  # Dir Top T2
        [ 857,  524],  # Dir Top T1
        [2610, 1470],  # Dir Mid T2
        [2130, 1823],  # Dir Mid T1
        [3223, 1890],  # Dir Bot T2
        [3552, 1245],  # Dir Bot T3
        [2866,  582],  # Dir Top T3
        [3045, 1070],  # Dir Mid T3
        [3290,  906],  # Dir Bot T4
        [ 684, 3260],  # Rad Bot T4
        [1624, 2329],  # Rad Mid T1
        [3539, 2409],  # Dir Bot T1
    ])

    # NOTE: For whatever reason, the above homography doesn't look good and is hard to fix.
    #       Instead, I found these coefficients manually to work great:
    class Map722(Map):
        def cv2pix(self, cs, vs, small=False):
            hw = np.array((self.img_small if small else self.img).shape[:2])
            xy_world = cv2world(cs, vs)
            return (xy_world + [0.0, -0.004]) * hw/2 + hw/2

    return Map722(fname, cv2world(TOWER_CV[:,:3], TOWER_CV[:,3:6]), TOWER_PIXELS, shrink)


def get_map_720(shrink=None):
    fname = os.path.join(os.path.dirname(__file__), 'map-7.20.jpg')

    TOWER_CV = np.array([
        # TODO
    ])

    # TODO: TOWER_PIXELS.
    # Hand-annotated on the above image.
    TOWER_PIXELS = np.array([
        # TODO
    ])

    return Map(fname, cv2world(TOWER_CV[:,:3], TOWER_CV[:,3:6]), TOWER_PIXELS, shrink)


def get_map_687(shrink=None):
    fname = os.path.join(os.path.dirname(__file__), 'map-6.87-b.png')

    TOWER_CV = np.array([
        [96, 80, 130, 142.906250, 52.937500, 127.968742],
        [90, 94, 130, 170.375000, 199.500000, 128.000000],
        [76, 100, 130, 39.031250, 174.906250, 128.000000],
        [126, 78, 130, 149.906250, 165.937485, 128.000000],
        [166, 80, 130, 23.937500, 63.406250, 127.968742],
        [100, 106, 130, 34.375000, 30.500000, 0.000000],
        [78, 120, 130, 235.031250, 157.906250, 127.968742],
        [80, 142, 130, 27.031250, 13.906250, 127.968742],
        [82, 90, 130, 149.375000, 3.500000, 127.968742],
        [166, 164, 130, 98.000000, 175.968750, 127.968742],
        [128, 174, 130, 0.000000, 127.968742, 128.000000],
        [90, 174, 130, 128.000000, 127.968742, 127.968742],
        [146, 144, 128, 192.000000, 63.968750, 255.968750],
        [134, 130, 130, 255.968750, 63.968750, 0.000000],
        [176, 114, 130, 64.000000, 127.968742, 127.968742],
        [176, 130, 130, 128.000000, 127.968742, 127.968742],
        [176, 150, 130, 132.000000, 215.968750, 127.968742],
        [154, 172, 130, 224.000000, 143.968750, 128.000000],
        [160, 156, 130, 176.000000, 174.968750, 128.000000],
        [168, 162, 130, 160.000000, 79.968742, 127.968742],
        [84, 86, 130, 242.375000, 159.500000, 127.968742],
        [114, 116, 128, 134.375000, 23.500000, 255.968750],
    ])

    # Sort them by cell, first y then x (oops lol), so we got a repeatable order.
    TOWER_CV = TOWER_CV[np.lexsort((TOWER_CV[:,0], TOWER_CV[:,1]))]

    # Hand-annotated on the above image.
    TOWER_PIXELS = [
        [7430, 13200],
        [3895, 13075],
        [12020,13040],
        [2580, 12275],
        [2260, 11950],
        [3215, 11300],
        [1445, 10615],
        [4260, 10035],
        [13215, 8970],
        [5995, 8865],
        [1855, 8285],
        [8460, 7160],
        [13270, 7090],
        [1890, 5830],
        [9800, 5520],
        [13260, 4650],
        [11430, 3993],
        [12350, 3366],
        [12060, 3050],
        [10775, 2160],
        [3160, 1960],
        [7500, 1940],
    ]

    return Map(fname, cv2world(TOWER_CV[:,:3], TOWER_CV[:,3:6]), TOWER_PIXELS, shrink)
