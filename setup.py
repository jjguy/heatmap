from distutils.core import setup, Extension
from distutils.command.install import install
from distutils.command.build_ext import build_ext
import os
import glob

# sorry for this, welcome feedback on the "right" way.
# shipping pre-compiled bainries on windows, have
# to hack things up here.
class mybuild(build_ext):
    def run(self):
        if "nt" in os.name:
            print "On Windows, skipping build_ext."
            return
        build_ext.run(self)

class post_install(install):
    def run(self):
        install.run(self)

        # on windows boxes, manually copy pre-compiled DLLs to 
        # site-packages (or wherever the module is being installed)
        if "nt" in os.name:
            basedir = os.path.dirname(__file__)
            for f in glob.glob(os.path.join(basedir, "*.dll")):
                src = os.path.join(basedir, f)
                dst = os.path.join(self.install_lib, f)
                open(dst, "wb").write(open(src, "rb").read())

module1 = Extension('cHeatmap', 
                    sources= [ 'heatmap.c',])

setup(name='heatmap',
      version='2.0',
      description='Module to create heatmaps',
      author='Jeffrey J. Guy',
      author_email='jjg@case.edu',
      url='http://jjguy.com/heatmap/',
      license='MIT License',
      packages=['heatmap',],
      py_modules=['heatmap.colorschemes',],
      ext_modules=[module1,],
      cmdclass={'install': post_install,
                'build_ext': mybuild},
     )

