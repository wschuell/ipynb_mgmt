#!/usr/bin/env python

import re
import sys

from setuptools import setup, find_packages

name = 'ipynb_mgmt'

def version():
    with open(name+'/_version.py') as f:
        return re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read()).group(1)

def requirements():
  with open('requirements.txt') as f:
    return f.readlines()

setup(name=name,
      version=version(),
      packages=find_packages(),
      install_requires=[requirements()],
      author='William Schueller',
      author_email='william.schueller@gmail.com',
      url='https://github.com/wschuell/'+name,
      license='GNU AFFERO GENERAL PUBLIC LICENSE Version 3',
      )
