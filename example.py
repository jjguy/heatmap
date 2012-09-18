import heatmap
import random

if __name__ == "__main__":    
    pts = []
    for x in range(400):
        pts.append((random.random(), random.random() ))

    print "Processing %d points..." % len(pts)

    hm = heatmap.Heatmap()
    hm.heatmap(pts, "classic.png")
