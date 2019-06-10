#python setup.py build_ext --inplace
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy as np
import os
# python setup.py build_ext --inplace
os.environ["CC"] = "gcc" 
os.environ["CXX"] = "gcc"


setup(
  name = {'trololo'},
  cmdclass = {'build_ext': build_ext},
  ext_modules = cythonize("pricing_fast.pyx"),
)

