from setuptools import setup
from subprocess import run, PIPE

# Consistent version as AUR
count = run(["git", "rev-list", "--count", "HEAD"], stdout=PIPE).stdout.splitlines()[0].decode('utf-8')
commit = run(["git", "rev-parse", "--short", "HEAD"], stdout=PIPE).stdout.splitlines()[0].decode('utf-8')
VERSION = "%s.%s" % (count, commit)
# print(VERSION)

share_files = [
('usr/share/bash-completion/completions', ['neopo/neopo-completion'])
]

script_files = ['neopo/neopo']


setup(
   name='neopo',
   version=VERSION,
   description='A lightweight solution for local Particle development.',
   author='Nathan Robinson',
   author_email='nrobinson2000@me.com',
   packages=['neopo'],
   data_files=share_files,
   scripts = script_files

#  install_requires=['foo', 'bar'], #external packages as dependencies
)