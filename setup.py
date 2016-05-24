from setuptools import setup
setup(
  name = 'pydmrs',
  packages = ['pydmrs'], # this must be the same as the name above
  version = '1.0.0',
  description = 'A library for manipulating DMRS graphs',
  author = 'Ann Copestake, Guy Emerson, Mike Goodman, Matic Horvat, Alex Kuhnle, Ewa Muszyńska',
  author_email = 'gete2@cam.ac.uk',
  license = 'MIT',
  url = 'https://github.com/delph-in/pydmrs',
  download_url = 'https://github.com/delph-in/pydmrs/tarball/1.0.0',
  keywords = ['NLP', 'Natural Language Processing', 'Computational Linguistics', 'Semantics'],
  install_requires = [
    'pydelphin'
  ]
)