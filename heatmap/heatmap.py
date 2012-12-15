import os
import sys
import ctypes
import platform
import math

import colorschemes

from PIL import Image

class Heatmap:
    """
    Create heatmaps from a list of 2D coordinates.

    Heatmap requires the Python Imaging Library and Python 2.5+ for ctypes.

    Coordinates autoscale to fit within the image dimensions, so if there are
    anomalies or outliers in your dataset, results won't be what you expect. You
    can override the autoscaling by using the area parameter to specify the data bounds.

    The output is a PNG with transparent background, suitable alone or to overlay another
    image or such.  You can also save a KML file to use in Google Maps if x/y coordinates
    are lat/long coordinates. Make your own wardriving maps or visualize the footprint of
    your wireless network.

    Most of the magic starts in heatmap(), see below for description of that function.
    """

    KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Folder>
    <GroundOverlay>
      <Icon>
        <href>%s</href>
      </Icon>
      <LatLonBox>
        <north>%2.16f</north>
        <south>%2.16f</south>
        <east>%2.16f</east>
        <west>%2.16f</west>
        <rotation>0</rotation>
      </LatLonBox>
    </GroundOverlay>
  </Folder>
</kml>"""

    def __init__(self, libpath=None):
        self.minXY = ()
        self.maxXY = ()
        self.img = None
        # if you're reading this, it's probably because this
        # hacktastic garbage failed.  sorry.  I deserve a jab or two via @jjguy.

        if libpath:
            self._heatmap = ctypes.cdll.LoadLibrary(libpath)

        else:
            # establish the right library name, based on platform and arch.  Windows
            # are pre-compiled binaries; linux machines are compiled during setup.
            self._heatmap = None
            libname = "cHeatmap.so"
            if "cygwin" in platform.system().lower():
                libname = "cHeatmap.dll"
            if "windows" in platform.system().lower():
                libname = "cHeatmap-x86.dll"
                if "64" in platform.architecture()[0]:
                    libname = "cHeatmap-x64.dll"
            # now rip through everything in sys.path to find 'em.  Should be in site-packages
            # or local dir
            for d in sys.path:
                if os.path.isfile(os.path.join(d, libname)):
                    self._heatmap = ctypes.cdll.LoadLibrary(
                        os.path.join(d, libname))

        if not self._heatmap:
            raise Exception("Heatmap shared library not found in PYTHONPATH.")

    def heatmap(self, points, dotsize=150, opacity=128, size=(1024, 1024), scheme="classic", area=None):
        """
        points  -> an iterable list of tuples, where the contents are the
                   x,y coordinates to plot. e.g., [(1, 1), (2, 2), (3, 3)]
        dotsize -> the size of a single coordinate in the output image in
                   pixels, default is 150px.  Tweak this parameter to adjust
                   the resulting heatmap.
        opacity -> the strength of a single coordiniate in the output image.
                   Tweak this parameter to adjust the resulting heatmap.
        size    -> tuple with the width, height in pixels of the output PNG
        scheme  -> Name of color scheme to use to color the output image.
                   Use schemes() to get list.  (images are in source distro)
        area    -> Specify bounding coordinates of the output image. Tuple of
                   tuples: ((minX, minY), (maxX, maxY)).  If None or unspecified,
                   these values are calculated based on the input data.
        """
        self.dotsize = dotsize
        self.opacity = opacity
        self.size = size
        self.points = points

        if area is not None:
            self.area = area
            self.override = 1
        else:
            self.area = ((0, 0), (0, 0))
            self.override = 0

        if scheme not in self.schemes():
            tmp = "Unknown color scheme: %s.  Available schemes: %s" % (
                scheme, self.schemes())
            raise Exception(tmp)

        arrPoints = self._convertPoints(points)
        arrScheme = self._convertScheme(scheme)
        arrFinalImage = self._allocOutputBuffer()

        ret = self._heatmap.tx(
            arrPoints, len(points) * 2, size[0], size[1], dotsize,
            arrScheme, arrFinalImage, opacity, self.override,
            ctypes.c_float(self.area[0][0]), ctypes.c_float(
                self.area[0][1]),
            ctypes.c_float(self.area[1][0]), ctypes.c_float(self.area[1][1]))

        if not ret:
            raise Exception("Unexpected error during processing.")

        self.img = Image.frombuffer('RGBA', (self.size[0], self.size[1]), 
                                    arrFinalImage, 'raw', 'RGBA', 0, 1)
        return self.img

    def _allocOutputBuffer(self):
        return (ctypes.c_ubyte * (self.size[0] * self.size[1] * 4))()

    def _convertPoints(self, pts):
        """ flatten the list of tuples, convert into ctypes array """

        #TODO is there a better way to do this??
        flat = []
        for i, j in pts:
            flat.append(i)
            flat.append(j)
        #build array of input points
        arr_pts = (ctypes.c_float * (len(pts) * 2))(*flat)
        return arr_pts

    def _convertScheme(self, scheme):
        """ flatten the list of RGB tuples, convert into ctypes array """

        #TODO is there a better way to do this??
        flat = []
        for r, g, b in colorschemes.schemes[scheme]:
            flat.append(r)
            flat.append(g)
            flat.append(b)
        arr_cs = (
            ctypes.c_int * (len(colorschemes.schemes[scheme]) * 3))(*flat)
        return arr_cs

    def _ranges(self, points):
        """ walks the list of points and finds the
        max/min x & y values in the set """
        minX = points[0][0]
        minY = points[0][1]
        maxX = minX
        maxY = minY
        for x, y in points:
            minX = min(x, minX)
            minY = min(y, minY)
            maxX = max(x, maxX)
            maxY = max(y, maxY)

        return ((minX, minY), (maxX, maxY))

    def saveKML(self, kmlFile):
        """
        Saves a KML template to use with google earth.  Assumes x/y coordinates
        are lat/long, and creates an overlay to display the heatmap within Google
        Earth.

        kmlFile ->  output filename for the KML.
        """
        if self.img is None:
            raise Exception("Must first run heatmap() to generate image file.")

        tilePath = os.path.splitext(kmlFile)[0] + ".png"
        self.img.save(tilePath)

        if self.override:
            ((east, south), (west, north)) = self.area
        else:
            ((east, south), (west, north)) = self._ranges(self.points)

        bytes = self.KML % (tilePath, north, south, east, west)
        file(kmlFile, "w").write(bytes)

    def schemes(self):
        """
        Return a list of available color scheme names.
        """
        return colorschemes.valid_schemes()
