#heatmap.py v1.0 20091004
from PIL import Image,ImageChops
import os
import random
import math
import sys
import colorschemes

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

        self.minXY, self.maxXY = self._ranges(points)
        dot = self._buildDot(self.dotsize)

        img = Image.new('RGBA', self.size, 'white')
        for x,y in points:
            tmp = Image.new('RGBA', self.size, 'white')
            tmp.paste( dot, self._translate([x,y]) )
            img = ImageChops.multiply(img, tmp)


        colors = colorschemes.schemes[scheme]
        img.save("bw.png", "PNG")
        self._colorize(img, colors)

        img.save(fout, "PNG")

    def saveKML(self, kmlFile):
        """ 
        Saves a KML template to use with google earth.  Assumes x/y coordinates 
        are lat/long, and creates an overlay to display the heatmap within Google
        Earth.

        kmlFile ->  output filename for the KML.
        """

        tilePath = os.path.basename(self.imageFile)
        north = self.maxXY[1]
        south = self.minXY[1]
        east = self.maxXY[0]
        west = self.minXY[0]
        
        bytes = KML % (tilePath, north, south, east, west)
        file(kmlFile, "w").write(bytes)

    def schemes(self):
        """
        Return a list of available color scheme names.
        """
        return colorschemes.schemes.keys() 

    def _buildDot(self, size):
        """ builds a temporary image that is plotted for 
            each point in the dataset"""
        img = Image.new("RGB", (size,size), 'white')
        md = 0.5*math.sqrt( (size/2.0)**2 + (size/2.0)**2 )
        for x in range(size):
            for y in range(size):
                d = math.sqrt( (x - size/2.0)**2 + (y - size/2.0)**2 )
                rgbVal = int(200*d/md + 50)
                rgb = (rgbVal, rgbVal, rgbVal)
                img.putpixel((x,y), rgb)
        return img

    def _colorize(self, img, colors):
        """ use the colorscheme selected to color the 
            image densities  """
        finalVals = {}
        w,h = img.size
        for x in range(w):
            for y in range(h):
                pix = img.getpixel((x,y))
                rgba = list(colors[pix[0]][:3])  #trim off alpha, if it's there.
                if pix[0] <= 254: 
                    alpha = self.opacity
                else:
                    alpha = 0 
                rgba.append(alpha) 

                img.putpixel((x,y), tuple(rgba))
            
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

    def _translate(self, point):
        """ translates x,y coordinates from data set into 
        pixel offsets."""
        x = point[0]
        y = point[1]

        #normalize points into range (0 - 1)...
        x = (x - self.minXY[0]) / float(self.maxXY[0] - self.minXY[0])
        y = (y - self.minXY[1]) / float(self.maxXY[1] - self.minXY[1])

        #...and the map into our image size...
        x = int(x*self.size[0])
        y = int((1-y)*self.size[1])
         
        # the upper-left corner of our dot is placed at
        # the x,y coordinate we provide. 
        # we care about their center.  shift up and left so
        # the center of the dot is at the point we expect.
        x = x - self.dotsize / 2
        y = y - self.dotsize / 2

        return (x,y)

if __name__ == "__main__":
    pts = []
    for x in range(400):
        pts.append((random.random(), random.random() ))

    print "Processing %d points..." % len(pts)

    hm = Heatmap()
    hm.heatmap(pts, "classic.png") 
