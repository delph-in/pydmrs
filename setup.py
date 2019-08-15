import os
from setuptools import setup, find_packages

VERSION = '1.0.5'

setup(
  name = 'pydmrs',
  version = VERSION,
  description = 'A library for manipulating DMRS graphs',
  author = 'Ann Copestake, Guy Emerson, Michael Wayne Goodman, Matic Horvat, Alex Kuhnle, Ewa Muszyńska',
  author_email = 'gete2@cam.ac.uk',
  license = 'MIT',
  url = 'https://github.com/delph-in/pydmrs',
  download_url = 'https://github.com/delph-in/pydmrs/tarball/'+VERSION,
  keywords = ['NLP', 'Natural Language Processing', 'Computational Linguistics', 'Semantics'],
  packages = find_packages(),
  package_data = {'pydmrs': ['__config__/*.conf']},
  install_requires = [
    'pydelphin >= 1.0.1'
  ]
)
