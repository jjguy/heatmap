#heatmap.py v1.1 20100326
from PIL import Image,ImageChops,ImageDraw
import os
import random
import math
import sys
import colorschemes
import ctypes
import platform

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
    def __init__(self, libpath = None):
        self.minXY = ()
        self.maxXY = ()
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
                    self._heatmap = ctypes.cdll.LoadLibrary(os.path.join(d, libname))

        if not self._heatmap:
            raise Exception("Heatmap shared library not found in PYTHONPATH.")

    def heatmap(self, points, fout, dotsize=150, opacity=128, size=(1024,1024), scheme="classic", area=None):
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
        area    -> Specify bounding coordinates of the output image. Tuple of 
                   tuples: ((minX, minY), (maxX, maxY)).  If None or unspecified, 
                   these values are calculated based on the input data.
        """
        
        self.dotsize = dotsize
        self.opacity = opacity
        self.size = size
        self.imageFile = fout
        self.points = points

        if area is not None:
            self.area = area
            self.override = 1
        else:
            self.area = ((0, 0), (0, 0))
            self.override = 0 
         
        if scheme not in self.schemes():
            tmp = "Unknown color scheme: %s.  Available schemes: %s"  % (scheme, self.schemes())
            raise Exception(tmp)

        arrPoints = self._convertPoints(points)
        arrScheme = self._convertScheme(scheme)
        arrFinalImage = self._allocOutputBuffer()

        ret = self._heatmap.tx(arrPoints, len(points)*2, size[0], size[1], dotsize, 
                             arrScheme, arrFinalImage, opacity, self.override, 
                             ctypes.c_float(self.area[0][0]), ctypes.c_float(self.area[0][1]), 
                             ctypes.c_float(self.area[1][0]), ctypes.c_float(self.area[1][0]))

        if not ret:
            raise Exception("Unexpected error during processing.")

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

    def _ranges(self, points):
        """ walks the list of points and finds the 
        max/min x & y values in the set """
        minX = points[0][0]; minY = points[0][1]
        maxX = minX; maxY = minY
        for x,y in points:
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
        tilePath = os.path.basename(self.imageFile)
        if self.override:
            ((east, south), (west, north)) = self.area
        else:
            ((east, south), (west, north)) = self._ranges(self.points) 

        bytes = KML % (tilePath, north, south, east, west)
        file(kmlFile, "w").write(bytes)

    def schemes(self):
        """
        Return a list of available color scheme names.
        """
        return colorschemes.schemes.keys() 

if __name__ == "__main__":
    hm = Heatmap("./cHeatmap.so")

    pts = [(random.random(), random.random()) for x in range(400)]
    hm.heatmap(pts, "01-400-random-defaults.png") 

    pts = [(50, x) for x in range(100)]
    hm.heatmap(pts, "02-100-vert-line-bottom-left.png", area=((0, 0), (200, 200)))

    pts = [(x, 300) for x in range(600, 700)]
    hm.heatmap(pts, "03-100-horz-line-bottom-right-rect.png", size=(800,400), area=((0, 0), (800, 400)))

    pts = [(random.random(), random.random()) for x in range(40000)]
    # this should also generate a warning on stderr of overly dense
    hm.heatmap(pts, "04-80k-random-ds25.png", dotsize=25, opacity=128)

    pts = [(x*100, 50) for x in range(2, 50)]
    pts.extend([(4850, x*100) for x in range(2, 50)])
    pts.extend([(x*100, 4850) for x in range(2, 50)])
    pts.extend([(50, x*100) for x in range(2, 50)])

    hm.heatmap(pts, "05-200-square.png", dotsize=100, area=((0,0), (5000, 5000)))

    hm.heatmap([(50,50),], "06-single-point.png")

    pts = [(random.uniform(-77.012, -77.050), random.uniform(38.888, 38.910)) for x in range(100)]
    hm.heatmap(pts, "07-random-google-earth-wash-dc.png")
    hm.saveKML("07-random-google-earth-wash-dc-data.kml")

    try:
        hm.heatmap([], "08-no-points-THIS-FILE-SHOULD-NOT-EXIST.png")
    except Exception, err:
        pass
    
