import os
from setuptools import setup, find_packages

VERSION = '1.0.3'

setup(
  name = 'pydmrs',
  version = VERSION,
  description = 'A library for manipulating DMRS graphs',
  author = 'Ann Copestake, Guy Emerson, Mike Goodman, Matic Horvat, Alex Kuhnle, Ewa Muszyńska',
  author_email = 'gete2@cam.ac.uk',
  license = 'MIT',
  url = 'https://github.com/delph-in/pydmrs',
  download_url = 'https://github.com/delph-in/pydmrs/tarball/'+VERSION,
  keywords = ['NLP', 'Natural Language Processing', 'Computational Linguistics', 'Semantics'],
  packages = find_packages().append('examples'),
  data_files = [('configs', ['configs/'+filename for filename in os.listdir('configs')])],
  install_requires = [
    'pydelphin'
  ]
)