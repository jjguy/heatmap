#heatmap.py v1.1 20100326
from PIL import Image,ImageChops,ImageDraw
import os
import random
import math
import sys
import colorschemes
import ctypes
import heatmap

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


class Heatmap:
    """
    Create heatmaps from a list of 2D coordinates.
    
    Heatmap requires the Python Imaging Library. The way I'm using PIL is
    almost atrocious.  I'm embarassed, but it works, albeit slowly.

    Coordinates autoscale to fit within the image dimensions, so if there are 
    anomalies or outliers in your dataset, results won't be what you expect. 

    The output is a PNG with transparent background, suitable alone or to overlay another
    image or such.  You can also save a KML file to use in Google Maps if x/y coordinates
    are lat/long coordinates. Make your own wardriving maps or visualize the footprint of 
    your wireless network.  
 
    Most of the magic starts in heatmap(), see below for description of that function.
    """
    def __init__(self):
        self.minXY = ()
        self.maxXY = ()
        # if you're reading this, it's probably because this 
        # hacktastic garbage failed.  sorry.  I deserve a jab or two via @jjguy.

        # establish the right library name, based on platform and arch.  Windows
        # are pre-compiled binaries; linux machines are compiled during setup.
        libname = "cHeatmap.so"
        if "nt" in os.name:
            libname = "cHeatmap-x86.dll"
            import platform
            if "64" in platform.architecture()[0]:
                libname = "cHeatmap-x64.dll"
        # now rip through everything in sys.path to find 'em.  Should be in site-packages 
        # or local dir
        for d in sys.path:
            if os.path.isfile(os.path.join(d, libname)):
                self._heatmap = ctypes.cdll.LoadLibrary(os.path.join(d, libname))

    def heatmap(self, points, fout, dotsize=150, opacity=128, size=(1024,1024), scheme="classic"):
        """
        points  -> an iterable list of tuples, where the contents are the 
                   x,y coordinates to plot. e.g., [(1, 1), (2, 2), (3, 3)]
        fout    -> output file for the PNG
        dotsize -> the size of a single coordinate in the output image in 
                   pixels, default is 150px.  Tweak this parameter to adjust 
                   the resulting heatmap.
        opacity -> the strength of a single coordiniate in the output image.  
                   Tweak this parameter to adjust the resulting heatmap.
        size    -> tuple with the width, height in pixels of the output PNG 
        scheme  -> Name of color scheme to use to color the output image.
                   Use schemes() to get list.  (images are in source distro)
        """
        
        self.dotsize = dotsize
        self.opacity = opacity
        self.size = size
        self.imageFile = fout
 
        if scheme not in self.schemes():
            tmp = "Unknown color scheme: %s.  Available schemes: %s"  % (scheme, self.schemes())
            raise Exception(tmp)

        arrPoints = self._convertPoints(points)
        arrScheme = self._convertScheme(scheme)
        arrFinalImage = self._allocOutputBuffer()

        self._heatmap.tx(arrPoints, len(points)*2, size[0], size[1], dotsize, 
                         arrScheme, arrFinalImage, opacity)
        img = Image.frombuffer('RGBA', (self.size[0], self.size[1]), arrFinalImage, 'raw', 'RGBA', 0, 1)
        img.save(fout, "PNG")

    def _allocOutputBuffer(self):
        return (ctypes.c_ubyte*(self.size[0]*self.size[1]*4))()

    def _convertPoints(self, pts):
        """ flatten the list of tuples, convert into ctypes array """

        #TODO is there a better way to do this??
        flat = []
        for i,j in pts:
           flat.append(i)
           flat.append(j)
        #build array of input points
        arr_pts = (ctypes.c_float*(len(pts)*2))(*flat)
        return arr_pts
    
    def _convertScheme(self, scheme):
        """ flatten the list of RGB tuples, convert into ctypes array """

        #TODO is there a better way to do this??
        flat = []
        for r,g,b in colorschemes.schemes[scheme]:
            flat.append(r)
            flat.append(g)
            flat.append(b)
        arr_cs = (ctypes.c_int*(len(colorschemes.schemes[scheme])*3))(*flat)
        return arr_cs

    def saveKML(self, kmlFile):
        """ 
        Saves a KML template to use with google earth.  Assumes x/y coordinates 
        are lat/long, and creates an overlay to display the heatmap within Google
        Earth.

        kmlFile ->  output filename for the KML.
        """

        tilePath = os.path.basename(self.imageFile)
        """
        north = self.maxXY[1]
        south = self.minXY[1]
        east = self.maxXY[0]
        west = self.minXY[0]
        """ 
        bytes = KML % (tilePath, north, south, east, west)
        file(kmlFile, "w").write(bytes)

    def schemes(self):
        """
        Return a list of available color scheme names.
        """
        return colorschemes.schemes.keys() 

if __name__ == "__main__":
    pts = []
    for x in range(400):
        pts.append((random.random(), random.random() ))

    print "Processing %d points..." % len(pts)

    hm = Heatmap()
    hm.heatmap(pts, "classic.png") 
