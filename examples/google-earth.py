import heatmap
import random

hm = heatmap.Heatmap()
pts = [(random.uniform(-77.012, -77.050), random.uniform(38.888, 38.910)) for x in range(100)]
hm.heatmap(pts)
hm.saveKML("wash-dc.kml")
