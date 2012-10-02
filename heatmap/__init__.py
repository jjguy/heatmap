try:
    __version__ = __import__('pkg_resources').get_distribution(__name__).version
except Exception, e:
    __version__ = 'unknown'

from heatmap import Heatmap